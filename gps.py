import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from streamlit_autorefresh import st_autorefresh

# --- GPS Function ---
GPS_URL = "http://192.168.171.179:8080/get?status&lat&lon&z&zwgs84&v&dir&dist&diststart&accuracy&zAccuracy&satellites"

def get_gps_data():
    try:
        response = requests.get(GPS_URL, timeout=5)
        data = response.json()
        buffer = data.get("buffer", {})

        def extract(key):
            val = buffer.get(key, {}).get("buffer", [None])[0]
            return val if val is not None else "N/A"

        return {
            "latitude": float(extract("lat")),
            "longitude": float(extract("lon")),
            "altitude": float(extract("z")),
            "speed": extract("v"),
            "direction": extract("dir"),
            "accuracy": float(extract("accuracy")),
            "satellites": int(float(extract("satellites"))),
        }

    except Exception as e:
        return {"error": str(e)}

# --- Streamlit UI ---
st.set_page_config(page_title="Live GPS", layout="centered")
st.title("📡 Live GPS Tracking")
st.markdown("This map updates every 5 seconds with your current location.")

# 🔁 Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="gps_autorefresh")

gps_data = get_gps_data()

if "error" in gps_data:
    st.error(f"GPS Error: {gps_data['error']}")
else:
    lat = gps_data["latitude"]
    lon = gps_data["longitude"]

    st.markdown(f"**Latitude:** `{lat}`")
    st.markdown(f"**Longitude:** `{lon}`")
    st.markdown(f"**Altitude:** `{gps_data['altitude']} m`")
    st.markdown(f"**Speed:** `{gps_data['speed']} m/s`")
    st.markdown(f"**Accuracy:** `{gps_data['accuracy']} m`")
    st.markdown(f"**Satellites:** `{gps_data['satellites']}`")

    # 🌍 Create and display Folium map
    m = folium.Map(location=[lat, lon], zoom_start=16)
    folium.Marker([lat, lon], tooltip="Current Location", popup=f"Lat: {lat}, Lon: {lon}").add_to(m)
    st_folium(m, width=700, height=500)
