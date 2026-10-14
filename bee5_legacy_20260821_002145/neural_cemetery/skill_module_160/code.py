def hamming_distance(s1, s2):
    if len(s1)!= len(s2):
        raise ValueError('Input strings must be of equal length')
    return sum(c1!= c2 for c1, c2 in zip(s1, s2))