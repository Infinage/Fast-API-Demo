from typing import List, Optional
from data.models.base import MongoBaseModel

class AssetConfig(MongoBaseModel):
    
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
    cloned_stocks: List[str] = []

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "brand": "Honor",
                "model": "Honor Magicbook",
                "model_number": "FRI-F56",
                "screen_size": "14 inches",
                "hdd_size": "512 GB",
                "ssd_size": "NA",
                "processor_type": "Intel Core i5-12450H",
                "processor_speed": "4.4 GHz ",
                "RAM": "16 GB",
                "graphics_type": "Intel UHD Integrated GDDR4",
                "graphics_memory": "NA",
                "OS": "Windows 11 Home",
                "price": 49990.0,
                "warranty_years": 2
            }
        }

class UpdateAssetConfig(MongoBaseModel):
    
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
    cloned_stocks: List[str] = []

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "brand": "Honor",
                "model": "Honor Magicbook",
                "model_number": "FRI-F56",
                "screen_size": "14 inches",
                "hdd_size": "512 GB",
                "ssd_size": "NA",
                "processor_type": "Intel Core i5-12450H",
                "processor_speed": "4.4 GHz ",
                "RAM": "16 GB",
                "graphics_type": "Intel UHD Integrated GDDR4",
                "graphics_memory": "NA",
                "OS": "Windows 11 Home",
                "price": 49990.0,
                "warranty_years": 2
            }
        }