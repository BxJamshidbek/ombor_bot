def format_product_list(products: list[dict], limit: int = 10,
                        payment_summary: dict | None = None,
                        allocation: dict | None = None) -> str:
    if not products:
        return "Sizda hozircha mahsulot mavjud emas."

    lines = ["📦 <b>Sizning mahsulotlaringiz:</b>\n"]
    shown = products[:limit]

    for i, p in enumerate(shown, 1):
        pid = p.get("id")
        alloc = (allocation or {}).get(pid, {}) if pid else {}
        paid = alloc.get("paid_amount", 0)
        rem = alloc.get("remaining_amount", p.get("total_price", 0))

        lines.append(
            f"{i}. <b>ID:</b> {pid}\n"
            f"   <b>{p['product_name']}</b>\n"
            f"   Kg: {p['kg_amount']}\n"
            f"   Quti: {p.get('box_count', 0)}\n"
            f"   1 kg narxi: {p['price_per_kg']:,.0f} so'm\n"
            f"   Umumiy: {p['total_price']:,.0f} so'm\n"
            f"   To'langan: {paid:,.0f} so'm\n"
            f"   Qolgan: {rem:,.0f} so'm"
        )

    remaining = len(products) - limit
    if remaining > 0:
        lines.append(f"\nYana {remaining} ta mahsulot bor.")

    if payment_summary is not None:
        lines.append(
            "\n💰 <b>Jami holat</b>\n"
            f"Umumiy summa: {payment_summary['total_amount']:,.0f} so'm\n"
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


def format_active_products_for_payment(
    products: list[dict], payment_summaries: dict[int, dict]
) -> str:
    if not products:
        return "Bu mijozda omborda aktiv mahsulot yo'q."

    lines = ["💳 <b>To'lov uchun mahsulotlar:</b>\n"]
    for p in products:
        pid = p["id"]
        summary = payment_summaries.get(pid, {})
        paid = summary.get("paid_amount", 0)
        rem = summary.get("remaining_amount", p["total_price"])

        lines.append(
            f"<b>ID:</b> {pid}\n"
            f"<b>Mahsulot:</b> {p['product_name']}\n"
            f"<b>Kg:</b> {p['kg_amount']}\n"
            f"<b>Quti:</b> {p.get('box_count', 0)}\n"
            f"<b>Umumiy:</b> {p['total_price']:,.0f} so'm\n"
            f"<b>To'langan:</b> {paid:,.0f} so'm\n"
            f"<b>Qolgan:</b> {rem:,.0f} so'm"
        )

    lines.append("\nTo'lov qilinadigan mahsulot ID sini kiriting:")
    return "\n\n---\n\n".join(lines)


def format_admin_stats(stats: dict) -> str:
    return (
        "📊 <b>Ombor hisoboti</b>\n\n"
        f"👥 Mijozlar soni: {stats['total_clients']}\n"
        f"📦 Jami mahsulot yozuvlari: {stats['total_products']}\n\n"
        f"🟢 <b>Omborda mavjud:</b>\n"
        f"Mahsulotlar: {stats['active_products']}\n"
        f"Kg jami: {stats['active_kg']:,.1f} kg\n"
        f"Umumiy summa: {stats['active_total_amount']:,.0f} so'm\n"
        f"To'langan: {stats['active_paid_amount']:,.0f} so'm\n"
        f"Qolgan: {stats['active_remaining_amount']:,.0f} so'm\n\n"
        f"📤 <b>Chiqarilganlar:</b>\n"
        f"Mahsulotlar: {stats['exited_products']}\n"
        f"Kg jami: {stats['exited_kg']:,.1f} kg\n"
        f"Umumiy summa: {stats['exited_total_amount']:,.0f} so'm"
    )
