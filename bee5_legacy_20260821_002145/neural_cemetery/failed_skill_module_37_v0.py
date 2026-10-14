# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def group_by(iterable, key_func):
    """
    Group elements of *iterable* by the result of *key_func*.

    Parameters
    ----------
    iterable : iterable
        The collection of items to be grouped.
    key_func : callable
        A function that takes an element from *iterable* and returns a hashable key.

    Returns
    -------
    dict
        A dictionary mapping each distinct key to a list of items that produced that key.

    Example
    -------
    >>> group_by(['apple', 'banana', 'apricot'], lambda x: x[0])
    {'a': ['apple', 'apricot'], 'b': ['banana']}
    """
    result = {}
    for item in iterable:
        key = key_func(item)
        result.setdefault(key, []).append(item)
    return result


if __name__ == "__main__":
    # Basic functionality test
    data = ['apple', 'banana', 'apricot', 'blueberry', 'avocado']
    expected = {
        'a': ['apple', 'apricot', 'avocado'],
        'b': ['banana', 'blueberry']
    }
    actual = group_by(data, lambda x: x[0])
    if actual != expected:
        raise AssertionError(f"group_by test failed: expected {expected}, got {actual}")

    # Test with numeric keys
    numbers = [1, 2, 3, 4, 5, 6]
    expected_even_odd = {
        'even': [2, 4, 6],
        'odd': [1, 3, 5]
    }
    actual_even_odd = group_by(numbers, lambda x: 'even' if x % 2 == 0 else 'odd')
    if actual_even_odd != expected_even_odd:
        raise AssertionError(f"group_by numeric test failed: expected {expected_even_odd}, got {actual_even_odd}")

    # Test with empty iterable
    if group_by([], lambda x: x) != {}:
        raise AssertionError("group_by empty iterable test failed")

    # Test with non-unique keys returning same list reference (should be separate lists)
    data2 = ['a', 'aa', 'b', 'bb']
    grouped = group_by(data2, lambda x: len(x))
    if grouped[1] is grouped[2]:
        raise AssertionError("group_by returned same list object for different keys")

    print("All tests passed.")