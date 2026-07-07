def format_product_list(products: list[dict], limit: int = 10) -> str:
    if not products:
        return "Sizda hozircha mahsulot mavjud emas."

    lines = ["📦 <b>Sizning mahsulotlaringiz:</b>\n"]
    shown = products[:limit]

    for i, p in enumerate(shown, 1):
        lines.append(
            f"{i}. <b>{p['product_name']}</b>\n"
            f"   Kg: {p['kg_amount']}\n"
            f"   1 kg narxi: {p['price_per_kg']:,.0f} so'm\n"
            f"   Saqlash muddati: {p['storage_days']} kun\n"
            f"   Umumiy summa: {p['total_price']:,.0f} so'm\n"
            f"   Status: {p['status']}\n"
            f"   Sana: {p['created_at'][:10]}"
        )

    remaining = len(products) - limit
    if remaining > 0:
        lines.append(f"\nYana {remaining} ta mahsulot bor. "
                     f"To'liq hisobot keyingi bosqichda qo'shiladi.")

    return "\n\n".join(lines)


def format_client_list(clients: list[dict], limit: int = 20) -> str:
    if not clients:
        return "Hozircha mijozlar mavjud emas."

    lines = ["📋 <b>Mijozlar ro'yxati:</b>\n"]
    shown = clients[:limit]

    for i, c in enumerate(shown, 1):
        name = c.get("full_name") or "Ismsiz"
        lines.append(
            f"{i}. {name}\n"
            f"   Telefon: {c['phone']}\n"
            f"   Telegram ID: {c['telegram_id']}\n"
            f"   Sana: {c['created_at'][:10]}"
        )

    remaining = len(clients) - limit
    if remaining > 0:
        lines.append(f"\nYana {remaining} ta mijoz bor.")

    return "\n\n".join(lines)


def format_active_products_for_exit(products: list[dict]) -> str:
    if not products:
        return "Bu mijozda faol mahsulotlar mavjud emas."

    lines = ["📤 <b>Chiqarish uchun mahsulotlar:</b>\n"]
    for i, p in enumerate(products, 1):
        lines.append(
            f"{i}. <b>{p['product_name']}</b>\n"
            f"   Kg: {p['kg_amount']}\n"
            f"   Narxi: {p['price_per_kg']:,.0f} so'm/kg\n"
            f"   Saqlash: {p['storage_days']} kun\n"
            f"   Summa: {p['total_price']:,.0f} so'm\n"
            f"   Sana: {p['created_at'][:10]}"
        )

    lines.append("\nChiqariladigan mahsulot raqamini kiriting:")
    return "\n\n".join(lines)


def format_admin_stats(stats: dict) -> str:
    return (
        "📊 <b>Ombor hisoboti</b>\n\n"
        f"Mijozlar soni: {stats['total_clients']}\n"
        f"Jami mahsulot yozuvlari: {stats['total_products']}\n"
        f"Faol mahsulotlar: {stats['active_products']}\n"
        f"Faol kg jami: {stats['total_kg']:,.1f} kg\n"
        f"Umumiy summa: {stats['total_amount']:,.0f} so'm"
    )
