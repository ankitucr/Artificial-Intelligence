# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def deep_merge(dict1, dict2):
    """
    Recursively merge two dictionaries.
    Values from dict2 take precedence over those from dict1.
    The merge is performed in a new dictionary; the inputs are not mutated.

    Example:
        a = {'x': 1, 'y': {'z': 2}}
        b = {'y': {'w': 3}, 'k': 4}
        deep_merge(a, b) -> {'x': 1, 'y': {'z': 2, 'w': 3}, 'k': 4}
    """
    if not isinstance(dict1, dict):
        raise TypeError("dict1 must be a dict")
    if not isinstance(dict2, dict):
        raise TypeError("dict2 must be a dict")

    result = {}
    # Start with a shallow copy of dict1
    for key, value in dict1.items():
        if isinstance(value, dict):
            result[key] = deep_copy_dict(value)
        else:
            result[key] = value

    # Merge/override with dict2
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            if isinstance(value, dict):
                result[key] = deep_copy_dict(value)
            else:
                result[key] = value
    return result


def deep_copy_dict(d):
    """
    Return a deep copy of a dictionary where values that are dictionaries
    are also recursively copied. Non-dict values are copied by reference
    (which is fine for immutable types).
    """
    copy = {}
    for k, v in d.items():
        if isinstance(v, dict):
            copy[k] = deep_copy_dict(v)
        else:
            copy[k] = v
    return copy


if __name__ == "__main__":
    # Basic merge
    a = {"a": 1, "b": {"c": 2, "d": 3}}
    b = {"b": {"e": 4}, "f": 5}
    merged = deep_merge(a, b)
    expected = {"a": 1, "b": {"c": 2, "d": 3, "e": 4}, "f": 5}
    if merged != expected:
        raise AssertionError(f"Basic merge failed: {merged} != {expected}")

    # Override values
    a = {"x": 1, "y": {"z": 2}}
    b = {"x": 10, "y": {"z": 20}}
    merged = deep_merge(a, b)
    expected = {"x": 10, "y": {"z": 20}}
    if merged != expected:
        raise AssertionError(f"Override failed: {merged} != {expected}")

    # Ensure original dicts are unchanged
    a_original = {"a": {"b": 1}}
    b_original = {"a": {"c": 2}}
    merged = deep_merge(a_original, b_original)
    if a_original != {"a": {"b": 1}} or b_original != {"a": {"c": 2}}:
        raise AssertionError("Original dictionaries were mutated")

    # Empty dicts
    if deep_merge({}, {}) != {}:
        raise AssertionError("Empty dict merge failed")

    # Non-dict inputs
    try:
        deep_merge([], {})
        raise AssertionError("TypeError not raised for non-dict dict1")
    except TypeError:
        pass

    try:
        deep_merge({}, [])
        raise AssertionError("TypeError not raised for non-dict dict2")
    except TypeError:
        pass

    print("All tests passed.")