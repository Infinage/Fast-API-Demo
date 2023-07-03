from fastapi import FastAPI
import uvicorn
from utils.util import settings
from data.db.client import mongo_client
from controllers.asset_config import asset_config_router
from controllers.stock import stock_router
from controllers.sale import sale_router
from controllers.user import user_router

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": 0}, redoc_url=None)

@app.get("/", tags=["ping"])
async def ping():
    return "Up & running"

# Include all routes
app.include_router(asset_config_router)
app.include_router(stock_router)
app.include_router(sale_router)
app.include_router(user_router)

@app.on_event("startup")
async def startup_db_client():
    USERNAME = settings['MONGO_INITDB_ROOT_USERNAME']
    PASSWORD = settings['MONGO_INITDB_ROOT_PASSWORD']
    DB_NAME = settings['MONGO_DB_NAME']
    URL = settings['MONGO_URL']

    CONNECTION_STRING = f"mongodb://{USERNAME}:{PASSWORD}@{URL}/{DB_NAME}?authSource=admin&retryWrites=true&w=majority"
    
    await mongo_client.establish_connection(CONNECTION_STRING)

    # Check if some user exists in the DB, else seed a dummy user
    atleast_one_user = await mongo_client.user.find_one({})
    insert_result = False
    if not atleast_one_user:
        insert_result = await mongo_client.user.insert_one({
            "username": "owner",
            "password": "$2b$12$ZdwvDfd74MtDuoRSOma19uryOEgnMZxdldndWg.y.VirSVwVEv6H2",
            "type": "owner",
            "disabled": False
        })

    if insert_result:
        print ("Dummy user inserted successfully.")
    else:
        print ("Dummy user not inserted.")


@app.on_event("shutdown")
async def shutdown_db_client():
    await mongo_client.close_connection()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings["SERVER_HOST"],
        reload=(settings["SERVER_DEBUG_MODE"] == "True"),
        port=int(settings["SERVER_PORT"])
    )