from fastapi import APIRouter, Body, status, Depends, Query
from data.models.stock import Stock, StockStatusEnum, UpdateStock
from data.models.user import User, UserTypeEnum
from utils.util import ResponseModel, get_class_attributes
from utils.security import JWTUtil, UserUtil
from data.db.client import mongo_client
from bson import ObjectId
from typing import Any, Annotated
import datetime as dt
from urllib.parse import unquote

stock_router = APIRouter(
    prefix="/stock",
    tags=["stock"]
)

@stock_router.get("/", description="Get all stocks", response_model=ResponseModel)
async def get_all_stocks(
        fields: str = Query("", description="Fields to display.<br>Format: `field1,field2,..`"), 
        in_filters: str = Query("", description="Filter by field matches.<br>Format: `brand=Acer.Dell, OS=windows`"),
        price_filter: str = Query("", description=(
            'Filter by price bounds (boundary included). Will take precedence over __in_filters__ if provided.' + 
            '<br>Format: Between 10000 and 20000 -> `10000,20000` (or) >= 100000 -> `100000`')),
        purchase_dt_filter: str = Query("", description=(
            'Filter by purchase date bounds (boundary included). Will take precedence over __in_filters__ if provided.' + 
            '<br>Format: >= 2023-10-10 -> `2023-10-10,`'))
    ):

    def parse_filters(in_filter_str: str, price_filter: str, pd_filter: str):

        filters = dict()

        # Parse the `in` filters
        for f in map(str.strip, in_filter_str.split(",")):
            f = f.split("=")
            if f[0] in attrs or (f[0] == "price" and not price_filter) or (f[0] == "purchase_date" and not pd_filter):
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
                filters["price"] = pf
            else:
                filters["price"] = {"$eq": float(price_filter)}

        # Parse in the Date filter
        if pd_filter:
            try:
                if "," in pd_filter:
                    pdf = dict()
                    pd_filter_parsed = list(map(lambda x: dt.datetime.fromisoformat(x.strip()) if x.strip() else None, pd_filter.split(",")))
                    if pd_filter_parsed[0]:
                        pdf["$gte"] = pd_filter_parsed[0]
                    if pd_filter_parsed[1]:
                        pdf["$lte"] = pd_filter_parsed[1]
                    filters["purchase_date"] = pdf
                else:
                    filters["purchase_date"] = {"$eq": dt.datetime.fromisoformat(pd_filter)}
            except ValueError as e:
                print (e)

        return filters
    
    def parse_projections(projection_str: str):
        return {k: 1 for k in filter(lambda x: x in attrs, map(str.strip, projection_str.split(",")))}

    attrs = get_class_attributes(Stock)
    filters = parse_filters(unquote(in_filters), price_filter, purchase_dt_filter)
    projection = parse_projections(fields)
    stocks: list[dict] = [stock async for stock in mongo_client.stock.find(
        filters, projection
    )]
    if (len(stocks) > 0):
        return ResponseModel(content=stocks)
    else:
        return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message="No relevant results were found.")

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

@stock_router.delete("/{serial}", response_model=ResponseModel)
async def delete_stock(user: Annotated[User, Depends(JWTUtil.get_current_user)], serial: str, soft: bool = True):
        '''
        Delete a stock. <br>
        Only user types admin and above can use this API.<br>
        Soft delete -> disables the stock<br>
        Hard delete -> removes it from the DB
        '''
        if (user["type"] == UserTypeEnum.admin and soft == True) or (user["type"] == UserTypeEnum.owner):
            if soft == False:
                data = await mongo_client.stock.delete_one({"serial": serial})
            else:
                current = await mongo_client.stock.find_one({"serial": serial})
                if current["current_status"] != StockStatusEnum.deleted:
                    data = await mongo_client.stock.update_one({"serial": serial}, {"$set": {
                        "current_status": StockStatusEnum.deleted}, 
                        "$push": {'status_history': {"status": StockStatusEnum.deleted, "date": dt.datetime.utcnow()}}
                    })
                else:
                    return ResponseModel(message=f"Serial Number: {serial} is already disabled.", status_code=status.HTTP_409_CONFLICT)
            if ((soft == False and data.deleted_count == 1) or (soft == True and data.modified_count == 1)):
                return ResponseModel(content=data.raw_result, message=f"Serial Number: {serial} {'disabled' if soft else 'deleted'} successfully.")
            else:
                return ResponseModel(message=f"Serial Number: {serial} not found.", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return ResponseModel(message="Insufficient privileges for this operation.")
        
@stock_router.patch("/{serial}", dependencies=[Depends(UserUtil.is_atleast_admin)])
async def update_stock(serial: str, update: UpdateStock = Body(...)):
    stock_current: dict = await mongo_client.stock.find_one({"serial": serial})
    stock_to_update = {k: v for k, v in update.dict().items() if v is not None}
    if stock_current:
        stock_current.update(stock_to_update)
        update_result = await mongo_client.stock.update_one({"serial": serial}, {"$set": stock_current})
        if update_result:
            return ResponseModel(content=stock_current, message=f"Update on Serial# {serial} was successful.")
        else:
            return ResponseModel(message=f"Update on Serial# {serial} failed.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"Serial# {serial} doesn't exist.")