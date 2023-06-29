from motor.motor_asyncio import AsyncIOMotorClient

class client:
    def __init__(self):
        self.client = AsyncIOMotorClient

    async def establish_connection(self, url: str):
        # Mongo drive client
        self.client = AsyncIOMotorClient(url)
        
        # Database name
        self.db = self.client.inventory

        # Collection names
        self.asset_config = self.db.get_collection("asset_config")
        self.stock = self.db.get_collection("stock")
        self.user = self.db.get_collection("user")
        self.sale = self.db.get_collection("sale")

    async def close_connection(self): 
        self.client.close()

# The mongo client instance that we would use from other classes
mongo_client = client()