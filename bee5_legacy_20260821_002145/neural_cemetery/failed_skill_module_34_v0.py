# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Split an iterable into consecutive chunks of given size.

    Args:
        iterable: Any iterable (list, tuple, generator, etc.).
        size (int): Positive integer size of each chunk.

    Returns:
        List[List[Any]]: A list where each element is a list representing a chunk.

    Raises:
        ValueError: If size is not a positive integer.
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
    # Basic tests
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]], "Test 1 failed"
    assert chunked([], 3) == [], "Test 2 failed"
    assert chunked([1, 2, 3], 5) == [[1, 2, 3]], "Test 3 failed"
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("Test 4 failed: did not raise ValueError for size=0")
    except ValueError:
        pass
    try:
        chunked([1, 2, 3], -1)
        raise AssertionError("Test 5 failed: did not raise ValueError for negative size")
    except ValueError:
        pass
    # Test with generator
    gen = (i for i in range(7))
    assert chunked(gen, 3) == [[0, 1, 2], [3, 4, 5], [6]], "Test 6 failed"
    print("All tests passed.")