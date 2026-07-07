import re


def validate_phone_number(phone: str) -> bool:
    cleaned = re.sub(r"[+\s\-()]", "", phone)
    return cleaned.isdigit() and len(cleaned) >= 10


def validate_quantity(value: str) -> float | None:
    try:
        qty = float(value.replace(",", "."))
        if qty <= 0:
            return None
        return qty
    except (ValueError, TypeError):
        return None


def normalize_phone(phone: str) -> str:
    return re.sub(r"[+\s\-()]", "", phone)
