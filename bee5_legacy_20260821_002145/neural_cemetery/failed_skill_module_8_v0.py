# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def group_by(iterable, key_func):
    """
    Group elements of `iterable` by the result of `key_func`.

    Parameters
    ----------
    iterable : iterable
        The collection of items to group.
    key_func : callable
        A function that takes an element and returns a hashable key.

    Returns
    -------
    dict
        A dictionary mapping each key to a list of items that produced that key.
    """
    result = {}
    for item in iterable:
        key = key_func(item)
        result.setdefault(key, []).append(item)
    return result


if __name__ == "__main__":
    # Test 1: group numbers by even/odd
    data = [1, 2, 3, 4, 5, 6]
    expected = {0: [2, 4, 6], 1: [1, 3, 5]}
    assert group_by(data, lambda x: x % 2) == expected, "Failed even/odd grouping"

    # Test 2: group strings by length
    words = ["hi", "test", "a", "hello"]
    expected = {2: ["hi"], 4: ["test"], 1: ["a"], 5: ["hello"]}
    assert group_by(words, len) == expected, "Failed length grouping"

    # Test 3: empty iterable
    assert group_by([], lambda x: x) == {}, "Failed empty iterable"

    # If all assertions pass, exit with success
    print("All group_by tests passed.")