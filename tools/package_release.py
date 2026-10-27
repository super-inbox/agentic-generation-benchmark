#!/usr/bin/env python3
"""Package committed DRAFT-Bench data and tools without the legacy VIR archive."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATHS = ["README.md", "README.zh-CN.md", "DATA_CARD.md", "CONTRIBUTING.md", "CHANGELOG.md", "CITATION.cff",
         "LICENSE", "LICENSE-CODE", "data/README.md", "data/draft-bench-v0.1", "draftbench", "docs", "schemas", "tests", "tools"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}"], cwd=ROOT, text=True).strip()
    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.out.resolve() / "draftbench-v0.1.0.zip"
    checksum = archive.with_suffix(".zip.sha256")
    if archive.exists() or checksum.exists():
        raise SystemExit("Refusing to replace an existing release package")
    subprocess.run(["git", "archive", "--format=zip", "--prefix=draftbench-v0.1.0/", f"--output={archive}", commit, *PATHS], cwd=ROOT, check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest, "commit": commit}))
