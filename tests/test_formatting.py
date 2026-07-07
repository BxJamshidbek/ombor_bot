from app.services.formatting_service import (
    format_active_products_for_exit,
    format_admin_stats,
    format_client_list,
    format_product_list,
)


def make_product(name: str, kg: float = 10, price: float = 2000,
                 days: int = 30, total: float = 600000,
                 status: str = "active", date: str = "2026-07-07T00:00:00"):
    return {
        "product_name": name,
        "kg_amount": kg,
        "price_per_kg": price,
        "storage_days": days,
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
    assert "600,000" in result
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
    p = make_product("Olma", kg=20, price=2000, days=30, total=1200000)
    result = format_product_list([p])
    assert "1." in result
    assert "Olma" in result
    assert "Kg: 20" in result
    assert "2,000" in result
    assert "30 kun" in result
    assert "1,200,000" in result
    assert "active" in result
    assert "2026-07-07" in result


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
        }
        result = format_admin_stats(stats)
        assert "10" in result
        assert "25" in result
        assert "23" in result
        assert "530.5" in result
        assert "4,500,000" in result

    def test_zeros(self):
        stats = {
            "total_clients": 0,
            "total_products": 0,
            "active_products": 0,
            "total_kg": 0,
            "total_amount": 0,
        }
        result = format_admin_stats(stats)
        assert "0" in result


class TestFormatActiveProductsForExit:
    def test_empty(self):
        assert format_active_products_for_exit([]) == \
            "Bu mijozda faol mahsulotlar mavjud emas."

    def test_single_product(self):
        products = [make_product("Olma")]
        result = format_active_products_for_exit(products)
        assert "Olma" in result
        assert "1." in result
        assert "raqamini kiriting" in result

    def test_multiple_products(self):
        products = [make_product(f"Mahsulot {i}") for i in range(3)]
        result = format_active_products_for_exit(products)
        assert "1." in result
        assert "2." in result
        assert "3." in result
        assert "Mahsulot 0" in result
        assert "Mahsulot 2" in result
