"""Utility to convert between CamelCase and snake_case strings."""

import re
from typing import Dict

SAMPLE_ARGS = {
    "text": "ExampleTextString",
    "direction": "to_snake"
}


def camel_to_snake(name: str) -> str:
    """Convert a CamelCase string to snake_case."""
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    # Insert underscore between lower/number and upper case letters
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before a capital letter that follows a lower case or digit
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return snake


def snake_to_camel(name: str, capitalize_first: bool = True) -> str:
    """Convert a snake_case string to CamelCase.

    If ``capitalize_first`` is False, the first component stays lower‑case,
    producing ``lowerCamelCase``; otherwise it produces ``UpperCamelCase``.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    parts = name.split("_")
    if not parts:
        return ""
    if capitalize_first:
        return "".join(p.title() for p in parts)
    else:
        return parts[0] + "".join(p.title() for p in parts[1:])


def run(args: Dict) -> Dict:
    """Entry point for the skill.

    Expected keys in ``args``:
        - ``text``: the input string.
        - ``direction`` (optional): ``"to_snake"`` or ``"to_camel"``.
          Defaults to ``"to_snake"``.

    Returns a dictionary containing:
        - ``original``: the original input string.
        - ``direction``: the performed conversion direction.
        - ``converted``: the result of the conversion.
        - ``alternate``: the conversion in the opposite direction.
    """
    text = args.get("text", "")
    direction = args.get("direction", "to_snake")
    if direction == "to_snake":
        converted = camel_to_snake(text)
        alternate = snake_to_camel(converted)
    elif direction == "to_camel":
        converted = snake_to_camel(text)
        alternate = camel_to_snake(converted)
    else:
        raise ValueError("direction must be either 'to_snake' or 'to_camel'")
    return {
        "original": text,
        "direction": direction,
        "converted": converted,
        "alternate": alternate
    }


if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_converted = "example_text_string"
    expected_alternate = "ExampleTextString"
    if result.get("converted") != expected_converted:
        raise AssertionError(
            f"Expected converted '{expected_converted}', got '{result.get('converted')}'"
        )
    if result.get("alternate") != expected_alternate:
        raise AssertionError(
            f"Expected alternate '{expected_alternate}', got '{result.get('alternate')}'"
        )
    print("CamelCase ↔ snake_case conversion test passed.")