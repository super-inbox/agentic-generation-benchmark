"""DRAFT-Bench data validation, portable episodes and online evaluation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import report, validate
from .common import DEFAULT_DATA, read_json, read_rows, unique, write_json
from .prepare import prepare
from .rfq.scoring import score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="release directory (defaults to the bundled v0.1)")
    parser.add_argument("--env-file", type=Path, help="optional KEY=value configuration, never executed as shell")
    parser.add_argument("--judge-model", help="Gemini evaluator model override; recorded with every run")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="verify checksums, boundaries, identities, counts, and all 100 RFQ scores")
    commands.add_parser("report", help="recompute archive counts, completion, RFQ metrics, and R1 repetitions")
    bundle = commands.add_parser("prepare", help="export one first-turn candidate input; does not run a model")
    bundle.add_argument("track", choices=("design", "rfq"))
    bundle.add_argument("identifier")
    bundle.add_argument("--out", type=Path, required=True)
    bundle.add_argument("--complete", action="store_true", help="include public deliverables and constraints (portable protocol v0.2)")
    listing = commands.add_parser("list", help="list and check every runnable public task input")
    listing.add_argument("--track", choices=("design", "rfq"))
    doctor = commands.add_parser("doctor", help="check inputs, evaluation dependencies and key presence")
    doctor.add_argument("--check-api", action="store_true", help="make one small paid API call; save its provenance")
    doctor.add_argument("--out", type=Path, default=Path("runs/api-check"))
    runner = commands.add_parser("run", help="run one task or an explicitly requested suite")
    runner.add_argument("track", choices=("design", "rfq"))
    runner.add_argument("identifier", nargs="?")
    runner.add_argument("--all", action="store_true", help="run the full public track; may incur model costs")
    runner.add_argument("--limit", type=int, help="limit an --all suite to its first N tasks")
    runner.add_argument("--agent-command", required=True, help="trusted command; JSON stdin/stdout, candidate cwd")
    runner.add_argument("--out", type=Path, required=True)
    runner.add_argument("--timeout", type=float, default=3600, help="candidate timeout per turn, seconds")
    runner.add_argument("--evaluate", action="store_true", help="evaluate each new run with the configured API key")
    evaluator = commands.add_parser("evaluate", help="evaluate an existing portable run; no candidate rerun")
    evaluator.add_argument("--run", type=Path, required=True)
    evaluator.add_argument("--out", type=Path, help="default: RUN/evaluation; must be new")
    summary = commands.add_parser("summarize", help="aggregate a run/suite into JSON and CSV")
    summary.add_argument("--runs", type=Path, required=True)
    summary.add_argument("--evaluation-name", default="evaluation", help="named rejudge directory to aggregate")
    summary.add_argument("--out", type=Path, help="new directory for summary.json and summary.csv")
    scorer = commands.add_parser("rfq-score", help="score independently annotated RFQ evidence")
    scorer.add_argument("--case-id", required=True)
    scorer.add_argument("--episode", type=Path, required=True)
    commands.add_parser("rfq-example", help="score the two explicitly synthetic reference examples")
    try:
        args = parser.parse_args()
        data = args.data.resolve()
        from .api import GeminiJudge, load_env
        from .catalog import catalog
        from .evaluate import evaluate
        from .runner import run
        from .summary import as_csv, summarize
        load_env(args.env_file)
        if args.command == "validate":
            result = validate(data)
        elif args.command == "report":
            result = report(data)
        elif args.command == "prepare":
            result = prepare(data, args.track, args.identifier, args.out, complete=args.complete)
        elif args.command == "list":
            result = catalog(data, args.track)
        elif args.command == "doctor":
            import importlib.util
            import os
            result = {"input_check": catalog(data)["task_count"],
                      "evaluation_dependencies": {m: importlib.util.find_spec(m) is not None for m in ("PIL", "pypdf")},
                      "evaluation_key_present": bool(os.environ.get("DRAFTBENCH_EVAL_API_KEY") or os.environ.get("GEMINI_API_KEY"))}
            if args.check_api:
                if data == args.out.resolve() or data in args.out.resolve().parents:
                    raise ValueError("Do not write API logs into frozen data")
                judge = GeminiJudge(args.judge_model)
                result["api_check"] = judge.call("connectivity_check", 'Return JSON {"ok":true}.', {"ping": True}, args.out)
                if result["api_check"] != {"ok": True}:
                    raise ValueError("API check returned unexpected content")
        elif args.command == "run":
            validate(data)
            if bool(args.identifier) == args.all:
                raise ValueError("Specify exactly one task ID or --all")
            if args.limit is not None and (not args.all or args.limit < 1):
                raise ValueError("--limit requires --all and a positive integer")
            if args.out.exists():
                raise ValueError("Run output already exists; use a new attempt directory")
            if data == args.out.resolve() or data in args.out.resolve().parents:
                raise ValueError("Do not write runs into frozen data")
            judge = GeminiJudge(args.judge_model) if args.evaluate or args.track == "rfq" else None
            identifiers = ([t["id"] for t in catalog(data, args.track)["tasks"]][:args.limit]
                           if args.all else [args.identifier])
            results = []
            if args.all:
                write_json(args.out / "suite.json", {"format": "draftbench-suite/0.2", "track": args.track,
                           "planned_ids": identifiers, "judge": judge.config() if judge else None})
            for i, identifier in enumerate(identifiers, 1):
                print(f"[{i}/{len(identifiers)}] {args.track}: {identifier}", file=sys.stderr)
                output = args.out / identifier if args.all else args.out
                item = run(data, args.track, identifier, output, args.agent_command, args.timeout, judge)
                if args.evaluate:
                    item["evaluation"] = evaluate(data, output, judge, output / "evaluation")["status"]
                results.append(item)
            result = {"runs": results}
            if args.all:
                summary_data = summarize(args.out)
                write_json(args.out / "summary.json", summary_data)
                (args.out / "summary.csv").write_text(as_csv(summary_data), encoding="utf-8")
        elif args.command == "evaluate":
            validate(data)
            result = evaluate(data, args.run, GeminiJudge(args.judge_model), args.out or args.run / "evaluation")
        elif args.command == "summarize":
            result = summarize(args.runs, args.evaluation_name)
            if args.out:
                if data == args.out.resolve() or data in args.out.resolve().parents:
                    raise ValueError("Do not write summaries into frozen data")
                args.out.mkdir(parents=True, exist_ok=False)
                write_json(args.out / "summary.json", result)
                (args.out / "summary.csv").write_text(as_csv(result), encoding="utf-8")
        elif args.command == "rfq-score":
            cases = unique(read_rows(data / "rfq/evaluator_cases.jsonl"), "case_id")
            result = score(cases[args.case_id], read_json(args.episode))
        else:
            example = read_json(Path(__file__).parent / "rfq/examples.json")
            result = {"kind": "synthetic_unit_test_examples_not_model_results",
                      "results": [score(example["case"], e) for e in example["episodes"]]}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        if args.command == "evaluate" and result["status"] == "evaluation_error":
            return 2
        if args.command == "run" and any(r["status"] in ("agent_error", "timeout", "router_error") or r.get("evaluation") == "evaluation_error" for r in result["runs"]):
            return 2
        return 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"draftbench: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
