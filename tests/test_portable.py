"""Protocol tests use fake judges/agents, never produce empirical benchmark results."""
import copy
import io
import json
import os
import shlex
import sys
import tempfile
import unittest
import urllib.error
import jsonschema
from pathlib import Path
from unittest.mock import patch

from draftbench.api import EvaluationError, GeminiJudge, load_env
from draftbench.catalog import catalog
from draftbench.common import DEFAULT_DATA, ROOT, read_json, write_json
from draftbench.evaluate import evaluate, inspect_evidence, validate_design_annotation
from draftbench.prepare import build_request, prepare
from draftbench.runner import invoke, run, validate_targets
from draftbench.summary import summarize

MOCK_COMMAND = shlex.join([sys.executable, str(ROOT / "examples/mock_agent.py")])
FIELDS = ["use_case", "volume", "input_assets", "output", "style_reference", "deadline", "budget"]


class FakeJudge:
    """A deterministic test double, not a meaningful design evaluator."""
    def __init__(self):
        self.calls = []

    def config(self):
        return {"provider": "FAKE_UNIT_TEST_ONLY", "model": "none"}

    def call(self, role, instruction, payload, log_dir, media=()):
        self.calls.append((role, copy.deepcopy(payload)))
        if role == "rfq_router":
            # Routing must not receive case truth or scoring state.
            assert set(payload) == {"field_ids", "public_history", "agent_message"}
            index = sum(m["role"] == "assistant" for m in payload["public_history"])
            return {"targets": [{"field_id": FIELDS[index], "request_quote": payload["agent_message"]}]}
        if role == "rfq_evidence_auditor":
            rows = []
            for turn in payload["turns"]:
                field = next(f for f in payload["case"]["fields"] if f["field_id"] == turn["selected_field"])
                rows.append({"round": turn["round"], "audited_targets": turn["targets"], "diagnostics": [],
                             "disclosures": [{"field_id": field["field_id"], "component_id": c["component_id"],
                                              "correct": True, "evidence_quote": turn["customer_message"]}
                                             for c in field["components"]]})
            return {"rounds": rows}
        return {"summary": "Synthetic judgment for software testing, not model evidence.",
                "dimensions": [{"id": key, "score": None if key == "efficiency" else .5,
                                "reason": "Unit test", "evidence": ["conversation"]}
                               for key in payload["rubric_weights"]],
                "requirements": [{"id": r["id"], "verdict": "UNKNOWN", "reason": "Unit test", "evidence": []}
                                 for r in payload["requirements"]]}


class PortableInputTests(unittest.TestCase):
    def test_every_public_task_has_materializable_input(self):
        tasks = catalog(DEFAULT_DATA)
        self.assertEqual(tasks["task_count"], 83)
        missing = [t for t in tasks["tasks"] if t.get("intentionally_missing_inputs")]
        self.assertEqual(len(missing), 3)
        with tempfile.TemporaryDirectory() as tmp:
            for task in tasks["tasks"]:
                dest = Path(tmp) / task["id"]
                prepare(DEFAULT_DATA, task["track"], task["id"], dest, complete=True)
                request = read_json(dest / "request.json")
                name = "candidate-bundle-v2.schema.json" if task["track"] == "design" else "candidate-bundle.schema.json"
                jsonschema.Draft202012Validator(read_json(ROOT / "schemas" / name)).validate(request)
                self.assertNotIn("rubric", request)
                self.assertNotIn("feedback", request)
                if task["track"] == "design":
                    self.assertTrue(request["task_contract"]["deliverables"])
                    self.assertEqual(request["format"], "draftbench-candidate-bundle/2")
                else:
                    self.assertNotIn("fields", request)

    def test_complete_input_preserves_ablation_and_future_feedback_boundary(self):
        request, _ = build_request(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", complete=True)
        contract = request["task_contract"]
        self.assertEqual(len(contract["reference_contract"]), 1)
        self.assertEqual({i["id"] for i in contract["inputs"]}, {"current-identity", "brand-facts"})
        self.assertNotIn("A 还是太网红，C 又太老", json.dumps(request, ensure_ascii=False))
        self.assertIsNone(request["preference_memory"])

    def test_missing_prerequisite_is_explicit_not_fabricated(self):
        request, _ = build_request(DEFAULT_DATA, "design", "DAB-L4-RDT-008@reference_grounded", complete=True)
        entry = next(i for i in request["task_contract"]["inputs"] if i["id"] == "manufacturer-dieline")
        self.assertEqual(entry["availability"], "intentionally_missing")
        self.assertNotIn("asset_id", entry)


class RunnerTests(unittest.TestCase):
    def test_design_multi_turn_snapshot_and_new_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            result = run(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", root, MOCK_COMMAND)
            self.assertEqual(result["agent_turns"], 4)
            record = read_json(root / "run.json")
            self.assertNotIn("A 还是太网红", json.dumps(record["turns"][0]["request"], ensure_ascii=False))
            self.assertIn("A 还是太网红", json.dumps(record["turns"][1]["request"], ensure_ascii=False))
            original = root / record["turns"][0]["artifacts"][0]["path"]
            (root / "candidate/outputs/v0/demo.svg").write_text("mutated candidate copy")
            self.assertIn("PLUMBING DEMO", original.read_text())
            judged = evaluate(DEFAULT_DATA, root, FakeJudge(), root / "evaluation")
            self.assertEqual(judged["status"], "evaluated")
            jsonschema.Draft202012Validator(read_json(ROOT / "schemas/evaluation-result.schema.json")).validate(judged)
            self.assertIsNone(judged["metrics"]["quality_point"])
            self.assertAlmostEqual(judged["metrics"]["observed_weight"], .95)
            self.assertIsNone(judged["metrics"]["accepted_delivery"])
            self.assertFalse(judged["human_reviewed"])
            summary = summarize(root)
            self.assertEqual(summary["tracks"]["design"]["evaluated"], 1)
            with self.assertRaises(ValueError):
                evaluate(DEFAULT_DATA, root, FakeJudge(), root / "evaluation")

    def test_all_design_conditions_execute_their_declared_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            for task in catalog(DEFAULT_DATA, "design")["tasks"]:
                result = run(DEFAULT_DATA, "design", task["id"], Path(tmp) / task["id"], MOCK_COMMAND)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["agent_turns"], task["turns"])

    def test_all_rfq_cases_route_then_score_independent_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            for task in catalog(DEFAULT_DATA, "rfq")["tasks"]:
                root = Path(tmp) / task["id"]
                judge = FakeJudge()
                result = run(DEFAULT_DATA, "rfq", task["id"], root, MOCK_COMMAND, judge=judge)
                self.assertEqual(result["status"], "completed")
                record = read_json(root / "run.json")
                self.assertEqual(sum("rfq" in t for t in record["turns"]), 7)
                self.assertNotIn("customer_message", record["turns"][-1])
                judged = evaluate(DEFAULT_DATA, root, judge, root / "evaluation")
                self.assertEqual(judged["status"], "evaluated")
                self.assertTrue(judged["metrics"]["success_at_8"])
            summary = summarize(Path(tmp))
            self.assertEqual(summary["tracks"]["rfq"]["rfq"]["success_denominator"], 40)

    def test_router_rejects_hallucinated_quotes_and_order(self):
        for targets in ([{"field_id": "volume", "request_quote": "never said"}],
                        [{"field_id": "volume", "request_quote": "quantity"}, {"field_id": "budget", "request_quote": "budget"}]):
            with self.assertRaises(ValueError):
                validate_targets(targets, "budget then quantity")

    def test_evaluator_secret_removed_from_candidate_environment(self):
        script = 'import os,json; print(json.dumps({"message":str("DRAFTBENCH_EVAL_API_KEY" in os.environ or "GEMINI_API_KEY" in os.environ)}))'
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DRAFTBENCH_EVAL_API_KEY": "test-secret", "GEMINI_API_KEY": "second"}):
            outcome = invoke(shlex.join([sys.executable, "-c", script]), {}, Path(tmp), 5)
            self.assertEqual(outcome["response"]["message"], "False")

    def test_timeout_and_bad_adapter_fail_without_quality_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = shlex.join([sys.executable, "-c", "import time; time.sleep(2)"])
            root = Path(tmp) / "timeout"
            result = run(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", root, command, timeout=.05)
            self.assertEqual(result["status"], "timeout")
            evaluation = evaluate(DEFAULT_DATA, root, FakeJudge(), root / "evaluation")
            self.assertIsNone(evaluation["metrics"])
            self.assertEqual(evaluation["status"], "not_evaluated")
            outcome = invoke(shlex.join([sys.executable, "-c", 'print("not JSON")']), {}, Path(tmp), 5)
            self.assertEqual(outcome["status"], "agent_error")

    def test_escaping_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = 'import json; print(json.dumps({"message":"x","artifacts":["../outside.txt"]}))'
            outcome = invoke(shlex.join([sys.executable, "-c", script]), {}, Path(tmp), 5)
            self.assertEqual(outcome["status"], "agent_error")

    def test_router_api_failure_cannot_become_zero_rfq_score(self):
        judge = FakeJudge()
        judge.call = lambda *a, **k: (_ for _ in ()).throw(EvaluationError("injected transport failure"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "rfq"
            result = run(DEFAULT_DATA, "rfq", "RFQ-IC-001", root, MOCK_COMMAND, judge=judge)
            self.assertEqual(result["status"], "router_error")
            evaluation = evaluate(DEFAULT_DATA, root, judge, root / "evaluation")
            self.assertEqual(evaluation["status"], "evaluation_error")
            self.assertIsNone(evaluation["metrics"])


class EvaluationTests(unittest.TestCase):
    def test_interrupted_suite_keeps_not_started_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "suite.json", {"format": "draftbench-suite/0.2", "track": "design",
                                           "planned_ids": ["DAB-L4-BID-001@zero_shot", "DAB-L4-BID-001@personalized"]})
            run(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", root / "first", MOCK_COMMAND)
            result = summarize(root)["tracks"]["design"]
            self.assertEqual((result["planned"], result["attempts"], result["not_started"]), (2, 1, 1))
            self.assertEqual(result["missing_evaluation"], 1)

    def test_mixed_candidate_configurations_cannot_be_pooled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", root / "a", MOCK_COMMAND, timeout=60)
            run(DEFAULT_DATA, "design", "DAB-L4-BID-001@personalized", root / "b", MOCK_COMMAND, timeout=61)
            with self.assertRaisesRegex(ValueError, "Mixed candidate"):
                summarize(root)

    def test_unknown_scores_keep_bounds_and_require_literal_evidence_ids(self):
        annotation = {"summary": "test", "dimensions": [{"id": "visual", "score": .8, "reason": "test", "evidence": ["image"]},
                                                       {"id": "technical", "score": None, "reason": "unobserved", "evidence": []}],
                      "requirements": [{"id": "gate-1", "verdict": "UNKNOWN", "reason": "unobserved", "evidence": []}]}
        weights, required = {"visual": .5, "technical": .5}, [{"id": "gate-1"}]
        result = validate_design_annotation(annotation, weights, required, {"image"})
        self.assertEqual((result["quality_lower"], result["quality_upper"]), (.4, .9))
        for value in (float("nan"), 1.2, True):
            bad = copy.deepcopy(annotation)
            bad["dimensions"][0]["score"] = value
            with self.assertRaises(ValueError):
                validate_design_annotation(bad, weights, required, {"image"})
        with self.assertRaises(ValueError):
            validate_design_annotation(annotation, weights, required, set())

    def test_actual_raster_content_is_attached_not_just_paths(self):
        from PIL import Image
        from draftbench.common import sha256
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.png"
            Image.new("RGB", (1800, 1000), "red").save(path)
            inventory, media = inspect_evidence([("v0/image.png", path, sha256(path))])
            self.assertTrue(inventory[0]["content_seen"])
            self.assertEqual(inventory[0]["width"], 1800)
            self.assertEqual(media[1]["inlineData"]["mimeType"], "image/jpeg")
            with self.assertRaises(ValueError):
                inspect_evidence([("v0/image.png", path, "wrong-hash")])

    def test_invalid_judge_output_is_saved_as_missing_not_zero(self):
        judge = FakeJudge()
        judge.call = lambda *a, **k: {"summary": "invalid", "dimensions": [], "requirements": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "design"
            run(DEFAULT_DATA, "design", "DAB-L4-BID-001@zero_shot", root, MOCK_COMMAND)
            result = evaluate(DEFAULT_DATA, root, judge, root / "evaluation")
            self.assertEqual(result["status"], "evaluation_error")
            self.assertIsNone(result["metrics"])
            self.assertTrue((root / "evaluation/annotation.json").is_file())


class ApiTests(unittest.TestCase):
    def response(self, text='{"ok":true}', finish="STOP"):
        return io.BytesIO(json.dumps({"candidates": [{"finishReason": finish,
                          "content": {"parts": [{"text": text}]}}], "modelVersion": "resolved-test"}).encode())

    def test_api_request_and_logs_do_not_contain_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DRAFTBENCH_EVAL_API_KEY": "test-secret"}), \
                patch("urllib.request.build_opener") as factory:
            factory.return_value.open.return_value = self.response()
            result = GeminiJudge().call("test", "JSON only", {"hello": True}, Path(tmp) / "call")
            self.assertEqual(result, {"ok": True})
            request = factory.return_value.open.call_args.args[0]
            self.assertNotIn("test-secret", request.full_url)
            self.assertNotIn(b"test-secret", request.data)
            for path in Path(tmp).rglob("*.json"):
                self.assertNotIn("test-secret", path.read_text())

    def test_http_auth_error_not_retried_and_error_body_not_logged(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DRAFTBENCH_EVAL_API_KEY": "test-secret"}), \
                patch("urllib.request.build_opener") as factory:
            factory.return_value.open.side_effect = urllib.error.HTTPError("url", 403, "test-secret", {}, io.BytesIO(b"test-secret"))
            with self.assertRaisesRegex(EvaluationError, "HTTP 403"):
                GeminiJudge().call("test", "JSON", {}, Path(tmp) / "call")
            self.assertEqual(factory.return_value.open.call_count, 1)
            self.assertNotIn("test-secret", (Path(tmp) / "call/call.json").read_text())

    def test_retry_429_but_never_resample_invalid_model_json(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DRAFTBENCH_EVAL_API_KEY": "test-secret"}), \
                patch("urllib.request.build_opener") as factory, patch("draftbench.api.time.sleep"):
            factory.return_value.open.side_effect = [urllib.error.HTTPError("url", 429, "busy", {}, None), self.response()]
            GeminiJudge().call("test", "JSON", {}, Path(tmp) / "retry")
            self.assertEqual(factory.return_value.open.call_count, 2)
            factory.return_value.open.reset_mock(side_effect=True)
            factory.return_value.open.return_value = self.response("broken JSON")
            with self.assertRaises(EvaluationError):
                GeminiJudge().call("test", "JSON", {}, Path(tmp) / "invalid")
            self.assertEqual(factory.return_value.open.call_count, 1)

    def test_env_loader_does_not_execute_shell_or_override_existing_environment(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DRAFTBENCH_TEST_VAR": "original"}):
            path = Path(tmp) / "env"
            path.write_text('DRAFTBENCH_TEST_VAR=$(echo unsafe)\nDRAFTBENCH_SECOND_TEST="literal"\n')
            load_env(path)
            self.assertEqual(os.environ["DRAFTBENCH_TEST_VAR"], "original")
            self.assertEqual(os.environ["DRAFTBENCH_SECOND_TEST"], "literal")


if __name__ == "__main__":
    unittest.main()
