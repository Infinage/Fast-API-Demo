from typing import Any
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from fastapi.encoders import jsonable_encoder
import inspect

def load_dotenv(fp: str) -> dict[str, str]:
    config: dict[str, str] = {}
    with open(fp, "r") as f:
            for line in f.readlines():
                if len(line) > 1 and line[0] != '#':
                    key, value = line.split("=")
                    config[key.strip()] = value.strip()

    return config

def get_class_attributes(clz):
    return clz.__fields__.keys()

class ResponseModel(BaseModel):

    content: list[dict[str, Any]] | dict[str, Any] = []
    message: str = "Request was successful"
    status_code: int = status.HTTP_200_OK

    @validator("content", pre=True)
    def _id_cleanup(cls, content: list[dict[str, Any]] | dict[str, Any]):
        if type(content) == list:
            for d in content: 
                if "_id" in d: d["_id"] = str(d["_id"])
        elif type(content) == dict:
            if "_id" in content: content["_id"] = str(content["_id"])
        return content

    def __new__(cls, *args, **kwargs):
        return JSONResponse(
            content={
                "content": jsonable_encoder(ResponseModel._id_cleanup(kwargs["content"])) if "content" in kwargs else [], 
                "message": kwargs["message"] if "message" in kwargs else "Request was successful",
                "status_code": kwargs["status_code"] if "status_code" in kwargs else status.HTTP_200_OK
            }, 
            status_code=kwargs["status_code"] if "status_code" in kwargs else status.HTTP_200_OK
        )
    
# Load the settings
settings = load_dotenv(".env")