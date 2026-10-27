"""Integrity, reference-score replay, and denominator-aware reporting."""
from __future__ import annotations

from .common import contained, read_json, read_rows, sha256, unique
from .rfq.scoring import aggregate, score, validate_case


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay_rfq(data):
    cases = unique(read_rows(data / "rfq/evaluator_cases.jsonl"), "case_id")
    episodes = read_rows(data / "results/rfq_episodes.jsonl")
    stored = read_rows(data / "results/rfq_scores.jsonl")
    expected = {}
    for row in stored:
        key = (row["model"], row["result"]["case_id"])
        require(key not in expected, f"Duplicate archived score: {key}")
        expected[key] = row
    seen = set()
    replayed = []
    for episode in episodes:
        key = (episode["model"], episode["case_id"])
        require(key not in seen, f"Multiple attempts require an explicit selection rule: {key}")
        seen.add(key)
        require(key in expected, f"Missing archived score: {key}")
        require(episode["batch"] == cases[episode["case_id"]]["batch"], f"Case/batch mismatch: {key}")
        fresh = score(cases[episode["case_id"]], episode)
        archived = expected[key]["result"]
        for field, value in fresh.items():
            require(archived.get(field) == value, f"Frozen score mismatch: {key} / {field}")
        replayed.append({"model": episode["model"], "batch": episode["batch"], "result": fresh})
    require(seen == set(expected), "Not every archived score has a replayable episode")
    return replayed


def report(data):
    observations = read_rows(data / "results/archive_observations.jsonl")
    units = read_rows(data / "results/archive_units.jsonl")
    unit_map = unique(units, "key")
    unique(observations, "observation_id")
    require(all(o["unit_key"] in unit_map for o in observations), "Observation references an unknown protocol unit")
    design = [u for u in units if u["kind"] == "design"]
    counts = {
        "brief_bank_briefs": len(read_rows(data / "briefs/episodes.jsonl")),
        "brief_bank_conditions": len(read_rows(data / "briefs/conditions.jsonl")),
        "input_fixtures": len(read_rows(data / "assets/manifest.jsonl")),
        "rfq_scenarios": len(read_rows(data / "rfq/openings.jsonl")),
        "archive_observations": len(observations), "archive_protocol_units": len(units),
        "archive_id_lineages": len({o["brief_id"] for o in observations}),
        "historical_associations": sum(o["reused"] for o in observations),
        "design_protocol_units": len(design),
    }
    groups = {}
    for group in sorted({u["group"] for u in design}):
        selected = [u for u in design if u["group"] == group]
        groups[group] = {"protocol_units": len(selected)}
        for model in ("astra", "claude"):
            values = [u["models"][model] for u in selected]
            groups[group][model] = {
                "completed": sum(v["completed"] is True for v in values),
                "scored": sum(v["score"] is not None and v["score"].get("lower") is not None for v in values),
            }
    results = replay_rfq(data)
    counts["rfq_run_records"] = len(results)
    counts["rfq_scored_runs"] = sum(r["result"]["status"] == "scored" for r in results)
    settings = read_json(data / "results/experiment_settings.json")
    eligible = {
        model: {r["result"]["case_id"] for r in results if r["model"] == model and r["result"]["status"] == "scored"}
        for model in ("astra", "claude")
    }
    paired = eligible["astra"] & eligible["claude"]
    strict = paired - set(settings["rfq_attempt_policy"]["original_reattempt_case_ids"])
    require(paired == set(settings["paired_rfq_case_ids"]), "Paired RFQ denominator differs from frozen policy")
    require(strict == set(settings["strict_rfq_case_ids"]), "Strict RFQ denominator differs from frozen policy")
    cohorts = {
        "original": {r["result"]["case_id"] for r in results if r["batch"] == "original"},
        "extension": {r["result"]["case_id"] for r in results if r["batch"] == "extension"},
        "paired_39": paired, "strict_36": strict,
    }
    cohorts["extension_paired"] = cohorts["extension"] & paired
    rfq = {}
    for cohort, ids in cohorts.items():
        rfq[cohort] = {}
        for model in ("astra", "claude", "sol"):
            if model == "sol" and cohort != "original":
                continue
            selected = [r["result"] for r in results if r["model"] == model and r["result"]["case_id"] in ids]
            if selected:
                summary = aggregate(selected)
                rfq[cohort][model] = {key: summary[key] for key in ("planned", "scored", "infrastructure_excluded", "provisional", "metrics", "success_count", "success_denominator", "leak_numerator", "leak_denominator")}
    r1 = read_json(data / "results/calibration_r1.json")
    varying = sum(any(max(r["lower"] for r in case[m]["repetitions"]) != min(r["lower"] for r in case[m]["repetitions"]) or max(r["upper"] for r in case[m]["repetitions"]) != min(r["upper"] for r in case[m]["repetitions"]) for m in ("sol", "astra")) for case in r1["cases"])
    return {"counts": counts, "design_completion_by_group": groups, "rfq": rfq,
            "r1": {"pairs": len(r1["cases"]), "judge_calls": sum(len(c["sol"]["repetitions"]) for c in r1["cases"]), "varying_pairs": varying, "mentor_final_approval": r1["mentor_final_approval"]},
            "interpretation": "Descriptive archived system comparisons; no pooled quality ranking or expert acceptance rate."}


def validate(data):
    manifest = read_json(data / "manifest.json")
    require(manifest["release_version"] == "0.1.0", "Unsupported release version")
    listed = unique(manifest["files"], "path")
    actual = {p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file() and p != data / "manifest.json"}
    # The asset manifest is manifest.jsonl, and is therefore included above.
    require(set(listed) == actual, "Release file inventory mismatch (missing or extra files)")
    for name, item in listed.items():
        path = contained(data, name)
        require(path.is_file(), f"Missing file: {name}")
        require(path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"], f"Checksum mismatch: {name}")
    briefs = unique(read_rows(data / "briefs/episodes.jsonl"), "id")
    conditions = unique(read_rows(data / "briefs/conditions.jsonl"), "id")
    assets = unique(read_rows(data / "assets/manifest.jsonl"), "asset_id")
    for asset in assets.values():
        path = contained(data, asset["path"])
        require(sha256(path) == asset["sha256"], f"Input fixture mismatch: {asset['asset_id']}")
        require(asset["license"] == "CC-BY-4.0" and asset["contains_personal_data"] is False, "Unexpected asset rights/privacy metadata")
    expected_ids = {f"{b['id']}@{c['id']}" for b in briefs.values() for c in b["context_conditions"]}
    require(set(conditions) == expected_ids, "Condition projections do not cover the authored brief conditions")
    for condition in conditions.values():
        brief = briefs[condition["base_brief_id"]]
        context = next(c for c in brief["context_conditions"] if c["id"] == condition["context_condition"])
        allowed = {i["id"]: i for i in brief["inputs"] if i["id"] in context["include_input_ids"] and i["availability"] == "provided"}
        require(condition["query"] == context.get("query_override", brief["initial_query"]), "Initial query was changed")
        require({i["id"] for i in condition["input_context"]} == set(allowed), "Condition input boundary mismatch")
        require(condition["preference_memory"] == (brief["preference_memory"] if context["include_preference_memory"] else None), "Preference-memory boundary mismatch")
        for item in condition["input_assets"]:
            require(item["asset_id"] in assets and allowed[item["input_id"]]["asset_id"] == item["asset_id"], "Missing or disallowed input fixture")
        require(not ({"feedback", "rubric", "expected_workflow"} & condition.keys()), "Evaluator-only data in first-turn projection")
    cases = unique(read_rows(data / "rfq/evaluator_cases.jsonl"), "case_id")
    openings = unique(read_rows(data / "rfq/openings.jsonl"), "case_id")
    require(set(cases) == set(openings), "RFQ opening/case identity mismatch")
    for cid, case in cases.items():
        validate_case(case)
        require(case["opening_message"] == openings[cid]["opening_message"], f"RFQ opening mismatch: {cid}")
        require(set(openings[cid]) == {"case_id", "opening_message", "language", "batch", "family"}, "Hidden fields found in RFQ opening projection")
    result = report(data)
    require(result["counts"] == manifest["counts"], "Release counts do not match recomputed records")
    return {"ok": True, "checked_files": len(listed), "counts": result["counts"], "rfq_scores_replayed": result["counts"]["rfq_run_records"], "new_model_calls": 0}
