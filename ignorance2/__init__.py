"""ignorance² — anti-hallucination engineering harness (reference implementation).

The doctrine, in one line:

    i^2 = -1

Imaginary input, squared, cancels into a real result. Every answer a model
wants to ship is treated as potentially imaginary. The harness squares the
claim against what the system ACTUALLY knows — the fact layer — and only
what survives ships.

risk = confidence^2 * (1 - evidence)

The imaginary part of a confident claim is the confidence squared times the
ignorance gap. High confidence with thin evidence is the hallucination
signature. This module measures exactly that, per claim, before anything
reaches a customer.

Zero dependencies. Python 3.10+. MIT license.
"""

from .core import Claim, Fact, Verdict, ClaimResult, check, risk, evidence_score, best_evidence, split_claims, load_facts, render_report
from .sources import init_sqlite, add_fact_sql, load_facts_sql

__version__ = "0.3.0"
__all__ = ["Claim", "Fact", "Verdict", "ClaimResult", "check", "risk",
           "evidence_score", "best_evidence", "split_claims", "load_facts",
           "render_report", "init_sqlite", "add_fact_sql", "load_facts_sql"]
