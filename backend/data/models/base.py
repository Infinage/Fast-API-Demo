from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MongoBaseModel(BaseModel):

    # Audit fields
    create_date: Optional[datetime]
    update_date: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]