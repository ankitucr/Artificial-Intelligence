def hamming_distance(s1, s2):
    if len(s1) != len(s2):
        return None
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))