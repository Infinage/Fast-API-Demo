from fastapi import APIRouter, Body, status
from data.models.stock import Stock
from utils.util import ResponseModel
from data.db.client import mongo_client
from bson import ObjectId
from typing import Any
import datetime as dt

stock_router = APIRouter(
    prefix="/stock",
    tags=["stock"]
)

@stock_router.get("/", description="Get all stocks", response_model=ResponseModel)
async def get_all_stocks():
    stocks: list[dict] = []
    async for stock in mongo_client.stock.find({}):
        stocks.append(stock)
    return ResponseModel(content=stocks)

@stock_router.post("/{config_id}", description="Create one or more stocks from a configuration", response_model=ResponseModel)
async def create_stocks(
    config_id: str, 
    stocks: list[Stock] = Body(..., description="List of stocks cloned from config ID provided, all fields must be provided.")
):
    '''
    Front end logic: 
        -> Select a config, choose qty 
        -> App creates x num of stock placeholders
        -> Scan the serial numbers, optionally edit the other values (iteratively or in one shot in the form of a table)
        -> Confirm and make a call to this API
    '''
    if (ObjectId.is_valid(config_id)):
        config = mongo_client.asset_config.find({"_id": ObjectId(config_id)})
    else:
        config = None
    if config:
        stock_ids: set[str] = set()
        for stock in stocks:
            stock.create_date = dt.datetime.utcnow()
            stock_ids.add(stock.serial)
        serial_num_exists_check = [stock async for stock in mongo_client.stock.find({"serial": {"$in": list(stock_ids)}})]
        if len(stock_ids) < len(stocks) or len(serial_num_exists_check) > 0:
            return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Please ensure that the serial# are unique.")
        else:
            async with await mongo_client.client.start_session() as sesssion:
                async with sesssion.start_transaction():
                    config_update_result = await mongo_client.asset_config.update_one({"_id": ObjectId(config_id)}, {"$set": {"cloned_stocks": list(stock_ids)}})
                    stock_insert_result = await mongo_client.stock.insert_many(list(map(lambda x: x.dict(), stocks)), ordered=False)
                    if config_update_result and stock_insert_result:
                        inserted_stocks: list[dict[str, Any]] = []
                        async for inserted_stock in mongo_client.stock.find({"_id": {"$in": stock_insert_result.inserted_ids}}):
                            inserted_stocks.append(inserted_stock)
                        return ResponseModel(content=inserted_stocks, message=f"Count: {len(stocks)} stocks created successfully.")
                    else:
                        return ResponseModel(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=f"The stocks couldn't be created. Please try again.")
    else:
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Config ID# {config_id} is either invalid or doesn't exist.")

@stock_router.delete(
        "/{serial}", deprecated=True, 
        description="To be used only during development. For production, update the status to `deleted` instead.",
        response_model=ResponseModel
    )
async def delete_stock(serial: str):
        data = await mongo_client.stock.delete_one({"serial": serial})
        if (data.deleted_count == 1):
            return ResponseModel(content=data.raw_result, message=f"Serial Number: {serial} deleted successfully.")
        else:
            return ResponseModel(message=f"Serial Number: {serial} not found.", status_code=status.HTTP_404_NOT_FOUND)