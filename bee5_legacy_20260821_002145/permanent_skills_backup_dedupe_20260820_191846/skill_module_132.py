def levenshtein_distance(s1: str, s2: str) -> int:
    """Return the Levenshtein distance between strings s1 and s2.

    The distance is the minimum number of single-character insertions,
    deletions, or substitutions required to change s1 into s2.
    """
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1
    # Initialize previous row of distances
    prev_row = list(range(len2 + 1))
    for i, c1 in enumerate(s1, start=1):
        cur_row = [i] + [0] * len2
        for j, c2 in enumerate(s2, start=1):
            insert_cost = cur_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (c1 != c2)
            cur_row[j] = min(insert_cost, delete_cost, replace_cost)
        prev_row = cur_row
    return prev_row[-1]