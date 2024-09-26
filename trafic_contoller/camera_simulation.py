import random
import time
import requests
from datetime import datetime

# Configurations
ENTRY_CAM_URL = "http://localhost:6000/entrycam"
EXIT_CAM_URL = "http://localhost:6000/exitcam"
LANES = 3
NUM_VEHICLES = 10  # Number of vehicles to simulate

def generate_license_number():
    return f"ABC-{random.randint(11, 20)}"

def simulate_vehicle_passing(vehicle_count):
    license_number = generate_license_number()
    entry_lane = random.randint(1, LANES)
    entry_timestamp = datetime.now().isoformat()

    # Send entry information
    entry_data = {
        "license_number": license_number,
        "lane": entry_lane,
        "timestamp": entry_timestamp
    }
    try:
        response = requests.post(ENTRY_CAM_URL, json=entry_data)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"%Vehicle {license_number} in Entry lane {entry_lane} passed entry camera at {entry_timestamp}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending entry data: {e}")

    # Simulate random delay before exiting
    time.sleep(random.randint(1, 5))  # Vehicle stays for 1 to 5 seconds

    exit_lane = random.randint(1, LANES)
    exit_timestamp = datetime.now().isoformat()

    # Send exit information
    exit_data = {
        "license_number": license_number,
        "lane": exit_lane,
        "timestamp": exit_timestamp
    }
    try:
        response = requests.post(EXIT_CAM_URL, json=exit_data)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"*Vehicle {license_number} in Exitline {exit_lane} passed exit camera at {exit_timestamp}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending exit data: {e}")

if __name__ == "__main__":
    try:
        for _ in range(NUM_VEHICLES):
            simulate_vehicle_passing(_)
            time.sleep(random.randint(1, 3))  # Simulate a vehicle every 1 to 3 seconds
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
