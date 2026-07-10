from app.keyboards import (
    admin_main_kb,
    clients_list_kb,
    client_actions_kb,
    client_products_kb,
    settings_kb,
    product_type_selection_kb,
    menu_only_kb,
    main_menu_kb,
    warehouse_location_confirm_kb,
)


def test_clients_list_kb_two_per_row():
    clients = [
        {"id": i, "full_name": f"Name{i}", "phone": f"+99890{i:07d}"}
        for i in range(5)
    ]
    kb = clients_list_kb(clients)
    rows = kb.inline_keyboard
    total = sum(len(row) for row in rows)
    assert total == 5
    for row in rows:
        assert len(row) <= 2
    # 5 items, 2 per row -> last row has a single button
    assert len(rows[-1]) == 1


def test_clients_list_kb_callback_data_and_label():
    clients = [{"id": 42, "full_name": "Ali", "phone": "+998901234567"}]
    kb = clients_list_kb(clients)
    btn = kb.inline_keyboard[0][0]
    assert btn.callback_data == "client:42"
    assert btn.text == "Ali — +998901234567"


def test_clients_list_kb_missing_name_label():
    clients = [{"id": 7, "full_name": None, "phone": "+998901111111"}]
    kb = clients_list_kb(clients)
    btn = kb.inline_keyboard[0][0]
    assert btn.text == "Ism kiritilmagan — +998901111111"
    assert btn.callback_data == "client:7"


def test_clients_list_kb_normalizes_phone():
    clients = [{"id": 9, "full_name": "Ali", "phone": "998901234567"}]
    kb = clients_list_kb(clients)
    btn = kb.inline_keyboard[0][0]
    assert btn.text == "Ali — +998901234567"


def test_client_actions_kb_callback_format():
    kb = client_actions_kb(7)
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert data == {
        "client_add_product:7",
        "client_products:7",
        "client_add_payment:7",
        "client_exit_product:7",
        "clients_back",
    }


def test_client_products_kb_has_back_buttons():
    kb = client_products_kb(7)
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert data == {"client_back_detail:7", "clients_back"}
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert any("Mijozga qaytish" in t for t in texts)
    assert any("Ortga" in t for t in texts)


def test_client_actions_kb_callback_within_telegram_limit():
    kb = client_actions_kb(1234567890)
    for row in kb.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode("utf-8")) <= 64


def test_admin_main_kb_has_three_buttons():
    kb = admin_main_kb()
    texts = {btn.text for row in kb.keyboard for btn in row}
    assert len(texts) == 3
    assert "📋 Mijozlarni ko'rish" in texts
    assert "📊 Hisobot" in texts
    assert "⚙️ Sozlash" in texts


def test_settings_kb_has_product_type_and_back():
    kb = settings_kb()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "settings:warehouse_location" in data
    assert "settings_product_types" in data
    assert "settings_add_product_type" in data
    assert "settings_back" in data


def test_product_type_selection_kb_has_types_and_custom():
    types = [
        {"id": 1, "name": "Olma", "emoji": "🍎"},
        {"id": 2, "name": "Nok", "emoji": "🍐"},
    ]
    kb = product_type_selection_kb(7, types)
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert data == {
        "pt_select:7:1",
        "pt_select:7:2",
        "pt_custom:7",
        "client_back_detail:7",
    }
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert "🍎 Olma" in texts
    assert "🍐 Nok" in texts
    assert "✍️ Boshqa mahsulot" in texts


def test_menu_only_kb_single_menu_button():
    kb = menu_only_kb()
    texts = [btn.text for row in kb.keyboard for btn in row]
    assert texts == ["☰ Menu"]


def test_settings_kb_has_warehouse_location_button():
    kb = settings_kb()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "settings:warehouse_location" in data
    assert "settings_product_types" in data
    assert "settings_add_product_type" in data
    assert "settings_back" in data


def test_warehouse_location_confirm_kb_has_buttons():
    kb = warehouse_location_confirm_kb()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "warehouse_location:confirm" in data
    assert "warehouse_location:cancel" in data
    texts = {btn.text for row in kb.inline_keyboard for btn in row}
    assert "Ha, saqlash" in texts
    assert "Yo'q, bekor qilish" in texts


def test_client_menu_has_warehouse_location():
    kb = main_menu_kb("client")
    texts = {btn.text for row in kb.keyboard for btn in row}
    assert "📍 Ombor lokatsiyasi" in texts


def test_admin_menu_has_no_warehouse_location_button():
    kb = main_menu_kb("admin")
    texts = {btn.text for row in kb.keyboard for btn in row}
    assert "📍 Ombor lokatsiyasi" not in texts
