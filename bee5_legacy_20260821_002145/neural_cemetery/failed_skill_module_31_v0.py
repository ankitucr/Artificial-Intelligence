# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Split an iterable into chunks of given size.

    Parameters
    ----------
    iterable : iterable
        The source iterable.
    size : int
        Desired chunk size. Must be a positive integer.

    Returns
    -------
    list[list]
        A list of chunks, each chunk being a list of up to `size` items.

    Raises
    ------
    ValueError
        If `size` is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    result = []
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            result.append(chunk)
            chunk = []
    if chunk:
        result.append(chunk)
    return result


if __name__ == "__main__":
    # Test normal usage
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunked(range(7), 3) == [[0, 1, 2], [3, 4, 5], [6]]
    # Test empty iterable
    assert chunked([], 3) == []
    # Test size larger than iterable
    assert chunked([1, 2], 5) == [[1, 2]]
    # Test size of 1
    assert chunked([1, 2, 3], 1) == [[1], [2], [3]]
    # Test invalid size
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("Expected ValueError for size 0")
    except ValueError:
        pass
    try:
        chunked([1, 2, 3], -2)
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass
    print("All tests passed.")