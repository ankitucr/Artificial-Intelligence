# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def deep_merge(a: dict, b: dict) -> dict:
    """
    Recursively merge two dictionaries.

    Values from ``b`` override those from ``a``. If both ``a`` and ``b`` contain
    a mapping for the same key and those values are also dictionaries, the
    merge is performed recursively.

    The function returns a new dictionary; neither ``a`` nor ``b`` is mutated.

    Example
    -------
    >>> deep_merge({"x": 1, "y": {"z": 2}}, {"y": {"w": 3}, "k": 4})
    {'x': 1, 'y': {'z': 2, 'w': 3}, 'k': 4}
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise TypeError("Both arguments must be dictionaries")

    result = {}
    # Start with a shallow copy of a
    for key, value in a.items():
        # If the value is a dict we copy it to avoid mutating original structures
        result[key] = value.copy() if isinstance(value, dict) else value

    for key, b_value in b.items():
        if key in result:
            a_value = result[key]
            if isinstance(a_value, dict) and isinstance(b_value, dict):
                # Recurse for nested dictionaries
                result[key] = deep_merge(a_value, b_value)
            else:
                # Overwrite with b's value
                result[key] = b_value
        else:
            # New key from b
            result[key] = b_value.copy() if isinstance(b_value, dict) else b_value

    return result


if __name__ == "__main__":
    # Test 1: simple non‑nested merge
    a1 = {"a": 1, "b": 2}
    b1 = {"b": 3, "c": 4}
    expected1 = {"a": 1, "b": 3, "c": 4}
    assert deep_merge(a1, b1) == expected1, "Test 1 failed"

    # Test 2: nested dictionaries
    a2 = {"x": {"y": 1, "z": 2}, "m": 5}
    b2 = {"x": {"z": 3, "w": 4}, "n": 6}
    expected2 = {"x": {"y": 1, "z": 3, "w": 4}, "m": 5, "n": 6}
    assert deep_merge(a2, b2) == expected2, "Test 2 failed"

    # Test 3: deep nesting
    a3 = {"a": {"b": {"c": 1}}}
    b3 = {"a": {"b": {"d": 2}, "e": 3}}
    expected3 = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
    assert deep_merge(a3, b3) == expected3, "Test 3 failed"

    # Test 4: ensure original dicts are not mutated
    a_orig = {"p": {"q": 1}}
    b_orig = {"p": {"r": 2}}
    result = deep_merge(a_orig, b_orig)
    assert a_orig == {"p": {"q": 1}}, "Original 'a' mutated"
    assert b_orig == {"p": {"r": 2}}, "Original 'b' mutated"
    assert result == {"p": {"q": 1, "r": 2}}, "Result incorrect"

    # Test 5: non‑dict arguments raise TypeError
    try:
        deep_merge({"a": 1}, ["not", "a", "dict"])
        raise AssertionError("TypeError not raised for non-dict b")
    except TypeError:
        pass

    try:
        deep_merge(["not", "a", "dict"], {"a": 1})
        raise AssertionError("TypeError not raised for non-dict a")
    except TypeError:
        pass

    print("All deep_merge tests passed.")