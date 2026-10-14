#!/usr/bin/env python3

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MEMORY_DIR = ROOT / "memory"

EPISODES = MEMORY_DIR / "episodes.jsonl"
KNOWLEDGE = MEMORY_DIR / "knowledge.jsonl"
STATS = MEMORY_DIR / "skill_stats.json"


def _ensure():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _append(path: Path, data: dict):
    _ensure()
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            ) + "\n"
        )


def _load_stats():
    _ensure()

    if not STATS.exists():
        return {}

    try:
        data = json.loads(
            STATS.read_text(encoding="utf-8")
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_stats(data):
    _ensure()
    STATS.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def record_skill_success(
    skill: str,
    args: dict,
    result: dict
):
    now = time.time()

    _append(
        EPISODES,
        {
            "time": now,
            "event": "skill_success_observation",
            "skill": skill,
            "args": args,
            "result": result
        }
    )

    _append(
        KNOWLEDGE,
        {
            "time": now,
            "type": "successful_procedure",
            "skill": skill,
            "input_keys": sorted(args.keys()),
            "result_keys": sorted(result.keys())
        }
    )

    stats = _load_stats()

    entry = stats.setdefault(
        skill,
        {
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "last_success": None,
            "last_failure": None
        }
    )

    entry["runs"] += 1
    entry["successes"] += 1
    entry["last_success"] = now

    _save_stats(stats)


def record_skill_failure(
    skill: str,
    args: dict,
    error: str
):
    now = time.time()

    _append(
        EPISODES,
        {
            "time": now,
            "event": "skill_failure_observation",
            "skill": skill,
            "args": args,
            "error": error
        }
    )

    _append(
        KNOWLEDGE,
        {
            "time": now,
            "type": "failed_procedure",
            "skill": skill,
            "error": error
        }
    )

    stats = _load_stats()

    entry = stats.setdefault(
        skill,
        {
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "last_success": None,
            "last_failure": None
        }
    )

    entry["runs"] += 1
    entry["failures"] += 1
    entry["last_failure"] = now

    _save_stats(stats)


def status():
    stats = _load_stats()

    print("========================================")
    print("          BEE5 MEMORY ENGINE")
    print("========================================")
    print(f"Tracked skills : {len(stats)}")

    for name, info in stats.items():
        runs = info["runs"]
        successes = info["successes"]
        failures = info["failures"]

        print(
            f"{name}: "
            f"runs={runs}, "
            f"success={successes}, "
            f"failure={failures}"
        )

    print("========================================")


if __name__ == "__main__":
    status()
