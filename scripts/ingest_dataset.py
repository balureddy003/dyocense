#!/usr/bin/env python3
"""
CLI helper to ingest datasets into the knowledge service.

Phase 1 ingestion supports CSV and JSONL files. Metadata such as schema_version
or source_uri can be provided via CLI flags to ensure downstream filtering is
possible.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import uuid
from typing import Dict, Iterable

from packages.knowledge import KnowledgeClient, KnowledgeDocument


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest datasets into Dyocense knowledge plane.")
    parser.add_argument("dataset_path", type=pathlib.Path)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--collection", default="default")
    parser.add_argument("--service-url", default=None, help="Knowledge service base URL.")
    parser.add_argument("--metadata", default="{}", help="JSON object with additional metadata.")
    parser.add_argument("--goal-field", default=None, help="Optional field containing goal text per row.")
    return parser.parse_args()


def load_records(path: pathlib.Path) -> Iterable[Dict[str, str]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                yield row
    elif path.suffix.lower() in {".jsonl", ".ndjson"}:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                yield json.loads(line)
    else:
        raise ValueError(f"Unsupported dataset format: {path.suffix}")


def main() -> None:
    args = parse_args()
    metadata = json.loads(args.metadata)
    client = KnowledgeClient(base_url=args.service_url)

    for row in load_records(args.dataset_path):
        text = args.goal_field and row.get(args.goal_field)
        if not text:
            text = json.dumps(row, sort_keys=True)
        document = KnowledgeDocument(
            tenant_id=args.tenant_id,
            project_id=args.project_id,
            collection=args.collection,
            document_id=str(uuid.uuid5(uuid.NAMESPACE_URL, text)),
            text=text,
            metadata=metadata,
        )
        client.ingest(document)


if __name__ == "__main__":
    main()
