from data.models.base import MongoBaseModel
from enum import Enum
from datetime import datetime
from pydantic import Field, BaseModel

from typing import Optional

class UserTypeEnum(str, Enum):
    owner="owner"
    admin="admin"
    user="user"

class Sale(MongoBaseModel):

    serial: str
    price: float = Field(..., gt=0)
    sale_date: datetime
    customer_name: str
    mobile: str
    address: str
    remarks: Optional[str]

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "serial": "123456789",
                "price": 70000.0,
                "sale_date": "2023-06-29 00:55:29.033394",
                "customer_name": "ABCDEF",
                "mobile": "+91 98104181041",
                "address": "Address goes here",
                "remarks": "A good sale, customer was satisfied."
            }
        }

class StockSale(BaseModel):
    serial: str
    price: float = Field(..., gt=0)

    class Config:
        schema_extra = {
            "example": {
                "serial": "123456789",
                "price": 70000.0
            }
        }

class SaleRequestObject(MongoBaseModel):
    sales: list[StockSale]
    sale_date: datetime
    customer_name: str
    mobile: str
    address: str
    remarks: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "sales": [
                    { "serial": "123456789", "price": 70000.0 },
                    { "serial": "987654321", "price": 50000.0 },
                ],
                "sale_date": "2023-06-29 00:55:29.033394",
                "customer_name": "Xyz",
                "mobile": "+91 8481918101",
                "address": "Address goes here",
                "remarks": "A good sale, customer was satisfied."
            }
        }
    