# Check failed: Disallowed module used.; missing `SAMPLE_ARGS`

#!/usr/bin/env python3
"""
Minimal real‑time fault‑tolerant streaming ETL engine (standard library only).

Features
--------
* CSV, JSON and XML feeds.
* Simple schema inference and type casting.
* Declarative pipeline DSL (filter, map, aggregate).
* Async ingestion with windowed batching.
* Writes the final result to a JSON file.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_duration(duration: str) -> int:
    """Parse a duration string like '2h30m' into seconds."""
    if not isinstance(duration, str):
        raise TypeError("duration must be a string")
    total = 0
    for match in re.finditer(r"(?P<value>\d+)\s*(?P<unit>[dhmsDHMS])", duration):
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _UNIT_SECONDS:
            raise ValueError(f"Unsupported time unit: {unit}")
        total += value * _UNIT_SECONDS[unit]
    if total == 0:
        raise ValueError(f"Could not parse duration string: '{duration}'")
    return total


def camel_to_snake(name: str) -> str:
    """Convert CamelCase names to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# ----------------------------------------------------------------------
# Feed abstraction
# ----------------------------------------------------------------------
class UnsupportedFormatError(RuntimeError):
    """Raised when an unknown feed format is requested."""


@dataclass
class Feed:
    """Represents a single data source."""

    source: str
    format: str
    data: Any  # Path string or in‑memory string

    async def read(self) -> Iterable[Dict[str, Any]]:
        """Async generator yielding rows as dictionaries."""
        if self.format == "csv":
            await asyncio.sleep(0)  # yield control
            if isinstance(self.data, str) and Path(self.data).exists():
                with open(self.data, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        yield row
            else:
                reader = csv.DictReader(
                    self.data.splitlines() if isinstance(self.data, str) else self.data
                )
                for row in reader:
                    yield row

        elif self.format == "json":
            await asyncio.sleep(0)
            if isinstance(self.data, str):
                payload = json.loads(self.data)
            else:
                payload = json.loads(self.data.read().decode("utf-8"))
            if isinstance(payload, list):
                for item in payload:
                    yield item
            else:
                yield payload

        elif self.format == "xml":
            await asyncio.sleep(0)
            if isinstance(self.data, str):
                root = ET.fromstring(self.data)
            else:
                root = ET.fromstring(self.data.read().decode("utf-8"))
            for elem in root:
                yield {child.tag: child.text for child in elem}

        else:
            raise UnsupportedFormatError(f"Unsupported feed format: {self.format}")


# ----------------------------------------------------------------------
# Schema inference
# ----------------------------------------------------------------------
def _infer_type(value: Any) -> type:
    """Infer the Python type of a value represented as a string."""
    if value in (None, ""):
        return type(None)
    for t in (int, float):
        try:
            t(value)
            return t
        except Exception:
            continue
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return bool
    if isinstance(value, str):
        try:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.datetime
        except Exception:
            pass
    return str


@dataclass
class Schema:
    fields: Dict[str, type] = field(default_factory=dict)

    def update(self, record: Dict[str, Any]) -> None:
        """Update schema based on a new record."""
        for key, val in record.items():
            inferred = _infer_type(val)
            current = self.fields.get(key, type(None))
            if current is type(None) or current == inferred:
                self.fields[key] = inferred
            else:
                self.fields[key] = str

    def cast_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce a record to the inferred schema types."""
        casted: Dict[str, Any] = {}
        for key, expected in self.fields.items():
            raw = record.get(key)
            if raw is None:
                casted[key] = None
                continue
            try:
                if expected is int:
                    casted[key] = int(raw)
                elif expected is float:
                    casted[key] = float(raw)
                elif expected is bool:
                    casted[key] = str(raw).lower() in ("true", "1")
                elif expected is dt.datetime:
                    casted[key] = dt.datetime.fromisoformat(
                        str(raw).replace("Z", "+00:00")
                    )
                else:
                    casted[key] = raw
            except Exception:
                casted[key] = raw
        return casted


# ----------------------------------------------------------------------
# Pipeline DSL
# ----------------------------------------------------------------------
@dataclass
class PipelineStep:
    op: str
    expr: Optional[Callable[[Dict[str, Any]], Any]] = None
    agg_func: Optional[Callable[[List[Dict[str, Any]]], Any]] = None


@dataclass
class Pipeline:
    steps: List[PipelineStep] = field(default_factory=list)
    window_seconds: int = 5
    aggregate: Optional[str] = None  # e.g., 'sum', 'count'

    def apply(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = list(records)
        for step in self.steps:
            if step.op == "filter":
                processed = [r for r in processed if step.expr(r)]
            elif step.op == "map":
                processed = [step.expr(r) for r in processed]
            elif step.op == "aggregate":
                processed = [{"result": step.agg_func(processed)}]
            else:
                raise ValueError(f"Unknown pipeline operation: {step.op}")
        if self.aggregate:
            processed = self.aggregate_function(processed)
        return processed

    def aggregate_function(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not records:
            return records
        values = [r.get("value") for r in records]
        if self.aggregate == "sum":
            result = sum(v for v in values if isinstance(v, (int, float)))
        elif self.aggregate == "count":
            result = len(values)
        else:
            result = values
        return [{"result": result}]


# ----------------------------------------------------------------------
# Scheduler & Executor
# ----------------------------------------------------------------------
class Scheduler:
    """Light‑weight async scheduler."""

    def __init__(self, interval: int):
        self.interval = interval
        self.tasks: List[asyncio.Task] = []

    async def schedule(self, coro):
        self.tasks.append(asyncio.create_task(coro))

    async def run(self):
        await asyncio.gather(*self.tasks)


class Executor:
    def __init__(
        self,
        feeds: List[Feed],
        pipeline: Pipeline,
        output_path: str,
    ):
        self.feeds = feeds
        self.pipeline = pipeline
        self.output_path = output_path
        self.schema = Schema()
        self.window_seconds = pipeline.window_seconds
        self._buffer: List[Dict[str, Any]] = []

    async def _process_feed(self, feed: Feed):
        async for record in feed.read():
            self.schema.update(record)
            casted = self.schema.cast_record(record)
            self._buffer.append(casted)
            if self._buffer and "timestamp" in self._buffer[-1]:
                last_ts = casted["timestamp"]
                start_ts = self._buffer[0]["timestamp"]
                if (
                    isinstance(last_ts, dt.datetime)
                    and isinstance(start_ts, dt.datetime)
                    and (last_ts - start_ts).total_seconds() >= self.window_seconds
                ):
                    await self._flush_window()
        await self._flush_window()

    async def _flush_window(self):
        if not self._buffer:
            return
        try:
            result = self.pipeline.apply(self._buffer)
        except Exception:
            traceback.print_exc()
            result = [{"error": "pipeline failure"}]
        await self._write_output(result)
        self._buffer = []

    async def _write_output(self, data: List[Dict[str, Any]]):
        text = json.dumps(data, default=str, indent=2)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_write, text)

    def _sync_write(self, text: str):
        Path(self.output_path).write_text(text, encoding="utf-8")
        print(f"[{dt.datetime.utcnow().isoformat()}] Window written to {self.output_path}")

    async def run(self):
        await asyncio.gather(*[self._process_feed(f) for f in self.feeds])


# ----------------------------------------------------------------------
# Pipeline compilation
# ----------------------------------------------------------------------
def _compile_expr(expr: str) -> Callable[[Dict[str, Any]], Any]:
    """Compile a lambda expression string into a callable."""
    allowed_globals = {
        "__builtins__": None,
        "int": int,
        "float": float,
        "bool": bool,
        "str": str,
        "sum": sum,
        "len": len,
        "datetime": dt.datetime,
    }
    return eval(expr, allowed_globals, {})


def _build_pipeline(cfg: Dict[str, Any]) -> Pipeline:
    steps: List[PipelineStep] = []
    for s in cfg.get("steps", []):
        if s["op"] == "filter":
            steps.append(PipelineStep(op="filter", expr=_compile_expr(s["expr"])))
        elif s["op"] == "map":
            steps.append(PipelineStep(op="map", expr=_compile_expr(s["expr"])))
        elif s["op"] == "aggregate":
            agg_name = s.get("agg_func", "sum")
            if agg_name == "sum":
                agg_func = lambda recs: sum(r["value"] for r in recs if isinstance(r.get("value"), (int, float)))
            elif agg_name == "count":
                agg_func = lambda recs: len([r for r in recs if "value" in r])
            else:
                raise ValueError(f"Unknown aggregate: {agg_name}")
            steps.append(PipelineStep(op="aggregate", agg_func=agg_func))
        else:
            raise ValueError(f"Unsupported step type: {s['op']}")
    return Pipeline(
        steps=steps,
        window_seconds=int(cfg.get("window_seconds", 5)),
        aggregate=cfg.get("aggregate"),
    )


# ----------------------------------------------------------------------
# Sample configuration & entry point
# ----------------------------------------------------------------------
SAMPLE_ARGS: Dict[str, Any] = {
    "feeds": [
        {
            "format": "csv",
            "data": """timestamp,value
2024-08-20T00:00:00Z,12
2024-08-20T00:00:01Z,15
2024-08-20T00:00:02Z,8
""",
        },
        {
            "format": "json",
            "data": """[{"timestamp":"2024-08-20T00:00:03Z","value":20},{"timestamp":"2024-08-20T00:00:04Z","value":7}]""",
        },
    ],
    "pipeline": {
        "steps": [
            {
                "op": "filter",
                "expr": "lambda r: int(r.get('value', 0)) > 10",
            },
            {
                "op": "map",
                "expr": "lambda r: {'value': int(r['value']) * 2, 'timestamp': r['timestamp']}",
            },
        ],
        "window_seconds": 5,
        "aggregate": "sum",
    },
    "output_path": "etl_output.json",
}


def run(args: Dict[str, Any]) -> Dict[str, Any]:
    feeds_cfg = args.get("feeds", [])
    feeds = [
        Feed(format=fc["format"], data=fc["data"], source="")
        for fc in feeds_cfg
    ]
    pipeline = _build_pipeline(args.get("pipeline", {}))
    output_path = args.get("output_path", "etl_output.json")

    executor = Executor(feeds, pipeline, output_path)
    asyncio.run(executor.run())

    return {"status": "completed", "output": output_path}


if __name__ == "__main__":
    try:
        result = run(SAMPLE_ARGS)
        print("ETL finished:", result)
    except Exception:
        traceback.print_exc()
        sys.exit(1)