import streamlit as st
import cv2
import numpy as np
import time
import board
import adafruit_dht
import Adafruit_BMP.BMP085 as BMP085
import smbus
import lgpio
from ultralytics import YOLO

# Initialize YOLO model
model = YOLO("yolov8n.pt")  # Using a lightweight YOLO model

# Initialize Camera
cap = cv2.VideoCapture(0)

# Initialize Sensors
MQ2_PIN = 17
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, MQ2_PIN)

DHT_SENSOR = adafruit_dht.DHT11(board.D4)
bus = smbus.SMBus(1)
bmp_sensor = BMP085.BMP085(busnum=1)

# Streamlit App Layout
st.set_page_config(page_title="Forest-Eye Monitoring System", layout="wide")

st.title("🌲 Forest-Eye Monitoring System")
col1, col2 = st.columns(2)

# Display Live Camera Feed
with col1:
    st.subheader("📹 Live Camera Feed")
    camera_placeholder = st.empty()

# Display Sensor Data
with col2:
    st.subheader("📊 Sensor Data")
    dht_placeholder = st.empty()
    bmp_placeholder = st.empty()
    mq2_placeholder = st.empty()

# Processing Loop
while True:
    # Read camera frame
    ret, frame = cap.read()
    if not ret:
        st.error("Failed to capture video")
        break

    # Perform YOLO Detection
    results = model(frame)
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf[0]
            cls = int(box.cls[0])
            label = model.names[cls]

            if label in ["person", "car", "truck", "dog", "cat", "cow"]:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Convert OpenCV frame to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    camera_placeholder.image(frame, channels="RGB", use_column_width=True)

    # Read Sensor Data
    try:
        dht_temp = DHT_SENSOR.temperature
        dht_humidity = DHT_SENSOR.humidity
        bmp_temp = bmp_sensor.read_temperature()
        bmp_pressure = bmp_sensor.read_pressure() / 100  # Convert to hPa
        bmp_altitude = bmp_sensor.read_altitude()
        mq2_value = lgpio.gpio_read(h, MQ2_PIN)

        # Update Sensor Readings in Streamlit
        dht_placeholder.write(f"🌡 **DHT11 Temperature**: {dht_temp:.1f}°C, **Humidity**: {dht_humidity:.1f}%")
        bmp_placeholder.write(f"🌎 **BMP180**: Temperature: {bmp_temp:.2f}°C, Pressure: {bmp_pressure:.2f} hPa, Altitude: {bmp_altitude:.2f}m")
        mq2_placeholder.write(f"💨 **MQ-2 Gas Detected**: {'Yes' if mq2_value == 0 else 'No'}")

    except RuntimeError as error:
        st.warning(f"Sensor Error: {error}")

    except Exception as e:
        st.error(f"Unexpected error: {e}")

    time.sleep(2)  # Refresh every 2 seconds

cap.release()
lgpio.gpiochip_close(h)
