#!/usr/bin/env python3
"""Bridge a prompt-reading CLI agent to the JSON adapter protocol.

Usage: python /absolute/path/command_adapter.py -- your-agent [flags]
The target receives the complete public request on stdin. An optional {prompt}
argument is replaced by that text for CLIs that take a positional prompt.
Run from the candidate workspace. No provider-specific flags are assumed.
"""
import json
import subprocess
import sys
from pathlib import Path

request = json.load(sys.stdin)
arguments = sys.argv[1:]
if arguments and arguments[0] == "--":
    arguments = arguments[1:]
if not arguments:
    raise SystemExit("Supply an installed candidate CLI command after --")
prompt = ("Complete the current task turn described in the JSON below. Read the attached local assets. "
          "Only current and previous user messages are available. Save all current deliverables and render "
          "previews under output_dir; retain prior versions. Return your user-facing reply as text. "
          "Do not print private reasoning.\n\n" + json.dumps(request, ensure_ascii=False, indent=2))
positional = "{prompt}" in arguments
arguments = [prompt if arg == "{prompt}" else arg for arg in arguments]
completed = subprocess.run(arguments, input=None if positional else prompt, text=True,
                           stdout=subprocess.PIPE, stderr=sys.stderr, check=True)
output = Path(request["output_dir"])
files = sorted(str(p) for p in output.rglob("*") if p.is_file())
print(json.dumps({"message": completed.stdout, "artifacts": files, "done": False}, ensure_ascii=False))
