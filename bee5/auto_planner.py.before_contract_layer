#!/usr/bin/env python3

import json
import re
import subprocess
import sys
from pathlib import Path

from bee5_runtime import LLAMA, MODEL, repair_json, load_registry
from capability_graph import build_graph, find_candidates
from plan_validator import validate_plan, repair_plan


ROOT = Path(__file__).resolve().parent
MEMORY = ROOT / "memory"

AUTO_PLAN_PATH = MEMORY / "auto_plan.json"
PLAN_HISTORY = MEMORY / "plan_history.jsonl"

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "order": {
                        "type": "integer"
                    },
                    "skill": {
                        "type": "string"
                    },
                    "args_template": {
                        "type": "object"
                    },
                    "reason": {
                        "type": "string"
                    }
                },
                "required": [
                    "order",
                    "skill",
                    "args_template",
                    "reason"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "query",
        "steps"
    ],
    "additionalProperties": False
}


def append_jsonl(data):
    MEMORY.mkdir(
        parents=True,
        exist_ok=True
    )

    with PLAN_HISTORY.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            ) + "\n"
        )


def build_planning_context(query):
    candidates = find_candidates(
        query,
        limit=8
    )

    registry = load_registry()

    usable = []

    for item in candidates:
        skill = item["skill"]

        if skill not in registry:
            continue

        usable.append({
            "skill": skill,
            "description": item.get(
                "description",
                ""
            ),
            "functions": item.get(
                "functions",
                []
            ),
            "sample_args": item.get(
                "sample_args",
                {}
            ),
            "score": item.get(
                "score",
                0
            ),
            "reliability": item.get(
                "reliability",
                0
            )
        })

    return usable


def deterministic_fallback(query, candidates):
    names = {
        item["skill"]
        for item in candidates
    }

    lowered = query.lower()

    if (
        "clean" in lowered
        and "analy" in lowered
        and "report" in lowered
        and {
            "text_cleaner",
            "text_analyzer",
            "text_reporter"
        }.issubset(names)
    ):
        return {
            "query": query,
            "steps": [
                {
                    "order": 1,
                    "skill": "text_cleaner",
                    "args_template": {
                        "text": "${input}"
                    },
                    "reason": (
                        "Clean the input text first."
                    )
                },
                {
                    "order": 2,
                    "skill": "text_analyzer",
                    "args_template": {
                        "text": "${previous.cleaned_text}"
                    },
                    "reason": (
                        "Analyze the cleaned text."
                    )
                },
                {
                    "order": 3,
                    "skill": "text_reporter",
                    "args_template": {
                        "text": "${previous.text}",
                        "word_count": (
                            "${previous.word_count}"
                        ),
                        "unique_word_count": (
                            "${previous.unique_word_count}"
                        ),
                        "longest_word": (
                            "${previous.longest_word}"
                        )
                    },
                    "reason": (
                        "Create a report from "
                        "the analysis."
                    )
                }
            ]
        }

    if candidates:
        first = candidates[0]
        skill = first["skill"]
        sample_args = first.get(
            "sample_args",
            {}
        )

        args_template = {}

        if isinstance(
            sample_args,
            dict
        ):
            for key, value in sample_args.items():
                if key in {
                    "text",
                    "input",
                    "input_text",
                    "query"
                }:
                    args_template[key] = "${input}"
                else:
                    args_template[key] = value

        return {
            "query": query,
            "steps": [
                {
                    "order": 1,
                    "skill": skill,
                    "args_template": args_template,
                    "reason": (
                        "Best verified candidate "
                        "for the task."
                    )
                }
            ]
        }

    return {
        "query": query,
        "steps": []
    }


def ask_local_planner(
    query,
    candidates,
    repair_error=""
):
    context = json.dumps(
        candidates,
        ensure_ascii=False,
        indent=2
    )

    repair_context = ""

    if repair_error:
        repair_context = f"""
PREVIOUS PLAN VALIDATION ERROR:
{repair_error}

Create a corrected plan.
Do not repeat the invalid reference or skill.
"""

    prompt = f"""
You are the BEE5 planning module.

Create a minimal executable plan for the user's task.

USER TASK:
{query}

VERIFIED AVAILABLE SKILLS:
{context}

{repair_context}

Rules:
1. Use ONLY exact registered skills listed above.
2. Never invent a skill.
3. Return ONLY valid JSON.
4. Step order starts at 1 and is sequential.
5. args_template MUST always be a JSON object.
6. Use "${{input}}" for original user input.
7. Use "${{previous.field}}" only if that exact field is produced by the immediately previous skill.
8. Prefer the smallest valid plan.
9. Do not add commentary.
""".strip()

    command = [
        str(LLAMA),
        "-m",
        str(MODEL),
        "-p",
        prompt,
        "-n",
        "256",
        "-j",
        json.dumps(
            PLAN_SCHEMA,
            separators=(",", ":")
        ),
        "-st",
        "--no-display-prompt",
        "--single-turn"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180
    )

    raw = (
        result.stdout
        + "\n"
        + result.stderr
    ).strip()

    if result.returncode != 0:
        raise RuntimeError(
            raw or "Local planner failed."
        )

    return repair_json(raw)


def validate_and_repair(
    plan,
    query,
    candidates
):
    plan = repair_plan(
        plan
    )

    ok, errors = validate_plan(
        plan
    )

    if ok:
        return plan, {
            "status": "valid",
            "errors": []
        }

    combined_error = "\n".join(
        errors
    )

    # One local-model repair attempt.
    try:
        repaired = ask_local_planner(
            query,
            candidates,
            combined_error
        )

        repaired = repair_plan(
            repaired
        )

        ok2, errors2 = validate_plan(
            repaired
        )

        if ok2:
            return repaired, {
                "status": "repaired",
                "errors": errors,
                "repair_errors": []
            }

        return repaired, {
            "status": "repair_failed",
            "errors": errors,
            "repair_errors": errors2
        }

    except Exception as exc:
        return plan, {
            "status": "repair_exception",
            "errors": errors,
            "repair_exception": str(exc)
        }


def create_auto_plan(query):
    build_graph()

    candidates = build_planning_context(
        query
    )

    if not candidates:
        plan = {
            "query": query,
            "steps": [],
            "planner": "no_candidates"
        }

        append_jsonl({
            "event": "plan_created",
            "query": query,
            "planner": "no_candidates",
            "valid": False
        })

        return plan

    planner_source = "local_model"

    try:
        raw_plan = ask_local_planner(
            query,
            candidates
        )

        plan, validation = validate_and_repair(
            raw_plan,
            query,
            candidates
        )

        if validation["status"] == "valid":
            planner_source = "local_model"

        elif validation["status"] == "repaired":
            planner_source = "local_model_repaired"

        else:
            raise RuntimeError(
                json.dumps(
                    validation,
                    ensure_ascii=False
                )
            )

    except Exception:
        plan = deterministic_fallback(
            query,
            candidates
        )

        planner_source = "deterministic_fallback"

        plan, validation = validate_and_repair(
            plan,
            query,
            candidates
        )

    valid, errors = validate_plan(
        plan
    )

    if not valid:
        plan = {
            "query": query,
            "steps": [],
            "planner": "rejected",
            "validation_errors": errors
        }

    else:
        plan["query"] = query
        plan["planner"] = planner_source
        plan["candidate_count"] = len(
            candidates
        )
        plan["validation"] = validation

    AUTO_PLAN_PATH.write_text(
        json.dumps(
            plan,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    append_jsonl({
        "event": "plan_created",
        "query": query,
        "planner": plan.get(
            "planner",
            "unknown"
        ),
        "valid": bool(
            plan.get("steps")
        ),
        "steps": len(
            plan.get(
                "steps",
                []
            )
        ),
        "validation": plan.get(
            "validation",
            {}
        )
    })

    return plan


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: python auto_planner.py "task"'
        )
        return 1

    query = " ".join(
        sys.argv[1:]
    )

    plan = create_auto_plan(
        query
    )

    print(
        json.dumps(
            plan,
            ensure_ascii=False,
            indent=2
        )
    )

    return (
        0
        if plan.get("steps")
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
