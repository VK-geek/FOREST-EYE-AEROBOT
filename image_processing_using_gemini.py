import cv2
import time
import base64
import streamlit as st
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Forest Eye Aerobot", layout="centered")

# Gemini API setup
genai.configure(api_key="AIzaSyAHlgdqZrbqPPTSW_pTNBCbPk3Aeadyn6E")  # Replace with your Gemini API Key
model = genai.GenerativeModel("gemini-2.0-flash")

st.title("🌲 Forest Eye Aerobot - Live Monitoring")

# Initialize session states
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "threat_counts" not in st.session_state:
    st.session_state.threat_counts = {
        "🔥 Fire/Smoke": 0,
        "🪓 Deforestation": 0,
        "🐾 Dangerous Animal": 0,
        "🧍‍♂️ Human Activity": 0
    }

# Sidebar for threat stats
st.sidebar.header("📊 Threat Statistics")

# Start/Stop Buttons
if not st.session_state.monitoring:
    if st.button("▶️ Start Monitoring"):
        st.session_state.monitoring = True
else:
    if st.button("❌ Stop Monitoring"):
        st.session_state.monitoring = False

status_box = st.empty()
frame_placeholder = st.empty()
threat_table_placeholder = st.sidebar.empty()
bar_chart_placeholder = st.sidebar.empty()

# Function to analyze frame using Gemini
def analyze_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode()

    response = model.generate_content(
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": "You are Forest Eye AI. Carefully analyze the given image "
                             "from a forest surveillance system. Respond ONLY if you detect:\n"
                             "- Fire or smoke (wildfire)\n"
                             "- Evidence of deforestation (e.g., chopped trees, land clearing)\n"
                             "- If any danger-causing animals found, say what animal and its threat\n"
                             "- Any unusual human activity or threats\n\n"
                             "If none of these are found, just respond with: '✅ No threats detected.'"},
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

# Function to update threat displays
def update_threat_display():
    df = pd.DataFrame.from_dict(st.session_state.threat_counts, orient='index', columns=["Count"])
    df.index.name = "Threat Type"
    df = df.sort_values("Count", ascending=False)

    # Show table
    threat_table_placeholder.dataframe(df)

    # Show bar chart
    fig, ax = plt.subplots()
    ax.bar(df.index, df["Count"], color=["red", "brown", "orange", "purple"])
    ax.set_ylabel("Detections")
    ax.set_title("📈 Detected Threats")
    ax.set_xticklabels(df.index, rotation=45, ha='right')
    bar_chart_placeholder.pyplot(fig)

# Monitoring loop
if st.session_state.monitoring:
    cap = cv2.VideoCapture(0)
    last_time = time.time()

    if not cap.isOpened():
        st.error("❌ Unable to access the webcam.")
        st.session_state.monitoring = False
    else:
        st.success("✅ Camera is active. Monitoring in progress...")

        while st.session_state.monitoring:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Failed to read from webcam.")
                break

            # Convert to RGB and show
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", caption="📷 Live Forest Feed")

            # Analyze every 10 seconds
            if time.time() - last_time > 10:
                try:
                    description = analyze_frame(frame)
                except Exception as e:
                    description = f"⚠️ Error: {e}"

                st.markdown(f"**🧠 Gemini says:** {description}")
                last_time = time.time()

                # Skip if no threats detected
                if "✅ no threats detected" not in description.lower():
                    desc_lower = description.lower()

                    # Keyword lists
                    fire_keywords = ["fire", "smoke", "wildfire"]
                    deforestation_keywords = ["deforestation", "chopped", "cut tree", "land clearing"]
                    animal_keywords = ["animal", "tiger", "elephant", "bear", "snake", "wild animal"]
                    human_keywords = ["human", "person", "intruder", "poacher", "man", "woman"]

                    # Update counts
                    if any(k in desc_lower for k in fire_keywords):
                        st.session_state.threat_counts["🔥 Fire/Smoke"] += 1
                    if any(k in desc_lower for k in deforestation_keywords):
                        st.session_state.threat_counts["🪓 Deforestation"] += 1
                    if any(k in desc_lower for k in animal_keywords):
                        st.session_state.threat_counts["🐾 Dangerous Animal"] += 1
                    if any(k in desc_lower for k in human_keywords):
                        st.session_state.threat_counts["🧍‍♂️ Human Activity"] += 1

                    update_threat_display()

            time.sleep(0.1)

        cap.release()
        st.warning("🛑 Monitoring stopped.")
