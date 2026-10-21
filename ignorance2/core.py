"""Core scoring. The arithmetic of the brand, implemented.

Pipeline per answer:
  1. split the answer into atomic claims (caller supplies them, or use
     split_claims() on sentence boundaries)
  2. for each claim, score evidence against the fact layer
  3. combine with the model's stated confidence -> hallucination risk
  4. verdict: VERIFIED / PARTIAL / UNSUPPORTED

The scoring is deliberately simple and inspectable. Fancy retrieval is a
deployment concern; the harness's job is the gate, and the gate must be
auditable by a human with a calculator.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Iterable


class Verdict(str, Enum):
    VERIFIED = "VERIFIED"      # evidence >= 0.80 — ship it
    PARTIAL = "PARTIAL"        # 0.50 <= evidence < 0.80 — ship with the frame attached
    UNSUPPORTED = "UNSUPPORTED"  # evidence < 0.50 — do not ship as fact


@dataclass
class Fact:
    """One record in the fact layer. `source` is not optional — an
    unsourced fact is a rumour, and rumours are how hallucinations breed."""
    id: str
    text: str
    source: str
    tags: list[str] = field(default_factory=list)


@dataclass
class Claim:
    text: str
    confidence: float = 1.0  # the model's own stated confidence, 0..1


@dataclass
class ClaimResult:
    claim: str
    confidence: float
    evidence: float
    risk: float
    verdict: str
    matched_facts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with",
    "is", "are", "was", "were", "be", "at", "by", "we", "our", "it", "its",
    "this", "that", "from", "as", "per",
}

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+(?:[.'-][a-z0-9]+)*", text.lower())
        if t not in _STOPWORDS and len(t) > 1
    }


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUM_RE.findall(text)}


def evidence_score(claim_text: str, fact: Fact) -> float:
    """Precision-weighted overlap between a claim and one fact record.

    The fact record is allowed to know MORE than the claim — extra detail in
    the layer must not dilute a true claim (claim verification is about
    whether the fact covers the claim, not whether the texts are equal
    length). So precision leads, recall sets a floor, and a shared exact
    number adds a boost: numbers are the hallucination's favourite hiding
    place, so a matched number counts double."""
    ct, ft = _tokens(claim_text), _tokens(fact.text)
    if not ct or not ft:
        return 0.0
    overlap = ct & ft
    precision = len(overlap) / len(ct)
    recall = len(overlap) / len(ft)
    score = precision * (0.5 + 0.5 * recall)
    cn, fn = _numbers(claim_text), _numbers(fact.text)
    if cn and fn and cn & fn:
        score = min(1.0, score + 0.10)
    return round(score, 4)


def best_evidence(claim_text: str, facts: Iterable[Fact]) -> tuple[float, list[str]]:
    """Return (evidence, matched_fact_ids) for the strongest fact record."""
    best, ids = 0.0, []
    for f in facts:
        s = evidence_score(claim_text, f)
        if s > best:
            best, ids = s, [f.id]
        elif s == best and s > 0:
            ids.append(f.id)
    return best, ids


def risk(confidence: float, evidence: float) -> float:
    """The i-squared term: confidence^2 * ignorance gap.

    A 0.95-confidence claim on 0.30 evidence: risk 0.63 — imaginary, loudly.
    A 0.60-confidence claim on 0.95 evidence: risk 0.02 — real, quietly."""
    return round(max(0.0, min(1.0, confidence)) ** 2 * (1.0 - evidence), 4)


def verdict_for(evidence: float) -> Verdict:
    if evidence >= 0.80:
        return Verdict.VERIFIED
    if evidence >= 0.50:
        return Verdict.PARTIAL
    return Verdict.UNSUPPORTED


def check(claims: Iterable[Claim], facts: Iterable[Fact]) -> list[ClaimResult]:
    """Gate every claim. Only VERIFIED/PARTIAL results ship; PARTIAL ships
    only with its frame and calibrated probability attached."""
    facts = list(facts)
    out = []
    for c in claims:
        ev, ids = best_evidence(c.text, facts)
        out.append(ClaimResult(
            claim=c.text,
            confidence=round(c.confidence, 4),
            evidence=ev,
            risk=risk(c.confidence, ev),
            verdict=verdict_for(evidence=ev).value,
            matched_facts=ids,
        ))
    return out


def split_claims(answer: str, confidence: float = 1.0) -> list[Claim]:
    """Sentence-split an AI answer into atomic claims. In production, pair
    this with your extraction model — the harness gates, extraction feeds."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if len(s.strip()) > 3]
    return [Claim(text=s, confidence=confidence) for s in sentences]


def load_facts(path: str) -> list[Fact]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return [Fact(id=r["id"], text=r["text"], source=r["source"],
                 tags=r.get("tags", [])) for r in raw]


def render_report(results: list[ClaimResult]) -> str:
    lines = ["claim | confidence | evidence | risk | verdict"]
    for r in results:
        lines.append(f"{r.claim[:60]} | {r.confidence:.2f} | {r.evidence:.2f} | {r.risk:.2f} | {r.verdict}")
    blocked = sum(1 for r in results if r.verdict == Verdict.UNSUPPORTED.value)
    lines.append(f"\n{len(results)} claims checked · {blocked} blocked as UNSUPPORTED")
    return "\n".join(lines)
