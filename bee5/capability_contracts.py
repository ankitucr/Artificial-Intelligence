#!/usr/bin/env python3

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACTIVE_SKILLS = ROOT / "skills" / "active"
CONTRACT_FILE = ROOT / "memory" / "capability_contracts.json"


def infer_arg_names(function_node):
    fields = set()

    for node in ast.walk(function_node):

        if not isinstance(node, ast.Call):
            continue

        # args.get("field", ...)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "args"
            and node.args
        ):
            key = node.args[0]

            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
            ):
                fields.add(key.value)

        # args["field"]
        if (
            isinstance(node.func, ast.Subscript)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "args"
        ):
            key = node.slice

            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
            ):
                fields.add(key.value)

    return fields


def infer_output_names(function_node):
    fields = set()

    for node in ast.walk(function_node):

        if not isinstance(node, ast.Return):
            continue

        value = node.value

        if not isinstance(value, ast.Dict):
            continue

        for key in value.keys:

            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
            ):
                fields.add(key.value)

    return fields


def infer_literal_type(node):
    if isinstance(node, ast.Constant):
        value = node.value

        if isinstance(value, bool):
            return "boolean"

        if isinstance(value, int):
            return "integer"

        if isinstance(value, float):
            return "number"

        if isinstance(value, str):
            return "string"

        if value is None:
            return "null"

    if isinstance(node, ast.List):
        return "array"

    if isinstance(node, ast.Dict):
        return "object"

    return "unknown"


def infer_output_types(function_node):
    output_types = {}

    for node in ast.walk(function_node):

        if not isinstance(node, ast.Return):
            continue

        value = node.value

        if not isinstance(value, ast.Dict):
            continue

        for key, val in zip(
            value.keys,
            value.values
        ):
            if not (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
            ):
                continue

            output_types[key.value] = infer_literal_type(
                val
            )

    return output_types


def build_contract(skill_path):
    try:
        source = skill_path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(source)

    except Exception as exc:
        return {
            "skill": skill_path.stem,
            "valid": False,
            "error": str(exc)
        }

    run_function = None

    for node in tree.body:

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "run"
        ):
            run_function = node
            break

    if run_function is None:
        return {
            "skill": skill_path.stem,
            "valid": False,
            "error": "run(args) function not found"
        }

    inputs = sorted(
        infer_arg_names(run_function)
    )

    outputs = sorted(
        infer_output_names(run_function)
    )

    output_types = infer_output_types(
        run_function
    )

    return {
        "skill": skill_path.stem,
        "valid": True,
        "inputs": {
            name: "unknown"
            for name in inputs
        },
        "outputs": {
            name: output_types.get(
                name,
                "unknown"
            )
            for name in outputs
        },
        "source": str(
            skill_path.relative_to(ROOT)
        )
    }


def build_all():
    ACTIVE_SKILLS.mkdir(
        parents=True,
        exist_ok=True
    )

    contracts = {}

    for path in sorted(
        ACTIVE_SKILLS.glob("*.py")
    ):
        contract = build_contract(
            path
        )

        if contract.get("valid"):
            contracts[
                contract["skill"]
            ] = contract

    CONTRACT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CONTRACT_FILE.write_text(
        json.dumps(
            contracts,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return contracts


def load_contracts():
    if not CONTRACT_FILE.exists():
        return {}

    try:
        data = json.loads(
            CONTRACT_FILE.read_text(
                encoding="utf-8"
            )
        )

        return (
            data
            if isinstance(data, dict)
            else {}
        )

    except Exception:
        return {}


def get_contract(skill):
    return load_contracts().get(
        skill
    )


def main():
    contracts = build_all()

    print(
        json.dumps(
            contracts,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
