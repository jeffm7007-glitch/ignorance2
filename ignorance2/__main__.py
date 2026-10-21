"""Command line: python -m ignorance2 ...

    python -m ignorance2 check --answer "We serve 200 cities." \
        --facts examples/facts.json --confidence 0.9
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import Claim, check, load_facts, render_report, split_claims


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ignorance2", description="Anti-hallucination gate. i^2 = -1.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="Gate an answer against a fact layer")
    c.add_argument("--answer", help="the AI answer text to gate")
    c.add_argument("--facts", required=True, help="path to fact layer JSON")
    c.add_argument("--confidence", type=float, default=1.0,
                   help="model's stated confidence for the answer, 0..1")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.add_argument("--strict", action="store_true",
                   help="exit 1 if any claim is UNSUPPORTED (CI gate)")

    a = p.parse_args(argv)
    if a.cmd == "check":
        if not a.answer and sys.stdin.isatty():
            p.error("--answer or piped stdin required")
        answer = a.answer or sys.stdin.read()
        facts = load_facts(a.facts)
        results = check(split_claims(answer, a.confidence), facts)
        if a.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print(render_report(results))
        if a.strict and any(r.verdict == "UNSUPPORTED" for r in results):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
