# Use case: scoring Google Harness² probes with the ignorance² gate

**Google Harness²** (`google-research/harness2`, Apache-2.0; paper: *Harness²:
Recursive Agent Harnessing for an Open World*, arXiv 2610.14224) lets an agent
improve its own harness — prompts, tools, memory, skills — while the model
weights stay fixed. A Propose → Probe → Compose loop tests harness changes
against real tasks and keeps what works.

It is a genuinely strong idea. It is also a Goodhart machine.

## The gap Harness² does not close

When a harness improves against a probe score, it drifts toward whatever the
probe measures. If the probe measures task success, the harness learns to
*sound* right — fluency inflates, grounding decays, and nothing in the loop
notices, because the loop and the drift are the same thing. Google ships the
framework; what the probe *scores against* is still the operator's job.

That is the ignorance² slot.

## The pairing

> **Harness² optimizes the wrapper. ignorance² verifies the wrapped.**
> A harness that improves itself still needs one component that never does:
> the truth.

The ignorance² gate sits on every probe output before it can be composed into
the next harness generation:

```python
from ignorance2.integrations.harness2 import Harness2Gate

gate = Harness2Gate(("facts/my-product.json",))

for probe_result in harness2.run(task):
    score = gate.score_probe(probe_result)
    if score["blocked"]:
        continue                    # never compose from a blocked probe
    harness2.compose(probe_result, score=score["mean_risk"])
```

And when comparing two harness candidates, honesty wins ties:

```python
gate.is_better(baseline_probe, candidate_probe)
# True only if the candidate improves the score AND stays honest —
# a candidate that scores better by drifting from the fact layer
# is a regression wearing a better number.
```

The fact layer can be JSON files or your own SQL (stdlib `sqlite3` in the
box; Postgres/MySQL through the same three-column contract — the data harness
runs on the owner's database, not the vendor's).

## What the demo shows

`examples/facts.json` ships a small product fact layer. Point the gate at any
probe output containing a claim like *"we also serve 900 cities in Europe"*
and the gate blocks it: no fact in the layer supports it, the confidence is
fluent and high, so the risk term does its one job. Deterministic, runnable
in ten seconds:

```bash
python -m ignorance2 examples/facts.json -s 0.9 -v
```

We publish the wiring, not vanity benchmarks. Numbers you generate yourself
inside your own Harness² loop are worth more than ours — run it on your
probes and quote what you measured.

## Why Google should want this on the radar

Harness²'s open-world premise assumes tasks nobody planned for. The moment an
agent self-modifies in an open world, verification has to come from outside
the loop. ignorance² is a small, MIT-licensed, zero-dependency outside — the
fitness function that cannot be gamed by the thing it scores, because the
fact layer does not change when the harness does.

- Harness² repo: https://github.com/google-research/harness2
- This gate: https://github.com/jeffm7007-glitch/ignorance2
- The doctrine: https://proplumnetwork.com/ignorance-squared
