# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def deep_merge(dict_a, dict_b):
    """
    Recursively merge two dictionaries.
    Values from dict_b take precedence over dict_a.
    If both values are dictionaries, they are merged recursively.
    The original dictionaries are not modified; a new merged dictionary is returned.
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
    # Test 1: simple non-overlapping keys
    a = {"x": 1, "y": 2}
    b = {"z": 3}
    expected = {"x": 1, "y": 2, "z": 3}
    assert deep_merge(a, b) == expected, "Test 1 failed"

    # Test 2: overlapping non-dict values (b overrides)
    a = {"x": 1, "y": 2}
    b = {"y": 20, "z": 3}
    expected = {"x": 1, "y": 20, "z": 3}
    assert deep_merge(a, b) == expected, "Test 2 failed"

    # Test 3: nested dictionaries merge recursively
    a = {"config": {"a": 1, "b": 2}, "val": 5}
    b = {"config": {"b": 20, "c": 30}, "extra": 99}
    expected = {"config": {"a": 1, "b": 20, "c": 30}, "val": 5, "extra": 99}
    assert deep_merge(a, b) == expected, "Test 3 failed"

    # Test 4: deep nesting
    a = {"a": {"b": {"c": 1}}}
    b = {"a": {"b": {"d": 2}, "e": 3}}
    expected = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
    assert deep_merge(a, b) == expected, "Test 4 failed"

    # Test 5: ensure original dicts are unchanged
    a_original = {"x": {"y": 1}}
    b_original = {"x": {"z": 2}}
    merged = deep_merge(a_original, b_original)
    assert a_original == {"x": {"y": 1}}, "Original dict_a mutated"
    assert b_original == {"x": {"z": 2}}, "Original dict_b mutated"
    assert merged == {"x": {"y": 1, "z": 2}}, "Merge result incorrect"

    # All tests passed
    print("All tests passed.")