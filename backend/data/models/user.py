from data.models.base import MongoBaseModel
from enum import Enum
from pydantic import Field

class UserTypeEnum(str, Enum):
    owner="owner"
    admin="admin"
    user="user"

class User(MongoBaseModel):
    
    user: str = Field(alias="_id")
    password: str
    type: UserTypeEnum

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "user": "owner",
                "password": "owner",
                "type": "owner"
            }
        }