# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Split *iterable* into chunks of length *size*.

    Args:
        iterable: Any iterable (list, tuple, generator, etc.).
        size (int): Positive integer indicating the maximum length of each chunk.

    Returns:
        List[List[Any]]: A list where each element is a list representing a chunk.

    Raises:
        ValueError: If *size* is not a positive integer.
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
    assert chunked([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 3) == [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [9],
    ], "Failed on simple list split"

    assert chunked(range(5), 2) == [[0, 1], [2, 3], [4]], "Failed on range iterator"

    assert chunked([], 4) == [], "Failed on empty iterable"

    # size larger than iterable length
    assert chunked([1, 2, 3], 10) == [[1, 2, 3]], "Failed when size > len(iterable)"

    # invalid size
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("Did not raise ValueError for non-positive size")
    except ValueError:
        pass

    # generator test
    gen = (i * i for i in range(7))  # squares 0..6
    expected = [[0, 1, 4], [9, 16, 25], [36]]
    assert chunked(gen, 3) == expected, "Failed on generator input"

    print("All tests passed.")