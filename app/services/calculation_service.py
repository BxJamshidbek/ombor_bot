import logging

logger = logging.getLogger(__name__)


def calculate_total_price(kg_amount: float, price_per_kg: float) -> float:
    return kg_amount * price_per_kg


def calculate_remaining_amount(total_price: float, paid_amount: float) -> float:
    return max(total_price - paid_amount, 0)


def validate_payment_amount(amount: float, remaining_amount: float) -> tuple[bool, str | None]:
    if amount <= 0:
        return False, "To'lov summasi musbat bo'lishi kerak."
    if amount > remaining_amount:
        return False, (
            f"Ortiqcha to'lov mumkin emas. "
            f"Bu mahsulot bo'yicha qolgan summa: {remaining_amount:,.0f} so'm"
        )
    return True, None


def allocate_payments_to_products(
    products: list[dict], payments: list[dict]
) -> dict[int, dict]:
    allocation: dict[int, dict] = {}
    payment_left = sum(p["amount"] for p in payments)

    for p in products:
        pid = p["id"]
        total = p["total_price"]
        pay_to_this = min(payment_left, total)
        paid = pay_to_this
        remaining = total - paid
        payment_left -= pay_to_this
        allocation[pid] = {
            "paid_amount": paid,
            "remaining_amount": remaining,
        }

    if payment_left > 0:
        logger.warning("Unallocated payment remainder: %s", payment_left)

    return allocation
