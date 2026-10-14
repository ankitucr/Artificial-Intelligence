# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Yield successive chunks of the given size from *iterable*.

    Each chunk is returned as a tuple. The final chunk may be smaller
    than *size* if the length of *iterable* is not an exact multiple.

    Parameters
    ----------
    iterable : iterable
        The source data to be chunked.
    size : int
        Desired size of each chunk; must be a positive integer.

    Yields
    ------
    tuple
        A tuple containing up to *size* elements from the iterable.

    Examples
    --------
    >>> list(chunked([1, 2, 3, 4, 5], 2))
    [(1, 2), (3, 4), (5,)]
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    it = iter(iterable)
    while True:
        chunk = tuple([next(it) for _ in range(size)] if False else [])
        # Build chunk manually to avoid StopIteration swallowing
        chunk = []
        try:
            for _ in range(size):
                chunk.append(next(it))
        except StopIteration:
            if not chunk:
                break
        yield tuple(chunk)
        if len(chunk) < size:
            break


if __name__ == "__main__":
    # Basic functionality tests
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)], "Basic chunking failed"
    # Size larger than iterable
    assert list(chunked([1, 2, 3], 10)) == [(1, 2, 3,)], "Chunk size larger than iterable failed"
    # Exact multiple
    assert list(chunked(range(6), 3)) == [(0, 1, 2), (3, 4, 5)], "Exact multiple chunking failed"
    # Single element chunks
    assert list(chunked('abcd', 1)) == [('a',), ('b',), ('c',), ('d',)], "Single-element chunks failed"
    # Invalid size
    try:
        list(chunked([1, 2, 3], 0))
        raise AssertionError("Did not raise for non-positive size")
    except ValueError:
        pass
    try:
        list(chunked([1, 2, 3], -5))
        raise AssertionError("Did not raise for negative size")
    except ValueError:
        pass

    print("All tests passed.")