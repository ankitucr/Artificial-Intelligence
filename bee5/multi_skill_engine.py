#!/usr/bin/env python3

import copy
import json
import sys
import time
from pathlib import Path

from bee5_runtime import execute_skill, load_registry
from step_reference import parse_reference
from capability_graph import build_graph
from goal_engine import extract_goals
from dependency_planner import create_plan as create_dependency_plan
from plan_validator_v3 import validate_plan


ROOT = Path(__file__).resolve().parent
MEMORY_DIR = ROOT / "memory"
MULTI_EPISODES = MEMORY_DIR / "multi_skill_episodes.jsonl"


def append_jsonl(path, data):
    MEMORY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            ) + "\n"
        )


def resolve_value(
    value,
    user_input,
    previous_result,
    step_results
):
    """
    Resolve execution-time references.

    Supported:
      ${input}
      ${previous.FIELD}          legacy compatibility
      ${step1.FIELD}
      ${step2.FIELD}
      ${stepN.FIELD}
    """

    if not isinstance(value, str):
        return value

    # Original user input.
    if value == "${input}":
        return user_input

    # New explicit step reference.
    reference = parse_reference(value)

    if reference is not None:
        step_number, field = reference

        result = step_results.get(
            step_number
        )

        if result is None:
            raise ValueError(
                f"Reference points to unavailable step "
                f"{step_number}: {value}"
            )

        if not isinstance(result, dict):
            raise ValueError(
                f"Step {step_number} result is not an object; "
                f"cannot resolve {value}"
            )

        if field not in result:
            raise ValueError(
                f"Step {step_number} does not produce "
                f"field '{field}'"
            )

        return result[field]

    # Legacy compatibility.
    if (
        value.startswith("${previous.")
        and value.endswith("}")
    ):
        key = value[len("${previous."):-1]

        if key not in previous_result:
            raise ValueError(
                f"Previous result does not contain "
                f"field '{key}'"
            )

        return previous_result[key]

    return value


def resolve_args(
    args,
    user_input,
    previous_result,
    step_results
):
    """
    Recursively resolve all argument references.
    """

    if not isinstance(args, dict):
        return {}

    resolved = {}

    for key, value in args.items():

        if isinstance(value, dict):

            resolved[key] = resolve_args(
                value,
                user_input,
                previous_result,
                step_results
            )

        elif isinstance(value, list):

            resolved[key] = [
                (
                    resolve_args(
                        item,
                        user_input,
                        previous_result,
                        step_results
                    )
                    if isinstance(item, dict)
                    else resolve_value(
                        item,
                        user_input,
                        previous_result,
                        step_results
                    )
                )
                for item in value
            ]

        else:

            resolved[key] = resolve_value(
                value,
                user_input,
                previous_result,
                step_results
            )

    return resolved


def validate_step(step, registry):
    skill = step.get(
        "skill",
        ""
    )

    if not isinstance(skill, str) or not skill:
        raise ValueError(
            "Planner produced an invalid skill name."
        )

    if skill not in registry:
        raise ValueError(
            f"Planner attempted to use unregistered skill: {skill}"
        )

    args_template = step.get(
        "args_template",
        {}
    )

    if not isinstance(args_template, dict):
        raise ValueError(
            f"Invalid args_template for skill: {skill}"
        )

    return skill, args_template


def execute_plan(
    plan,
    user_input,
    stop_on_failure=True
):
    registry = load_registry()

    if not isinstance(plan, dict):
        raise ValueError(
            "Plan must be a dictionary."
        )

    steps = plan.get(
        "steps",
        []
    )

    if not isinstance(steps, list) or not steps:
        return {
            "ok": False,
            "status": "no_steps",
            "query": user_input,
            "steps": []
        }

    run_id = f"{time.time_ns()}"

    previous_result = {}
    step_results = {}
    observations = []
    started = time.time()

    for index, step in enumerate(
        steps,
        start=1
    ):
        skill, args_template = validate_step(
            step,
            registry
        )

        args = resolve_args(
            args_template,
            user_input,
            previous_result,
            step_results
        )

        record = {
            "order": index,
            "skill": skill,
            "args": copy.deepcopy(args),
            "status": "running"
        }

        try:
            result = execute_skill(
                skill,
                args
            )

            record["status"] = "success"
            record["result"] = result

            previous_result = (
                result
                if isinstance(result, dict)
                else {"value": result}
            )

            step_results[index] = copy.deepcopy(
                previous_result
            )

            observations.append(record)

        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)

            observations.append(record)

            if stop_on_failure:
                break

    success_count = sum(
        1
        for item in observations
        if item["status"] == "success"
    )

    failure_count = sum(
        1
        for item in observations
        if item["status"] == "failed"
    )

    elapsed = round(
        time.time() - started,
        4
    )

    ok = (
        bool(observations)
        and failure_count == 0
        and success_count == len(steps)
    )

    episode = {
        "time": time.time(),
        "event": "multi_skill_execution",
        "run_id": run_id,
        "query": user_input,
        "plan": plan,
        "observations": observations,
        "success": ok,
        "elapsed_seconds": elapsed
    }

    append_jsonl(
        MULTI_EPISODES,
        episode
    )

    return {
        "ok": ok,
        "run_id": run_id,
        "query": user_input,
        "steps_planned": len(steps),
        "steps_succeeded": success_count,
        "steps_failed": failure_count,
        "elapsed_seconds": elapsed,
        "observations": observations
    }


def plan_and_execute(
    query,
    limit=5
):
    """
    Full BEE5 autonomous execution pipeline:

        User task
          ↓
        Goal extraction
          ↓
        Deterministic dependency planning
          ↓
        V3 validation
          ↓
        Step-reference execution
          ↓
        Final result
    """

    build_graph()

    # -----------------------------------------------------
    # 1. Understand the user's task.
    # -----------------------------------------------------

    goal_data = extract_goals(
        query
    )

    goals = goal_data.get(
        "goals",
        []
    )

    if not goals:
        return {
            "ok": False,
            "status": "no_goals",
            "query": query,
            "goal_data": goal_data
        }

    # -----------------------------------------------------
    # 2. Build deterministic executable plan.
    # -----------------------------------------------------

    plan = create_dependency_plan(
        query,
        goals
    )

    if not isinstance(
        plan,
        dict
    ):
        return {
            "ok": False,
            "status": "invalid_plan_object",
            "query": query,
            "goals": goals
        }

    steps = plan.get(
        "steps",
        []
    )

    if not steps:
        return {
            "ok": False,
            "status": "no_executable_plan",
            "query": query,
            "goals": goals,
            "plan": plan
        }

    # -----------------------------------------------------
    # 3. Validate the complete dependency plan.
    # -----------------------------------------------------

    valid, errors = validate_plan(
        plan
    )

    if not valid:
        return {
            "ok": False,
            "status": "plan_validation_failed",
            "query": query,
            "goals": goals,
            "plan": plan,
            "validation_errors": errors
        }

    # -----------------------------------------------------
    # 4. Execute the validated plan.
    # -----------------------------------------------------

    execution = execute_plan(
        plan,
        query
    )

    return {
        "ok": execution.get(
            "ok",
            False
        ),
        "query": query,
        "goals": goal_data,
        "plan": plan,
        "validation": {
            "ok": True,
            "errors": []
        },
        "execution": execution
    }



def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            '  python multi_skill_engine.py plan "task"\n'
            '  python multi_skill_engine.py run "task"\n'
            "  python multi_skill_engine.py execute-plan <json-file>"
        )
        return 1

    command = sys.argv[1]

    if command == "plan":
        if len(sys.argv) < 3:
            print(
                'Usage: python multi_skill_engine.py plan "task"'
            )
            return 1

        query = sys.argv[2]

        result = plan_and_execute(
            query
        )

        print(
            json.dumps(
                {
                    "ok": result.get("ok"),
                    "query": query,
                    "goals": result.get("goals"),
                    "plan": result.get("plan"),
                    "validation": result.get("validation"),
                },
                ensure_ascii=False,
                indent=2
            )
        )

        return (
            0
            if result.get("plan")
            else 2
        )

    if command == "run":
        if len(sys.argv) < 3:
            print(
                'Usage: python multi_skill_engine.py run "task"'
            )
            return 1

        result = plan_and_execute(
            sys.argv[2]
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return (
            0
            if result.get("ok")
            else 2
        )

    if command == "execute-plan":
        if len(sys.argv) < 3:
            print(
                "Usage: python multi_skill_engine.py execute-plan <json-file>"
            )
            return 1

        path = Path(sys.argv[2])

        if not path.exists():
            print(
                f"Plan file not found: {path}"
            )
            return 1

        plan = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        query = plan.get(
            "query",
            "manual multi-skill execution"
        )

        result = execute_plan(
            plan,
            query
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return (
            0
            if result.get("ok")
            else 2
        )

    print(
        f"Unknown command: {command}"
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
