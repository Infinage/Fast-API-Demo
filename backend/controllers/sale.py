from fastapi import APIRouter, Body, status
from data.models.stock import Stock
from data.models.sale import Sale, SaleRequestObject
from utils.util import ResponseModel
from data.db.client import mongo_client
from bson import ObjectId
from typing import Any
import datetime as dt

sale_router = APIRouter(
    prefix="/sale",
    tags=["sale"]
)

@sale_router.get("/", response_model=ResponseModel)
async def get_all_sales():
     sales = [sale async for sale in mongo_client.sale.find({})]
     return ResponseModel(content=sales)

@sale_router.post("/", response_model=ResponseModel)
async def sell_stock(sales_request_obj: SaleRequestObject = Body(...)):

    # Get all the serial numbers
    stock_ids_for_sale: set[str] = {sale.serial_num for sale in sales_request_obj.sales}

    # Find the serial numbers from DB & ensure that all of them exists
    stocks_for_sale: list[dict[str, Any]] = [stock async for stock in mongo_client.stock.find({"serial": {"$in": list(stock_ids_for_sale)}})]

    if any(map(lambda x: x["current_status"] in ("sold", "deleted", "returned"), stocks_for_sale)):
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Some of stocks are not in a valid status for sale.")

    elif (len(stocks_for_sale) != len(sales_request_obj.sales)):
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Only {len(stocks_for_sale)} stock(s) could be found out of the provided {len(sales_request_obj.sales)} stock(s).")
    
    else:
        # Flatten the object to Sales
        sales: list[Sale] = [
            Sale(
                customer_name=sales_request_obj.customer_name,
                mobile=sales_request_obj.mobile,
                address=sales_request_obj.address,
                remarks=sales_request_obj.remarks,
                serial_num=sale.serial_num,
                price=sale.price,
                sale_date=sales_request_obj.sale_date,
                create_date=dt.datetime.utcnow(),
                update_date=dt.datetime.utcnow(),
                created_by=None,
                updated_by=None
            ) for sale in sales_request_obj.sales
        ]

        async with await mongo_client.client.start_session() as sesssion:
                async with sesssion.start_transaction():

                    # Update the status to sold
                    stock_status_update_result = await mongo_client.stock.update_many(
                        filter={"serial": {"$in": list(stock_ids_for_sale)}}, 
                        update={"$set": {"current_status": "sold"}, "$push": {'status_history': {"status": "sold", "date": dt.datetime.utcnow()}}}, 
                        upsert=False
                    )

                    sale_insert_result = await mongo_client.sale.insert_many(list(map(dict, sales)), ordered=False)

                    if len(sale_insert_result.inserted_ids) == stock_status_update_result.modified_count == len(sales):
                        inserted_sales: list[dict[str, Any]] = [
                             sale async for sale in mongo_client.sale.find({"_id": {"$in": sale_insert_result.inserted_ids}})
                        ]
                        return ResponseModel(content=inserted_sales, message=f"{len(sales)} created successfully.")
                    else:
                        return ResponseModel(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=f"The sales couldn't be created. Please try again.")
        
@sale_router.delete(
        "/{id}", deprecated=True, 
        description="To be used only during development. For production, this API is irrelevant.",
        response_model=ResponseModel
    )
async def remove_sale(id: str):
        if ObjectId.is_valid(id):
            data = await mongo_client.sale.delete_one({"_id": ObjectId(id)})
            if (data.deleted_count == 1):
                return ResponseModel(content=data.raw_result, message=f"Sale Object#: {id} deleted successfully.")
            else:
                return ResponseModel(message=f"Sale ID#: {id} not found.", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return ResponseModel(message=f"Object ID provided is invalid: {id}")