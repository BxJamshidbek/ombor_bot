from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_phone = State()


class AdminAddClient(StatesGroup):
    waiting_for_phone = State()
    confirming_client = State()


class AdminAddProduct(StatesGroup):
    waiting_for_client = State()
    waiting_for_product_name = State()
    waiting_for_quantity = State()
    waiting_for_unit = State()
    waiting_for_expiry = State()
    waiting_for_notes = State()


class AdminRemoveProduct(StatesGroup):
    waiting_for_product = State()
    waiting_for_quantity = State()
