# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunk(iterable, size):
    """
    Split an iterable into consecutive chunks of a given size.

    Args:
        iterable: Any iterable (list, tuple, generator, etc.).
        size (int): The maximum size of each chunk. Must be > 0.

    Returns:
        generator: Yields lists, each containing up to `size` elements.

    Example:
        >>> list(chunk([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")

    it = iter(iterable)
    while True:
        batch = []
        try:
            for _ in range(size):
                batch.append(next(it))
        except StopIteration:
            if batch:
                yield batch
            break
        yield batch


if __name__ == "__main__":
    # Basic functionality tests
    assert list(chunk([], 3)) == []
    assert list(chunk([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert list(chunk((i for i in range(7)), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
    # Edge cases
    try:
        list(chunk([1, 2, 3], 0))
        raise AssertionError("Expected ValueError for size=0")
    except ValueError:
        pass
    try:
        list(chunk([1, 2, 3], -1))
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass
    # Large chunk size (larger than iterable)
    assert list(chunk([1, 2, 3], 10)) == [[1, 2, 3]]
    # Verify that the original iterable is not consumed unexpectedly
    gen = (i * i for i in range(5))
    chunks = list(chunk(gen, 2))
    assert chunks == [[0, 1], [4, 9], [16]]
    # If all tests pass, exit normally
    print("All chunk tests passed.")