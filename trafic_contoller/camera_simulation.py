import random
import time
import requests
from datetime import datetime
from config import config

def generate_license_number():
    return f"ABC-{random.randint(1110, 1120)}"

def simulate_vehicle_passing(vehicle_count):
    license_number = generate_license_number()
    entry_lane = random.randint(1, config.app.lanes)
    entry_timestamp = datetime.now().isoformat()

    # Send entry information
    entry_data = {
        "license_number": license_number,
        "lane": entry_lane,
        "timestamp": entry_timestamp
    }
    try:
        response = requests.post(config.services.entry_cam_url, json=entry_data)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"Vehicle {license_number} passed entry camera at {entry_timestamp}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending entry data: {e}")

    # Simulate random delay before exiting
    time.sleep(random.randint(
        config.app.simulation_delay_range.min_seconds,
        config.app.simulation_delay_range.max_seconds
    ))  # Vehicle stays for min to max seconds

    exit_lane = random.randint(1, config.app.lanes)
    exit_timestamp = datetime.now().isoformat()

    # Send exit information
    exit_data = {
        "license_number": license_number,
        "lane": exit_lane,
        "timestamp": exit_timestamp
    }
    try:
        response = requests.post(config.services.exit_cam_url, json=exit_data)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"Vehicle {license_number} passed exit camera at {exit_timestamp}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending exit data: {e}")

if __name__ == "__main__":
    try:
        for vehicle_count in range(config.app.num_vehicles):
            simulate_vehicle_passing(vehicle_count)
            time.sleep(random.randint(
                config.app.simulation_delay_range.min_seconds,
                config.app.simulation_delay_range.max_seconds
            ))  # Simulate a vehicle every min to max seconds
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")