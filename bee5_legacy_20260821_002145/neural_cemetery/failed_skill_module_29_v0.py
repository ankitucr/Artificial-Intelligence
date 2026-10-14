# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Yield successive chunks from `iterable` of length `size`.

    Parameters
    ----------
    iterable : iterable
        The source iterable.
    size : int
        Desired chunk size; must be a positive integer.

    Yields
    ------
    tuple
        Tuples containing up to `size` items from the iterable.

    Raises
    ------
    ValueError
        If `size` is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    iterator = iter(iterable)
    while True:
        chunk = []
        try:
            for _ in range(size):
                chunk.append(next(iterator))
        except StopIteration:
            if chunk:
                yield tuple(chunk)
            break
        yield tuple(chunk)


if __name__ == "__main__":
    # Test normal case
    result = list(chunked([1, 2, 3, 4, 5], 2))
    expected = [(1, 2), (3, 4), (5,)]
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")

    # Test size larger than iterable
    result = list(chunked([1, 2, 3], 10))
    expected = [(1, 2, 3)]
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")

    # Test exact division
    result = list(chunked(range(6), 3))
    expected = [(0, 1, 2), (3, 4, 5)]
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")

    # Test size of 1
    result = list(chunked([7, 8, 9], 1))
    expected = [(7,), (8,), (9,)]
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")

    # Test invalid size
    try:
        list(chunked([1, 2, 3], 0))
        raise AssertionError("Expected ValueError for size=0")
    except ValueError:
        pass

    try:
        list(chunked([1, 2, 3], -5))
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass

    # All tests passed
    print("All tests passed.")