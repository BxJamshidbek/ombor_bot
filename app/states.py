from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_phone = State()


class AdminAddClient(StatesGroup):
    waiting_for_phone = State()
    confirming_client = State()


class AdminAddProduct(StatesGroup):
    waiting_for_client_phone = State()
    waiting_for_product_name = State()
    waiting_for_kg_amount = State()
    waiting_for_price_per_kg = State()
    waiting_for_storage_days = State()
    waiting_for_confirmation = State()


class AdminRemoveProduct(StatesGroup):
    waiting_for_product = State()
    waiting_for_quantity = State()
