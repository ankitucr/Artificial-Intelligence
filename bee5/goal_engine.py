#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

from bee5_runtime import LLAMA, MODEL


ROOT = Path(__file__).resolve().parent


GOAL_SCHEMA = {
    "type": "object",
    "properties": {
        "goals": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": ["goals"],
    "additionalProperties": False
}


def extract_json_object(raw):
    if not isinstance(raw, str):
        raise RuntimeError("Goal model output is not text.")

    decoder = json.JSONDecoder()

    for index, char in enumerate(raw):
        if char != "{":
            continue

        try:
            obj, _ = decoder.raw_decode(raw[index:])
        except Exception:
            continue

        if not isinstance(obj, dict):
            continue

        goals = obj.get("goals")

        if isinstance(goals, list) and goals:
            cleaned = [
                str(goal).strip()
                for goal in goals
                if str(goal).strip()
            ]

            if cleaned:
                return {
                    "goals": cleaned
                }

    raise RuntimeError(
        "No valid goal JSON object found."
    )


def deterministic_goal_fallback(user_task):
    text = user_task.lower()
    goals = []

    if any(
        x in text
        for x in (
            "clean",
            "normalize",
            "format text",
            "remove whitespace"
        )
    ):
        goals.append("clean text")

    if any(
        x in text
        for x in (
            "analyze",
            "analyse",
            "inspect",
            "count words"
        )
    ):
        goals.append("analyze text")

    if any(
        x in text
        for x in (
            "report",
            "summary",
            "summarize"
        )
    ):
        goals.append("create report")

    if not goals:
        goals.append(user_task.strip())

    return {
        "goals": goals,
        "source": "deterministic_fallback"
    }


def extract_goals(user_task):
    prompt = f"""
You are BEE5's goal interpreter.

Convert the user task into ordered capability goals.

USER TASK:
{user_task}

Rules:
- Return ONLY valid JSON.
- Do not invent tools or skills.
- Describe WHAT must be done.
- Preserve the requested order.
- Keep goals short.

Example:
{{
  "goals": [
    "clean text",
    "analyze text",
    "create report"
  ]
}}
""".strip()

    command = [
        str(LLAMA),
        "-m",
        str(MODEL),
        "-p",
        prompt,
        "-n",
        "120",
        "-j",
        json.dumps(
            GOAL_SCHEMA,
            separators=(",", ":")
        ),
        "-st",
        "--no-display-prompt",
        "--simple-io",
        "--single-turn",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except Exception:
        return deterministic_goal_fallback(
            user_task
        )

    raw = (
        result.stdout
        + "\n"
        + result.stderr
    ).strip()

    if result.returncode == 0:
        try:
            result_json = extract_json_object(raw)

            result_json["source"] = "local_model"

            return result_json

        except Exception:
            pass

    return deterministic_goal_fallback(
        user_task
    )


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: python goal_engine.py "task"'
        )
        return 1

    task = " ".join(
        sys.argv[1:]
    )

    print(
        json.dumps(
            extract_goals(task),
            ensure_ascii=False,
            indent=2
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
