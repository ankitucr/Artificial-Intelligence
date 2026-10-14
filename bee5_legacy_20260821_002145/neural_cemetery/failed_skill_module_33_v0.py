# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Yield successive chunks of *size* from *iterable*.

    Args:
        iterable: Any iterable collection.
        size (int): The maximum length of each chunk. Must be a positive integer.

    Yields:
        tuple: A tuple containing up to *size* elements from the iterable.

    Raises:
        ValueError: If *size* is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    from itertools import islice
    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, size))
        if not chunk:
            break
        yield chunk


if __name__ == "__main__":
    # Test normal chunking
    result = list(chunked([1, 2, 3, 4, 5], 2))
    expected = [(1, 2), (3, 4), (5,)]
    assert result == expected, f"Expected {expected}, got {result}"

    # Test when size exactly divides the length
    result = list(chunked(range(6), 3))
    expected = [(0, 1, 2), (3, 4, 5)]
    assert result == expected, f"Expected {expected}, got {result}"

    # Test single-element chunks
    result = list(chunked('abc', 1))
    expected = [('a',), ('b',), ('c',)]
    assert result == expected, f"Expected {expected}, got {result}"

    # Test size larger than iterable
    result = list(chunked([1, 2], 5))
    expected = [(1, 2)]
    assert result == expected, f"Expected {expected}, got {result}"

    # Test empty iterable
    result = list(chunked([], 3))
    expected = []
    assert result == expected, f"Expected {expected}, got {result}"

    # Test invalid size
    try:
        list(chunked([1, 2, 3], 0))
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError not raised for size=0")

    try:
        list(chunked([1, 2, 3], -1))
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError not raised for negative size")

    print("All chunked tests passed.")