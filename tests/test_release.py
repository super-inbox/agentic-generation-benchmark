"""Release invariants and role-boundary regressions."""
import json
import tempfile
import unittest
from pathlib import Path

from draftbench.audit import report, validate
from draftbench.common import DEFAULT_DATA, contained, read_rows
from draftbench.prepare import build_request, prepare


class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = report(DEFAULT_DATA)

    def test_release_integrity_and_replay(self):
        result = validate(DEFAULT_DATA)
        self.assertTrue(result["ok"])
        self.assertEqual(result["rfq_scores_replayed"], 100)

    def test_archive_denominators_are_not_model_run_counts(self):
        counts = self.result["counts"]
        self.assertEqual((counts["archive_observations"], counts["archive_protocol_units"], counts["archive_id_lineages"]), (333, 301, 272))
        self.assertEqual(counts["historical_associations"], 32)
        self.assertEqual((counts["brief_bank_briefs"], counts["brief_bank_conditions"], counts["rfq_scenarios"]), (35, 43, 40))
        self.assertEqual(counts["rfq_scored_runs"], 99)

    def test_paired_and_strict_denominators(self):
        metrics = self.result["rfq"]
        self.assertEqual((metrics["paired_39"]["astra"]["success_count"], metrics["paired_39"]["claude"]["success_count"]), (36, 34))
        self.assertEqual(metrics["paired_39"]["claude"]["success_denominator"], 39)
        self.assertEqual((metrics["strict_36"]["astra"]["success_count"], metrics["strict_36"]["claude"]["success_count"]), (33, 32))
        self.assertEqual(metrics["strict_36"]["claude"]["success_denominator"], 36)
        self.assertEqual(metrics["extension"]["claude"]["infrastructure_excluded"], 1)

    def test_timeout_does_not_become_an_observed_quality_zero(self):
        rows = read_rows(DEFAULT_DATA / "results/archive_units.jsonl")
        missing = [u["models"]["claude"] for u in rows if u["group"] == "brief-bank-v03" and not u["models"]["claude"]["completed"]]
        self.assertEqual(len(missing), 8)
        self.assertTrue(all(v["score"] is None or v["score"]["lower"] is None for v in missing))

    def test_initial_bundle_excludes_future_feedback_and_gold(self):
        request, files = build_request(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot")
        self.assertEqual(len(files), 1)
        self.assertIsNone(request["preference_memory"])
        self.assertNotIn("feedback", request)
        self.assertNotIn("rubric", request)
        self.assertNotIn("A 还是太网红，C 又太老", json.dumps(request, ensure_ascii=False))
        reference, _ = build_request(DEFAULT_DATA, "design", "DAB-L4-BID-001@reference_grounded")
        personalized, _ = build_request(DEFAULT_DATA, "design", "DAB-L4-BID-001@personalized")
        self.assertEqual(len(reference["assets"]), 4)
        self.assertIsNone(reference["preference_memory"])
        self.assertIsNotNone(personalized["preference_memory"])

    def test_rfq_bundle_is_only_role_prompt_and_opening(self):
        request, files = build_request(DEFAULT_DATA, "rfq", "RFQ-IC-001")
        self.assertEqual(files, [])
        self.assertEqual(request["messages"][-1]["content"], "Hi, I need some pictures for the shop. Can you help?")
        self.assertNotIn("fields", request)
        self.assertNotIn("36 for the first collection", json.dumps(request))

    def test_export_is_self_contained_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "candidate"
            prepare(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", output)
            data = json.loads((output / "request.json").read_text())
            for asset in data["assets"]:
                self.assertTrue((output / asset["path"]).is_file())
            self.assertEqual(len(list(output.rglob("*.json"))), 1)
            with self.assertRaises(ValueError):
                prepare(DEFAULT_DATA, "rfq", "RFQ-IC-001", output)

    def test_path_traversal_is_rejected(self):
        for path in ("../secret", "/etc/passwd", "assets/../../secret"):
            with self.assertRaises(ValueError):
                contained(DEFAULT_DATA, path)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            (root / "escape").symlink_to(Path(tmp))
            with self.assertRaises(ValueError):
                contained(root, "escape/secret")

    def test_calibration_is_not_human_ground_truth(self):
        self.assertEqual(self.result["r1"]["pairs"], 7)
        self.assertEqual(self.result["r1"]["judge_calls"], 14)
        self.assertEqual(self.result["r1"]["varying_pairs"], 3)
        self.assertFalse(self.result["r1"]["mentor_final_approval"])


if __name__ == "__main__":
    unittest.main()
