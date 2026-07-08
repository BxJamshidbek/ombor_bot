from app.services.calculation_service import (
    allocate_payments_to_products,
    calculate_total_price,
)


def test_calculate_total_price():
    assert calculate_total_price(10, 2000) == 20000
    assert calculate_total_price(0, 1000) == 0
    assert calculate_total_price(10, 0) == 0
    assert calculate_total_price(1.5, 3000) == 4500


def test_allocate_payments_basic():
    products = [
        {"id": 1, "total_price": 40000},
        {"id": 2, "total_price": 60000},
    ]
    payments = [{"amount": 50000}]
    result = allocate_payments_to_products(products, payments)
    assert result[1]["paid_amount"] == 40000
    assert result[1]["remaining_amount"] == 0
    assert result[2]["paid_amount"] == 10000
    assert result[2]["remaining_amount"] == 50000


def test_allocate_payments_exact():
    products = [{"id": 1, "total_price": 10000}]
    payments = [{"amount": 10000}]
    result = allocate_payments_to_products(products, payments)
    assert result[1]["paid_amount"] == 10000
    assert result[1]["remaining_amount"] == 0


def test_allocate_payments_overpay():
    products = [{"id": 1, "total_price": 10000}]
    payments = [{"amount": 15000}]
    result = allocate_payments_to_products(products, payments)
    assert result[1]["paid_amount"] == 10000
    assert result[1]["remaining_amount"] == 0


def test_allocate_payments_no_payments():
    products = [
        {"id": 1, "total_price": 40000},
        {"id": 2, "total_price": 60000},
    ]
    result = allocate_payments_to_products(products, [])
    assert result[1]["paid_amount"] == 0
    assert result[1]["remaining_amount"] == 40000
    assert result[2]["paid_amount"] == 0
    assert result[2]["remaining_amount"] == 60000


def test_allocate_payments_multiple_products():
    products = [
        {"id": 1, "total_price": 20000},
        {"id": 2, "total_price": 30000},
        {"id": 3, "total_price": 50000},
    ]
    payments = [{"amount": 25000}]
    result = allocate_payments_to_products(products, payments)
    assert result[1]["paid_amount"] == 20000
    assert result[1]["remaining_amount"] == 0
    assert result[2]["paid_amount"] == 5000
    assert result[2]["remaining_amount"] == 25000
    assert result[3]["paid_amount"] == 0
    assert result[3]["remaining_amount"] == 50000
