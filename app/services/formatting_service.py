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
