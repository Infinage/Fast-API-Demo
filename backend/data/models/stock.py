from enum import Enum
from typing import Optional
from pydantic import Field, validator, BaseModel
from data.models.base import MongoBaseModel
from datetime import timedelta, datetime
from uuid import uuid4

class StockStatusEnum(str, Enum):
    sold="sold"               # Sold to customer
    deleted="deleted"         # 'Soft' deleted
    new="new"                 # Ready for sale, new item
    returned="returned"       # stocks must be refurbished before it can be sold
    refurbished="refurbished" # ready for sale at a discounted price

class StockStatus(BaseModel):
    status: StockStatusEnum = Field(default="new")
    date: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: str}

class Stock(MongoBaseModel):

    brand: str
    model: str
    model_number: str
    screen_size: str
    hdd_size: str
    ssd_size: str
    processor_type: str
    processor_speed: str
    RAM: str
    graphics_type: str
    graphics_memory: str
    OS: str
    price: float
    warranty_years: float
    serial: str = Field(default_factory=lambda: str(uuid4()))
    purchase_date: datetime
    remarks: str = ""
    current_status: StockStatusEnum = Field(default=StockStatusEnum.new)
    status_history: list[StockStatus] = [StockStatus(status=StockStatusEnum.new, date=datetime.now())]

    def __getitem__(self, item):
        return getattr(self, item)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: str}
        schema_extra = {
            "example": {
                "brand": "Honor",
                "model": "Honor Magicbook",
                "model_number": "FRI-F56",
                "screen_size": "14 inches",
                "hdd_size": "512 GB",
                "ssd_size": "NA",
                "processor_type": "Intel Core i5-12450",
                "processor_speed": "4.4 GHz ",
                "RAM": "16 GB",
                "graphics_type": "Intel UHD Integrated GDDR4",
                "graphics_memory": "NA",
                "OS": "Windows 11 Home ",
                "price": 50000.0,
                "warranty_years": 3, 
                "serial": "123456789",
                "purchase_date": "2023-06-29 00:55:29.033394",
                "remarks": "In excellent working condition"
            }
        }

class UpdateStock(MongoBaseModel):

    brand: Optional[str]
    model: Optional[str]
    model_number: Optional[str]
    screen_size: Optional[str]
    hdd_size: Optional[str]
    ssd_size: Optional[str]
    processor_type: Optional[str]
    processor_speed: Optional[str]
    RAM: Optional[str]
    graphics_type: Optional[str]
    graphics_memory: Optional[str]
    OS: Optional[str]
    price: Optional[float]
    warranty_years: Optional[float]
    serial: Optional[str]
    purchase_date: Optional[datetime]
    remarks: Optional[str]
    current_status: Optional[StockStatusEnum]
    status_history: Optional[list[StockStatus]]

    def __getitem__(self, item):
        return getattr(self, item)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: str}
        schema_extra = {
            "example": {
                "brand": "Honor",
                "model": "Honor Magicbook",
                "model_number": "FRI-F56",
                "screen_size": "14 inches",
                "hdd_size": "512 GB",
                "ssd_size": "NA",
                "processor_type": "Intel Core i5-12450",
                "processor_speed": "4.4 GHz ",
                "RAM": "16 GB",
                "graphics_type": "Intel UHD Integrated GDDR4",
                "graphics_memory": "NA",
                "OS": "Windows 11 Home ",
                "price": 50000.0,
                "warranty_years": 3, 
                "serial": "123456789",
                "purchase_date": "2023-06-29 00:55:29.033394",
                "remarks": "In excellent working condition",
                "current_status": "new",
                "status_history": []
            }
        }