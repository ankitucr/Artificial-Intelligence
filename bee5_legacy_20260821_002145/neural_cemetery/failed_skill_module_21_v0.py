# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def group_by(iterable, key_func):
    """
    Group elements of *iterable* by the result of *key_func*.

    Returns a dictionary where each key is the result of applying *key_func* to
    an element, and the corresponding value is a list of all elements that map
    to that key.

    Example:
        >>> group_by([1, 2, 3, 4], lambda x: 'even' if x % 2 == 0 else 'odd')
        {'odd': [1, 3], 'even': [2, 4]}
    """
    result = {}
    for item in iterable:
        key = key_func(item)
        if key in result:
            result[key].append(item)
        else:
            result[key] = [item]
    return result


if __name__ == "__main__":
    # Test 1: parity grouping
    data = [1, 2, 3, 4, 5, 6]
    expected = {"odd": [1, 3, 5], "even": [2, 4, 6]}
    actual = group_by(data, lambda x: "odd" if x % 2 else "even")
    if actual != expected:
        raise AssertionError(f"Parity test failed: expected {expected}, got {actual}")

    # Test 2: grouping strings by length
    words = ["cat", "dog", "mouse", "rat", "elephant"]
    expected_len = {3: ["cat", "dog", "rat"], 5: ["mouse"], 8: ["elephant"]}
    actual_len = group_by(words, len)
    if actual_len != expected_len:
        raise AssertionError(f"Length grouping failed: expected {expected_len}, got {actual_len}")

    # Test 3: empty iterable
    empty = []
    expected_empty = {}
    actual_empty = group_by(empty, lambda x: x)
    if actual_empty != expected_empty:
        raise AssertionError(f"Empty iterable test failed: expected {expected_empty}, got {actual_empty}")

    print("All group_by tests passed.")