"""Runnable inventory; archive-only observations are deliberately not tasks."""
from .common import read_rows, unique
from .prepare import build_request


def catalog(data, track=None):
    episodes = unique(read_rows(data / "briefs/episodes.jsonl"), "id")
    rows = []
    if track in (None, "design"):
        for condition in read_rows(data / "briefs/conditions.jsonl"):
            request, files = build_request(data, "design", condition["id"])
            episode = episodes[condition["base_brief_id"]]
            rows.append({"track": "design", "id": condition["id"], "brief_id": episode["id"],
                         "asset_count": len(files), "turns": 1 + len(episode["feedback"]),
                         "intentionally_missing_inputs": [i["id"] for i in episode["inputs"]
                                                          if i.get("availability") == "intentionally_missing"],
                         "input_ready": True})
    if track in (None, "rfq"):
        for opening in read_rows(data / "rfq/openings.jsonl"):
            build_request(data, "rfq", opening["case_id"])
            rows.append({"track": "rfq", "id": opening["case_id"], "asset_count": 0,
                         "max_customer_rounds": 8, "input_ready": True})
    return {"data_version": "draft-bench-v0.1", "task_count": len(rows), "tasks": rows,
            "archive_only_groups_excluded": True}
