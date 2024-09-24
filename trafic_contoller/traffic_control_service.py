from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
from datetime import datetime
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

# Models
class VehicleEntry(BaseModel):
    license_number: str
    lane: int
    timestamp: str

class VehicleExit(BaseModel):
    license_number: str
    lane: int
    timestamp: str

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
    vehicle_state = await db.vehicle_states.find_one({"license_number": vehicle_exit.license_number})

    if not vehicle_state:
        raise HTTPException(status_code=404, detail="Vehicle entry not found")

    try:
        entry_time = datetime.fromisoformat(vehicle_state["entry_timestamp"])
        exit_time = datetime.fromisoformat(vehicle_exit.timestamp)
        speed = calculate_speed(entry_time, exit_time)

        if speed > 60:  # Assuming speed limit is 60 km/h
            await notify_fine_collection(vehicle_exit.license_number, speed, vehicle_exit.timestamp)

        vehicle_state["exit_timestamp"] = vehicle_exit.timestamp
        await db.vehicle_states.replace_one({"license_number": vehicle_exit.license_number}, vehicle_state)
        
        logger.info(f"Vehicle exit recorded: {vehicle_state}, Speed: {speed} km/h")
        return {"message": "Vehicle exit recorded", "speed": speed}
    
    except Exception as e:
        logger.error(f"Error processing vehicle exit: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def calculate_speed(entry_time, exit_time):
    time_diff = (exit_time - entry_time).total_seconds() / 3600  # in hours
    distance = 1  # assuming 1 km between entry and exit
    if time_diff > 0:
        return distance / time_diff
    else:
        return 0  # Prevent division by zero

async def notify_fine_collection(license_number, speed, timestamp):
    payload = {
        "license_number": license_number,
        "speed": speed,
        "timestamp": timestamp
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:6001/collectfine", json=payload)
            response.raise_for_status()  # Raise an error for bad responses
            logger.info(f"Fine collection notified for {license_number} with speed {speed} km/h")
    except httpx.RequestError as e:
        logger.error(f"Error notifying fine collection service: {e}")
    except Exception as e:
        logger.error(f"Error in notifying fine collection service: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
