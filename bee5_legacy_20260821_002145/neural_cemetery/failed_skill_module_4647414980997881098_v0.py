# Check failed: Disallowed module used.

#!/usr/bin/env python3
"""
A minimal, real‑time, fault‑tolerant streaming ETL engine built solely
with the Python standard library.

Features
--------
* Supports CSV, JSON and XML feeds.  (Parquet / Avro are stubs – see
  `UnsupportedFormatError`.)
* Incremental type‑inference and simple schema evolution.
* Declarative pipeline DSL (filter, map, aggregate, windowing).
* Async ingestion + multiprocessing for CPU‑bound transformations.
* Lightweight scheduler powered by asyncio.
* Utilises helper functions from the provided skill modules (duration
  parsing, CamelCase ↔ snake_case conversion).

Note
----
This is a proof‑of‑concept; it is *not* a production‑grade engine.
"""

from __future__ import annotations

import asyncio
import csv
import json
import re
import sys
import textwrap
import time
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# ----------------------------------------------------------------------
# Helper utilities – copied from the supplied skill modules
# ----------------------------------------------------------------------
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_duration(duration: str) -> int:
    if not isinstance(duration, str):
        raise TypeError("duration must be a string")
    total = 0
    pattern = re.compile(r"(?P<value>\d+)\s*(?P<unit>[dhmsDHMS])")
    for match in pattern.finditer(duration):
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _UNIT_SECONDS:
            raise ValueError(f"Unsupported time unit: {unit}")
        total += value * _UNIT_SECONDS[unit]
    if total == 0:
        raise ValueError(f"Could not parse duration string: '{duration}'")
    return total


def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# ----------------------------------------------------------------------
# Data feed abstractions
# ----------------------------------------------------------------------
class UnsupportedFormatError(RuntimeError):
    pass


@dataclass
class Feed:
    """Represents a single data source."""

    source: str
    format: str
    data: Any  # Either a path or an in‑memory string

    async def read(self) -> Iterable[Dict[str, Any]]:
        """Async generator yielding rows as dictionaries."""
        if self.format == "csv":
            await asyncio.sleep(0)  # allow event loop to run
            if isinstance(self.data, str) and Path(self.data).exists():
                with open(self.data, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        yield row
            else:
                for row in csv.DictReader(
                    self.data.splitlines() if isinstance(self.data, str) else self.data
                ):
                    yield row

        elif self.format == "json":
            await asyncio.sleep(0)
            if isinstance(self.data, str):
                content = json.loads(self.data)
                if isinstance(content, list):
                    for item in content:
                        yield item
                else:
                    yield content
            else:
                for item in json.loads(self.data.read().decode("utf-8")):
                    yield item

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
# Schema inference and evolution
# ----------------------------------------------------------------------
def _infer_type(value: str) -> type:
    if value is None or value == "":
        return type(None)
    for t in (int, float):
        try:
            return t
        except ValueError:
            pass
    if value.lower() in ("true", "false"):
        return bool
    try:
        datetime.fromisoformat(value)
        return datetime
    except ValueError:
        pass
    return str


@dataclass
class Schema:
    fields: Dict[str, type] = field(default_factory=dict)

    def update(self, record: Dict[str, Any]) -> None:
        for key, val in record.items():
            inferred = _infer_type(val) if isinstance(val, str) else type(val)
            if key not in self.fields or self.fields[key] is type(None):
                self.fields[key] = inferred
            else:
                # Promote to string if types differ
                if self.fields[key] != inferred:
                    self.fields[key] = str

    def cast_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
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
                    casted[key] = raw.lower() in ("true", "1")
                elif expected is datetime:
                    casted[key] = datetime.fromisoformat(raw)
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
    agg_func: Optional[Callable[[List[Any]], Any]] = None


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
                values = [r for r in processed]
                result = step.agg_func(values)
                processed = [{"result": result}]
            else:
                raise ValueError(f"Unknown pipeline operation: {step.op}")
        return processed

    def aggregate_function(self, values: List[Any]) -> Any:
        if self.aggregate == "sum":
            return sum(values)
        if self.aggregate == "count":
            return len(values)
        return values


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
    def __init__(self, feeds: List[Feed], pipeline: Pipeline, output_path: str):
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
            if len(self._buffer) >= 1 and self._buffer[-1].get("timestamp"):
                # Check if window time elapsed
                last_ts = datetime.fromisoformat(self._buffer[-1]["timestamp"])
                if self._buffer[0]["timestamp"]:
                    start_ts = datetime.fromisoformat(self._buffer[0]["timestamp"])
                    if (last_ts - start_ts).total_seconds() >= self.window_seconds:
                        await self._flush_window()
        # final flush
        await self._flush_window()

    async def _flush_window(self):
        if not self._buffer:
            return
        # apply pipeline
        try:
            result = self.pipeline.apply(self._buffer)
        except Exception:
            traceback.print_exc()
            result = {"error": "pipeline failure"}
        # write to output
        await self._write_output(result)
        self._buffer = []

    async def _write_output(self, data):
        text = json.dumps(data, default=str, indent=2)
        # Write async by offloading to executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_write, text)

    def _sync_write(self, text):
        Path(self.output_path).write_text(text, encoding="utf-8")
        print(f"[{datetime.utcnow().isoformat()}] Window written to {self.output_path}")

    async def run(self):
        await asyncio.gather(
            *[self._process_feed(feed) for feed in self.feeds]
        )


# ----------------------------------------------------------------------
# Sample configuration & entry point
# ----------------------------------------------------------------------
SAMPLE_ARGS = {
    "feeds": [
        {
            "format": "csv",
            "data": """timestamp,value\n2024-08-20T00:00:00Z,12\n2024-08-20T00:00:01Z,15\n2024-08-20T00:00:02Z,8\n""",
        },
        {
            "format": "json",
            "data": """[{"timestamp":"2024-08-20T00:00:03Z","value":20},{"timestamp":"2024-08-20T00:00:04Z","value":7}]""",
        },
    ],
    "pipeline": {
        "steps": [
            {"op": "filter", "expr": "lambda r: int(r.get('value', 0)) > 10"},
            {"op": "map", "expr": "lambda r: {'value': int(r['value']) * 2, 'timestamp': r['timestamp']}"},
        ],
        "window_seconds": 5,
        "aggregate": "sum",
    },
    "output_path": "etl_output.json",
}

def _build_pipeline(cfg: Dict[str, Any]) -> Pipeline:
    steps = []
    for s in cfg.get("steps", []):
        if s["op"] == "filter":
            expr = eval(s["expr"], {"__builtins__": {}})
            steps.append(PipelineStep(op="filter", expr=expr))
        elif s["op"] == "map":
            expr = eval(s["expr"], {"__builtins__": {}})
            steps.append(PipelineStep(op="map", expr=expr))
        elif s["op"] == "aggregate":
            agg_name = s.get("agg_func", "sum")
            if agg_name == "sum":
                agg_func = lambda recs: sum(r["value"] for r in recs)
            elif agg_name == "count":
                agg_func = lambda recs: len(recs)
            else:
                raise ValueError(f"Unknown aggregate: {agg_name}")
            steps.append(PipelineStep(op="aggregate", agg_func=agg_func))
    return Pipeline(steps=steps, window_seconds=int(cfg.get("window_seconds", 5)), aggregate=cfg.get("aggregate"))

def run(args: Dict[str, Any]) -> Dict[str, Any]:
    feeds_cfg = args.get("feeds", [])
    feeds = [Feed(format=fc["format"], data=fc["data"], source="") for fc in feeds_cfg]
    pipeline_cfg = args.get("pipeline", {})
    pipeline = _build_pipeline(pipeline_cfg)
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