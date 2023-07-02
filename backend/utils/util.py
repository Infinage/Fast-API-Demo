from typing import Any
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from fastapi.encoders import jsonable_encoder
import datetime as dt

def load_dotenv(fp: str) -> dict[str, str]:
    config: dict[str, str] = {}
    with open(fp, "r") as f:
            for line in f.readlines():
                if len(line) > 1 and line[0] != '#':
                    key, value = line.split("=")
                    config[key.strip()] = value.strip()

    return config

def get_class_attributes(clz) -> list[str]:
    return list(clz.__fields__.keys())

def parse_projections(projection_str: str, attrs: Any) -> dict:
        '''
        Utility function to parse the list of attributes and return a dict suitable for 
        passing as the projection attribute to mongo find query. 
        '''
        return {k: 1 for k in filter(lambda x: x in attrs, map(str.strip, projection_str.split(",")))}

def parse_filters(
        attrs: list[str], in_filter_str: str = "", price_filter: str = "", dt_filter: str = "", 
        price_field_name: str = "price", dt_field_name: str = "purchase_date"
    ):
        
    '''
    Utility function to parse the `in_filters`, `price_filter` & `date_filter` and 
    based on the input return a dictionary that is in a suitable format for mongo 
    find query.
    '''

    filters = dict()

    # Parse the `in` filters
    for f in map(str.strip, in_filter_str.split(",")):
        f = f.split("=")
        if f[0] in attrs or (f[0] == "price" and not price_filter) or (f[0] == "sale_date" and not dt_filter):
            filters[f[0]] = {"$in": list(map(str.strip, f[1].split(".")))}

    # Parse in the Price filter
    if price_filter:
        if "," in price_filter:
            pf = dict()
            price_filter_parsed = list(map(lambda x: float(x.strip()) if x.strip().isnumeric() else None, price_filter.split(",")))
            if price_filter_parsed[0]:
                pf["$gte"] = price_filter_parsed[0]
            if price_filter_parsed[1]:
                pf["$lte"] = price_filter_parsed[1]
            filters[price_field_name] = pf
        else:
            filters[price_field_name] = {"$eq": float(price_filter)}

    # Parse in the Date filter
    if dt_filter:
        try:
            if "," in dt_filter:
                pdf = dict()
                dt_filter_parsed = list(map(lambda x: dt.datetime.fromisoformat(x.strip()) if x.strip() else None, dt_filter.split(",")))
                if dt_filter_parsed[0]:
                    pdf["$gte"] = dt_filter_parsed[0]
                if dt_filter_parsed[1]:
                    pdf["$lte"] = dt_filter_parsed[1]
                filters[dt_field_name] = pdf
            else:
                filters[dt_field_name] = {"$eq": dt.datetime.fromisoformat(dt_filter)}
        except ValueError as e:
            print (e)

    return filters

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