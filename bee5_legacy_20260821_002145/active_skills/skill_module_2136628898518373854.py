"""Utility to compute the Levenshtein (edit) distance between two strings."""

from typing import Dict

SAMPLE_ARGS = {
    "s1": "kitten",
    "s2": "sitting"
}

def levenshtein_distance(s1: str, s2: str) -> int:
    """Return the Levenshtein distance between *s1* and *s2*.

    The implementation uses a classic dynamic‑programming matrix
    with O(len(s1) * len(s2)) time and O(min(len(s1), len(s2))) space.
    """
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    # Ensure that s1 is the shorter string to minimise memory usage.
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1

    previous_row = list(range(len1 + 1))
    for i, c2 in enumerate(s2, 1):
        current_row = [i] + [0] * len1
        for j, c1 in enumerate(s1, 1):
            insertions = previous_row[j] + 1      # Deletion from s2 (insert into s1)
            deletions = current_row[j - 1] + 1    # Insertion into s2 (delete from s1)
            substitutions = previous_row[j - 1] + (c1 != c2)
            current_row[j] = min(insertions, deletions, substitutions)
        previous_row = current_row
    return previous_row[-1]

def run(args: Dict) -> Dict:
    """Entry point for the skill.

    Expects a dictionary with keys ``s1`` and ``s2`` (both strings).
    Returns a dictionary containing the computed ``distance``.
    """
    s1 = args.get("s1", "")
    s2 = args.get("s2", "")
    distance = levenshtein_distance(s1, s2)
    return {"distance": distance, "s1": s1, "s2": s2}

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    # The known distance between "kitten" and "sitting" is 3.
    expected = 3
    if result.get("distance") != expected:
        raise AssertionError(f"Expected distance {expected}, got {result.get('distance')}")
    print("Levenshtein distance test passed.")