#!/usr/bin/env python3
"""Rebuild the release checksum manifest after a reviewed data change."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from draftbench.audit import report
from draftbench.common import DEFAULT_DATA, sha256, write_json


if __name__ == "__main__":
    data = DEFAULT_DATA
    files = [{"path": p.relative_to(data).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
             for p in sorted(data.rglob("*")) if p.is_file() and p != data / "manifest.json"]
    write_json(data / "manifest.json", {"release_version": "0.1.0", "release_date": "2026-10-26", "archive_as_of": "2026-10-23",
                                      "license": "CC-BY-4.0", "counts": report(data)["counts"], "files": files})
    print(f"Wrote {len(files)} checksums")
