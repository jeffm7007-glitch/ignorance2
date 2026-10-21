"""The gate, under test. If the arithmetic breaks, the brand breaks."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ignorance2 import (Claim, Fact, Verdict, check, evidence_score, risk,
                        split_claims, init_sqlite, add_fact_sql, load_facts_sql)


FACTS = [
    Fact(id="geo-200", text="ProPlum Network covers 200 US cities, geocoded with the Google Geocoding API.", source="https://proplumnetwork.com/stack/"),
    Fact(id="s500", text="Restoration documentation is disciplined to the ANSI/IICRC S500 water-damage standard.", source="https://proplumnetwork.com/stack/"),
]


class TestEvidence(unittest.TestCase):
    def test_supported_claim_verifies(self):
        results = check([Claim("ProPlum covers 200 US cities.", 0.9)], FACTS)
        self.assertEqual(results[0].verdict, Verdict.VERIFIED.value)
        self.assertIn("geo-200", results[0].matched_facts)
        # residual risk stays on the label: 0.9^2 * (1 - 0.85) = 0.1215
        self.assertLess(results[0].risk, 0.20)

    def test_invented_claim_blocked(self):
        results = check([Claim("ProPlum operates in 900 cities worldwide.", 0.95)], FACTS)
        self.assertEqual(results[0].verdict, Verdict.UNSUPPORTED.value)
        self.assertGreater(results[0].risk, 0.5)

    def test_confidence_squared_punishes_overreach(self):
        # Same thin evidence: the confident claim is riskier than the humble one.
        high = risk(0.95, 0.30)
        low = risk(0.60, 0.30)
        self.assertGreater(high, low)
        self.assertAlmostEqual(high, round(0.95 ** 2 * 0.70, 4))

    def test_number_match_boosts_evidence(self):
        boosted = evidence_score("Coverage spans 200 cities.", FACTS[0])
        plain = evidence_score("Coverage spans many cities.", FACTS[0])
        self.assertGreater(boosted, plain)

    def test_partial_band(self):
        r = check([Claim("S500 standard documentation for restoration.", 0.8)], FACTS)
        self.assertIn(r[0].verdict, {Verdict.PARTIAL.value, Verdict.VERIFIED.value})
        self.assertGreaterEqual(r[0].evidence, 0.50)


class TestCLI(unittest.TestCase):
    def test_strict_mode_exits_nonzero_on_unsupported(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump([{"id": "f1", "text": "The sky over the office is blue today.", "source": "https://example.com"}], fh)
            path = fh.name
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "ignorance2", "check", "--answer",
                 "ProPlum covers 900 cities. The sky over the office is blue today.",
                 "--facts", path, "--strict"],
                capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), ".."))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("UNSUPPORTED", proc.stdout)
        finally:
            os.unlink(path)


class TestSplitting(unittest.TestCase):
    def test_atomic_claims(self):
        claims = split_claims("We cover 200 cities. Documentation follows S500.")
        self.assertEqual(len(claims), 2)


class TestSQLSource(unittest.TestCase):
    def test_sqlite_roundtrip_and_gate(self):
        conn = init_sqlite(":memory:")
        add_fact_sql(conn, Fact(id="geo-200",
                                text="ProPlum Network covers 200 US cities, geocoded with the Google Geocoding API.",
                                source="https://proplumnetwork.com/stack/"))
        facts = load_facts_sql(conn)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].id, "geo-200")
        results = check([Claim("ProPlum covers 900 cities.", 0.9)], facts)
        self.assertEqual(results[0].verdict, Verdict.UNSUPPORTED.value)
        conn.close()

    def test_disk_path_schema(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            path = fh.name
        try:
            conn = init_sqlite(path)
            add_fact_sql(conn, Fact(id="s500", text="S500 standard.", source="https://example.com"))
            self.assertEqual(len(load_facts_sql(conn)), 1)
            conn.close()
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
