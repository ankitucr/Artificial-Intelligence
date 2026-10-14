# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Split an iterable into consecutive chunks of given size.

    Args:
        iterable: An iterable (e.g., list, tuple, generator).
        size (int): Desired chunk size (must be > 0).

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
    # Basic functionality tests
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]], "Test case 1 failed"
    assert chunked([], 3) == [], "Test case 2 failed"
    assert chunked((0, 1, 2, 3, 4, 5, 6), 3) == [[0, 1, 2], [3, 4, 5], [6]], "Test case 3 failed"
    assert chunked('abcdef', 2) == [['a', 'b'], ['c', 'd'], ['e', 'f']], "Test case 4 failed"

    # Edge case: size larger than iterable
    assert chunked([1, 2, 3], 10) == [[1, 2, 3]], "Test case 5 failed"

    # Error handling
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("ValueError not raised for size=0")
    except ValueError:
        pass

    try:
        chunked([1, 2, 3], -1)
        raise AssertionError("ValueError not raised for negative size")
    except ValueError:
        pass

    print("All tests passed.")