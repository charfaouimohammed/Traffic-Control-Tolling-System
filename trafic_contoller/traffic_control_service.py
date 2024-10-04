# vehicle_state_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
from datetime import datetime
import httpx
import logging
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(config.database.uri)
db = client[config.database.name]

# Models
class VehicleEntry(BaseModel):
    license_number: str
    lane: int
    timestamp: str

class VehicleExit(BaseModel):
    license_number: str
    lane: int
    timestamp: str

# Function to calculate speed
def calculate_speed(entry_time: datetime, exit_time: datetime) -> float:
    time_diff = ((exit_time - entry_time).total_seconds()) # Time difference in seconds
    distance_meters = 1000  # Fixed distance in meters
    
    if time_diff > 0:
        speed_kmh = (distance_meters / time_diff) * 3.6  # Convert to km/h
        return speed_kmh
    else:
        return 0.0

# Function to notify fine collection service
async def notify_fine_collection(license_number, speed, timestamp):
    payload = {
        "license_number": license_number,
        "speed": speed,
        "timestamp": timestamp
    }
    try:
        async with httpx.AsyncClient() as client_httpx:
            response = await client_httpx.post(config.services.collect_fine_service, json=payload)
            response.raise_for_status()  # Raise an error for bad responses
            logger.info(f"Fine collection notified for {license_number} with speed {speed} km/h, response: {response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Error notifying fine collection service: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in notifying fine collection service: {e}")

# Endpoints
@app.post("/entrycam")
async def entry_cam(vehicle_entry: VehicleEntry):
    vehicle_state = {
        "license_number": vehicle_entry.license_number,
        "entry_timestamp": vehicle_entry.timestamp,
        "entry_lane": vehicle_entry.lane
    }
    try:
        await db.vehicle_states.insert_one(vehicle_state)
        logger.info(f"Vehicle entry recorded: {vehicle_state}")
        return {"message": "Vehicle entry recorded"}
    except Exception as e:
        logger.error(f"Error recording vehicle entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/exitcam")
async def exit_cam(vehicle_exit: VehicleExit):
    # Find the most recent vehicle state based on the entry timestamp
    vehicle_state = await db.vehicle_states.find_one(
        {"license_number": vehicle_exit.license_number},
        sort=[("entry_timestamp", -1)]  # Sort by entry_timestamp in descending order to get the latest entry
    )
    
    if not vehicle_state:
        raise HTTPException(status_code=404, detail="Vehicle entry not found")

    try:
        # Parse timestamps
        entry_time = datetime.fromisoformat(vehicle_state["entry_timestamp"])
        exit_time = datetime.fromisoformat(vehicle_exit.timestamp)
        
        # Calculate speed
        speed = calculate_speed(entry_time, exit_time)
        logger.info(f"Speed calculated: {speed} km/h")

        # Notify fine collection service if speed exceeds limit
        if speed > 60:  # Assuming speed limit is 60 km/h
            await notify_fine_collection(vehicle_exit.license_number, speed, vehicle_exit.timestamp)

        # Use update_one with $set to update only specific fields
        await db.vehicle_states.update_one(
            {"_id": vehicle_state["_id"]},  # Ensure we are updating the correct document by _id
            {"$set": {
                "exit_timestamp": vehicle_exit.timestamp,
                "exit_lane": vehicle_exit.lane,
                "speed": speed
            }}
        )

        logger.info(f"Vehicle exit recorded: {vehicle_exit.license_number}, Speed: {speed} km/h")
        return {"message": "Vehicle exit recorded", "speed": speed}
    
    except Exception as e:
        logger.error(f"Error processing vehicle exit: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.fastapi_ports.vehicle_state_service)
