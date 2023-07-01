from data.models.base import MongoBaseModel
from enum import Enum
from typing import Optional

class UserTypeEnum(str, Enum):
    owner="owner"
    admin="admin"
    user="user"

class User(MongoBaseModel):
    
    username: str
    password: str
    type: UserTypeEnum
    disabled: bool = False

    def __getitem__(self, item):
        return getattr(self, item)

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "username": "owner",
                "password": "owner",
                "type": "owner"
            }
        }

class UpdateUser(MongoBaseModel):
    
    password: Optional[str]
    disabled: Optional[bool]
    deleted: Optional[bool]

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "password": "updated-password",
                "disabled": False,
                "deleted": False
            }
        }