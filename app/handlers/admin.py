from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.states import AdminAddClient, AdminAddProduct, AdminRemoveProduct

router = Router()


@router.message(Command("admin"), F.from_user.id.in_({}))  # admin_ids will be injected
async def admin_panel(message: Message):
    await message.answer("👑 Admin panel\n\nQuyidagi buyruqlardan birini tanlang:")


@router.message(Command("add_client"))
async def add_client_start(message: Message, state: FSMContext):
    await state.set_state(AdminAddClient.waiting_for_phone)
    await message.answer("Mijozning telefon raqamini kiriting:")


@router.message(AdminAddClient.waiting_for_phone)
async def add_client_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(AdminAddClient.confirming_client)
    await message.answer(f"Mijoz topildi. Ism-familiyasini kiriting:")


@router.message(AdminAddClient.confirming_client)
async def add_client_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(
        f"✅ Mijoz qo'shildi:\n"
        f"Telefon: {data.get('phone')}\n"
        f"Ism: {message.text}"
    )
    await state.clear()
