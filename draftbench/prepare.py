"""Export a single candidate-visible input bundle, without evaluator material.

File projection is not an operating-system sandbox. Mount only the exported
directory in the candidate environment; keep this repository with the evaluator.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .common import ROOT, contained, read_rows, sha256, unique, write_json


def build_request(data, track, identifier, complete=False):
    if track == "rfq":
        opening = unique(read_rows(data / "rfq/openings.jsonl"), "case_id")[identifier]
        prompt = (ROOT / "draftbench/rfq/candidate_prompt.txt").read_text(encoding="utf-8")
        return {"format": "draftbench-candidate-bundle/1", "track": "rfq", "id": identifier,
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": opening["opening_message"]}],
                "assets": [], "max_customer_rounds": 8}, []
    condition = unique(read_rows(data / "briefs/conditions.jsonl"), "id")[identifier]
    assets = unique(read_rows(data / "assets/manifest.jsonl"), "asset_id")
    files, visible_assets = [], []
    for item in condition["input_assets"]:
        asset = assets[item["asset_id"]]
        source = contained(data, asset["path"])
        if sha256(source) != asset["sha256"]:
            raise ValueError(f"Fixture checksum mismatch: {asset['asset_id']}")
        destination = "assets/" + asset["asset_id"] + source.suffix
        files.append((source, destination))
        visible_assets.append({**item, "path": destination, "sha256": asset["sha256"]})
    request = {"format": "draftbench-candidate-bundle/1", "track": "design", "id": identifier,
            "messages": [{"role": "user", "content": condition["query"]}],
            "input_context": condition["input_context"], "assets": visible_assets,
            "preference_memory": condition["preference_memory"]}
    if complete:
        episode = unique(read_rows(data / "briefs/episodes.jsonl"), "id")[condition["base_brief_id"]]
        visible_ids = {i["id"] for i in condition["input_context"]}
        request["format"] = "draftbench-candidate-bundle/2"
        request["task_contract"] = {
            "constraints": episode["constraints"], "deliverables": episode["deliverables"],
            "structured_artifacts": episode["structured_artifacts"],
            "reference_contract": [r for r in episode.get("reference_contract", []) if r["input_id"] in visible_ids],
            "human_checkpoints": episode.get("human_checkpoints", []),
            "inputs": [i for i in episode["inputs"] if i["id"] in visible_ids
                       or i.get("availability") == "intentionally_missing"],
            "edit_parameters": [{k: v for k, v in p.items() if k != "verification"}
                                for p in episode.get("edit_parameters", [])],
            "initial_project_state": episode.get("project_state"),
        }
    return request, files


def prepare(data, track, identifier, destination, complete=False):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("Output already exists; use a new directory to avoid mixing runs")
    try:
        destination.relative_to(data.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("Do not write candidate runs into the frozen dataset")
    # Validate identifiers and all source hashes before writing any output.
    request, files = build_request(data, track, identifier, complete=complete)
    for source, relative in files:
        target = contained(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    write_json(destination / "request.json", request)
    return {"output": str(destination), "track": track, "id": identifier, "asset_count": len(files),
            "scope": "initial_candidate_input_only", "sandbox_created": False}
