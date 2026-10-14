# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """Yield successive chunks of *size* from *iterable*.

    Args:
        iterable: Any iterable source of items.
        size (int): Number of items per chunk; must be > 0.

    Yields:
        list: A list containing up to *size* items.

    Examples:
        >>> list(chunked([1, 2, 3, 4, 5], 2))
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


__all__ = ["chunked"]


if __name__ == "__main__":
    # Basic correctness tests
    assert list(chunked([], 3)) == [], "Empty iterable should yield no chunks"
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]], "Standard case failed"
    assert list(chunked(range(5), 5)) == [[0, 1, 2, 3, 4]], "Exact size case failed"
    assert list(chunked(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]], "Multiple chunks case failed"

    # Edge cases
    try:
        list(chunked([1, 2, 3], 0))
        raise AssertionError("size=0 should have raised ValueError")
    except ValueError:
        pass

    try:
        list(chunked([1, 2, 3], -1))
        raise AssertionError("negative size should have raised ValueError")
    except ValueError:
        pass

    # Large iterable test (does not exhaust memory)
    large_gen = (i for i in range(10000))
    count = 0
    for _ in chunked(large_gen, 100):
        count += 1
    assert count == 100, "Chunk count mismatch for large generator"

    print("All tests passed.")