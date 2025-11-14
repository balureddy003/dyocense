#!/usr/bin/env python3
"""
Validate OPS JSON documents against the canonical schema.

Usage:
    python scripts/validate_ops.py examples/inventory_simple.ops.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "payloads",
        nargs="+",
        type=Path,
        help="One or more OPS JSON files to validate.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("packages/contracts/schemas/ops.schema.json"),
        help="Path to the OPS JSON Schema.",
    )
    args = parser.parse_args()

    try:
        import jsonschema
    except ImportError:
        sys.stderr.write(
            "The 'jsonschema' package is required. Install with 'pip install jsonschema'.\n"
        )
        return 1

    schema = load_json(args.schema)
    validator = jsonschema.Draft202012Validator(schema)

    failed = False
    for payload_path in args.payloads:
        document = load_json(payload_path)
        errors = sorted(validator.iter_errors(document), key=lambda e: e.path)
        if errors:
            failed = True
            sys.stderr.write(f"{payload_path}: invalid\n")
            for error in errors:
                location = "/".join(str(part) for part in error.path) or "<root>"
                sys.stderr.write(f"  - {location}: {error.message}\n")
        else:
            sys.stdout.write(f"{payload_path}: valid\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
