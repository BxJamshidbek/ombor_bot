"""
Hisoblash va hisobot xizmati.

Hozircha skeleton, keyingi bosqichlarda to'ldiriladi.
"""

from dataclasses import dataclass


@dataclass
class StorageReport:
    total_products: int = 0
    total_clients: int = 0
    occupancy_percent: float = 0.0


def generate_report() -> StorageReport:
    return StorageReport()
