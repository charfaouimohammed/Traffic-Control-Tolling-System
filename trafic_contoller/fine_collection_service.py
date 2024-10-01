from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
import httpx

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

# Models
class SpeedingViolation(BaseModel):
    license_number: str
    speed: float
    timestamp: str

# Function to get vehicle owner information from the registration service
async def get_owner_info(license_number):
    response:str
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:6002/vehicleinfo/{license_number}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Error contacting Vehicle Registration Service: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=response.status_code, detail=f"Vehicle not found: {exc}")
    # finally: return response

# Endpoint to collect fine for a speeding violation
@app.post("/collectfine")
async def collect_fine(violation: SpeedingViolation):
    fine_amount = calculate_fine(violation.speed)

    # Store fine information initially without owner details
    fine_data = {
        "license_number": violation.license_number,
        "speed": violation.speed,
        "fine_amount": fine_amount,
        "timestamp": violation.timestamp
    } 
    result = await db.fines.insert_one(fine_data)
    # Get vehicle owner information from the registration service
    owner_info = await get_owner_info(violation.license_number)

    # Update the fine record with owner information
    try:
        await db.fines.update_one(
            {"_id": result.inserted_id},
            {"$set": {
            "owner_name": owner_info.get("owner_name"),
            "email": owner_info.get("email")
            }}
        )
        return {"message": "Fine recorded successfully", "fine_id": str(result.inserted_id)}
    except  :
        raise HTTPException("not ok")


# Function to calculate fine based on speed
def calculate_fine(speed):
    base_fine = 100  # Base fine amount
    if speed > 60:
        return base_fine + (speed - 60) * 10  # $10 fine for each km/h above the limit
    return base_fine

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6001)
