#!/usr/bin/env python3
"""Deterministic plumbing demo. This is NOT a design agent or benchmark result."""
import json
import sys
from pathlib import Path

request = json.load(sys.stdin)
if request["track"] == "rfq":
    questions = ["What will this be used for?", "How many do you need?", "What materials do you have?",
                 "What should the finished deliverable be?", "What look or references do you like?",
                 "What is your deadline?", "What is your budget?", "Thank you, I have no more questions."]
    index = request["turn_index"]
    result = {"message": questions[index], "artifacts": [], "done": index == 7}
else:
    path = Path(request["output_dir"]) / "demo.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
                    '<rect width="400" height="200" fill="#eeeeee"/>'
                    '<text x="20" y="100">PLUMBING DEMO ONLY</text></svg>', encoding="utf-8")
    result = {"message": "Synthetic plumbing demo; no attempt to satisfy this brief.", "artifacts": [str(path)]}
print(json.dumps(result))
