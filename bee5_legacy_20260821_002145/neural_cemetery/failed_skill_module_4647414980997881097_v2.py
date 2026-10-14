# Check failed: missing `SAMPLE_ARGS`

#!/usr/bin/env python3
"""
A minimal asynchronous data‑pipeline framework that

* ingests CSV, JSON and XML feeds from strings
* performs automatic type inference and schema‑evolution
* applies simple columnar transformations (filter, aggregate)
* streams the result to multiple sinks (currently stdout only)

Only the Python standard library is used.
"""

import asyncio
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from io import StringIO
from typing import Any, Dict, Iterable, List, Union

# --------------------------------------------------------------------------- #
# Sample configuration

SAMPLE_ARGS: Dict[str, Any] = {
    "sources": [
        {
            "type": "csv",
            "data": """name,age,score
Alice,30,85
Bob,25,90
Charlie,35,95
Dana,28,88""",
        },
        {
            "type": "json",
            "data": """[
                {"name":"Eve", "age":40, "score":92},
                {"name":"Frank", "age":22, "score":80}
            ]""",
        },
        {
            "type": "xml",
            "data": """<root>
                <row><name>Grace</name><age>33</age><score>89</score></row>
                <row><name>Heidi</name><age>29</age><score>91</score></row>
            </root>""",
        },
    ],
    "transformations": [
        {"op": "filter", "column": "age", "condition": ">", "value": 28},
        {"op": "aggregate", "column": "age", "func": "sum"},
    ],
    "sinks": ["stdout"],
}

# --------------------------------------------------------------------------- #
# Parsing helpers

def parse_csv(data: str) -> List[Dict[str, Any]]:
    """Parse CSV data into a list of row dictionaries."""
    reader = csv.DictReader(StringIO(data))
    return [row for row in reader]


def parse_json(data: str) -> List[Dict[str, Any]]:
    """Parse JSON array data into a list of dictionaries."""
    return json.loads(data)


def parse_xml(data: str) -> List[Dict[str, Any]]:
    """Parse a very simple XML format into a list of dictionaries."""
    root = ET.fromstring(data)
    rows: List[Dict[str, Any]] = []
    for child in root:
        rows.append({elem.tag: elem.text for elem in child})
    return rows


PARSERS: Dict[str, Any] = {
    "csv": parse_csv,
    "json": parse_json,
    "xml": parse_xml,
}


def parse_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse a single source into a list of row dictionaries."""
    src_type = source.get("type")
    data = source.get("data")
    if not src_type or not data:
        raise ValueError("Source must contain 'type' and 'data'")
    parser = PARSERS.get(src_type.lower())
    if parser is None:
        raise ValueError(f"Unsupported source type: {src_type}")
    return parser(data)


# --------------------------------------------------------------------------- #
# Schema inference

def infer_column_type(values: List[Any]) -> type:
    """Infer a Python type for a column based on its values."""
    has_int = has_float = has_str = has_bool = False
    for v in values:
        if v is None or v == "":
            continue
        s = str(v).strip()
        if s.lower() in ("true", "false"):
            has_bool = True
            continue
        try:
            int(v)
            has_int = True
            continue
        except Exception:
            pass
        try:
            float(v)
            has_float = True
            continue
        except Exception:
            pass
        has_str = True
    if has_str:
        return str
    if has_bool and not has_int and not has_float:
        return bool
    if has_float:
        return float
    if has_int:
        return int
    return str


def infer_schema(rows: List[Dict[str, Any]]) -> Dict[str, type]:
    """Infer schema from a list of rows."""
    columns: Dict[str, List[Any]] = defaultdict(list)
    for row in rows:
        for k, v in row.items():
            columns[k].append(v)
    return {k: infer_column_type(vs) for k, vs in columns.items()}


# --------------------------------------------------------------------------- #
# Zero‑copy columnar storage helpers

def to_columnar(rows: List[Dict[str, Any]], schema: Dict[str, type]) -> Dict[str, List[Any]]:
    """Convert a list of row dictionaries to a columnar dictionary."""
    columns: Dict[str, List[Any]] = {k: [] for k in schema}
    for row in rows:
        for k in columns:
            v = row.get(k)
            if v is None or v == "":
                columns[k].append(None)
                continue
            try:
                if schema[k] is bool:
                    columns[k].append(str(v).lower() in ("true", "1", "yes"))
                else:
                    columns[k].append(schema[k](v))
            except Exception:
                columns[k].append(None)
    return columns


# --------------------------------------------------------------------------- #
# Transformations

async def filter_rows(columns: Dict[str, List[Any]], condition: Dict[str, Any]) -> Dict[str, List[Any]]:
    col = condition["column"]
    op = condition["condition"]
    val = condition["value"]

    indices: List[int] = []
    for i, v in enumerate(columns.get(col, [])):
        if v is None:
            continue
        try:
            if op == ">":
                if float(v) > float(val):
                    indices.append(i)
            elif op == "<":
                if float(v) < float(val):
                    indices.append(i)
            elif op == "==":
                if v == val:
                    indices.append(i)
        except Exception:
            continue

    return {k: [v[i] for i in indices] for k, v in columns.items()}


async def aggregate_rows(columns: Dict[str, List[Any]], agg: Dict[str, Any]) -> Dict[str, Any]:
    col = agg["column"]
    func = agg["func"]
    values = [v for v in columns.get(col, []) if v is not None]
    if func == "sum":
        return {f"sum_{col}": sum(float(v) for v in values)}
    if func == "count":
        return {f"count_{col}": len(values)}
    raise ValueError(f"Unsupported aggregation function: {func}")


# --------------------------------------------------------------------------- #
# Async pipeline

async def source_reader(source: Dict[str, Any], queue: asyncio.Queue):
    rows = parse_source(source)
    await queue.put(rows)


async def sink_writer(result: Union[Dict[str, Any], List[Any]], sink_type: str):
    if sink_type == "stdout":
        print("Pipeline output:")
        print(json.dumps(result, indent=2))
    # Additional sinks can be added here in the future


async def process_pipeline(args: Dict[str, Any]) -> Dict[str, Any]:
    sources = args.get("sources", [])
    transformations = args.get("transformations", [])
    sinks = args.get("sinks", [])

    # Step 1: read all sources concurrently
    source_queue: asyncio.Queue = asyncio.Queue()
    read_tasks = [asyncio.create_task(source_reader(src, source_queue)) for src in sources]
    await asyncio.gather(*read_tasks)

    # Combine all rows
    all_rows: List[Dict[str, Any]] = []
    while not source_queue.empty():
        all_rows.extend(source_queue.get_nowait())

    # Step 2: infer schema and build columnar format
    schema = infer_schema(all_rows)
    columns = to_columnar(all_rows, schema)

    # Step 3: apply transformations sequentially
    for trans in transformations:
        op = trans["op"]
        if op == "filter":
            columns = await filter_rows(columns, trans)
        elif op == "aggregate":
            columns = await aggregate_rows(columns, trans)  # returns a flat dict
        else:
            raise ValueError(f"Unsupported operation: {op}")

    # Step 4: stream results to sinks
    result = columns if isinstance(columns, dict) else {"result": columns}
    for sink in sinks:
        await sink_writer(result, sink)

    return result


def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the pipeline."""
    return asyncio.run(process_pipeline(args))


# --------------------------------------------------------------------------- #
# Main entry

if __name__ == "__main__":
    output = run(SAMPLE_ARGS)

    # Sanity check – verify the aggregated age sum is correct
    expected_age_sum = 30 + 35 + 40 + 33  # filtered rows > 28
    if output.get("sum_age") != expected_age_sum:
        raise AssertionError(
            f"Expected sum_age {expected_age_sum}, got {output.get('sum_age')}"
        )
    print("Pipeline executed successfully.")