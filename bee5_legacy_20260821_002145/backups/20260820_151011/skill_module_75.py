import re
from datetime import datetime, date
from typing import List

_DATE_PATTERNS = [
    r'\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2},\s+\d{4}\b',
    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
]

_MONTH_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}

def _parse_long_form(date_str: str) -> date:
    parts = date_str.replace(',', '').split()
    month_str, day_str, year_str = parts[0].lower(), parts[1], parts[2]
    month = _MONTH_MAP[month_str[:3]]
    day = int(day_str)
    year = int(year_str)
    return date(year, month, day)

def _parse_numeric(date_str: str) -> date:
    sep = '/' if '/' in date_str else '-'
    parts = [int(p) for p in date_str.split(sep)]
    if len(parts[0]) == 4:  # YYYY/MM/DD
        year, month, day = parts
    else:
        # Assume MM/DD/YY or MM/DD/YYYY
        month, day, year = parts
        if year < 100:
            year += 2000 if year < 70 else 1900
    return date(year, month, day)

def extract_dates(text: str) -> List[date]:
    """
    Scan the input text and return a list of datetime.date objects
    representing all dates found. Supports common English long forms
    (e.g., "January 5, 2023") and numeric forms (e.g., "01/05/2023",
    "2023-01-05").
    """
    found_dates: List[date] = []
    for pattern in _DATE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            date_str = match.group(0)
            try:
                if any(month in date_str.lower() for month in _MONTH_MAP):
                    parsed = _parse_long_form(date_str)
                else:
                    parsed = _parse_numeric(date_str)
                found_dates.append(parsed)
            except Exception:
                continue
    return found_dates