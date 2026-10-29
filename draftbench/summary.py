"""New-run summaries, with execution and evaluation coverage kept separate."""
import csv
import io
import json
from collections import Counter

from .common import read_json, sha256
from .rfq.scoring import aggregate


def summarize(root, evaluation_name="evaluation"):
    if not evaluation_name or "/" in evaluation_name or "\\" in evaluation_name or evaluation_name in (".", ".."):
        raise ValueError("Evaluation name must be a directory basename")
    records, evaluations, seen, configurations, routers = [], [], set(), set(), set()
    suite = read_json(root / "suite.json") if (root / "suite.json").exists() else None
    for path in sorted(root.rglob("run.json")):
        # Candidate-produced files are untrusted; only harness records have this schema.
        if "candidate" in path.relative_to(root).parts or "evidence" in path.relative_to(root).parts:
            continue
        run = read_json(path)
        identity = (run["track"], run["id"])
        if identity in seen:
            raise ValueError("Repeated task IDs: summarize separate suites/attempts, not pooled repeats")
        seen.add(identity)
        if run["track"] == "rfq":
            routers.add(json.dumps(run.get("router"), sort_keys=True))
        if suite and (run["track"] != suite["track"] or run["id"] not in suite["planned_ids"]):
            raise ValueError("Run is not a member of the declared suite")
        configurations.add(json.dumps({k: run.get(k) for k in ("agent_command", "timeout_per_turn_seconds",
                                                              "data_manifest_sha256", "toolkit_sources", "harness_python")}, sort_keys=True))
        row = {"track": run["track"], "id": run["id"], "execution_status": run["status"],
               "elapsed_seconds": run.get("elapsed_seconds"), "evaluation_status": "missing"}
        evaluation_path = path.parent / evaluation_name / "result.json"
        if evaluation_path.exists():
            evaluation = read_json(evaluation_path)
            if evaluation["run_sha256"] != sha256(path) or (evaluation["track"], evaluation["id"]) != identity:
                raise ValueError("Evaluation does not match the run")
            row["evaluation_status"] = evaluation["status"]
            row.update(evaluation.get("metrics") or {})
            evaluations.append(evaluation)
        records.append(row)
    if not records and not suite:
        raise ValueError("No harness run.json records found")
    if len(configurations) > 1:
        raise ValueError("Mixed candidate/runtime/data/toolkit settings; summarize separately")
    if len(routers) > 1:
        raise ValueError("Mixed RFQ router settings; summarize separately")
    judge_configs = {json.dumps({k: e.get(k) for k in ("judge", "evaluator_sources", "inspection_libraries")}, sort_keys=True)
                     for e in evaluations}
    if len(judge_configs) > 1:
        raise ValueError("Mixed evaluator settings; summarize separately")
    resolved_models = {e["judge_resolved_model"] for e in evaluations if e.get("judge_resolved_model")}
    if len(resolved_models) > 1:
        raise ValueError("Resolved judge model changed within the suite; summarize separately")
    tracks = {}
    for track in ("design", "rfq"):
        rows = [r for r in records if r["track"] == track]
        if not rows and not (suite and suite["track"] == track):
            continue
        scored = [r for r in rows if r["evaluation_status"] == "evaluated"]
        section = {"attempts": len(rows), "completed": sum(r["execution_status"] == "completed" for r in rows),
                   "execution_counts": dict(Counter(r["execution_status"] for r in rows)),
                   "evaluated": len(scored), "evaluation_counts": dict(Counter(r["evaluation_status"] for r in rows)),
                   "missing_evaluation": len(rows) - len(scored)}
        section["planned"] = len(suite["planned_ids"]) if suite and suite["track"] == track else len(rows)
        section["not_started"] = section["planned"] - len(rows)
        if track == "rfq":
            section["rfq"] = aggregate([e["scoring_result"] for e in evaluations
                                        if e["track"] == "rfq" and e["status"] == "evaluated"])
        else:
            section["mean_quality_bounds_over_evaluated_only"] = {
                key: sum(r[key] for r in scored) / len(scored) if scored else None
                for key in ("quality_lower", "quality_upper", "observed_weight")}
            section["accepted_delivery_rate"] = None
        tracks[track] = section
    return {"format": "draftbench-suite-summary/0.2", "tracks": tracks, "records": records,
            "human_validated": False, "historical_scores_pooled": False}


def as_csv(summary):
    fields = sorted({k for row in summary["records"] for k in row})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(summary["records"])
    return output.getvalue()
