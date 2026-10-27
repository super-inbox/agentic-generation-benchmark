"""Offline command-line tools for the DRAFT-Bench data release."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import report, validate
from .common import DEFAULT_DATA, read_json, read_rows, unique
from .prepare import prepare
from .rfq.scoring import score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="release directory (defaults to the bundled v0.1)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="verify checksums, boundaries, identities, counts, and all 100 RFQ scores")
    commands.add_parser("report", help="recompute archive counts, completion, RFQ metrics, and R1 repetitions")
    bundle = commands.add_parser("prepare", help="export one first-turn candidate input; does not run a model")
    bundle.add_argument("track", choices=("design", "rfq"))
    bundle.add_argument("identifier")
    bundle.add_argument("--out", type=Path, required=True)
    scorer = commands.add_parser("rfq-score", help="score independently annotated RFQ evidence")
    scorer.add_argument("--case-id", required=True)
    scorer.add_argument("--episode", type=Path, required=True)
    commands.add_parser("rfq-example", help="score the two explicitly synthetic reference examples")
    try:
        args = parser.parse_args()
        data = args.data.resolve()
        if args.command == "validate":
            result = validate(data)
        elif args.command == "report":
            result = report(data)
        elif args.command == "prepare":
            result = prepare(data, args.track, args.identifier, args.out)
        elif args.command == "rfq-score":
            cases = unique(read_rows(data / "rfq/evaluator_cases.jsonl"), "case_id")
            result = score(cases[args.case_id], read_json(args.episode))
        else:
            example = read_json(Path(__file__).parent / "rfq/examples.json")
            result = {"kind": "synthetic_unit_test_examples_not_model_results",
                      "results": [score(example["case"], e) for e in example["episodes"]]}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"draftbench: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
