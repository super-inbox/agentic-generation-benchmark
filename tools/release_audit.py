#!/usr/bin/env python3
"""Audit the new release's text and local documentation links; no network access."""
from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/draft-bench-v0.1"
PATTERNS = {
    "local_absolute_path": re.compile(r"/(?:Users|home|private|mnt)/"),
    "email_address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "signed_or_authenticated_url": re.compile(r"X-Amz-Signature|X-Goog-Signature|access_token=|api_key=", re.I),
    "credential_token": re.compile(r"(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_-]{15,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def main():
    failures = []
    data_files = [p for p in DATA.rglob("*") if p.suffix in {".json", ".jsonl"}]
    for path in data_files:
        text = path.read_text(encoding="utf-8")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)}: {name}")
    docs = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md")) + [ROOT / "data/README.md"]
    for path in docs:
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            link = match.group(1)
            if "://" in link or link.startswith("#") or link.startswith("mailto:"):
                continue
            local = unquote(link.split("#", 1)[0])
            if local and not (path.parent / local).exists():
                failures.append(f"{path.relative_to(ROOT)}: broken local link {link}")
    print(json.dumps({"ok": not failures, "data_text_files": len(data_files), "documents": len(docs), "failures": failures}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
