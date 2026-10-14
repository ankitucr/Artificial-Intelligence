#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from capability_contracts import build_all
from step_reference import parse_reference


ROOT = Path(__file__).resolve().parent


def validate_reference(
    reference,
    current_step,
    contracts
):
    step_number, field = reference

    if step_number >= current_step:
        return (
            f"reference points to future/current step "
            f"{step_number}"
        )

    # We need to know which skill occupies that step.
    return None


def validate_plan(plan):
    errors = []

    if not isinstance(
        plan,
        dict
    ):
        return (
            False,
            ["Plan must be a JSON object."]
        )

    steps = plan.get(
        "steps"
    )

    if not isinstance(
        steps,
        list
    ) or not steps:
        return (
            False,
            ["Plan must contain non-empty steps."]
        )

    contracts = build_all()

    step_map = {}

    for index, step in enumerate(
        steps,
        start=1
    ):
        if not isinstance(
            step,
            dict
        ):
            errors.append(
                f"Step {index} is not an object."
            )
            continue

        order = step.get(
            "order"
        )

        skill = step.get(
            "skill"
        )

        args = step.get(
            "args_template"
        )

        if order != index:
            errors.append(
                f"Step {index} has invalid order "
                f"{order}; expected {index}."
            )

        if not isinstance(
            skill,
            str
        ):
            errors.append(
                f"Step {index} has invalid skill."
            )
            continue

        step_map[index] = skill

        if skill not in contracts:
            errors.append(
                f"Step {index} references unknown "
                f"skill '{skill}'."
            )
            continue

        if not isinstance(
            args,
            dict
        ):
            errors.append(
                f"Step {index} args_template "
                f"must be an object."
            )

    # ---------------------------------------------------------
    # Validate each reference against the actual producer.
    # ---------------------------------------------------------

    for index, step in enumerate(
        steps,
        start=1
    ):
        if not isinstance(
            step,
            dict
        ):
            continue

        skill = step.get(
            "skill"
        )

        if skill not in contracts:
            continue

        outputs = contracts[skill].get(
            "outputs",
            {}
        )

        args = step.get(
            "args_template",
            {}
        )

        if not isinstance(
            args,
            dict
        ):
            continue

        for argument, value in args.items():

            if not isinstance(
                value,
                str
            ):
                continue

            if value == "${input}":
                continue

            reference = parse_reference(
                value
            )

            if reference is None:
                continue

            source_step, field = reference

            if source_step >= index:
                errors.append(
                    f"Step {index} argument "
                    f"'{argument}' references "
                    f"future/current step "
                    f"{source_step}."
                )
                continue

            source_skill = step_map.get(
                source_step
            )

            if source_skill is None:
                errors.append(
                    f"Step {index} argument "
                    f"'{argument}' references "
                    f"missing step {source_step}."
                )
                continue

            source_contract = contracts.get(
                source_skill,
                {}
            )

            source_outputs = source_contract.get(
                "outputs",
                {}
            )

            if field not in source_outputs:
                errors.append(
                    f"Step {index} argument "
                    f"'{argument}' references "
                    f"step {source_step} "
                    f"({source_skill})."
                    f"{field}, but that skill "
                    f"does not produce '{field}'."
                )

    return (
        not errors,
        errors
    )


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python plan_validator_v3.py "
            "<plan.json>"
        )
        return 1

    path = Path(
        sys.argv[1]
    )

    if not path.exists():
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": [
                        f"Plan file not found: {path}"
                    ]
                },
                indent=2
            )
        )
        return 2

    try:
        plan = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": [
                        f"Invalid JSON: {exc}"
                    ]
                },
                indent=2
            )
        )
        return 3

    ok, errors = validate_plan(
        plan
    )

    print(
        json.dumps(
            {
                "ok": ok,
                "errors": errors,
                "steps": len(
                    plan.get(
                        "steps",
                        []
                    )
                )
            },
            ensure_ascii=False,
            indent=2
        )
    )

    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
