import streamlit as st
import joblib
import time
import board
import adafruit_dht
import Adafruit_BMP.BMP085 as BMP085

# --- Title ---
st.set_page_config(page_title="Forest-Eye Dashboard", layout="wide")
st.title("🌲 Forest-Eye: Environmental & Weather Monitoring")

# --- Initialize Sensors ---
DHT_SENSOR = adafruit_dht.DHT11(board.D4)
bmp_sensor = BMP085.BMP085(busnum=1)

# --- Sensor Data Section ---
st.header("🌡️ Live Sensor Readings")

# Read sensor data
try:
    dht_temp = DHT_SENSOR.temperature
    dht_humidity = DHT_SENSOR.humidity
    bmp_temp = bmp_sensor.read_temperature()
    bmp_pressure = bmp_sensor.read_pressure() / 100  # Convert to hPa

    # Use BMP180 pressure and DHT11 humidity and temperature
    temperature = dht_temp if dht_temp is not None else bmp_temp
    humidity = dht_humidity if dht_humidity is not None else 50  # default fallback
    pressure = bmp_pressure

    temp_col, hum_col, pres_col = st.columns(3)
    temp_col.metric("Temperature (°C)", f"{temperature:.1f}")
    hum_col.metric("Humidity (%)", f"{humidity:.1f}")
    pres_col.metric("Pressure (hPa)", f"{pressure:.1f}")

    # --- Weather Prediction Models ---
    fire_model = joblib.load("fire_risk_model.pkl")
    storm_model = joblib.load("storm_alert_model.pkl")
    anomaly_model = joblib.load("weather_anomaly_model.pkl")
    weather_model = joblib.load("weather_classification_model.pkl")

    # Prepare input data
    input_data = [[temperature, humidity, pressure]]

    # Make predictions
    fire_risk = fire_model.predict(input_data)[0]
    storm_alert = storm_model.predict(input_data)[0]
    anomaly = anomaly_model.predict(input_data)[0]
    weather_class = weather_model.predict(input_data)[0]

    weather_labels = {0: "Sunny", 1: "Cloudy", 2: "Rainy", 3: "Stormy"}

    # --- Display Predictions ---
    st.header("📊 Weather Condition Predictions")

    st.subheader("🔥 Fire Risk Prediction")
    if fire_risk:
        st.error("High Fire Risk Detected!")
    else:
        st.success("No Fire Risk.")

    st.subheader("⛈ Storm Alert")
    if storm_alert:
        st.warning("Storm Alert Active!")
    else:
        st.info("No Storm Predicted.")

    st.subheader("🚨 Anomaly Detection")
    if anomaly == -1:
        st.error("Abnormal Weather Conditions Detected")
    else:
        st.success("Weather Conditions Normal")

    st.subheader("🌦 Weather Classification")
    st.info(f"Predicted Weather: **{weather_labels.get(weather_class, 'Unknown')}**")

except RuntimeError as error:
    st.warning(f"Sensor Error: {error}")

except Exception as e:
    st.error(f"Unexpected error: {e}")
