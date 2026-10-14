# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunks(iterable, size):
    """
    Split an iterable into consecutive chunks of a given size.

    Parameters
    ----------
    iterable : iterable
        The source iterable.
    size : int
        Desired size of each chunk. Must be a positive integer.

    Yields
    ------
    list
        Lists containing up to ``size`` elements from the iterable.

    Examples
    --------
    >>> list(chunks([1, 2, 3, 4, 5], 2))
    [[1, 2], [3, 4], [5]]
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


if __name__ == "__main__":
    # Test with a list
    result = list(chunks([1, 2, 3, 4, 5], 2))
    assert result == [[1, 2], [3, 4], [5]], f"Unexpected result: {result}"

    # Test with a generator
    gen = (i * i for i in range(7))  # 0,1,4,9,16,25,36
    result = list(chunks(gen, 3))
    assert result == [[0, 1, 4], [9, 16, 25], [36]], f"Unexpected result: {result}"

    # Test size validation
    try:
        list(chunks([1, 2, 3], 0))
        raise AssertionError("Expected ValueError for size=0")
    except ValueError:
        pass

    print("All tests passed.")