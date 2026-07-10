import math
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


def validate_positive_int(value: str) -> int | None:
    try:
        num = int(value)
        if num <= 0:
            return None
        return num
    except (ValueError, TypeError):
        return None


def validate_full_name(name: str) -> str | None:
    if not name:
        return None
    cleaned = re.sub(r"\s+", " ", name.strip())
    if len(cleaned) < 2 or len(cleaned) > 100:
        return None
    return cleaned


def validate_coordinates(latitude: float, longitude: float) -> bool:
    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def build_google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps?q={latitude:.7f},{longitude:.7f}"
