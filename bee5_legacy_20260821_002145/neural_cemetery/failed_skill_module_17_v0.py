# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def group_by(iterable, key_func):
    """Group elements of *iterable* by the result of *key_func*.

    Returns a dictionary mapping each distinct key to a list of items that
    produced that key.  The keys must be hashable; otherwise a TypeError is
    raised.

    Example:
        >>> group_by([1, 2, 3, 4], lambda x: x % 2)
        {1: [1, 3], 0: [2, 4]}
    """
    result = {}
    for item in iterable:
        key = key_func(item)
        if not isinstance(key, (int, float, str, tuple, frozenset, bool, bytes)):
            # Let Python raise the appropriate error when used as a dict key.
            try:
                hash(key)
            except Exception as e:
                raise TypeError(f"Unhashable key produced: {key!r}") from e
        result.setdefault(key, []).append(item)
    return result


if __name__ == "__main__":
    # Test 1: basic even/odd grouping
    data = [1, 2, 3, 4, 5, 6]
    expected = {"odd": [1, 3, 5], "even": [2, 4, 6]}
    result = group_by(data, lambda x: "even" if x % 2 == 0 else "odd")
    if result != expected:
        raise AssertionError(f"Test 1 failed: expected {expected}, got {result}")

    # Test 2: grouping by length of string
    words = ["apple", "bat", "car", "doge", "egg"]
    expected = {5: ["apple"], 3: ["bat", "car"], 4: ["doge", "egg"]}
    result = group_by(words, len)
    if result != expected:
        raise AssertionError(f"Test 2 failed: expected {expected}, got {result}")

    # Test 3: empty iterable
    result = group_by([], lambda x: x)
    if result != {}:
        raise AssertionError(f"Test 3 failed: expected empty dict, got {result}")

    # Test 4: unhashable key should raise TypeError
    try:
        group_by([1, 2], lambda x: [])
        raise AssertionError("Test 4 failed: TypeError not raised for unhashable key")
    except TypeError:
        pass  # Expected

    print("All tests passed.")