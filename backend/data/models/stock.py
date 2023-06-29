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
    warranty_end_date: Optional[datetime]
    remarks: str = ""
    current_status: StockStatusEnum = Field(default=StockStatusEnum.new)
    status_history: list[StockStatus] = [StockStatus(status=StockStatusEnum.new, date=datetime.now())]

    @validator('warranty_end_date', always=True)
    def set_warranty_end_date(cls, v, values, **kwargs):
        return v or values["purchase_date"] + (values["warranty_years"] * timedelta(days=365))

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
                "processor_type": "Intel Core i5-12450H ",
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