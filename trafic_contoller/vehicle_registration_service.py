from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

class VehicleInfo(BaseModel):
    license_number: str
    owner_name: str
    email:str

@app.get("/vehicleinfo/{license_number}")
async def get_vehicle_info(license_number: str):
    print("info===>>>>",license_number)
    vehicleinfo = await db.vehicleinfo.find_one({"license_number": license_number})
    print("info===>>??",vehicleinfo)
    if not vehicleinfo:
        return {"message": "Vehicle not found"}
    # return license_number
    return {"license_number": vehicleinfo["license_number"], "owner_name": vehicleinfo["owner_name"],"email":vehicleinfo["email"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6002)