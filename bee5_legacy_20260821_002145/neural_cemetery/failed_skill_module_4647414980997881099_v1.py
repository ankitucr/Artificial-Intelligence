# Dispatcher failed: Expecting value: line 1 column 1 (char 0)

#!/usr/bin/env python3
"""
schema_engine.py
=================
A minimal, self‑contained schema‑evolution engine.

The module parses CSV, JSON and XML payloads, infers a canonical Avro
schema for each source, and publishes schema changes via a tiny publish/subscribe
mechanism.  It is intentionally lightweight and uses only the Python
standard library.

Author: OpenAI ChatGPT
"""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Callable, Dict, Iterable, List, Sequence

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _parse_csv(data: str) -> List[Dict[str, Any]]:
    """Parse a CSV string into a list of dictionaries."""
    reader = csv.DictReader(StringIO(data))
    return [dict(row) for row in reader]


def _parse_json(data: str) -> Any:
    """Parse JSON string into a Python object."""
    if not data.strip():
        raise ValueError("Empty JSON payload")
    return json.loads(data)


def _parse_xml(data: str) -> List[Dict[str, Any]]:
    """Parse simple XML into a list of dictionaries.

    The XML must have a single root element whose children represent rows.
    Text nodes are converted to values; attributes are prefixed with '@'.
    """
    root = ET.fromstring(data)

    def element_to_dict(elem: ET.Element) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        # Process attributes
        for k, v in elem.attrib.items():
            d[f"@{k}"] = v
        # Process children
        for child in elem:
            if list(child):
                d[child.tag] = element_to_dict(child)
            else:
                d[child.tag] = child.text
        return d

    return [element_to_dict(child) for child in root]


# --------------------------------------------------------------------------- #
# Schema inference helpers
# --------------------------------------------------------------------------- #

_AvroType = Any  # simple representation of an Avro type

def _infer_type(value: Any) -> _AvroType:
    """Infer an Avro type from a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "long"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        # Assume homogeneous list; use first non‑null item
        if not value:
            return {"type": "array", "items": "string"}
        for item in value:
            if item is not None:
                return {"type": "array", "items": _infer_type(item)}
        return {"type": "array", "items": "string"}
    if isinstance(value, dict):
        # Nested record: will be handled separately
        return {"type": "record", "name": "Nested", "fields": []}
    return "string"


def _merge_types(a: _AvroType, b: _AvroType) -> _AvroType:
    """Return a unified Avro type for two candidate types."""
    # If types are equal, keep one
    if a == b:
        return a

    # Helper to normalise a type into a list of possible types
    def to_list(t: _AvroType) -> List[Any]:
        if isinstance(t, list):
            return t
        return [t]

    a_list = to_list(a)
    b_list = to_list(b)

    # Add 'null' if either side is nullable
    if "null" in a_list or "null" in b_list:
        types = set(a_list + b_list)
        return sorted(types, key=str)  # deterministic order
    # If both are simple types, create a nullable union
    return sorted([a, b, "null"], key=str)


def _infer_schema_from_records(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Infer an Avro schema from a sequence of dictionaries."""
    field_types: Dict[str, _AvroType] = defaultdict(lambda: "null")

    for record in records:
        for key, value in record.items():
            field_types[key] = _merge_types(field_types[key], _infer_type(value))

    fields: List[Dict[str, Any]] = []

    for name, typ in field_types.items():
        if isinstance(typ, dict) and typ.get("type") == "record":
            # Gather nested records for this field
            nested_vals = [r[name] for r in records if isinstance(r.get(name), dict)]
            nested_schema = _infer_schema_from_records(nested_vals) if nested_vals else {"fields": []}
            field_type = {
                "type": "record",
                "name": f"{name.capitalize()}Record",
                "fields": nested_schema["fields"],
            }
        else:
            field_type = typ

        fields.append(
            {"name": name, "type": field_type, "default": None}
        )

    return {"type": "record", "name": "RootRecord", "fields": fields}


# --------------------------------------------------------------------------- #
# Pub‑Sub
# --------------------------------------------------------------------------- #

@dataclass
class PubSub:
    """Very small publish/subscribe system for schema changes."""
    _subscribers: List[Callable[[Dict[str, Any]], None]] = field(default_factory=list)

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, schema: Dict[str, Any]) -> None:
        for cb in self._subscribers:
            cb(schema)


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #

@dataclass
class SchemaEvolutionEngine:
    pubsub: PubSub = field(default_factory=PubSub)
    _current_schema: Dict[str, Any] | None = None

    def ingest(self, source_type: str, data: str | bytes, source_name: str = "") -> Dict[str, Any]:
        """Ingest a payload and produce an Avro schema."""
        # Normalize to string
        if isinstance(data, bytes):
            data = data.decode()

        if source_type.lower() == "csv":
            records = _parse_csv(data)
        elif source_type.lower() == "json":
            records = _parse_json(data)
            records = records if isinstance(records, list) else [records]
        elif source_type.lower() == "xml":
            records = _parse_xml(data)
        else:
            raise ValueError(f"Unsupported source type: {source_type!r}")

        schema = _infer_schema_from_records(records)

        # Notify if schema changed
        if schema != self._current_schema:
            self._current_schema = schema
            self.pubsub.publish(schema)

        return schema

    def run(self, sources: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple sources."""
        return [self.ingest(src.get("type", ""), src.get("data", ""), src.get("name", "")) for src in sources]


# --------------------------------------------------------------------------- #
# Sample data
# --------------------------------------------------------------------------- #

SAMPLE_CSV = """\
id,name,age,score
1,Alice,30,85.5
2,Bob,25,90
3,Charlie,,78
"""

SAMPLE_JSON = """
[
    {"id": 1, "name": "Alice", "age": 30, "score": 85.5},
    {"id": 2, "name": "Bob", "age": 25, "score": 90},
    {"id": 3, "name": "Charlie", "age": null, "score": 78}
]
"""

SAMPLE_XML = """
<records>
  <record>
    <id>1</id>
    <name>Alice</name>
    <age>30</age>
    <score>85.5</score>
  </record>
  <record>
    <id>2</id>
    <name>Bob</name>
    <age>25</age>
    <score>90</score>
  </record>
  <record>
    <id>3</id>
    <name>Charlie</name>
    <age/>
    <score>78</score>
  </record>
</records>
"""


def _print_schema(schema: Dict[str, Any]) -> None:
    """Simple listener that prints a nicely formatted schema."""
    print("\n=== New schema published ===")
    print(json.dumps(schema, indent=2, ensure_ascii=False))


SAMPLE_ARGS = {
    "sources": [
        {"type": "csv", "data": SAMPLE_CSV, "name": "users_csv"},
        {"type": "json", "data": SAMPLE_JSON, "name": "users_json"},
        {"type": "xml", "data": SAMPLE_XML, "name": "users_xml"},
    ]
}


def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the skill.

    Parameters
    ----------
    args : dict
        Expected to contain a key ``sources`` which is a list of dictionaries
        with keys ``type`` (csv|json|xml) and ``data`` (string or bytes).

    Returns
    -------
    dict
        Mapping with a key ``schemas`` that contains the list of produced
        Avro schemas.
    """
    engine = SchemaEvolutionEngine()
    engine.pubsub.subscribe(_print_schema)
    schemas = engine.run(args.get("sources", []))
    return {"schemas": schemas}


if __name__ == "__main__":
    result = run(SAMPLE_ARGS)

    # Basic sanity check: every schema must have at least four fields.
    for schema in result["schemas"]:
        assert isinstance(schema, dict)
        assert len(schema.get("fields", [])) >= 4, "Expected at least 4 fields"

    print("\nAll schemas generated successfully.")