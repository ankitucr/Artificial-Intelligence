# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def levenshtein(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein distance between two strings.

    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions or substitutions) required to change one string
    into the other.

    Parameters
    ----------
    s1 : str
        First string.
    s2 : str
        Second string.

    Returns
    -------
    int
        The Levenshtein distance between s1 and s2.
    """
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Initialize the distance matrix with the first row and column.
    prev_row = list(range(len2 + 1))
    for i, c1 in enumerate(s1, 1):
        current_row = [i] + [0] * len2
        for j, c2 in enumerate(s2, 1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (c1 != c2)
            current_row[j] = min(insert_cost, delete_cost, replace_cost)
        prev_row = current_row
    return prev_row[-1]


if __name__ == "__main__":
    # Basic sanity checks
    assert levenshtein("", "") == 0
    assert levenshtein("a", "") == 1
    assert levenshtein("", "abc") == 3
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("flaw", "lawn") == 2
    assert levenshtein("intention", "execution") == 5
    # Test identical strings
    assert levenshtein("same", "same") == 0
    # Test case sensitivity
    assert levenshtein("Case", "case") == 1
    # Test longer strings
    long1 = "the quick brown fox jumps over the lazy dog"
    long2 = "the quick brown fox jumped over a lazy dog"
    assert levenshtein(long1, long2) == 3

    print("All tests passed.")