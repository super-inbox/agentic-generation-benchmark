"""Reference information policy; semantic target recognition is a separate role."""

import json
from pathlib import Path

RUBRIC = json.loads(Path(__file__).with_name("rubric.json").read_text())
FIELDS = tuple(RUBRIC["field_order"])


def select_field(ordered_targets):
    """Never skip repeated/unknown first requests to find a more useful answer."""
    for target in ordered_targets:
        if target not in FIELDS:
            raise ValueError(f"Unknown target field: {target}")
    if len(set(ordered_targets)) != len(ordered_targets):
        raise ValueError("Router targets must be deduplicated")
    return ordered_targets[0] if ordered_targets else None


def renderer_payload(case, ordered_targets, neutral_voice="Brief, everyday English."):
    """Project only one authored reply; do not pass the full case to a renderer."""
    selected = select_field(ordered_targets)
    reply = "I'm not sure what you mean. Could you explain that a little?"
    if selected is not None:
        field = next(f for f in case["fields"] if f["field_id"] == selected)
        reply = field["reply"]
    return {"neutral_voice": neutral_voice, "selected_answer": reply}


def render_fixed(case, ordered_targets):
    """Default MVP language mode: no model call and no response resampling."""
    return renderer_payload(case, ordered_targets)["selected_answer"]
