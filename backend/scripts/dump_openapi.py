"""Dump the FastAPI OpenAPI schema to stdout (or to a file with --out).

Used by the schema-drift CI gate: regenerate the schema from the live app and
diff against the committed `backend/openapi.json` snapshot. Any divergence
fails the build.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def dump() -> str:
    from app.main import app

    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump FastAPI OpenAPI schema as JSON.")
    parser.add_argument("--out", type=Path, default=None, help="Write to file instead of stdout.")
    args = parser.parse_args()
    text = dump()
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
