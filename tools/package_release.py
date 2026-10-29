#!/usr/bin/env python3
"""Package committed DRAFT-Bench data and tools without the legacy VIR archive."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
PATHS = ["README.md", "README.zh-CN.md", "DATA_CARD.md", "CONTRIBUTING.md", "CHANGELOG.md", "CITATION.cff",
         "LICENSE", "LICENSE-CODE", "data/README.md", "data/draft-bench-v0.1", "draftbench", "docs", "schemas", "tests", "tools",
         "examples", "requirements-eval.txt", "requirements-dev.txt", ".env.example", ".gitignore"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--version", default="0.2.0", help="toolkit version; frozen dataset stays v0.1")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise SystemExit("Version must be a semantic version number")
    commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}"], cwd=ROOT, text=True).strip()
    args.out.mkdir(parents=True, exist_ok=True)
    name = "draftbench-v" + args.version
    archive = args.out.resolve() / (name + ".zip")
    checksum = archive.with_suffix(".zip.sha256")
    if archive.exists() or checksum.exists():
        raise SystemExit("Refusing to replace an existing release package")
    subprocess.run(["git", "archive", "--format=zip", f"--prefix={name}/", f"--output={archive}", commit, *PATHS], cwd=ROOT, check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest, "commit": commit}))
