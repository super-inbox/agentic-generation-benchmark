"""Behavioral contract tests; no network, model calls, or fabricated run results."""

import copy
import json
import unittest
from pathlib import Path

from draftbench.rfq.disclosure_policy import render_fixed, renderer_payload, select_field
from draftbench.rfq.scoring import aggregate, score, validate_case

BUNDLE = json.loads((Path(__file__).resolve().parents[1] / "draftbench" / "rfq" / "examples.json").read_text())


class MetricContract(unittest.TestCase):
    def setUp(self):
        self.case = copy.deepcopy(BUNDLE["case"])
        self.clean, self.leak = copy.deepcopy(BUNDLE["episodes"])

    def episode_for(self, field_ids):
        turns = {t["selected_field"]: t for t in self.clean["turns"] if t["selected_field"]}
        ep = copy.deepcopy(self.clean)
        ep["turns"] = [copy.deepcopy(turns[f]) for f in field_ids]
        for n, turn in enumerate(ep["turns"], 1):
            turn["round"] = n
        return ep

    def test_clean_prefixes_and_four_headlines(self):
        result = score(self.case, self.clean)
        self.assertEqual(len(result["metrics"]), 4)
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_6"], 6/7)
        self.assertEqual(result["metrics"]["elicited_coverage_at_8"], 1)
        self.assertTrue(result["metrics"]["success_at_8"])
        self.assertEqual(result["metrics"]["leak_rate"], 0)

    def test_no_future_answer_backfill(self):
        before = score(self.case, self.clean)["checkpoints"]["6"]
        self.clean["turns"][6]["disclosures"][0]["correct"] = False
        after = score(self.case, self.clean)
        self.assertEqual(after["checkpoints"]["6"], before)
        self.assertAlmostEqual(after["metrics"]["elicited_coverage_at_8"], 6/7)

    def test_missing_secondary_can_succeed(self):
        self.clean["turns"] = self.clean["turns"][:6]
        result = score(self.case, self.clean)
        self.assertTrue(result["metrics"]["success_at_8"])
        self.assertEqual(result["checkpoints"]["8"]["actual_customer_rounds"], 6)
        self.assertEqual(result["metrics"]["elicited_coverage_at_6"], result["metrics"]["elicited_coverage_at_8"])

    def test_six_of_seven_with_missing_critical_fails(self):
        self.clean["turns"][2]["disclosures"][0]["correct"] = False
        result = score(self.case, self.clean)
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_8"], 6/7)
        self.assertFalse(result["metrics"]["success_at_8"])
        self.assertEqual(result["checkpoints"]["8"]["missing_critical_fields"], ["input_assets"])

    def test_all_critical_but_below_threshold_fails(self):
        self.clean["turns"] = self.clean["turns"][:5]
        self.assertFalse(score(self.case, self.clean)["metrics"]["success_at_8"])

    def test_exact_eighty_percent_passes(self):
        for f in self.case["fields"]:
            if f["field_id"] in {"deadline", "budget"}:
                f.update(availability="not_applicable", components=[], not_applicable_reason="Authored test scope")
        ep = self.episode_for(["use_case", "volume", "input_assets", "output"])
        result = score(self.case, ep)
        self.assertEqual(result["metrics"]["elicited_coverage_at_8"], 0.8)
        self.assertTrue(result["metrics"]["success_at_8"])

    def test_leak_does_not_invalidate_episode_or_launder_after_reasking(self):
        result = score(self.case, self.leak)
        last = result["checkpoints"]["8"]
        self.assertEqual(result["status"], "scored")
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_8"], 5/7)
        self.assertEqual(last["observed_coverage"], 1)
        self.assertEqual(last["unprompted_disclosure_count"], 2)
        self.assertEqual(last["first_correct_disclosures"]["budget.amount"]["source"], "unprompted")
        self.assertAlmostEqual(result["metrics"]["leak_rate"], 2/7)
        self.assertFalse(result["metrics"]["success_at_8"])

    def test_first_response_leak_rate_has_its_own_denominator(self):
        self.leak["turns"] = self.leak["turns"][:1]
        result = score(self.case, self.leak)
        self.assertAlmostEqual(result["metrics"]["leak_rate"], 2/3)
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_8"], 1/7)

    def test_router_error_audited_as_leak_without_rewriting_live_selection(self):
        ep = self.episode_for(["volume"])
        turn = ep["turns"][0]
        turn["audited_targets"] = []
        result = score(self.case, ep)
        self.assertEqual(turn["selected_field"], "volume")
        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["metrics"]["elicited_coverage_at_8"], 0)
        self.assertEqual(result["metrics"]["leak_rate"], 1)

    def test_audited_target_needs_literal_evidence(self):
        ep = self.episode_for(["volume"])
        ep["turns"][0]["audited_targets"] = [{"field_id":"volume", "request_quote":"Invented question"}]
        with self.assertRaises(ValueError):
            score(self.case, ep)

    def test_targeted_policy_overflow_is_not_unprompted(self):
        ep = self.episode_for(["volume"])
        t = ep["turns"][0]
        extra = self.clean["turns"][6]
        t["agent_message"] += " " + extra["agent_message"]
        t["targets"] += extra["targets"]
        t["customer_message"] += " " + extra["customer_message"]
        t["disclosures"] += extra["disclosures"]
        result = score(self.case, ep)
        last = result["checkpoints"]["8"]
        self.assertEqual(last["policy_overflow_fields"], ["budget"])
        self.assertAlmostEqual(last["observed_coverage"], 2/7)
        self.assertAlmostEqual(last["elicited_coverage"], 1/7)
        self.assertEqual(last["leak_rate"], 0)

    def test_initial_field_is_neither_free_credit_nor_required_to_reask(self):
        self.case["initially_known_component_ids"] = ["use_case.purpose"]
        ep = self.episode_for(["volume", "input_assets", "output", "style_reference", "deadline", "budget"])
        result = score(self.case, ep)
        self.assertEqual(result["checkpoints"]["8"]["field_denominator"], 6)
        self.assertEqual(result["metrics"]["elicited_coverage_at_6"], 1)
        self.assertTrue(result["metrics"]["success_at_8"])

    def test_partial_field_and_partial_opening(self):
        f = self.case["fields"][1]
        f["components"].append({"component_id": "volume.period", "value": "per month"})
        ep = self.episode_for(["volume"])
        self.assertEqual(score(self.case, ep)["metrics"]["elicited_coverage_at_8"], 0)
        self.case["initially_known_component_ids"] = ["volume.period"]
        self.assertAlmostEqual(score(self.case, ep)["metrics"]["elicited_coverage_at_8"], 1/7)

    def test_genuine_undecided_state_is_a_correct_answer(self):
        f = self.case["fields"][-1]
        f.update(availability="undecided", reply="We haven't decided on a budget.")
        f["components"][0]["value"] = {"state": "undecided"}
        t = self.clean["turns"][6]
        t["customer_message"] = f["reply"]
        t["disclosures"][0]["evidence_quote"] = f["reply"]
        self.assertEqual(score(self.case, self.clean)["metrics"]["elicited_coverage_at_8"], 1)

    def test_wrong_answer_gives_no_credit_and_does_not_drop_case(self):
        ep = self.episode_for(["volume"])
        t = ep["turns"][0]
        t["customer_message"] = "About 500 pictures a week."
        t["disclosures"][0].update(correct=False, evidence_quote=t["customer_message"])
        result = score(self.case, ep)
        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["metrics"]["elicited_coverage_at_8"], 0)
        self.assertIsNone(result["metrics"]["leak_rate"])

    def test_agent_no_output_stays_in_denominator(self):
        self.clean["turns"] = []
        result = score(self.case, self.clean)
        total = aggregate([result])
        self.assertEqual(total["scored"], 1)
        self.assertEqual(total["metrics"]["success_at_8"], 0)
        self.assertIsNone(total["metrics"]["leak_rate"])

    def test_uncertain_component_keeps_episode_with_provisional_bounds(self):
        self.clean["turns"][2]["disclosures"][0]["correct"] = None
        result = score(self.case, self.clean)
        self.assertTrue(result["provisional"])
        self.assertFalse(result["metrics"]["success_at_8"])
        self.assertTrue(result["diagnostic_bounds"]["success_at_8_upper"])
        self.assertIsNone(result["metrics"]["leak_rate"])
        self.assertEqual(aggregate([result])["scored"], 1)

    def test_case_macro_coverage_but_micro_leak_rate(self):
        first = score(self.case, self.clean)
        second = score(self.case, {**self.leak, "turns": self.leak["turns"][:1]})
        second["case_id"] = "SECOND-AUTHORED-CASE"
        total = aggregate([first, second])
        self.assertAlmostEqual(total["metrics"]["elicited_coverage_at_8"], (1+1/7)/2)
        self.assertAlmostEqual(total["metrics"]["leak_rate"], 2/(7+3))
        self.assertEqual(total["success_denominator"], 2)

    def test_ambiguous_repetition_does_not_erase_prior_certain_acquisition(self):
        ep = self.episode_for(["volume", "volume"])
        ep["turns"][1]["disclosures"][0]["correct"] = None
        result = score(self.case, ep)
        self.assertFalse(result["provisional"])
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_8"], 1/7)

    def test_uncertain_first_source_stays_provisional_after_later_answer(self):
        ep = self.episode_for(["volume", "volume"])
        ep["turns"][0]["disclosures"][0]["correct"] = None
        result = score(self.case, ep)
        self.assertTrue(result["provisional"])
        self.assertEqual(result["metrics"]["elicited_coverage_at_8"], 0)
        total = aggregate([result])
        self.assertAlmostEqual(total["diagnostic_upper_bounds"]["elicited_coverage_at_8_upper"], 1/7)

    def test_only_predeclared_infrastructure_reasons_exclude(self):
        bad = {**self.clean, "status": "infrastructure_excluded", "exclusion_reason": "unprompted_disclosure"}
        with self.assertRaises(ValueError):
            score(self.case, bad)
        bad["exclusion_reason"] = "infrastructure_interruption"
        total = aggregate([score(self.case, bad)])
        self.assertEqual(total["infrastructure_excluded"], 1)
        self.assertIsNone(total["metrics"]["success_at_8"])

    def test_missing_annotations_are_not_silent_zeroes(self):
        self.clean["annotation_complete"] = False
        with self.assertRaises(ValueError):
            score(self.case, self.clean)

    def test_evidence_must_exist_in_actual_customer_reply(self):
        self.clean["turns"][0]["disclosures"][0]["evidence_quote"] = "Invented evidence"
        with self.assertRaises(ValueError):
            score(self.case, self.clean)

    def test_unknown_field_and_reordered_requests_are_rejected(self):
        with self.assertRaises(ValueError):
            select_field(["future_undocumented_field"])
        ep = self.episode_for(["volume", "budget"])
        t, other = ep["turns"]
        t["agent_message"] += " " + other["agent_message"]
        t["targets"] = other["targets"] + t["targets"]
        t["selected_field"] = "budget"
        with self.assertRaises(ValueError):
            score(self.case, ep)

    def test_repeated_requests_do_not_skip_to_new_information(self):
        self.assertEqual(select_field(["volume", "budget"]), "volume")
        self.assertEqual(render_fixed(self.case, ["volume", "budget"]), self.case["fields"][1]["reply"])
        self.assertEqual(select_field([]), None)

    def test_renderer_projection_contains_no_hidden_state_or_scores(self):
        payload = renderer_payload(self.case, ["volume", "budget"])
        self.assertEqual(set(payload), {"neutral_voice", "selected_answer"})
        serialized = json.dumps(payload)
        self.assertNotIn("RMB", serialized)
        self.assertNotIn("critical", serialized)
        self.assertNotIn("Taobao", serialized)

    def test_empty_target_case_and_critical_na_rejected_before_run(self):
        self.case["initially_known_component_ids"] = [c["component_id"] for f in self.case["fields"] for c in f["components"]]
        with self.assertRaises(ValueError):
            validate_case(self.case)
        self.case["initially_known_component_ids"] = []
        self.case["fields"][0]["availability"] = "not_applicable"
        with self.assertRaises(ValueError):
            validate_case(self.case)

    def test_repeated_case_cannot_masquerade_as_independent_customer(self):
        result = score(self.case, self.clean)
        with self.assertRaises(ValueError):
            aggregate([result, result])

    def test_confirmations_do_not_add_information(self):
        ep = self.episode_for(["use_case"])
        ep["turns"].append(copy.deepcopy(self.clean["turns"][-1]))
        ep["turns"][-1]["round"] = 2
        result = score(self.case, ep)
        self.assertAlmostEqual(result["metrics"]["elicited_coverage_at_8"], 1/7)

    def test_transcript_cannot_sneak_in_a_ninth_customer_reply(self):
        self.clean["turns"].append(copy.deepcopy(self.clean["turns"][-1]))
        self.clean["turns"][-1]["round"] = 9
        with self.assertRaises(ValueError):
            score(self.case, self.clean)


if __name__ == "__main__":
    unittest.main()
