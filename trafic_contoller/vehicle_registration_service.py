from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

class VehicleInfo(BaseModel):
    license_number: str
    owner_name: str

@app.get("/vehicleinfo/{license_number}")
async def get_vehicle_info(license_number: str):
    vehicle_info = await db.vehicle_info.find_one({"license_number": license_number})
    
    if not vehicle_info:
        return {"message": "Vehicle not found"}
    
    return {"license_number": vehicle_info["license_number"], "owner_name": vehicle_info["owner_name"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6002)
