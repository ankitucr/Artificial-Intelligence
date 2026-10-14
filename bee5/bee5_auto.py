#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MEMORY = ROOT / "memory"

GOAL_ENGINE = ROOT / "goal_engine.py"
DEPENDENCY_PLANNER = ROOT / "dependency_planner.py"
VALIDATOR = ROOT / "plan_validator_v3.py"
EXECUTOR = ROOT / "multi_skill_engine.py"

PLAN_FILE = MEMORY / "dependency_plan.json"


def run_command(command):
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def parse_json_output(text):
    decoder = json.JSONDecoder()

    for index, char in enumerate(text):
        if char != "{":
            continue

        try:
            obj, _ = decoder.raw_decode(text[index:])
        except Exception:
            continue

        if isinstance(obj, dict):
            return obj

    return None


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: python bee5_auto.py "task"'
        )
        return 1

    task = " ".join(sys.argv[1:])

    MEMORY.mkdir(
        parents=True,
        exist_ok=True
    )

    print("========================================")
    print("        BEE5 AUTONOMOUS PIPELINE")
    print("========================================")
    print()
    print("TASK:")
    print(task)
    print()

    # -------------------------------------------------
    # STEP 1 — GOAL EXTRACTION
    # -------------------------------------------------

    print("===== 1. GOAL ENGINE =====")

    code, stdout, stderr = run_command([
        sys.executable,
        str(GOAL_ENGINE),
        task
    ])

    if code != 0:
        print(stdout)
        print(stderr)
        print("❌ GOAL ENGINE FAILED")
        return 2

    goals_result = parse_json_output(
        stdout
    )

    if not goals_result:
        print(stdout)
        print("❌ Could not parse goal engine output.")
        return 2

    goals = goals_result.get(
        "goals",
        []
    )

    if not isinstance(goals, list) or not goals:
        print(
            json.dumps(
                goals_result,
                ensure_ascii=False,
                indent=2
            )
        )
        print("❌ No goals generated.")
        return 2

    print(
        json.dumps(
            goals_result,
            ensure_ascii=False,
            indent=2
        )
    )

    # -------------------------------------------------
    # STEP 2 — DEPENDENCY PLANNING
    # -------------------------------------------------

    print()
    print("===== 2. DEPENDENCY PLANNER =====")

    command = [
        sys.executable,
        str(DEPENDENCY_PLANNER),
        task,
        *goals
    ]

    code, stdout, stderr = run_command(
        command
    )

    if code != 0:
        print(stdout)
        print(stderr)
        print("❌ DEPENDENCY PLANNER FAILED")
        return 3

    plan = parse_json_output(
        stdout
    )

    if not plan:
        print(stdout)
        print("❌ Could not parse dependency plan.")
        return 3

    print(
        json.dumps(
            plan,
            ensure_ascii=False,
            indent=2
        )
    )

    if not plan.get("steps"):
        print("❌ Planner generated no steps.")
        return 3

    # -------------------------------------------------
    # STEP 3 — VALIDATION
    # -------------------------------------------------

    print()
    print("===== 3. PLAN VALIDATOR =====")

    code, stdout, stderr = run_command([
        sys.executable,
        str(VALIDATOR),
        str(PLAN_FILE)
    ])

    print(stdout)

    if stderr:
        print(stderr)

    validation = parse_json_output(
        stdout
    )

    if code != 0 or not validation or not validation.get("ok"):
        print("❌ PLAN VALIDATION FAILED")
        return 4

    print("✅ PLAN VALIDATED")

    # -------------------------------------------------
    # STEP 4 — EXECUTION
    # -------------------------------------------------

    print()
    print("===== 4. MULTI-SKILL EXECUTOR =====")

    code, stdout, stderr = run_command([
        sys.executable,
        str(EXECUTOR),
        "execute-plan",
        str(PLAN_FILE)
    ])

    print(stdout)

    if stderr:
        print(stderr)

    execution = parse_json_output(
        stdout
    )

    if code != 0 or not execution or not execution.get("ok"):
        print("❌ EXECUTION FAILED")
        return 5

    # -------------------------------------------------
    # FINAL RESULT
    # -------------------------------------------------

    print()
    print("========================================")
    print("       ✅ BEE5 PIPELINE COMPLETE")
    print("========================================")

    print(
        json.dumps(
            {
                "ok": True,
                "query": task,
                "goals": goals,
                "steps_planned": execution.get(
                    "steps_planned"
                ),
                "steps_succeeded": execution.get(
                    "steps_succeeded"
                ),
                "steps_failed": execution.get(
                    "steps_failed"
                ),
                "elapsed_seconds": execution.get(
                    "elapsed_seconds"
                )
            },
            ensure_ascii=False,
            indent=2
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
