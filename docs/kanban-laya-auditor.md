# Kanban Lead Machine — Laya decisions, K3 supervision (2026-10-24)

The lead machine runs ON this repo's doctrine: Laya decides, K3 audits, the
kanban directs. Slower than a swarm, accurate by construction. Quality over
count — every lead gated before it ships.

## Stack seats (from README doctrine)
- **Laya** (decision layer) = `python3 -m ignorance2 check --facts <fact-layer> --strict`.
  Every outbound claim, every lead record, every SMS draft is split into atomic
  claims and gated. UNSUPPORTED never ships. Abstention is the failure mode.
- **K3 Auditor** (standing audit lane) = `graded-audit` bench re-runs: sampled
  station outputs re-checked against sources on a schedule; scorecards logged
  in `bench-realdata/results-*.md` style.
- **Kanban** (Hermes ops) = board state in the workspace (`kanban-workers/`),
  cards move: backlog → running → review → done. One station per fire.

## Operating rules (Jeff rulings 2026-10-24)
1. One station at a time, cron `:17 */2`. No groupthink, no parallel runs.
2. PRIMARY lead source: 1–3 star business reviews of SEO/GEO/AEO agencies.
   Agencies cluster in metros; their burned clients are nationwide — harvest
   national, territory math at sale time.
3. Success metric = qualified, gated leads — not record count.
4. The Trail: never lie, only imply, let prospects draw conclusions. The gate
   enforces it mechanically.
5. Permanent bans: Reddit · Instantly.ai · comments on any property · RVM spend.
6. Free tools only; OpenRouter free-tier LLMs for swarm-class jobs
   (key pending — human-in-the-loop step, batched).

## Quality gate (Station 6)
Each lead record must carry: source_url (attributed), complaint quote (their
words, not ours), budget if stated, agency burned, and a gate verdict.
Records failing the gate are quarantined, never deleted — the auditor reviews
the quarantine.

i² = −1. The gate decides; the bench supervises; the kanban remembers.