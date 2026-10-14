# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def deep_merge(dict1, dict2):
    """
    Recursively merge two dictionaries.

    Keys from ``dict2`` take precedence over ``dict1``. If the value for a key
    in both dictionaries is itself a dictionary, those sub‑dictionaries are
    merged recursively.

    The function returns a **new** dictionary; the input dictionaries are not
    modified.

    Parameters
    ----------
    dict1, dict2 : dict
        Dictionaries to merge.

    Returns
    -------
    dict
        The merged dictionary.
    """
    if not isinstance(dict1, dict):
        raise TypeError("dict1 must be a dict")
    if not isinstance(dict2, dict):
        raise TypeError("dict2 must be a dict")

    merged = dict1.copy()
    for key, value2 in dict2.items():
        if key in merged:
            value1 = merged[key]
            if isinstance(value1, dict) and isinstance(value2, dict):
                merged[key] = deep_merge(value1, value2)
            else:
                merged[key] = value2
        else:
            merged[key] = value2
    return merged


if __name__ == "__main__":
    # Basic overwrite
    a = {"a": 1, "b": 2}
    b = {"b": 3, "c": 4}
    expected = {"a": 1, "b": 3, "c": 4}
    result = deep_merge(a, b)
    if result != expected:
        raise AssertionError(f"Test 1 failed: {result} != {expected}")

    # Nested dictionaries
    a = {"x": {"y": 1, "z": 2}, "w": 5}
    b = {"x": {"y": 10, "new": 3}, "new_top": 7}
    expected = {"x": {"y": 10, "z": 2, "new": 3}, "w": 5, "new_top": 7}
    result = deep_merge(a, b)
    if result != expected:
        raise AssertionError(f"Test 2 failed: {result} != {expected}")

    # Ensure original dicts are unchanged
    a_original = {"a": 1}
    b_original = {"a": {"b": 2}}
    merged = deep_merge(a_original, b_original)
    if a_original != {"a": 1} or b_original != {"a": {"b": 2}}:
        raise AssertionError("Original dictionaries were modified")

    # Non-dict values should be overridden
    a = {"key": [1, 2, 3]}
    b = {"key": "override"}
    expected = {"key": "override"}
    result = deep_merge(a, b)
    if result != expected:
        raise AssertionError(f"Test 4 failed: {result} != {expected}")

    # Deep nesting
    a = {"a": {"b": {"c": 1}}}
    b = {"a": {"b": {"d": 2}}}
    expected = {"a": {"b": {"c": 1, "d": 2}}}
    result = deep_merge(a, b)
    if result != expected:
        raise AssertionError(f"Test 5 failed: {result} != {expected}")

    # Empty dicts
    if deep_merge({}, {}) != {}:
        raise AssertionError("Test 6 failed: empty dict merge not {}")
    if deep_merge({"a": 1}, {}) != {"a": 1}:
        raise AssertionError("Test 7 failed: merge with empty dict2")
    if deep_merge({}, {"b": 2}) != {"b": 2}:
        raise AssertionError("Test 8 failed: merge with empty dict1")

    # Type errors
    try:
        deep_merge([], {})
        raise AssertionError("Test 9 failed: did not raise TypeError for dict1")
    except TypeError:
        pass
    try:
        deep_merge({}, [])
        raise AssertionError("Test 10 failed: did not raise TypeError for dict2")
    except TypeError:
        pass

    # If all tests pass, exit silently
    # (The process will exit with code 0)