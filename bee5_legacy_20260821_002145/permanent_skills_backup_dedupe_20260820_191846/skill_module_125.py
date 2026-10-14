def levenshtein_distance(s1: str, s2: str) -> int:
    """Return the Levenshtein distance between strings s1 and s2.

    The implementation uses a dynamic programming matrix with O(min(len(s1), len(s2)))
    space complexity.
    """
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    # Ensure that s1 is the shorter string to use less space
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    previous_row = list(range(len1 + 1))
    for i, c2 in enumerate(s2, 1):
        current_row = [i]
        for j, c1 in enumerate(s1, 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]