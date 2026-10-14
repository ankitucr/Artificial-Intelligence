# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Split an iterable into consecutive chunks of the given size.

    Parameters:
        iterable: Any iterable (e.g., list, tuple, generator).
        size (int): Desired maximum size of each chunk. Must be >= 1.

    Returns:
        List[List]: A list where each element is a list representing a chunk.

    Example:
        >>> chunked([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be an integer >= 1")
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
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunked([], 3) == []
    assert chunked((i for i in range(7)), 3) == [[0, 1, 2], [3, 4, 5], [6]]
    # Edge case: size of 1 returns each element in its own list
    assert chunked([9, 8, 7], 1) == [[9], [8], [7]]
    # Invalid size should raise ValueError
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("Expected ValueError for size=0")
    except ValueError:
        pass
    try:
        chunked([1, 2, 3], -2)
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass
    print("All tests passed.")