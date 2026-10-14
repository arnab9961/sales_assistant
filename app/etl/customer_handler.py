import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple


def clean_customer_record(record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Clean and validate a generic customer record adhering to strict missing-value policy.

    Missing-Value Policy:
    1. Financial/Sales metrics (deposit, balance, income):
       - NEVER silently replace missing or NaN with 0.
       - Missing = Unknown. Keep None / NULL.
       - Exclude from specific monetary calculations (e.g., mean deposit) while retaining record.
       - Flag missing value for audit.
    2. Categorical/Text fields (name, city, channel):
       - Missing text values are replaced with "Unknown".
    3. Age:
       - Valid range: 18 <= age <= 120.
       - Missing, non-numeric, or out-of-range values become None and are flagged.
    4. Phone number:
       - Strips country code (+88, 88), spaces, dashes.
       - Must have at least 10 digits; invalid or missing becomes None and is flagged.
    5. Dates (registration, dob):
       - Parsed into standard date (YYYY-MM-DD); unparseable becomes None and is flagged.

    Returns:
        (cleaned_record_dict, list_of_quality_flags)
    """
    flags: List[str] = []
    cleaned: Dict[str, Any] = {}

    # 1. Customer Name
    name = record.get("name")
    if name is None or str(name).strip() == "":
        cleaned["name"] = "Unknown"
        flags.append("Missing customer name; defaulted to 'Unknown'")
    else:
        cleaned["name"] = str(name).strip()

    # 2. Age
    age = record.get("age")
    if age is None or str(age).strip() in ("", "nan", "None"):
        cleaned["age"] = None
        flags.append("Missing age; kept as None")
    else:
        try:
            age_int = int(float(age))
            if 18 <= age_int <= 120:
                cleaned["age"] = age_int
            else:
                cleaned["age"] = None
                flags.append(f"Age {age_int} out of valid range (18-120); set to None")
        except (ValueError, TypeError):
            cleaned["age"] = None
            flags.append(f"Invalid age format '{age}'; set to None")

    # 3. Phone
    phone = record.get("phone")
    if phone is None or str(phone).strip() in ("", "nan", "None"):
        cleaned["phone"] = None
        flags.append("Missing phone number; kept as None")
    else:
        digits = re.sub(r"\D", "", str(phone))
        # Handle Bangladesh leading 880 or international prefix
        if digits.startswith("880") and len(digits) >= 13:
            digits = digits[2:]  # Remove '88'
        if len(digits) >= 10:
            cleaned["phone"] = digits
        else:
            cleaned["phone"] = None
            flags.append(f"Phone '{phone}' has fewer than 10 digits; set to None")

    # 4. Registration Date
    reg_date = record.get("registration_date")
    if reg_date is None or str(reg_date).strip() in ("", "nan", "None"):
        cleaned["registration_date"] = None
        flags.append("Missing registration date; kept as None")
    elif isinstance(reg_date, (datetime, date)):
        cleaned["registration_date"] = reg_date.date() if isinstance(reg_date, datetime) else reg_date
    else:
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%d.%m.%y", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(str(reg_date).strip(), fmt).date()
                break
            except ValueError:
                continue
        if parsed_date:
            cleaned["registration_date"] = parsed_date
        else:
            cleaned["registration_date"] = None
            flags.append(f"Invalid date format '{reg_date}'; set to None")

    # 5. Financial metrics (e.g. initial_deposit, budget)
    deposit = record.get("initial_deposit")
    if deposit is None or str(deposit).strip() in ("", "nan", "None", "-"):
        cleaned["initial_deposit"] = None
        flags.append("Missing initial deposit; retained as None (NOT zero)")
    else:
        try:
            cleaned_num = float(re.sub(r"[^\d.-]", "", str(deposit)))
            cleaned["initial_deposit"] = cleaned_num
        except ValueError:
            cleaned["initial_deposit"] = None
            flags.append(f"Invalid deposit amount '{deposit}'; set to None")

    return cleaned, flags
