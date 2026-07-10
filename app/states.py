from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()


class AdminAddProduct(StatesGroup):
    waiting_for_client_phone = State()
    waiting_for_product_name = State()
    waiting_for_kg_amount = State()
    waiting_for_price_per_kg = State()
    waiting_for_box_count = State()
    waiting_for_confirmation = State()


class AdminExitProduct(StatesGroup):
    waiting_for_client_phone = State()
    waiting_for_product_id = State()
    waiting_for_confirmation = State()


class AdminAddPayment(StatesGroup):
    waiting_for_client_phone = State()
    waiting_for_product_id = State()
    waiting_for_amount = State()
    waiting_for_confirmation = State()


class AdminSettings(StatesGroup):
    waiting_for_product_type_name = State()


class AdminWarehouseLocation(StatesGroup):
    waiting_for_location = State()
    waiting_for_confirmation = State()
