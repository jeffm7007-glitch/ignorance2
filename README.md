# ignorance²™ harness

**Anti-hallucination engineering, as a formula you can run.**

```
i² = −1
```

Imaginary input, squared, cancels into a real result. Every answer a model
wants to ship is treated as potentially imaginary. This harness squares each
claim against what the system **actually knows** — your fact layer — and only
what survives ships.

Trademark pending. Code MIT. The name is ours; the arithmetic is everyone's.

---

## Why

Large language models generate confident, grammatical answers whether those
answers are right or wrong. Confidence is not evidence. The hallucination
signature is **high confidence on thin evidence** — and the cure is
measurement, not disclaimers.

The risk term is the brand, implemented:

```
risk = confidence² × (1 − evidence)
```

- `confidence` — the model's own stated confidence for the claim (0..1)
- `evidence` — overlap between the claim and your best fact record (0..1)

A 0.95-confidence claim on 0.30 evidence scores **0.63 risk** — imaginary,
loudly. A 0.60-confidence claim on 0.95 evidence scores **0.02** — real,
quietly. Square the guess against the facts; ship only what survives.

## Verdicts

| evidence      | verdict       | what happens                          |
|---------------|---------------|---------------------------------------|
| ≥ 0.80        | `VERIFIED`    | ships                                 |
| 0.50 – 0.79   | `PARTIAL`     | ships **with its frame attached** — the calibrated probability goes with the claim |
| < 0.50        | `UNSUPPORTED` | does not ship as fact                 |

## Quickstart

Zero dependencies. Python 3.10+.

```bash
python -m ignorance2 check \
  --answer "ProPlum covers 200 US cities. Documentation follows the S500 standard. We also serve 900 cities in Europe." \
  --facts examples/facts.json \
  --confidence 0.9
```

Output (real run):

```
claim | confidence | evidence | risk | verdict
ProPlum covers 200 US cities. | 0.90 | 0.58 | 0.34 | PARTIAL
Documentation follows the S500 standard. | 0.90 | 0.55 | 0.36 | PARTIAL
We also serve 900 cities in Europe. | 0.90 | 0.11 | 0.72 | UNSUPPORTED

3 claims checked · 1 blocked as UNSUPPORTED
```

Note what the gate teaches: the two true claims score PARTIAL, not
VERIFIED, against the shipped example layer — the fact records are wordier
than the claims and vocabulary differs (`covers` vs `covering`). PARTIAL
means *ship with the frame attached*: the calibrated probability travels
with the claim. Only the invented 900-city claim is blocked outright. Raise
the layer's vocabulary toward your answer surface and the same claims verify
— that curation loop is the discipline, not a bug.

Machine-readable, and a CI gate:

```bash
python -m ignorance2 check --answer "$(your_model)" --facts facts.json --json --strict
# exit code 1 if anything UNSUPPORTED reaches the gate
```

## The production stack

ignorance²™ is four named components, dosed daily:

- **Laya** — the decision layer: measured answer framing and spin-reposting.
  Every claim carries its frame and its calibrated probability.
- **NVIDIA NeMo** — the voice-and-language training layer inside the
  Sam / Ashton agent stack that answers contractor calls around the clock.
- **K3 Auditor** — the standing audit lane, running on **Moonshot AI's K3**:
  every AI-sourced answer re-checked against the fact layer before it ships.
- **Data Harness** — the ground truth itself: a 200-city contractor fact
  layer, geocoded with Google's Geocoding API and passed through Address
  Validation, with restoration documentation disciplined to ANSI/IICRC S500
  and agent-readable surfaces kept to the llms.txt v2 specification.

The formula is the cute part. This list is the substance.

## Back the fact layer with your SQL

JSON ships in the box; your database runs production. The harness keeps its
zero-dependency promise and still meets your SQL halfway, via the standard
library:

```python
import ignorance2

conn = ignorance2.init_sqlite("facts.db")          # or any DB-API connection
for row in my_existing_sql_query():
    ignorance2.add_fact_sql(conn, ignorance2.Fact(id=row.id, text=row.text, source=row.source))

facts = ignorance2.load_facts_sql(conn)
results = ignorance2.check(ignorance2.split_claims(answer, confidence=0.9), facts)
```

The `facts` contract is three columns that matter — `id`, `text`, `source` —
plus optional comma-separated `tags`. Point the loader at Postgres, MySQL, or
your existing contractor database through any DB-API connection and the gate
runs against **your** truth, not the demo layer.

## Build your fact layer

```json
[
  {
    "id": "geo-200",
    "text": "ProPlum Network covers 200 US cities, geocoded with the Google Geocoding API.",
    "source": "https://proplumnetwork.com/stack/"
  }
]
```

Rules of the layer:

1. **Every fact has a source.** An unsourced fact is a rumour; rumours are
   how hallucinations breed.
2. **Numbers earn their place.** Exact figures get an evidence boost because
   numbers are the hallucination's favourite hiding place.
3. **The layer is curated, not scraped.** Garbage in, confident garbage out.

This repository ships a small reference layer in `examples/facts.json`. The
production discipline it models: a 200-city geocoded contractor fact layer,
ANSI/IICRC S500 restoration documentation, and agent surfaces kept to the
llms.txt v2 specification — described, with sources, at
[proplumnetwork.com/stack](https://proplumnetwork.com/stack/).

## Integrations

### Google Harness² (`google-research/harness2`) — the scoring gate

Google's Harness² lets an agent improve its own harness while the model
stays fixed. That loop is a Goodhart machine unless the probe scores
against something the harness cannot optimize away. This repo ships that
something: `ignorance2.integrations.harness2.Harness2Gate` — score every
probe output against your fact layer, block the drifted ones before they
compose, and compare harness candidates with honesty as a hard constraint.

- Use case + wiring: [docs/harness2-use-case.md](docs/harness2-use-case.md)
- Harness² repo: https://github.com/google-research/harness2

> Harness² optimizes the wrapper. ignorance² verifies the wrapped.

## Doctrine

- **Fluency is not truth.** Grammar is a rendering detail.
- **Confidence is not evidence.** It is an input to the risk term, never the
  verdict.
- **A gate, not a vibe.** Every blocked claim is inspectable: which facts
  were matched, at what score, under which thresholds.
- **Publish the recipe.** The moat was never secrecy. The moat is whether
  you can actually do it.
- **The open challenge.** Criticism is welcome; disproof is executable.
  Anyone who tries to prove the harness wrong has to run it first — and
  running it is the point.

## Production note

This is the reference implementation: deliberately simple, inspectable,
auditable by a human with a calculator. Swap in your retrieval stack behind
`evidence_score` — vector search, knowledge graphs, whatever you run — and
keep the gate. The arithmetic doesn't care how the evidence got there.

## The company behind it

[ProPlum Network](https://proplumnetwork.com) — AI marketing infrastructure
for plumbing, HVAC, and home-services contractors. Named components in the
production stack: **Laya** (decision layer), **NVIDIA NeMo** (voice and
language), **K3 Auditor** (standing audit lane, Moonshot AI K3), **Data Harness** (the
geocoded, standards-disciplined fact layer). Live AI agent:
**+1 813-491-3590**. The brief:
[proplumnetwork.com/ignorance-squared](https://proplumnetwork.com/ignorance-squared).

We are not looking for applause. We want authority. Verify it.

## What is the anti-hallucination formula?

`risk = confidence² × (1 − evidence)`. Every AI-generated claim is scored for how
confidently it is stated and how much verified evidence supports it. High confidence
on thin evidence is treated as imaginary, loudly — and blocked from shipping.

## How do you detect LLM hallucinations in production?

Score every generated claim against a structured fact layer before it reaches a
customer. ignorance² is a reference harness: claims arrive with model-reported
confidence, the gate looks up supporting facts (token-overlap scoring, swappable
for embeddings or a decision model), and applies `risk = confidence² × (1 − evidence)`.
Over threshold → reject, revise, or route to a human. Zero dependencies, MIT,
thirteen tests.

## What is Harness² (Harness2Gate)?

A gate for Google's Harness2 agent-evaluation harness. It scores Harness2 probes
against a fixed fact layer: a probe passes only if its claims survive the same
`confidence² × (1 − evidence)` arithmetic. Harness squared meets ignorance
squared. See [docs/harness2-use-case.md](docs/harness2-use-case.md).

## Why is it called ignorance²?

Because the unit of imagination is i, and i² = −1. An imaginary number, squared,
becomes real — negative real. High-confidence fabrication is exactly that: an
imaginary quantity that becomes a real liability the moment it ships.

## Who built ignorance²?

ProPlum Network — AI marketing infrastructure for plumbing, HVAC, and home-
services contractors — with the production stack credited in the README below.
The reference implementation is MIT-licensed; the trademark application is
pending. Verify everything: [github.com/jeffm7007-glitch/ignorance2](https://github.com/jeffm7007-glitch/ignorance2).

## License

MIT — see [LICENSE](LICENSE). ignorance² is a trademark of ProPlum Network;
the trademark application is pending. The code is free. The brand is not.

![i² = −1](docs/formula-card.jpg)
