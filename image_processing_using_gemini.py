import cv2
import time
import base64
import streamlit as st
import google.generativeai as genai

# ✅ Set page config FIRST
st.set_page_config(page_title="Forest Eye Aerobot", layout="centered")

# Configure Gemini API
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

# Analyze function using Gemini
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

# Monitoring loop
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

            # Convert and show live feed
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", caption="📷 Live Forest Feed")

            # Analyze every 10 seconds
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
