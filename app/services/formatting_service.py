def format_product_list(products: list[dict], limit: int = 10,
                        payment_summary: dict | None = None) -> str:
    if not products:
        return "Sizda hozircha mahsulot mavjud emas."

    lines = ["📦 <b>Sizning mahsulotlaringiz:</b>\n"]
    shown = products[:limit]

    for i, p in enumerate(shown, 1):
        lines.append(
            f"{i}. <b>{p['product_name']}</b>\n"
            f"   Kg: {p['kg_amount']}\n"
            f"   Quti: {p.get('box_count', 0)}\n"
            f"   1 kg narxi: {p['price_per_kg']:,.0f} so'm\n"
            f"   Umumiy summa: {p['total_price']:,.0f} so'm\n"
            f"   Status: {p['status']}\n"
            f"   Sana: {p['created_at'][:10]}"
        )

    remaining = len(products) - limit
    if remaining > 0:
        lines.append(f"\nYana {remaining} ta mahsulot bor. "
                     f"To'liq hisobot keyingi bosqichda qo'shiladi.")

    if payment_summary is not None:
        lines.append(
            "\n💰 <b>To'lov holati</b>\n"
            f"Jami to'lov: {payment_summary['total_amount']:,.0f} so'm\n"
            f"To'langan: {payment_summary['paid_amount']:,.0f} so'm\n"
            f"Qolgan: {payment_summary['remaining_amount']:,.0f} so'm"
        )

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
    for p in products:
        lines.append(
            f"<b>ID:</b> {p['id']}\n"
            f"<b>Mahsulot:</b> {p['product_name']}\n"
            f"<b>Kg:</b> {p['kg_amount']}\n"
            f"<b>Quti:</b> {p.get('box_count', 0)}\n"
            f"<b>1 kg narxi:</b> {p['price_per_kg']:,.0f} so'm\n"
            f"<b>Summa:</b> {p['total_price']:,.0f} so'm\n"
            f"<b>Sana:</b> {p['created_at'][:10]}"
        )

    lines.append("\nChiqariladigan mahsulot ID sini kiriting:")
    return "\n\n---\n\n".join(lines)


def format_admin_stats(stats: dict) -> str:
    return (
        "📊 <b>Ombor hisoboti</b>\n\n"
        f"Mijozlar soni: {stats['total_clients']}\n"
        f"Jami mahsulot yozuvlari: {stats['total_products']}\n"
        f"Faol mahsulotlar: {stats['active_products']}\n"
        f"Faol kg jami: {stats['total_kg']:,.1f} kg\n"
        f"Umumiy summa: {stats['total_amount']:,.0f} so'm\n"
        f"To'langan: {stats['paid_amount']:,.0f} so'm\n"
        f"Qolgan: {stats['remaining_amount']:,.0f} so'm"
    )
