from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    telegram_id: int
    phone_number: str
    full_name: str
    role: str  # "admin" or "client"
    created_at: datetime


@dataclass
class Product:
    id: int
    client_id: int
    name: str
    quantity: float
    unit: str  # kg, dona, quti, etc.
    entry_date: datetime
    expiry_date: datetime | None
    notes: str | None


@dataclass
class Transaction:
    id: int
    product_id: int
    type: str  # "entry" or "exit"
    quantity: float
    performed_by: int
    created_at: datetime
