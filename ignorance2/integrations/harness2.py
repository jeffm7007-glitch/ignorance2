"""ignorance2 x Google Harness2 (google-research/harness2).

Wrap Harness2's Propose -> Probe -> Compose loop with the ignorance2 gate:
the gate scores every probe output against your fact layer, so a harness
that improves itself still answers to fixed ground truth.

Why this pairing exists
-----------------------
Harness2 lets an agent optimize its own harness (prompts, tools, memory,
skills) while model weights stay fixed. That is powerful — and it is also
a Goodhart machine: the harness will drift toward whatever the probe
scores. If the probe only scores task success, the harness learns to
sound right. The ignorance2 gate is the fixed external check the harness
cannot optimize away, because the fact layer does not change when the
harness does. A self-modifying system needs at least one component that
never modifies itself. This is that component.

Duck-typed: works with any probe result that is a string or exposes its
answer text as ``.text`` / ``.output`` / ``.answer``. There is no
dependency on harness2 itself — import this gate inside your own runner.

MIT. See ../docs/harness2-use-case.md for the full use case.
"""

from ignorance2.core import check, load_facts, split_claims


def _text_of(probe):
    if isinstance(probe, str):
        return probe
    for attr in ("text", "output", "answer", "response"):
        value = getattr(probe, attr, None)
        if isinstance(value, str):
            return value
    raise TypeError(
        "probe result must be a str or expose .text/.output/.answer/.response"
    )


class Harness2Gate:
    """Score Harness2 probe outputs against a fixed fact layer.

    Parameters
    ----------
    fact_paths:
        JSON file(s) of facts, or ``(":memory:",)`` / a sqlite path via
        ``sqlite=...`` for the SQL fact layer. Same sources the CLI uses.
    strict:
        Block when *any* claim scores PARTIAL. Default: block only
        UNSUPPORTED claims (ship the rest with their calibrated frames).
    block_risk:
        Risk threshold that hard-blocks an output regardless of verdict.

    Use it in a Harness2 runner
    ---------------------------
    >>> gate = Harness2Gate(("facts/my-product.json",))
    >>> for probe_result in harness2.run(task):
    ...     score = gate.score_probe(probe_result)
    ...     if score["blocked"]:
    ...         continue  # never compose from a blocked probe
    ...     harness2.compose(probe_result, score=score["mean_risk"])

    And to compare two harness candidates honestly::

        gate.is_better(baseline_probe, candidate_probe)  # True only if the
            # candidate is better AND no less honest
    """

    def __init__(self, fact_paths=None, strict=False, block_risk=0.35,
                 confidence=0.9):
        # confidence: how confident probe outputs sound, on average. The
        # doctrine demo number. Raise it for overconfident agents — risk
        # grows quadratically, which is the entire point.
        self.confidence = confidence
        self.facts = []
        for path in (fact_paths or ()):
            self.facts.extend(load_facts(path))
        if not self.facts:
            raise ValueError(
                "Harness2Gate needs a fact layer — self-improvement without "
                "ground truth is just faster drift."
            )
        self.strict = strict
        self.block_risk = block_risk

    def score_probe(self, probe):
        """Gate one probe output. Returns a dict, never raises on content."""
        text = _text_of(probe)
        results = check(split_claims(text, self.confidence), self.facts)
        if not results:
            return {
                "text": text,
                "claims": 0,
                "mean_risk": 0.0,
                "verdicts": [],
                "blocked": False,
            }
        mean_risk = sum(r.risk for r in results) / len(results)
        blocked = any(
            r.verdict == "UNSUPPORTED" or r.risk >= self.block_risk
            for r in results
        )
        if self.strict:
            blocked = blocked or any(r.verdict == "PARTIAL" for r in results)
        return {
            "text": text,
            "claims": len(results),
            "mean_risk": round(mean_risk, 4),
            "verdicts": [
                {"claim": r.claim, "verdict": r.verdict, "risk": r.risk}
                for r in results
            ],
            "blocked": blocked,
        }

    def is_better(self, baseline_probe, candidate_probe):
        """True only if the candidate improves the score AND stays honest.

        Honesty first: a candidate that scores better by drifting from the
        fact layer (any blocked claim) is not better. It is a regression
        wearing a better number.
        """
        base = self.score_probe(baseline_probe)
        cand = self.score_probe(candidate_probe)
        if cand["blocked"]:
            return False
        return cand["mean_risk"] < base["mean_risk"]
