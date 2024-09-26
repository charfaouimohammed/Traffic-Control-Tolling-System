from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

# Model for vehicle information
class VehicleInfo(BaseModel):
    license_number: str
    owner_name: str
    email: str

@app.get("/vehicleinfo/{license_number}")
async def get_vehicle_info(license_number: str):
    # Retrieve vehicle information from the MongoDB collection
    vehicle_info = await db.vehicleinfo.find_one({"license_number": license_number})
    
    if vehicle_info is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Remove the MongoDB ID field before returning
    vehicle_info.pop("_id", None)
    return vehicle_info

@app.post("/vehicleinfo")
async def register_vehicle(vehicle_info: VehicleInfo):
    # Check if vehicle is already registered
    existing_vehicle = await db.vehicleinfo.find_one({"license_number": vehicle_info.license_number})
    if existing_vehicle:
        raise HTTPException(status_code=400, detail="Vehicle already registered")

    # Insert new vehicle information into the MongoDB collection
    await db.vehicleinfo.insert_one(vehicle_info.dict())
    return {"message": "Vehicle registered successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6002)
