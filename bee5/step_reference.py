#!/usr/bin/env python3

import re


REFERENCE_RE = re.compile(
    r"^\$\{step(\d+)\.([A-Za-z_][A-Za-z0-9_]*)\}$"
)


def parse_reference(value):
    if not isinstance(value, str):
        return None

    match = REFERENCE_RE.fullmatch(
        value.strip()
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        match.group(2),
    )


def resolve_value(value, step_results, user_input):
    """
    Resolve:
      ${input}
      ${step1.field}
      ${step2.word_count}
    """

    if not isinstance(value, str):
        return value

    stripped = value.strip()

    if stripped == "${input}":
        return user_input

    reference = parse_reference(
        stripped
    )

    if reference is None:
        return value

    step_number, field = reference

    result = step_results.get(
        step_number
    )

    if not isinstance(result, dict):
        raise KeyError(
            f"Step {step_number} result not available."
        )

    if field not in result:
        raise KeyError(
            f"Step {step_number} does not provide "
            f"output field '{field}'."
        )

    return result[field]


def resolve_args(
    args_template,
    step_results,
    user_input
):
    if not isinstance(
        args_template,
        dict
    ):
        raise TypeError(
            "args_template must be an object."
        )

    resolved = {}

    for key, value in args_template.items():

        resolved[key] = resolve_value(
            value,
            step_results,
            user_input
        )

    return resolved


def find_references(value):
    found = []

    if not isinstance(value, dict):
        return found

    for key, item in value.items():

        if not isinstance(
            item,
            str
        ):
            continue

        reference = parse_reference(
            item
        )

        if reference is not None:
            found.append({
                "argument": key,
                "step": reference[0],
                "field": reference[1]
            })

    return found


if __name__ == "__main__":
    results = {
        1: {
            "cleaned_text": "Hello BEE5",
            "word_count": 2,
        },
        2: {
            "text": "Hello BEE5",
            "word_count": 2,
            "unique_word_count": 2,
            "longest_word": "Hello",
        },
    }

    template = {
        "text": "${step1.cleaned_text}",
        "word_count": "${step2.word_count}",
        "unique_word_count": (
            "${step2.unique_word_count}"
        ),
        "longest_word": (
            "${step2.longest_word}"
        ),
    }

    print(
        resolve_args(
            template,
            results,
            "Original input"
        )
    )
