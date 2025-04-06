import streamlit as st
import joblib
import time
import board
import adafruit_dht
import Adafruit_BMP.BMP085 as BMP085
import lgpio
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- Config ----------------
st.set_page_config(page_title="🌲 Forest-Eye Live Dashboard", layout="wide")
st.title("🌲 Forest-Eye: Live Environmental Monitoring")

# ---------------- Sensor Setup ----------------
DHT_SENSOR = adafruit_dht.DHT11(board.D4)
bmp_sensor = BMP085.BMP085(busnum=1)

MQ2_PIN = 17
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, MQ2_PIN)

# ---------------- Load Models ----------------
@st.cache_resource
def load_models():
    return {
        "fire": joblib.load("fire_risk_model.pkl"),
        "storm": joblib.load("storm_alert_model.pkl"),
        "anomaly": joblib.load("weather_anomaly_model.pkl"),
        "weather": joblib.load("weather_classification_model.pkl")
    }

models = load_models()
weather_labels = {0: "Sunny", 1: "Cloudy", 2: "Rainy", 3: "Stormy"}

# ---------------- Session States for History ----------------
if "history" not in st.session_state:
    st.session_state.history = {
        "Time": [],
        "Temperature": [],
        "Humidity": [],
        "Pressure": [],
        "Gas": []
    }

# ---------------- Live Mode Toggle ----------------
placeholder = st.empty()
running = st.toggle("▶️ Live Mode", value=True)

# ---------------- Live Loop ----------------
if running:
    while running:
        with placeholder.container():
            try:
                # --- Read DHT ---
                MAX_RETRIES = 3
                dht_temp = dht_humidity = None
                for _ in range(MAX_RETRIES):
                    try:
                        dht_temp = DHT_SENSOR.temperature
                        dht_humidity = DHT_SENSOR.humidity
                        if dht_temp is not None and dht_humidity is not None:
                            break
                    except RuntimeError:
                        time.sleep(0.5)

                bmp_temp = bmp_sensor.read_temperature()
                bmp_pressure = bmp_sensor.read_pressure() / 100

                temperature = dht_temp if dht_temp is not None else bmp_temp
                humidity = dht_humidity if dht_humidity is not None else 50
                pressure = bmp_pressure

                mq2_value = lgpio.gpio_read(h, MQ2_PIN)
                gas_status = "Gas Detected" if mq2_value == 0 else "Clear"

                # --- Record in history ---
                timestamp = time.strftime("%H:%M:%S")
                st.session_state.history["Time"].append(timestamp)
                st.session_state.history["Temperature"].append(temperature)
                st.session_state.history["Humidity"].append(humidity)
                st.session_state.history["Pressure"].append(pressure)
                st.session_state.history["Gas"].append(0 if mq2_value == 0 else 1)

                # --- Display Live Metrics ---
                st.subheader("📡 Live Sensor Readings")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🌡 Temp (°C)", f"{temperature:.1f}")
                col2.metric("💧 Humidity (%)", f"{humidity:.1f}")
                col3.metric("📟 Pressure (hPa)", f"{pressure:.1f}")
                col4.metric("🧪 MQ-2 Gas", gas_status)

                # --- Model Predictions ---
                st.subheader("📊 Predictions")
                input_data = [[temperature, humidity, pressure]]
                fire_risk = models["fire"].predict(input_data)[0]
                storm_alert = models["storm"].predict(input_data)[0]
                anomaly = models["anomaly"].predict(input_data)[0]
                weather_class = models["weather"].predict(input_data)[0]

                st.write("🔥 **Fire Risk:**", "🚨 High" if fire_risk else "✅ Safe")
                st.write("⛈ **Storm Alert:**", "⚠️ Yes" if storm_alert else "✅ No")
                st.write("🚨 **Anomaly Detection:**", "❗ Anomaly" if anomaly == -1 else "✅ Normal")
                st.write("🌦 **Weather:**", f"**{weather_labels.get(weather_class, 'Unknown')}**")

                # --- Plot Sensor Graphs ---
                st.subheader("📈 Sensor Trends")
                df = pd.DataFrame(st.session_state.history)

                col1, col2 = st.columns(2)
                with col1:
                    st.line_chart(df.set_index("Time")[["Temperature", "Humidity"]])
                with col2:
                    st.line_chart(df.set_index("Time")[["Pressure"]])

                st.line_chart(df.set_index("Time")[["Gas"]].rename(columns={"Gas": "Gas Detected (0=Yes, 1=Clear)"}))

            except Exception as e:
                st.error(f"❌ Error: {e}")

        time.sleep(2)

else:
    st.info("⏸ Live updates paused. Toggle 'Live Mode' to resume.")

# Cleanup on exit
def cleanup():
    try:
        DHT_SENSOR.exit()
        lgpio.gpiochip_close(h)
    except:
        pass

st.on_event("shutdown", cleanup)
