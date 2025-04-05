import streamlit as st
import pandas as pd
import numpy as np
import joblib
import serial
import time
import cv2
import base64
import google.generativeai as genai
from sklearn.ensemble import IsolationForest

# ✅ Set page config FIRST
st.set_page_config(page_title="Forest Eye Aerobot", layout="centered")

# ---------------- Gemini AI Setup ---------------- #
genai.configure(api_key="AIzaSyBQqhaMjm5_60lQoWvpUOYIZQJIEw8RYik")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-2.0-flash")

st.title("🌲 Forest Eye Aerobot - Live Monitoring")

# Initialize session state
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

# Buttons to start/stop
if not st.session_state.monitoring:
    if st.button("▶️ Start Monitoring", key="start_button"):
        st.session_state.monitoring = True
else:
    if st.button("❌ Stop Monitoring", key="stop_button"):
        st.session_state.monitoring = False

status_box = st.empty()

# ---------------- Gemini Frame Analysis ---------------- #
def analyze_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode()

    response = model.generate_content(
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": "You are Forest Eye AI. Carefully analyze the given image from a forest surveillance system. Respond ONLY if you detect:\n- Fire or smoke (wildfire)\n- Evidence of deforestation (e.g., chopped trees, land clearing)\n- If any danger-causing animals found, say what animal and its threat\n- Any unusual human activity or threats\n\nIf none of these are found, just respond with: '✅ No threats detected.'"},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ]
    )
    return response.text.strip()

# ---------------- Sensor Models ---------------- #
fire_model = joblib.load("fire_risk_model.pkl")
storm_model = joblib.load("storm_alert_model.pkl")
anomaly_model = joblib.load("weather_anomaly_model.pkl")
weather_model = joblib.load("weather_classification_model.pkl")

def predict_conditions(temp, hum, pres):
    data = [[temp, hum, pres]]
    fire = fire_model.predict(data)[0]
    storm = storm_model.predict(data)[0]
    anomaly = anomaly_model.predict(data)[0]
    weather = weather_model.predict(data)[0]
    return fire, storm, anomaly, weather

# ---------------- Display Streamlit Widgets ---------------- #
st.sidebar.header("Sensor Input")
temp = st.sidebar.slider("Temperature (°C)", -10, 50, 25)
hum = st.sidebar.slider("Humidity (%)", 0, 100, 50)
pres = st.sidebar.slider("Pressure (hPa)", 900, 1100, 1013)

if st.sidebar.button("🔍 Analyze Conditions"):
    fire, storm, anomaly, weather = predict_conditions(temp, hum, pres)
    st.sidebar.markdown(f"**🔥 Fire Risk:** {'Yes' if fire else 'No'}")
    st.sidebar.markdown(f"**🌩️ Storm Alert:** {'Yes' if storm else 'No'}")
    st.sidebar.markdown(f"**❗ Anomaly:** {'Yes' if anomaly == -1 else 'No'}")
    st.sidebar.markdown(f"**🌤️ Weather Type:** {weather}")

# ---------------- Gemini Live Monitoring Loop ---------------- #
if st.session_state.monitoring:
    cap = cv2.VideoCapture(0)
    last_time = time.time()

    if not cap.isOpened():
        st.error("❌ Unable to access the webcam.")
        st.session_state.monitoring = False
    else:
        st.success("✅ Camera is active. Monitoring in progress...")
        frame_placeholder = st.empty()

        while st.session_state.monitoring:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Failed to read from webcam.")
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", caption="📷 Live Forest Feed")

            if time.time() - last_time > 10:
                try:
                    description = analyze_frame(frame)
                except Exception as e:
                    description = f"⚠️ Error: {e}"
                status_box.markdown(f"**🧠 Gemini says:** {description}")
                last_time = time.time()

            time.sleep(0.1)

        cap.release()
        st.warning("🛑 Monitoring stopped.")
