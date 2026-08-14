#!/usr/bin/env python3
"""Create a consistent SQLite snapshot, including WAL content."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} SOURCE_DB DEST_DB", file=sys.stderr)
        return 2
    source_path, destination_path = map(Path, sys.argv[1:])
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(destination_path)
    try:
        with destination:
            source.backup(destination)
    finally:
        source.close()
        destination.close()
    print(f"SQLite snapshot created: {destination_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
