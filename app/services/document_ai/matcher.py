import re
from datetime import date, datetime
from typing import Optional, Tuple
from rapidfuzz import fuzz

UDIN_REGEX = r"^[0-9]{2}[0-9]{6}[A-Z0-9]{10}$"


def calculate_fuzzy_match_score(name1: str, name2: str) -> float:
    """
    Calculates composite fuzzy match ratio between two legal or trade names
    using token sort ratio and token set ratio.
    Returns score between 0.0 and 100.0.
    """
    if not name1 or not name2:
        return 0.0

    n1 = name1.strip().upper()
    n2 = name2.strip().upper()

    if n1 == n2:
        return 100.0

    token_set = fuzz.token_set_ratio(n1, n2)
    token_sort = fuzz.token_sort_ratio(n1, n2)
    partial = fuzz.partial_ratio(n1, n2)

    # Weighted composite score
    composite = (token_set * 0.5) + (token_sort * 0.3) + (partial * 0.2)
    return round(float(composite), 2)


def is_fuzzy_name_match(name1: str, name2: str, threshold: float = 75.0) -> Tuple[bool, float]:
    """
    Returns True if the fuzzy match score meets or exceeds the threshold.
    """
    score = calculate_fuzzy_match_score(name1, name2)
    return score >= threshold, score


def validate_icai_udin(udin: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validates the 18-character ICAI Unique Document Identification Number (UDIN).
    Format: YY (2 digits) + Member Reg No (6 digits) + 10 alphanumeric document token.
    """
    if not udin:
        return False, "UDIN missing or empty"

    clean_udin = udin.strip().upper()
    if not re.match(UDIN_REGEX, clean_udin):
        return False, f"Invalid UDIN syntax '{clean_udin}'. Must be 18 alphanumeric characters."

    return True, None


def parse_date_flexible(date_str: str) -> Optional[date]:
    """
    Parses various standard Indian date formats (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, Month DD, YYYY).
    """
    if not date_str:
        return None

    clean = date_str.strip()
    patterns = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%d %b %Y",
    ]

    for pat in patterns:
        try:
            dt = datetime.strptime(clean, pat)
            return dt.date()
        except ValueError:
            continue

    return None
