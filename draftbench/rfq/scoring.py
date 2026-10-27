"""Deterministic RFQ v0.3 arithmetic over independently annotated evidence.

This module does not make semantic judgments or run any models.
"""

import json
import sys
from fractions import Fraction
from pathlib import Path

from .disclosure_policy import FIELDS, RUBRIC, select_field


def validate_case(case):
    if case["protocol_id"] != RUBRIC["protocol_id"]:
        raise ValueError("Protocol mismatch")
    if sorted(f["field_id"] for f in case["fields"]) != sorted(FIELDS):
        raise ValueError("Every canonical field must occur exactly once")
    components = {}
    fields = {}
    for field in case["fields"]:
        fid = field["field_id"]
        fields[fid] = field
        if type(field["critical"]) is not bool:
            raise ValueError("critical must be boolean")
        if field["availability"] not in RUBRIC["availability"]:
            raise ValueError("Unknown availability")
        if not isinstance(field.get("reply"), str) or not field["reply"].strip():
            raise ValueError("Every field needs an authored ordinary-language reply")
        if field["availability"] == "not_applicable":
            if field["critical"] or field["components"] or not field.get("not_applicable_reason"):
                raise ValueError("N/A fields need a reason, no components, and cannot be critical")
        elif not field["components"]:
            raise ValueError("Applicable fields need minimum-answer components")
        for component in field["components"]:
            cid = component["component_id"]
            if not cid or cid in components or "value" not in component:
                raise ValueError("Components need unique IDs and frozen values")
            components[cid] = fid
    initial = case["initially_known_component_ids"]
    if len(initial) != len(set(initial)) or not set(initial).issubset(components):
        raise ValueError("Invalid initial component IDs")
    if not any(f["critical"] for f in fields.values()):
        raise ValueError("Freeze a nonempty critical set")
    remaining = {
        fid: {c["component_id"] for c in f["components"]} - set(initial)
        for fid, f in fields.items() if f["availability"] != "not_applicable"
    }
    if not any(remaining.values()):
        raise ValueError("No clarification target remains after the opening")
    return fields, components, remaining


def validate_episode(case, episode, components):
    if episode["case_id"] != case["case_id"]:
        raise ValueError("Case mismatch")
    if episode["status"] not in RUBRIC["episode_accounting"]["statuses"]:
        raise ValueError("Unsupported status; simulator violations are not exclusions")
    if episode["status"] == "infrastructure_excluded":
        allowed = RUBRIC["episode_accounting"]["infrastructure_excluded"]
        if episode.get("exclusion_reason") not in allowed:
            raise ValueError("Missing or unapproved infrastructure exclusion reason")
        return
    if episode.get("annotation_complete") is not True:
        raise ValueError("Missing annotations are not official zero scores")
    turns = episode["turns"]
    if len(turns) > RUBRIC["interaction"]["max_rounds"]:
        raise ValueError("Transcript exceeds declared customer-round budget")
    for number, turn in enumerate(turns, 1):
        if turn["round"] != number:
            raise ValueError("Customer rounds must be contiguous and one-based")
        targets = [t["field_id"] for t in turn["targets"]]
        if turn["selected_field"] != select_field(targets):
            raise ValueError("Selected field does not match frozen policy")
        for label in ("targets", "audited_targets"):
            if label not in turn:
                continue
            select_field([t["field_id"] for t in turn[label]])
            positions = []
            for target in turn[label]:
                quote = target["request_quote"]
                if not quote or quote not in turn["agent_message"]:
                    raise ValueError("Target request lacks literal agent evidence")
                positions.append(turn["agent_message"].index(quote))
            if positions != sorted(positions):
                raise ValueError("Target fields must preserve agent request order")
        seen = set()
        for disclosure in turn["disclosures"]:
            cid = disclosure["component_id"]
            if cid not in components or components[cid] != disclosure["field_id"]:
                raise ValueError("Disclosure references a foreign component")
            if cid in seen:
                raise ValueError("Duplicate component label in one response")
            seen.add(cid)
            correct = disclosure["correct"]
            if correct is not None and type(correct) is not bool:
                raise ValueError("correct must be true, false, or null")
            quote = disclosure["evidence_quote"]
            if not quote or quote not in turn["customer_message"]:
                raise ValueError("Disclosure lacks literal customer evidence")


def checkpoint(case, episode, k, fields, remaining):
    initial = set(case["initially_known_component_ids"])
    first = {}
    unresolved = set()
    incorrect = 0
    for turn in episode["turns"][:k]:
        # Live routing determines what was actually said. Independent audit may
        # correct elicitation attribution, but must never rewrite that history.
        targeted = {t["field_id"] for t in turn.get("audited_targets", turn["targets"])}
        for disclosure in turn["disclosures"]:
            cid, fid = disclosure["component_id"], disclosure["field_id"]
            if disclosure["correct"] is None:
                if cid not in initial and cid not in first:
                    unresolved.add(fid)
                continue
            if not disclosure["correct"]:
                incorrect += 1
                continue
            if cid in initial or cid in first:
                continue
            source = (
                "unprompted" if fid not in targeted else
                "elicited" if fid == turn["selected_field"] else "policy_overflow"
            )
            first[cid] = {"field_id": fid, "round": turn["round"],
                          "source": source, "evidence_quote": disclosure["evidence_quote"]}
    goals = {fid: components for fid, components in remaining.items() if components}
    elicited = {}
    observed = {}
    upper = {}
    for fid, needed in goals.items():
        observed[fid] = int(fid not in unresolved and needed.issubset(first))
        elicited[fid] = int(observed[fid] and all(first[c]["source"] == "elicited" for c in needed))
        upper[fid] = 1 if fid in unresolved else elicited[fid]
    baseline = [fid for fid, needed in remaining.items() if not needed]
    critical = [fid for fid, f in fields.items() if f["critical"]]
    missing = [fid for fid in critical if fid not in baseline and not elicited[fid]]
    upper_missing = [fid for fid in critical if fid not in baseline and not upper[fid]]
    denominator = len(goals)
    ec = Fraction(sum(elicited.values()), denominator)
    ec_upper = Fraction(sum(upper.values()), denominator)
    threshold = Fraction(str(RUBRIC["success"]["min_elicited_coverage"]))
    disclosed = {v["field_id"] for v in first.values()}
    leaked = {v["field_id"] for v in first.values() if v["source"] == "unprompted"}
    overflow = {v["field_id"] for v in first.values() if v["source"] == "policy_overflow"}
    leak_rate = len(leaked) / len(disclosed) if disclosed and not unresolved else None
    return {
        "checkpoint": k, "actual_customer_rounds": min(k, len(episode["turns"])),
        "field_denominator": denominator, "elicited_field_count": sum(elicited.values()),
        "elicited_coverage": float(ec), "elicited_coverage_upper": float(ec_upper),
        "observed_coverage": sum(observed.values()) / denominator,
        "elicited_fields": elicited, "observed_fields": observed,
        "initially_known_fields": baseline, "missing_critical_fields": missing,
        "threshold_and_critical_met": ec >= threshold and not missing,
        "threshold_and_critical_upper": ec_upper >= threshold and not upper_missing,
        "first_correct_disclosures": first, "unprompted_fields": sorted(leaked),
        "disclosed_fields": sorted(disclosed), "policy_overflow_fields": sorted(overflow),
        "unprompted_disclosure_count": len(leaked), "disclosed_field_count": len(disclosed),
        "leak_rate": leak_rate, "unresolved_fields": sorted(unresolved),
        "incorrect_disclosure_count": incorrect,
    }


def score(case, episode):
    fields, components, remaining = validate_case(case)
    validate_episode(case, episode, components)
    result = {"protocol_id": RUBRIC["protocol_id"], "case_id": case["case_id"],
              "episode_id": episode["episode_id"], "status": episode["status"]}
    if episode["status"] == "infrastructure_excluded":
        return {**result, "metrics": None, "exclusion_reason": episode["exclusion_reason"]}
    snapshots = {str(k): checkpoint(case, episode, k, fields, remaining)
                 for k in RUBRIC["interaction"]["checkpoints"]}
    last = snapshots["8"]
    return {**result, "provisional": bool(last["unresolved_fields"]),
            "metrics": {"elicited_coverage_at_6": snapshots["6"]["elicited_coverage"],
                        "elicited_coverage_at_8": last["elicited_coverage"],
                        "success_at_8": last["threshold_and_critical_met"],
                        "leak_rate": last["leak_rate"]},
            "checkpoints": snapshots,
            "diagnostic_bounds": {"elicited_coverage_at_6_upper": snapshots["6"]["elicited_coverage_upper"],
                                  "elicited_coverage_at_8_upper": last["elicited_coverage_upper"],
                                  "success_at_8_upper": last["threshold_and_critical_upper"]}}


def aggregate(results):
    if any(r["protocol_id"] != RUBRIC["protocol_id"] for r in results):
        raise ValueError("Cannot pool protocols")
    if len({r["case_id"] for r in results}) != len(results):
        raise ValueError("Aggregate one attempt per case; reduce paired repeats within case first")
    scored = [r for r in results if r["status"] == "scored"]
    n = len(scored)
    leaks = sum(r["checkpoints"]["8"]["unprompted_disclosure_count"] for r in scored)
    disclosures = sum(r["checkpoints"]["8"]["disclosed_field_count"] for r in scored)
    pending = sum(r["provisional"] for r in scored)
    metrics = {}
    for name in (m["name"] for m in RUBRIC["headline_metrics"]):
        metrics[name] = (leaks / disclosures if disclosures and not pending else None) if name == "leak_rate" else (
            sum(r["metrics"][name] for r in scored) / n if n else None)
    return {"protocol_id": RUBRIC["protocol_id"], "planned": len(results), "scored": n,
            "infrastructure_excluded": len(results) - n, "provisional": pending,
            "metrics": metrics,
            "diagnostic_upper_bounds": {
                name: sum(r["diagnostic_bounds"][name] for r in scored) / n if n else None
                for name in ("elicited_coverage_at_6_upper", "elicited_coverage_at_8_upper", "success_at_8_upper")
            },
            "success_count": sum(r["metrics"]["success_at_8"] for r in scored),
            "success_denominator": n, "leak_numerator": leaks, "leak_denominator": disclosures,
            "excluded_cases": [{"case_id": r["case_id"], "reason": r["exclusion_reason"]}
                               for r in results if r["status"] == "infrastructure_excluded"]}


if __name__ == "__main__":
    bundle = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps([score(bundle["case"], episode) for episode in bundle["episodes"]],
                     ensure_ascii=False, indent=2))
