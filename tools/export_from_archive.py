#!/usr/bin/env python3
"""Maintainer-only export from archived inputs; normal users need no source archive.

This allowlist export excludes raw tool traces, provider logs, model-generated
design outputs, and third-party media. Existing release directories are immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for r in rows), encoding="utf-8")


def pick(record, keys):
    return {key: record[key] for key in keys if key in record}


def export(eval_root, dashboard, paper_snapshot, output):
    if output.exists():
        raise ValueError("Refusing to overwrite a release; choose a new output directory")
    bank = eval_root / "brief_bank"
    archive = read_json(dashboard / "all/data.json")
    rfq = read_json(dashboard / "rfq/all/data.json")
    paper = read_json(paper_snapshot)
    for relative in ("all/data.json", "rfq/all/data.json"):
        matches = [f for f in paper["source_files"] if f["path"].endswith("/dist/" + relative)]
        if len(matches) != 1 or digest(dashboard / relative) != matches[0]["sha256"]:
            raise ValueError(f"Dashboard input does not match the frozen paper snapshot: {relative}")
    if paper["publication"]["source_commit"] != "67815928a139bd2f878e1bdedf517a93f00da5ba":
        raise ValueError("This exporter targets the pinned v9 archive; update the release protocol for a new source")
    assert archive["as_of"] == paper["dashboard_as_of"] == "2026-10-23"
    briefs = read_rows(bank / "briefs.v0.3.jsonl")
    conditions = read_rows(bank / "initial_queries.v0.3.jsonl")
    assert len(briefs) == 35 and len(conditions) == 43 and len(rfq["cases"]) == 40
    source_files = [
        ("brief-bank/episodes", bank / "briefs.v0.3.jsonl"),
        ("brief-bank/conditions", bank / "initial_queries.v0.3.jsonl"),
        ("dashboard/archive", dashboard / "all/data.json"),
        ("dashboard/rfq", dashboard / "rfq/all/data.json"),
        ("paper/dashboard-reconciliation", paper_snapshot),
    ]
    # The authored contracts have no real customer data. Preserve their wording.
    assert all(b["provenance"]["customer_data"] is False for b in briefs)
    write_rows(output / "briefs/episodes.jsonl", briefs)
    for c in conditions:
        c["episode_source"] = "briefs/episodes.jsonl"
    write_rows(output / "briefs/conditions.jsonl", conditions)

    assets = []
    for pack_name in ("reference-pack-v0.2", "brief-bank-v0.3"):
        pack = eval_root / "assets" / pack_name
        source_files.append((f"assets/{pack_name}/manifest", pack / "manifest.jsonl"))
        for original in read_rows(pack / "manifest.jsonl"):
            assert original["license"] == "project_owned_test_fixture"
            assert original["contains_personal_data"] is False
            relative = Path(original["path"])
            assert not relative.is_absolute() and ".." not in relative.parts
            source = pack / relative
            assert digest(source) == original["sha256"]
            assert source.stat().st_size == original["bytes"]
            target = output / "assets" / pack_name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            asset = dict(original)
            asset["path"] = target.relative_to(output).as_posix()
            asset["upstream_rights_status"] = asset.pop("license")
            asset["license"] = "CC-BY-4.0"
            asset["attribution"] = "Curify, DRAFT-Bench"
            assets.append(asset)
    write_rows(output / "assets/manifest.jsonl", assets)

    openings, cases, episodes, results = [], [], [], []
    turn_keys = ("round", "agent_message", "customer_message", "targets", "selected_field", "disclosures", "audited_targets")
    for original in rfq["cases"]:
        cid = original["id"]
        openings.append({"case_id": cid, "opening_message": original["opening"], "language": "en", "batch": original["batch"], "family": original["family"]})
        fields = []
        for field in original["fields"]:
            # Keep the frozen truth and scoring components; omit private source references.
            value = pick(field, ("field_id", "critical", "availability", "reply", "components", "not_applicable_reason"))
            fields.append(value)
        cases.append({
            "protocol_id": rfq["protocol_id"], "case_id": cid,
            "title": original["title"], "family": original["family"], "batch": original["batch"],
            "opening_message": original["opening"], "fields": fields,
            "initially_known_component_ids": original["initially_known"],
            "variant": original["variant"], "customer_data": False,
            "provenance_kind": "authored_synthetic" if original["batch"] == "original" else "real_scenario_grounded_authored_variant",
        })
        for model in ("astra", "claude", "sol"):
            run = original.get(model)
            if not isinstance(run, dict) or not run.get("result"):
                continue
            result = run["result"]
            episode = {
                "case_id": cid, "episode_id": result["episode_id"], "model": model,
                "batch": original["batch"], "status": result["status"],
                "annotation_complete": result["status"] == "scored",
                "turns": [pick(t, turn_keys) for t in run["turns"]],
                "human_review_status": "not_performed", "annotation_source": "archived_model_annotation",
            }
            if result["status"] == "infrastructure_excluded":
                episode["exclusion_reason"] = result["exclusion_reason"]
            episodes.append(episode)
            results.append({"model": model, "batch": original["batch"], "result": result})
    write_rows(output / "rfq/openings.jsonl", openings)
    write_rows(output / "rfq/evaluator_cases.jsonl", cases)
    write_rows(output / "results/rfq_episodes.jsonl", episodes)
    write_rows(output / "results/rfq_scores.jsonl", results)

    observations = archive["observations"]
    write_rows(output / "results/archive_observations.jsonl", observations)
    units = []
    for unit in archive["units"].values():
        row = pick(unit, ("key", "id", "group", "category_id", "partition", "kind", "layer", "metric", "weights", "historical_comparable"))
        row["models"] = {}
        for model in ("astra", "claude", "sol"):
            if model not in unit:
                continue
            row["models"][model] = {
                "status": unit.get(f"{model}_status"),
                "completed": unit.get(f"{model}_completed"),
                "score": pick(unit[model], ("lower", "upper", "pass")) if isinstance(unit[model], dict) else None,
                "dimensions": {
                    name: pick(value, ("score",))
                    for name, value in unit.get("dimensions", {}).get(model, {}).items()
                    if isinstance(value, dict)
                },
            }
        row["human_review_status"] = "not_performed"
        row["input_release"] = "full_contract_and_fixtures" if row["group"] == "brief-bank-v03" else "rfq_case" if row["kind"] == "rfq" else "metadata_only"
        units.append(row)
    write_rows(output / "results/archive_units.jsonl", units)
    write_json(output / "results/calibration_r1.json", paper["r1"])
    write_json(output / "results/experiment_settings.json", {
        "archive_as_of": archive["as_of"], "paper_revision": paper["paper_revision"],
        "model_labels_as_recorded": archive["models"],
        "model_label_note": "Archived configuration labels, not a claim that these are currently available public API identifiers.",
        "rfq_models": rfq["models"], "rfq_source_settings": rfq["source_settings"],
        "rfq_attempt_policy": rfq["attempt_policy"],
        "paired_rfq_case_ids": rfq["paired_case_ids"], "strict_rfq_case_ids": rfq["strict_case_ids"],
        "extension_astra_continuation": {"earlier_candidate_questions_retained": 13, "sol_routed_customer_replies_retained": 1},
        "design": {
            "conditions": 43, "per_turn_timeout_seconds": 3600,
            "candidate_repetitions": 1, "claude_infrastructure_retries": 0,
            "astra_image_generation": True, "claude_image_generation": False,
            "astra_isolation": "instruction_based_read_isolation", "claude_isolation": "operating_system",
            "judge": "gemini-2.5-pro", "temperature": 0,
            "scoring_policy": "v04-weighted-only-v1", "hard_gate_veto": False,
            "external_weighted_pass_threshold": 0.7, "expert_acceptance_measured": False,
        },
        "sol_extension_attempt": {"planned": 20, "scored": 0, "native_calls": 64, "http_429_calls": 60, "actual_customer_rounds": 2, "exclusion": "infrastructure_interruption", "included_in_rfq_episodes": False},
    })
    write_json(output / "provenance.json", {
        "release_version": "0.1.0", "release_date": "2026-10-26", "archive_as_of": archive["as_of"],
        "dashboard_source_commit": paper["publication"]["source_commit"],
        "paper_revision": "2026-10-24", "new_model_calls": 0, "new_human_labels": 0,
        "source_files": [{"source_id": name, "sha256": digest(path), "bytes": path.stat().st_size} for name, path in source_files],
        "transformations": [
            "Preserve 35 authored brief contracts; rewrite condition episode_source to its portable path.",
            "Copy all 24 verified project-owned input fixtures; assign the repository CC-BY-4.0 license and preserve upstream rights status.",
            "Project 40 RFQ cases into separate opening-only and evaluator-only files; omit private source pointers.",
            "Export 100 archived RFQ candidate/customer dialogues with scoring annotations; omit provider/tool logs, final summaries, and diagnostics.",
            "Preserve archived RFQ scores; expose only numeric status/score metadata for the 301 archive protocol units.",
            "Retain 333 observation associations to reproduce lineage counts; these are not 333 independent tasks or model runs.",
            "Export separate historical Sol/Astra R1 score repetitions without replacing original scores.",
        ],
        "excluded": ["private credentials and local filesystem paths", "raw tool traces and hidden reasoning", "third-party source media", "model-generated design outputs", "original customer conversations", "private mentor identities or decisions"],
    })
    print(json.dumps({"output": str(output), "briefs": len(briefs), "conditions": len(conditions), "assets": len(assets), "rfq_cases": len(cases), "rfq_run_records": len(episodes), "observations": len(observations), "units": len(units)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--dashboard-dist", type=Path, required=True)
    parser.add_argument("--paper-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.eval_root, args.dashboard_dist, args.paper_snapshot, args.output)
