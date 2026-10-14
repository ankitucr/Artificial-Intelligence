# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(sequence, size):
    """
    Split a sequence into chunks of given size.

    Parameters
    ----------
    sequence : Sequence
        The input sequence (list, tuple, string, etc.) to be chunked.
    size : int
        Desired size of each chunk. Must be a positive integer.

    Returns
    -------
    List[List]
        A list where each element is a list representing a chunk of the original sequence.
        The final chunk may contain fewer than ``size`` elements if the sequence length
        is not a multiple of ``size``.

    Raises
    ------
    ValueError
        If ``size`` is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    result = []
    for i in range(0, len(sequence), size):
        result.append(list(sequence[i:i + size]))
    return result


if __name__ == "__main__":
    # Test 1: basic functionality
    seq = list(range(1, 11))  # [1,2,...,10]
    expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
    if chunked(seq, 3) != expected:
        raise AssertionError("Test 1 failed")

    # Test 2: size larger than sequence
    expected = [seq]
    if chunked(seq, 20) != expected:
        raise AssertionError("Test 2 failed")

    # Test 3: size equals 1 (should return list of single-element lists)
    expected = [[x] for x in seq]
    if chunked(seq, 1) != expected:
        raise AssertionError("Test 3 failed")

    # Test 4: empty sequence
    if chunked([], 5) != []:
        raise AssertionError("Test 4 failed")

    # Test 5: invalid size
    try:
        chunked(seq, 0)
        raise AssertionError("Test 5 failed: did not raise for size 0")
    except ValueError:
        pass

    try:
        chunked(seq, -3)
        raise AssertionError("Test 5 failed: did not raise for negative size")
    except ValueError:
        pass

    print("All tests passed.")