from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

# Models
class SpeedingViolation(BaseModel):
    license_number: str
    speed: float
    timestamp: str

@app.post("/collectfine")
async def collect_fine(violation: SpeedingViolation):
    fine_amount = calculate_fine(violation.speed)
    
    # Store fine information
    await db.fines.insert_one({
        "license_number": violation.license_number,
        "speed": violation.speed,
        "fine_amount": fine_amount,
        "timestamp": violation.timestamp
    })
    
    # Call vehicle registration service for owner information (assuming the service exists)
    # Placeholder for vehicle registration service URL
    # response = await requests.get(f"http://localhost:6002/vehicleinfo/{violation.license_number}")
    
    return {"message": "Fine collected", "fine_amount": fine_amount}

def calculate_fine(speed):
    over_speed = speed - 60  # Assuming speed limit is 60 km/h
    return over_speed * 10  # Fine of 10 currency units per km/h over the limit

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6001)
