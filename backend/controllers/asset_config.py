from fastapi import APIRouter, status, Body, Depends, Query
from data.db.client import mongo_client
from data.models.asset_config import AssetConfig, UpdateAssetConfig
from data.models.user import User
import datetime as dt
from utils.util import ResponseModel, get_class_attributes, parse_projections, parse_filters
from utils.security import UserUtil
from bson import ObjectId
from urllib.parse import unquote

asset_config_router = APIRouter(
    prefix="/asset-config",
    tags=["asset-config"]
)

@asset_config_router.get(path="/", response_model=ResponseModel, dependencies=[Depends(UserUtil.is_authenticated)])
async def get_configurations(
        fields: str = Query("", description="Fields to display.<br>Format: `field1,field2,..`"), 
        in_filters: str = Query("", description="Filter by field matches.<br>Format: `brand=Acer.Dell, OS=windows`"),
        price_filter: str = Query("", description=(
            'Filter by price bounds (boundary included). Will take precedence over __in_filters__ if provided.' + 
            '<br>Format: Between 10000 and 20000 -> `10000,20000` (or) >= 100000 -> `100000`'))
    ):

    '''Get Configuration(s).'''
    
    attrs = get_class_attributes(AssetConfig)
    filters = parse_filters(attrs, unquote(in_filters), price_filter, price_field_name="price", dt_field_name="sale_date")
    projection = parse_projections(fields, attrs)
    
    configs: list[dict] = [config async for config in mongo_client.asset_config.find(filters, projection)]
    if len(configs):
        return ResponseModel(content=configs)
    else:
        return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message="No relevant results were found.")

@asset_config_router.post(path="/", description="Add a new configuration", response_model=ResponseModel)
async def add_config(config: AssetConfig, user: User = Depends(UserUtil.is_authenticated)):
    
    # Add the audit fields
    config.create_date = user["AH_DATE"]()
    config.created_by = user["AH_USER"]

    inserted = await mongo_client.asset_config.insert_one(config.dict())
    new_config = await mongo_client.asset_config.find_one({"_id": inserted.inserted_id})
    return ResponseModel(
        content=new_config, 
        message="Configuration has been successfully added",
        status_code=status.HTTP_201_CREATED
    )

@asset_config_router.patch(path="/{id}", response_model=ResponseModel)
async def update_config(id: str, config: UpdateAssetConfig = Body(...), user: User = Depends(UserUtil.is_atleast_admin)):
    '''Update a configuration, only the fields to updated could be provided in the request body. Requires that the user be atleast an admin.'''

    config_to_update = {k: v for k, v in config.dict().items() if (v is not None and k not in ('create_date', 'created_by'))}
    if not ObjectId.is_valid(id):
        return ResponseModel(message=f"Object ID: {id} is not valid.", status_code=status.HTTP_400_BAD_REQUEST)
    elif len(config_to_update) == 0:
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message="Atleast one of the fields to be present.")
    else:
        old = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
        if old:
            old.update(config_to_update)

            # Add the audit fields
            old["update_date"] = user["AH_DATE"]()
            old["updated_by"] = user["AH_USER"]

            update_result = await mongo_client.asset_config.update_one({"_id": ObjectId(id)}, {"$set": old})
            if update_result:
                return ResponseModel(content=old, message=f"Update on Object ID {id} was successful.")
            else:
                return ResponseModel(message=f"Update on Object ID {id} failed.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"Object ID {id} doesn't exist.")
        
@asset_config_router.post(path="/{id}", response_model=ResponseModel)
async def clone_config(id: str, config: UpdateAssetConfig = Body(...), user: User = Depends(UserUtil.is_authenticated)):
    '''Clone from an existing Configuration. Fields can be optionally updated.'''
    config_to_update = {k: v for k, v in config.dict().items() if v is not None}
    if not ObjectId.is_valid(id):
        return ResponseModel(message=f"Clone Object ID: {id} is not valid.", status_code=status.HTTP_400_BAD_REQUEST)
    else:
        clone = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
        if clone:
            clone.update(config_to_update)
            clone.pop("_id", None)

            # Add the audit fields
            clone["create_date"] = user["AH_DATE"]()
            clone["created_by"] = user["AH_USER"]

            insert_result = await mongo_client.asset_config.insert_one(clone)
            new_config = await mongo_client.asset_config.find_one({"_id": insert_result.inserted_id})
            return ResponseModel(content=new_config, message=f"Cloned from Object ID {id} successfully.", status_code=status.HTTP_200_OK)
        else:
            return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"Clone Object ID {id} doesn't exist.")

@asset_config_router.delete(path="/{id}", response_model=ResponseModel, dependencies=[Depends(UserUtil.is_atleast_admin)])
async def delete_config(id: str):
    '''
    Delete a configuration. There is no soft deletion, fails when there are cloned stocks that exists. 
    Only users that atleast admin can access this API.
    '''
    if not ObjectId.is_valid(id):
        return ResponseModel(message=f"Object ID: {id} is not valid.", status_code=status.HTTP_400_BAD_REQUEST)
    else:
        data = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
        if data and len(data["cloned_stocks"]) == 0:
            delete_result = await mongo_client.asset_config.delete_one({"_id": ObjectId(id)})
            if (delete_result.deleted_count == 1):
                return ResponseModel(content=delete_result.raw_result, message=f"Object ID: {id} deleted successfully.")
        elif len(data["cloned_stocks"]) > 0:
            return ResponseModel(
                message=f"Please delete the cloned stock(s) before deleting this configuration.", 
                status_code=status.HTTP_409_CONFLICT, content={ "cloned_stocks": data['cloned_stocks'] }
            )
        else:
            return ResponseModel(message=f"Object ID: {id} not found.", status_code=status.HTTP_404_NOT_FOUND)
        