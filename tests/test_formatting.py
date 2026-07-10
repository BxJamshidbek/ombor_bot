from app.services.formatting_service import (
    format_active_products_for_exit,
    format_active_products_for_payment,
    format_admin_stats,
    format_client_list,
    format_client_products_message,
    format_product_types_list,
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
    assert "Izoh" not in result
    assert "Saqlash muddati" not in result


def test_formatting_with_payment_summary():
    products = [make_product("Olma", total=100000)]
    summary = {
        "total_amount": 100000,
        "paid_amount": 30000,
        "remaining_amount": 70000,
    }
    result = format_product_list(products, payment_summary=summary)
    assert "Umumiy summa" in result
    assert "100,000" in result
    assert "To'langan" in result
    assert "30,000" in result
    assert "Qolgan" in result
    assert "70,000" in result


def test_formatting_without_payment_summary():
    products = [make_product("Olma", total=50000)]
    result = format_product_list(products)
    assert "Umumiy summa" not in result


def test_formatting_with_allocation():
    products = [make_product("Olma", total=40000, _id=1)]
    allocation = {1: {"paid_amount": 15000, "remaining_amount": 25000}}
    result = format_product_list(products, allocation=allocation)
    assert "To'langan: 15,000" in result
    assert "Qolgan: 25,000" in result


def test_no_note_in_product_list():
    p = make_product("Olma", total=40000)
    result = format_product_list([p])
    assert "Izoh" not in result
    assert "note" not in result.lower()


def test_product_id_in_list():
    p = make_product("Olma", _id=42)
    result = format_product_list([p])
    assert "42" in result
    assert "ID" in result


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
            "active_kg": 530.5,
            "active_total_amount": 4500000,
            "active_paid_amount": 2000000,
            "active_remaining_amount": 2500000,
            "exited_products": 2,
            "exited_kg": 100.0,
            "exited_total_amount": 800000,
        }
        result = format_admin_stats(stats)
        assert "10" in result
        assert "25" in result
        assert "23" in result
        assert "530.5" in result
        assert "4,500,000" in result
        assert "2,000,000" in result
        assert "2,500,000" in result
        assert "Omborda mavjud" in result
        assert "Chiqarilganlar" in result

    def test_zeros(self):
        stats = {
            "total_clients": 0,
            "total_products": 0,
            "active_products": 0,
            "active_kg": 0,
            "active_total_amount": 0,
            "active_paid_amount": 0,
            "active_remaining_amount": 0,
            "exited_products": 0,
            "exited_kg": 0,
            "exited_total_amount": 0,
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


class TestFormatActiveProductsForPayment:
    def test_empty(self):
        assert format_active_products_for_payment([], {}) == \
            "Bu mijozda omborda aktiv mahsulot yo'q."

    def test_single_product(self):
        products = [make_product("Olma", total=50000, _id=1)]
        summaries = {1: {"paid_amount": 20000, "remaining_amount": 30000}}
        result = format_active_products_for_payment(products, summaries)
        assert "Olma" in result
        assert "1" in result
        assert "50,000" in result
        assert "20,000" in result
        assert "30,000" in result
        assert "ID sini kiriting" in result

    def test_no_overpay_info(self):
        products = [make_product("Olma", total=50000, _id=1)]
        summaries = {1: {"paid_amount": 50000, "remaining_amount": 0}}
        result = format_active_products_for_payment(products, summaries)
        assert "0 so'm" in result


def test_client_products_empty():
    client = {"full_name": "Ali", "phone": "+998901234567"}
    result = format_client_products_message(client, [])
    assert "hali kiritilmagan" in result


def test_client_products_active_status():
    client = {"full_name": "Ali", "id": 1}
    products = [make_product("Pomidor", kg=120, price=2000, total=240000, status="active")]
    result = format_client_products_message(client, products)
    assert "Pomidor" in result
    assert "120 kg" in result
    assert "Omborda" in result


def test_client_products_exited_status():
    client = {"full_name": "Ali", "id": 1}
    products = [make_product("Bodring", status="exited")]
    result = format_client_products_message(client, products)
    assert "Bodring" in result
    assert "Chiqarilgan" in result


def test_product_types_list_has_olma_and_nok():
    types = [
        {"id": 1, "name": "Olma", "emoji": "🍎"},
        {"id": 2, "name": "Nok", "emoji": "🍐"},
    ]
    result = format_product_types_list(types)
    assert "Olma" in result
    assert "Nok" in result


def test_product_types_list_empty():
    result = format_product_types_list([])
    assert "mavjud emas" in result
