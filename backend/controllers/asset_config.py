from fastapi import APIRouter, status, Body
from fastapi.responses import JSONResponse
from data.db.client import mongo_client
from data.models.asset_config import AssetConfig, UpdateAssetConfig
import datetime as dt
from utils.util import ResponseModel
from bson import ObjectId

asset_config_router = APIRouter(
    prefix="/asset-config",
    tags=["asset-config"]
)

@asset_config_router.get("/", description="Get Configuration(s)", response_model=ResponseModel)
async def get_configurations(id: str = ""):
    configs: list[dict] = []
    if (id):
        if ObjectId.is_valid(id):
            config = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
            if config:
                configs.append(config)
            else:
                return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"The Object ID: {id} doesn't exist.")
        else:
            return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Please enter a valid object ID.")
    else:
        async for config in mongo_client.asset_config.find({}):
            configs.append(config)

    return ResponseModel(content=configs)

@asset_config_router.post("/", response_model=ResponseModel)
async def add_config(config: AssetConfig):
    config.create_date = dt.datetime.utcnow()
    inserted = await mongo_client.asset_config.insert_one(config.dict())
    new_config = await mongo_client.asset_config.find_one({"_id": inserted.inserted_id})
    return ResponseModel(
        content=new_config, 
        message="Configuration has been successfully added",
        status_code=status.HTTP_201_CREATED
    )

@asset_config_router.patch("/{id}", response_model=ResponseModel)
async def update_config(id: str, config: UpdateAssetConfig = Body(...)):
    config_to_update = {k: v for k, v in config.dict().items() if v is not None}
    if not ObjectId.is_valid(id):
        return ResponseModel(message=f"Object ID: {id} is not valid.", status_code=status.HTTP_400_BAD_REQUEST)
    elif len(config_to_update) == 0:
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message="Atleast one of the fields to be present.")
    else:
        old = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
        if old:
            old.update(config_to_update)
            update_result = await mongo_client.asset_config.update_one({"_id": ObjectId(id)}, {"$set": old})
            if update_result:
                return ResponseModel(content=old, message=f"Update on Object ID {id} was successful.")
            else:
                return ResponseModel(message=f"Update on Object ID {id} failed.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"Object ID {id} doesn't exist.")
        
@asset_config_router.post("/{id}", description="Clone from an existing Configuration. Fields can be optionally updated.", response_model=ResponseModel)
async def clone_config(id: str, config: UpdateAssetConfig = Body(...)):
    config_to_update = {k: v for k, v in config.dict().items() if v is not None}
    if not ObjectId.is_valid(id):
        return ResponseModel(message=f"Clone Object ID: {id} is not valid.", status_code=status.HTTP_400_BAD_REQUEST)
    else:
        clone = await mongo_client.asset_config.find_one({"_id": ObjectId(id)})
        if clone:
            clone.update(config_to_update)
            clone.pop("_id", None)
            insert_result = await mongo_client.asset_config.insert_one(clone)
            new_config = await mongo_client.asset_config.find_one({"_id": insert_result.inserted_id})
            return ResponseModel(content=new_config, message=f"Cloned from Object ID {id} successfully.", status_code=status.HTTP_200_OK)
        else:
            return ResponseModel(status_code=status.HTTP_404_NOT_FOUND, message=f"Clone Object ID {id} doesn't exist.")

@asset_config_router.delete("/{id}", response_model=ResponseModel)
async def delete_config(id: str):
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
        