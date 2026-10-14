import re
from typing import List

def extract_iso_dates(text: str) -> List[str]:
    """
    Extract all substrings from the given text that match the ISO date format YYYY-MM-DD.
    Returns a list of the matching date strings in the order they appear.
    """
    pattern = r'\b\d{4}-\d{2}-\d{2}\b'
    return re.findall(pattern, text)

# Simple self‑test (can be removed or ignored by the caller)
if __name__ == "__main__":
    sample = "Events: 2023-07-15, 2022-12-01, and an invalid date 2022-13-01."
    print(extract_iso_dates(sample))  # Expected: ['2023-07-15', '2022-12-01']