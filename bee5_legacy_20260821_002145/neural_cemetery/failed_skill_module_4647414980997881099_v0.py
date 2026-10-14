# Dispatcher failed: Expecting value: line 1 column 1 (char 0)

#!/usr/bin/env python3
"""
skill_module_4647415001234567890
Dynamic Schema‑Evolution Engine
================================

This module provides a minimal implementation of a dynamic schema‑evolution engine
capable of ingesting CSV, JSON, XML, Parquet and Avro feeds (the last two are
stubbed because the standard library does not provide native readers for them),
inferring a canonical Avro schema, and propagating schema changes to downstream
consumers via a simple publish–subscribe model.

The engine keeps its own in‑memory registry of subscribers. Whenever a new schema
is produced, all subscribers are notified with the updated schema. The schema
generation logic is intentionally lightweight: it supports nested structures,
arrays, and simple type promotion, while keeping the public API small.

The implementation uses only the Python standard library and is suitable for
small‑to‑medium data volumes typically found in unit tests or demonstrations.
"""

from __future__ import annotations

import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple, Union

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _parse_csv(data: str) -> List[Dict[str, Any]]:
    """Parse CSV string into a list of dictionaries."""
    reader = csv.DictReader(StringIO(data))
    return [dict(row) for row in reader]


def _parse_json(data: str) -> Any:
    """Parse JSON string and return the corresponding Python object."""
    return json.loads(data)


def _parse_xml(data: str) -> List[Dict[str, Any]]:
    """Parse simple XML into a list of dictionaries.

    This function expects the XML to have a single root element with multiple
    child elements that represent records. Each child element's attributes and
    text nodes are converted into dictionary entries.
    """
    root = ET.fromstring(data)
    records = []

    def elem_to_dict(elem: ET.Element) -> Dict[str, Any]:
        d = {}
        for child in elem:
            d[child.tag] = elem_to_dict(child) if list(child) else child.text
        # Include attributes
        if elem.attrib:
            d.update({f"@{k}": v for k, v in elem.attrib.items()})
        return d

    for child in root:
        records.append(elem_to_dict(child))
    return records


# --------------------------------------------------------------------------- #
# Schema inference
# --------------------------------------------------------------------------- #

_AvroType = Union[str, Dict[str, Any]]  # simple type name or complex type


def _infer_type(value: Any) -> _AvroType:
    """Infer a simple Avro type for a single Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        # Avro distinguishes int and long; use long for all integers
        return "long"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        # Assume homogenous lists; infer item type from first non-None element
        if not value:
            return {"type": "array", "items": "string"}  # fallback
        for item in value:
            if item is not None:
                item_type = _infer_type(item)
                break
        else:
            item_type = "string"
        return {"type": "array", "items": item_type}
    if isinstance(value, dict):
        # Nested record
        return {"type": "record", "name": "Nested", "fields": []}  # placeholder
    return "string"  # fallback


def _merge_types(a: _AvroType, b: _AvroType) -> _AvroType:
    """Merge two Avro types into a union if necessary."""
    if a == b:
        return a
    # Handle null union
    if a == "null":
        return ["null", b] if isinstance(b, str) else ["null", b]
    if b == "null":
        return ["null", a] if isinstance(a, str) else ["null", a]
    # For simplicity, convert to string if types differ
    return ["null", a, b] if a != b else a


def _infer_schema_from_records(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Infer an Avro schema from a list of dictionaries."""
    field_types: Dict[str, _AvroType] = {}
    for record in records:
        for key, value in record.items():
            typ = _infer_type(value)
            field_types[key] = _merge_types(field_types.get(key, "null"), typ)

    fields = []
    for name, typ in field_types.items():
        # Build field dict
        if isinstance(typ, list):
            field_type = typ
        elif isinstance(typ, dict) and typ.get("type") == "record":
            # Recursive nested record inference
            nested_records = [v for v in records if isinstance(v.get(name), dict)]
            nested_schema = _infer_schema_from_records([v[name] for v in nested_records])
            field_type = {
                "type": "record",
                "name": f"{name.capitalize()}Record",
                "fields": nested_schema["fields"],
            }
        else:
            field_type = typ
        fields.append(
            {
                "name": name,
                "type": field_type,
                "default": None,  # for simplicity
            }
        )
    return {
        "type": "record",
        "name": "RootRecord",
        "fields": fields,
    }


# --------------------------------------------------------------------------- #
# Pub‑Sub mechanism
# --------------------------------------------------------------------------- #

@dataclass
class PubSub:
    """Very small publish–subscribe system for schema changes."""

    _subscribers: List[Callable[[Dict[str, Any]], None]] = field(default_factory=list)

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, schema: Dict[str, Any]) -> None:
        for cb in self._subscribers:
            cb(schema)


# --------------------------------------------------------------------------- #
# Main engine
# --------------------------------------------------------------------------- #

@dataclass
class SchemaEvolutionEngine:
    pubsub: PubSub = field(default_factory=PubSub)
    _current_schema: Dict[str, Any] | None = None

    def ingest(self, source_type: str, data: str | bytes, source_name: str = "") -> Dict[str, Any]:
        """Ingest data of a given type and produce an Avro schema."""
        # Load raw data
        if source_type.lower() == "csv":
            records = _parse_csv(data.decode() if isinstance(data, bytes) else data)
        elif source_type.lower() == "json":
            obj = _parse_json(data.decode() if isinstance(data, bytes) else data)
            records = obj if isinstance(obj, list) else [obj]
        elif source_type.lower() == "xml":
            records = _parse_xml(data.decode() if isinstance(data, bytes) else data)
        elif source_type.lower() in ("parquet", "avro"):
            # Placeholder: not supported in stdlib
            raise NotImplementedError(f"'{source_type}' format is not supported without external libraries")
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        # Infer schema
        schema = _infer_schema_from_records(records)

        # Detect change
        if self._current_schema != schema:
            self._current_schema = schema
            self.pubsub.publish(schema)

        return schema

    def run(self, sources: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of sources. Each source dict must contain:
           - type: one of csv, json, xml
           - data: str or bytes
           - name: optional identifier
        """
        schemas = []
        for src in sources:
            schema = self.ingest(src.get("type", ""), src.get("data", ""), src.get("name", ""))
            schemas.append(schema)
        return schemas


# --------------------------------------------------------------------------- #
# Example usage / tests
# --------------------------------------------------------------------------- #

# Sample data in different formats
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

# Define a simple subscriber that prints the schema
def schema_listener(schema: Dict[str, Any]) -> None:
    print("\n=== New schema published ===")
    print(json.dumps(schema, indent=2))


# Sample arguments for the skill entry point
SAMPLE_ARGS = {
    "sources": [
        {"type": "csv", "data": SAMPLE_CSV, "name": "users_csv"},
        {"type": "json", "data": SAMPLE_JSON, "name": "users_json"},
        {"type": "xml", "data": SAMPLE_XML, "name": "users_xml"},
    ]
}


def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the skill.

    Expects a dictionary with key ``sources`` – a list of source descriptors
    each containing ``type`` and ``data`` (and optional ``name``).
    Returns a dictionary with the list of generated schemas.
    """
    engine = SchemaEvolutionEngine()
    engine.pubsub.subscribe(schema_listener)
    schemas = engine.run(args.get("sources", []))
    return {"schemas": schemas}


if __name__ == "__main__":
    # Run the skill with sample arguments
    result = run(SAMPLE_ARGS)

    # Basic sanity check: each source produced a schema with at least 4 fields
    for schema in result["schemas"]:
        assert isinstance(schema, dict)
        fields = schema.get("fields", [])
        assert len(fields) >= 4, f"Expected at least 4 fields, got {len(fields)}"

    print("\nAll schemas generated successfully.")