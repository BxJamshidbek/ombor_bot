from app.services.calculation_service import calculate_total_price


def test_calculate_total_price():
    assert calculate_total_price(10, 2000) == 20000
    assert calculate_total_price(0, 1000) == 0
    assert calculate_total_price(10, 0) == 0
    assert calculate_total_price(1.5, 3000) == 4500
