from app.services.formatting_service import (
    format_active_products_for_exit,
    format_admin_stats,
    format_client_list,
    format_product_list,
)


def make_product(name: str, kg: float = 10, price: float = 2000,
                 box_count: int = 2, total: float = 20000,
                 status: str = "active", date: str = "2026-07-07T00:00:00",
                 _id: int = 1):
    return {
        "id": _id,
        "product_name": name,
        "kg_amount": kg,
        "price_per_kg": price,
        "box_count": box_count,
        "total_price": total,
        "status": status,
        "created_at": date,
    }


def test_empty_list():
    result = format_product_list([])
    assert result == "Sizda hozircha mahsulot mavjud emas."


def test_single_product():
    products = [make_product("Olma")]
    result = format_product_list(products)
    assert "Olma" in result
    assert "Kg: 10" in result
    assert "Quti: 2" in result
    assert "20,000" in result
    assert "Yana" not in result


def test_limit_not_exceeded():
    products = [make_product(f"Product {i}") for i in range(10)]
    result = format_product_list(products)
    assert "Yana" not in result


def test_limit_exceeded():
    products = [make_product(f"Product {i}") for i in range(11)]
    result = format_product_list(products)
    assert "Yana 1 ta mahsulot bor" in result


def test_limit_exceeded_many():
    products = [make_product(f"Product {i}") for i in range(15)]
    result = format_product_list(products)
    assert "Yana 5 ta mahsulot bor" in result


def test_formatting_elements():
    p = make_product("Olma", kg=20, price=2000, box_count=5, total=40000)
    result = format_product_list([p])
    assert "1." in result
    assert "Olma" in result
    assert "Kg: 20" in result
    assert "Quti: 5" in result
    assert "2,000" in result
    assert "40,000" in result
    assert "active" in result
    assert "2026-07-07" in result
    assert "Saqlash muddati" not in result
    assert "Tugash" not in result


def test_formatting_with_payment_summary():
    products = [make_product("Olma", total=100000)]
    summary = {
        "total_amount": 100000,
        "paid_amount": 30000,
        "remaining_amount": 70000,
    }
    result = format_product_list(products, payment_summary=summary)
    assert "Jami to'lov" in result
    assert "100,000" in result
    assert "To'langan" in result
    assert "30,000" in result
    assert "Qolgan" in result
    assert "70,000" in result


def test_formatting_without_payment_summary():
    products = [make_product("Olma", total=50000)]
    result = format_product_list(products)
    assert "Jami to'lov" not in result
    assert "To'langan" not in result
    assert "Qolgan" not in result


def make_client(name: str = "Ali Valiyev", phone: str = "+998901234567",
                tid: int = 123456789, date: str = "2026-07-07T00:00:00"):
    return {
        "full_name": name,
        "phone": phone,
        "telegram_id": tid,
        "created_at": date,
    }


class TestFormatClientList:
    def test_empty(self):
        result = format_client_list([])
        assert result == "Hozircha mijozlar mavjud emas."

    def test_one_client(self):
        clients = [make_client()]
        result = format_client_list(clients)
        assert "1." in result
        assert "Ali Valiyev" in result
        assert "+998901234567" in result
        assert "123456789" in result

    def test_limit_exceeded(self):
        clients = [make_client(name=f"Client {i}") for i in range(21)]
        result = format_client_list(clients)
        assert "Yana 1 ta mijoz bor" in result

    def test_within_limit(self):
        clients = [make_client(name=f"Client {i}") for i in range(20)]
        result = format_client_list(clients)
        assert "Yana" not in result

    def test_no_name(self):
        clients = [make_client(name=None)]
        result = format_client_list(clients)
        assert "Ismsiz" in result


class TestFormatAdminStats:
    def test_all_fields(self):
        stats = {
            "total_clients": 10,
            "total_products": 25,
            "active_products": 23,
            "total_kg": 530.5,
            "total_amount": 4500000,
            "paid_amount": 2000000,
            "remaining_amount": 2500000,
        }
        result = format_admin_stats(stats)
        assert "10" in result
        assert "25" in result
        assert "23" in result
        assert "530.5" in result
        assert "4,500,000" in result
        assert "2,000,000" in result
        assert "2,500,000" in result

    def test_zeros(self):
        stats = {
            "total_clients": 0,
            "total_products": 0,
            "active_products": 0,
            "total_kg": 0,
            "total_amount": 0,
            "paid_amount": 0,
            "remaining_amount": 0,
        }
        result = format_admin_stats(stats)
        assert "0" in result


class TestFormatActiveProductsForExit:
    def test_empty(self):
        assert format_active_products_for_exit([]) == \
            "Bu mijozda faol mahsulotlar mavjud emas."

    def test_single_product(self):
        products = [make_product("Olma", _id=1)]
        result = format_active_products_for_exit(products)
        assert "Olma" in result
        assert "<b>ID:</b> 1" in result
        assert "ID sini kiriting" in result
        assert "Quti:" in result

    def test_multiple_products(self):
        products = [
            make_product("Olma", _id=1),
            make_product("Banan", _id=5),
            make_product("Anor", _id=12),
        ]
        result = format_active_products_for_exit(products)
        assert "<b>ID:</b> 1" in result
        assert "<b>ID:</b> 5" in result
        assert "<b>ID:</b> 12" in result
        assert "Olma" in result
        assert "Banan" in result
        assert "Anor" in result
