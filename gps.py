import requests
import time

# PyPhox live endpoint
url = "http://192.168.171.179:8080/get?status&lat&lon&z&zwgs84&v&dir&dist&diststart&accuracy&zAccuracy&satellites"

def get_gps_data():
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        buffer = data.get("buffer", {})

        def extract(key):
            val = buffer.get(key, {}).get("buffer", [None])[0]
            return val if val is not None else "N/A"

        # Convert scientific notation (e.g., 1.2839442E1) into float
        latitude = float(extract("lat"))
        longitude = float(extract("lon"))
        altitude = float(extract("z"))
        speed = extract("v")
        direction = extract("dir")
        accuracy = float(extract("accuracy"))
        sat_count = int(float(extract("satellites")))

        print("\n--- Live GPS Data ---")
        print(f"Latitude      : {latitude}")
        print(f"Longitude     : {longitude}")
        print(f"Altitude (m)  : {altitude}")
        print(f"Speed (m/s)   : {speed}")
        print(f"Direction (°) : {direction}")
        print(f"Accuracy (m)  : {accuracy}")
        print(f"Satellites    : {sat_count}")

    except Exception as e:
        print("Error:", e)

# Continuous loop
while True:
    get_gps_data()
    time.sleep(2)
