from dataclasses import dataclass


@dataclass
class StorageReport:
    total_products: int = 0
    total_clients: int = 0
    occupancy_percent: float = 0.0


def generate_report() -> StorageReport:
    return StorageReport()


def calculate_total_price(
    kg_amount: float,
    price_per_kg: float,
    storage_days: int,
) -> float:
    return kg_amount * price_per_kg * storage_days
