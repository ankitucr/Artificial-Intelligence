# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def deep_merge(dict_a, dict_b):
    """
    Recursively merge two dictionaries.
    Values from dict_b take precedence over dict_a.
    Nested dictionaries are merged recursively.
    The original dictionaries are not modified; a new dictionary is returned.
    """
    if not isinstance(dict_a, dict):
        raise TypeError("dict_a must be a dict")
    if not isinstance(dict_b, dict):
        raise TypeError("dict_b must be a dict")
    result = {}
    for key in dict_a:
        if key in dict_b:
            val_a = dict_a[key]
            val_b = dict_b[key]
            if isinstance(val_a, dict) and isinstance(val_b, dict):
                result[key] = deep_merge(val_a, val_b)
            else:
                result[key] = val_b
        else:
            result[key] = dict_a[key]
    for key in dict_b:
        if key not in dict_a:
            result[key] = dict_b[key]
    return result


if __name__ == "__main__":
    # Basic override
    a = {"x": 1, "y": 2}
    b = {"y": 3, "z": 4}
    merged = deep_merge(a, b)
    assert merged == {"x": 1, "y": 3, "z": 4}, f"Failed basic merge: {merged}"

    # Nested dictionaries
    a = {"config": {"timeout": 30, "retries": 3}, "debug": True}
    b = {"config": {"retries": 5, "verbose": False}, "debug": False}
    merged = deep_merge(a, b)
    expected = {
        "config": {"timeout": 30, "retries": 5, "verbose": False},
        "debug": False,
    }
    assert merged == expected, f"Failed nested merge: {merged}"

    # Deep nesting with non-dict override
    a = {"level1": {"level2": {"value": 1}}}
    b = {"level1": {"level2": 2}}
    merged = deep_merge(a, b)
    expected = {"level1": {"level2": 2}}
    assert merged == expected, f"Failed deep override: {merged}"

    # Ensure originals are untouched
    original_a = {"a": {"b": 1}}
    original_b = {"a": {"c": 2}}
    merged = deep_merge(original_a, original_b)
    assert original_a == {"a": {"b": 1}}, "original_a was mutated"
    assert original_b == {"a": {"c": 2}}, "original_b was mutated"

    # Empty dictionaries
    assert deep_merge({}, {}) == {}, "Failed empty dict merge"
    assert deep_merge({"a": 1}, {}) == {"a": 1}, "Failed merge with empty dict_b"
    assert deep_merge({}, {"b": 2}) == {"b": 2}, "Failed merge with empty dict_a"

    # Type errors
    try:
        deep_merge([], {})
        raise AssertionError("Did not raise TypeError for non-dict dict_a")
    except TypeError:
        pass
    try:
        deep_merge({}, [])
        raise AssertionError("Did not raise TypeError for non-dict dict_b")
    except TypeError:
        pass

    print("All tests passed.")