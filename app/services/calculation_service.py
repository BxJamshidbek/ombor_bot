import logging

logger = logging.getLogger(__name__)


def calculate_total_price(kg_amount: float, price_per_kg: float) -> float:
    return kg_amount * price_per_kg


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
