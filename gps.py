import streamlit as st
import folium
from streamlit_folium import folium_static
import time
from gps import get_gps_data

def initialize_map():
    # Set initial map view to a default location
    default_location = [0, 0]  # Will be updated with actual GPS data
    m = folium.Map(location=default_location, zoom_start=16)
    return m

def update_map(m, gps_data):
    if not gps_data:
        return m
    
    # Clear existing markers
    m = folium.Map(location=[gps_data["Latitude"], gps_data["Longitude"]], zoom_start=16)
    
    # Add marker for current position
    folium.Marker(
        [gps_data["Latitude"], gps_data["Longitude"]],
        popup=f"Speed: {gps_data['Speed (m/s)']} m/s<br>Altitude: {gps_data['Altitude']} m",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    return m

def display_gps_metrics(gps_data):
    if not gps_data:
        st.warning("⚠️ No GPS data received")
        return
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Speed", f"{gps_data['Speed (m/s)']:.2f} m/s")
        st.metric("Direction", f"{gps_data['Direction (°)']:.1f}°")
    
    with col2:
        st.metric("Altitude", f"{gps_data['Altitude']:.1f} m")
        st.metric("Satellites", int(gps_data['Satellites']))
    
    with col3:
        st.metric("Accuracy", f"{gps_data['Accuracy (m)']:.1f} m")
        st.metric("Distance", f"{gps_data['Distance (m)']:.1f} m")

def main():
    st.title("Live GPS Tracking")
    
    # Initialize the map
    map_placeholder = st.empty()
    metrics_placeholder = st.empty()
    
    # Create a flag for tracking
    tracking = st.checkbox("Enable Live Tracking", value=True)
    
    # Initialize map
    m = initialize_map()
    
    while tracking:
        # Get GPS data
        gps_data = get_gps_data()
        
        # Update map if we have valid GPS data
        if gps_data:
            m = update_map(m, gps_data)
            with map_placeholder:
                folium_static(m)
            
            with metrics_placeholder:
                display_gps_metrics(gps_data)
        
        # Wait before next update
        time.sleep(1)

if __name__ == "__main__":
    main()
