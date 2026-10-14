# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunk_sequence(seq, size):
    """
    Split a sequence into consecutive chunks of a given size.

    Parameters
    ----------
    seq : sequence
        The input sequence (list, tuple, range, etc.).
    size : int
        Desired size of each chunk. Must be a positive integer.

    Returns
    -------
    list[tuple]
        A list where each element is a tuple representing a chunk of the
        original sequence. The final chunk may be shorter if the length of
        ``seq`` is not a multiple of ``size``.

    Raises
    ------
    ValueError
        If ``size`` is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    # Ensure we can index the sequence; convert to list if needed
    try:
        length = len(seq)
    except TypeError:
        seq = list(seq)
        length = len(seq)
    result = []
    for start in range(0, length, size):
        result.append(tuple(seq[start:start + size]))
    return result


if __name__ == "__main__":
    # Basic functionality tests
    assert chunk_sequence([], 1) == []
    assert chunk_sequence([1, 2, 3, 4, 5], 2) == [(1, 2), (3, 4), (5,)]
    assert chunk_sequence(range(10), 3) == [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]
    assert chunk_sequence('abcdef', 4) == [('a', 'b', 'c', 'd'), ('e', 'f')]

    # Edge case: size larger than sequence
    assert chunk_sequence([1, 2], 5) == [(1, 2)]

    # Invalid size raises ValueError
    try:
        chunk_sequence([1, 2, 3], 0)
        raise AssertionError("Expected ValueError for size=0")
    except ValueError:
        pass

    try:
        chunk_sequence([1, 2, 3], -1)
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass

    print("All tests passed.")