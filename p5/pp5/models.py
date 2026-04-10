from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Role:
    """Справочник ролей"""
    role_id: int
    role_name: str

@dataclass
class User:
    """Пользователь системы"""
    user_id: int
    login: str
    password: str
    role_id: int  # Теперь ID роли
    role_name: str = ""  # Для отображения (заполняется при загрузке)
    failed_attempts: int = 0
    is_locked: bool = False
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class Employee:
    employee_id: int
    full_name: str

@dataclass
class Customer:
    customer_code: str
    customer_name: str
    inn: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_supplier: bool = False
    is_buyer: bool = False

@dataclass
class Product:
    product_code: str
    product_name: str
    unit: str
    price: float = 0.0

@dataclass
class Material:
    material_code: str
    material_name: str
    unit: str
    cost_per_unit: float = 0.0

@dataclass
class Specification:
    specification_id: int
    product_code: str
    material_code: str
    consumption_rate: float
    unit: str

@dataclass
class Order:
    order_id: int
    order_number: str
    order_date: datetime
    customer_code: str
    total_amount: float = 0.0
    executor_id: Optional[int] = None

@dataclass
class OrderItem:
    order_item_id: int
    order_id: int
    product_code: str
    quantity: float
    price: float
    amount: float

@dataclass
class Production:
    production_id: int
    production_number: str
    production_date: datetime
    product_code: str
    quantity: float
    executor_id: Optional[int] = None

@dataclass
class OrderCostCalculation:
    order_number: str
    order_date: datetime
    customer_name: str
    product_code: str
    product_name: str
    order_quantity: float
    sale_price: float
    sale_amount: float
    material_cost_per_unit: float
    total_material_cost: float
    profit: float