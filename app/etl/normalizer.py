import re
from datetime import datetime, date
from typing import Any, Optional, Tuple


COLUMN_TYPO_MAPPING = {
    "sahre": "share",
    "achived": "achieved",
    "1-30 sep. achived": "achieved_sep",
    "1-31 aug. achived": "achieved_aug",
    "prevoius": "previous",
    "prevoius token": "previous_token",
    "divison": "division",
    "orginal price": "original_price",
    "total deposit up to -26": "total_deposit",
    "total deposit up to - 26": "total_deposit",
    "total deposit": "total_deposit",
    "bking/ emi": "booking_status",
    "bking/emi": "booking_status",
    "bking / emi": "booking_status",
    "lat 5 days": "last_5_days",
    "sepaerion": "separation",
    "mgt given target": "target",
    "clients name": "client_name",
    "d.o name": "sales_officer",
    "sales price": "sales_price",
    "august-26 deposited": "august_deposited",
    "last deposited date": "last_deposited_date",
    "c. id": "client_id",
    "types": "unit_types",
    "discount": "discount_amount",
    "%": "discount_pct",
    "dues": "dues",
    "sl.no": "sl_no",
    "s.no": "sl_no",
    "team": "team",
    "client": "clients_target",
    "new sales": "new_sales",
    "emi": "emi",
    "total collection": "total_collection",
}


def normalize_column_name(col: Any) -> str:
    """Normalize messy Excel column names using the mapping table."""
    if col is None:
        return ""
    col_str = str(col).strip().lower()
    col_str = re.sub(r"\s+", " ", col_str)

    # Direct match in mapping
    if col_str in COLUMN_TYPO_MAPPING:
        return COLUMN_TYPO_MAPPING[col_str]

    # Partial / regex transformations
    cleaned = re.sub(r"[^\w\s%]", "", col_str)
    cleaned = cleaned.replace(" ", "_")
    return COLUMN_TYPO_MAPPING.get(cleaned, cleaned)


def clean_number(val: Any, allow_zero: bool = True) -> Optional[float]:
    """Clean numeric values without silently converting missing/unknown values to 0.
    Missing = None / unknown.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if str(val) == "nan":
            return None
        return float(val)

    val_str = str(val).strip()
    if val_str in ("", "-", "--", "N/A", "n/a", "null", "None", "nan"):
        return None

    # Remove commas, currency symbols, and extra whitespace
    cleaned = re.sub(r"[^\d.-]", "", val_str)
    if not cleaned or cleaned == "-":
        return None

    try:
        f = float(cleaned)
        return f
    except ValueError:
        return None


def clean_int(val: Any) -> Optional[int]:
    """Clean integer counts (clients, shares). None if unknown."""
    num = clean_number(val)
    if num is None:
        return None
    return int(round(num))


def clean_date(val: Any) -> Optional[date]:
    """Robust date parser for Excel dates, ISO strings, and DD.MM.YY formats."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val

    val_str = str(val).strip()
    if not val_str or val_str in ("-", "None", "nan"):
        return None

    # Handle formats: DD.MM.YY, DD.MM.YYYY, YYYY-MM-DD
    formats = [
        "%Y-%m-%d",
        "%d.%m.%y",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue

    return None


def extract_role_and_name(text: str) -> Tuple[str, str]:
    """Extract designation/role tag from name string.
    E.g.: 'Mehajabin Adita (TL)' -> ('Mehajabin Adita', 'Team Leader')
          'Nahid Hasan Emon(C.O)' -> ('Nahid Hasan Emon', 'Coordinator')
          'Gazi Mahfuz Kashem(G.L)' -> ('Gazi Mahfuz Kashem', 'Group Leader')
          'Sowaib Ahmed' -> ('Sowaib Ahmed', 'Executive')
    """
    if not text:
        return ("Unknown", "Executive")

    clean_text = str(text).replace("\n", " ").strip()
    clean_text = re.sub(r"\s+", " ", clean_text)

    # Search for role in parentheses
    match = re.search(r"\(([^)]+)\)$", clean_text)
    if match:
        tag = match.group(1).strip().upper()
        name_part = clean_text[: match.start()].strip()

        tag_map = {
            "TL": "Team Leader",
            "T.L": "Team Leader",
            "C.O": "Coordinator",
            "CO": "Coordinator",
            "G.L": "Group Leader",
            "GL": "Group Leader",
            "DEP. MAN": "Deputy Manager",
            "DEP.MAN": "Deputy Manager",
            "AST.M": "Assistant Manager",
            "ASST. MAN": "Assistant Manager",
            "MAN": "Manager",
            "SR.EX": "Senior Executive",
            "SR.EXE": "Senior Executive",
            "EXE": "Executive",
            "EXE.": "Executive",
        }
        normalized_role = tag_map.get(tag, tag)
        return (name_part if name_part else clean_text, normalized_role)

    # If no parentheses, default role is Executive
    return (clean_text, "Executive")
