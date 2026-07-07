import re


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"

    if len(digits) == 9:
        return f"+998{digits}"

    return f"+{digits}"


def validate_phone_number(phone: str) -> bool:
    normalized = normalize_phone(phone)
    return bool(re.match(r"^\+998\d{9}$", normalized))


def validate_quantity(value: str) -> float | None:
    try:
        qty = float(value.replace(",", "."))
        if qty <= 0:
            return None
        return qty
    except (ValueError, TypeError):
        return None
