from fastapi import FastAPI
import uvicorn
from utils.util import settings
from data.db.client import mongo_client
from controllers.asset_config import asset_config_router
from controllers.stock import stock_router
from controllers.sale import sale_router
from controllers.user import user_router

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": 0})

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
    USERNAME = settings['MONGO.INITDB_ROOT_USERNAME']
    PASSWORD = settings['MONGO.INITDB_ROOT_PASSWORD']
    URL = settings['MONGO.URL']
    DB_NAME = settings['MONGO.INITDB_DATABASE']

    # CONNECTION_STRING = f"mongodb+srv://{USERNAME}:{PASSWORD}@{URL}/{DB_NAME}?retryWrites=true&w=majority"
    CONNECTION_STRING = f"mongodb://{USERNAME}:{PASSWORD}@{URL}/{DB_NAME}?authSource=admin&retryWrites=true&w=majority"
    
    await mongo_client.establish_connection(CONNECTION_STRING)

@app.on_event("shutdown")
async def shutdown_db_client():
    await mongo_client.close_connection()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings["SERVER.HOST"],
        reload=(settings["SERVER.DEBUG_MODE"] == "True"),
        port=int(settings["SERVER.PORT"])
    )