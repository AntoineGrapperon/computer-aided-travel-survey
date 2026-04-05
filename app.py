import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
from datetime import datetime, time

# Set page configuration
st.set_page_config(
    page_title="CATS - City Travel Survey",
    page_icon="🏙️",
    layout="centered"
)

# Constants
CSV_FILE = "survey_responses.csv"
DEFAULT_LOCATION = [48.8566, 2.3522]  # Paris

# Initialize Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

if 'trip_data' not in st.session_state:
    st.session_state.trip_data = {}

if 'origin_coord' not in st.session_state:
    st.session_state.origin_coord = None

if 'dest_coord' not in st.session_state:
    st.session_state.dest_coord = None

def navigate_to(page):
    st.session_state.current_page = page

def save_response(data):
    """Saves the trip data to a local CSV file."""
    # Add submission timestamp
    data['submission_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create DataFrame from new entry
    new_df = pd.DataFrame([data])
    
    # Append to file or create new with header
    if not os.path.isfile(CSV_FILE):
        new_df.to_csv(CSV_FILE, index=False)
    else:
        # Check if the file has all columns (handle schema updates)
        existing_df = pd.read_csv(CSV_FILE, nrows=0)
        if set(new_df.columns) != set(existing_df.columns):
            # If schema changed, we read everything and re-save with new headers
            # (Simple approach for small datasets)
            full_df = pd.read_csv(CSV_FILE)
            combined = pd.concat([full_df, new_df], ignore_index=True)
            combined.to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, mode='a', header=False, index=False)

# --- Pages ---

def show_landing_page():
    st.title("🏙️ Welcome to the City Travel Survey")
    st.markdown("""
    Thank you for participating in our effort to improve urban mobility. 
    By sharing your daily travel habits, you help us design better public transit, 
    safer cycling infrastructure, and more efficient roads.

    ### How it works:
    1. Click **Start Survey** below.
    2. Select your **Origin** and **Destination** on the map.
    3. Enter trip details (time, mode, purpose).
    4. Submit your response.

    *Your data is anonymized and used exclusively for city planning purposes.*
    """)
    
    if st.button("Start Survey", type="primary"):
        navigate_to('trip_form')

def show_trip_form():
    st.title("🚆 Record Your Trip")
    st.write("First, select your travel points on the map, then fill in the details.")

    # --- Mapping Section ---
    st.subheader("1. Where did you go?")
    
    # Map selection mode
    selection_mode = st.radio("Select point to place on map:", ["Origin", "Destination"], horizontal=True)

    # Initialize map
    m = folium.Map(location=DEFAULT_LOCATION, zoom_start=12)
    
    # Add existing markers
    if st.session_state.origin_coord:
        folium.Marker(
            st.session_state.origin_coord, 
            popup="Origin", 
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)
    
    if st.session_state.dest_coord:
        folium.Marker(
            st.session_state.dest_coord, 
            popup="Destination", 
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)

    # Capture clicks
    output = st_folium(m, width=700, height=400)

    if output.get("last_clicked"):
        lat = output["last_clicked"]["lat"]
        lng = output["last_clicked"]["lng"]
        
        if selection_mode == "Origin":
            if st.session_state.origin_coord != [lat, lng]:
                st.session_state.origin_coord = [lat, lng]
                st.rerun()
        else:
            if st.session_state.dest_coord != [lat, lng]:
                st.session_state.dest_coord = [lat, lng]
                st.rerun()

    # Display selected coordinates status
    col_o, col_d = st.columns(2)
    with col_o:
        if st.session_state.origin_coord:
            st.success(f"✅ Origin Set")
        else:
            st.info("📍 Click map to set Origin")
    with col_d:
        if st.session_state.dest_coord:
            st.success(f"✅ Destination Set")
        else:
            st.info("📍 Click map to set Destination")

    # --- Details Section ---
    st.subheader("2. Trip Details")
    with st.form("trip_details_form"):
        # Descriptive names (optional but helpful)
        col_orig_name, col_dest_name = st.columns(2)
        with col_orig_name:
            origin_name = st.text_input("Origin Name", placeholder="e.g., Home")
        with col_dest_name:
            destination_name = st.text_input("Destination Name", placeholder="e.g., Work")

        # Time Inputs
        col1, col2 = st.columns(2)
        with col1:
            departure_time = st.time_input("Departure Time", value=time(8, 0))
        with col2:
            arrival_time = st.time_input("Arrival Time", value=time(8, 30))

        # Categorical Inputs
        mode_options = ["Walk", "Bicycle", "Car (Driver)", "Car (Passenger)", "Public Transit", "Motorcycle", "Other"]
        travel_mode = st.selectbox("How did you travel?", options=mode_options)

        purpose_options = ["Work", "Education", "Shopping", "Social/Leisure", "Personal Business", "Other"]
        trip_purpose = st.selectbox("What was the purpose of this trip?", options=purpose_options)

        # Submit Button
        submitted = st.form_submit_button("Submit Response", type="primary")

    if submitted:
        # Validation Logic
        if not st.session_state.origin_coord or not st.session_state.dest_coord:
            st.error("❌ Please select both Origin and Destination on the map.")
        elif arrival_time <= departure_time:
            st.error("❌ Arrival time must be after the departure time.")
        else:
            # Prepare data
            st.session_state.trip_data = {
                "origin_name": origin_name,
                "origin_lat": st.session_state.origin_coord[0],
                "origin_lon": st.session_state.origin_coord[1],
                "dest_name": destination_name,
                "dest_lat": st.session_state.dest_coord[0],
                "dest_lon": st.session_state.dest_coord[1],
                "departure_time": departure_time.strftime("%H:%M"),
                "arrival_time": arrival_time.strftime("%H:%M"),
                "mode": travel_mode,
                "purpose": trip_purpose
            }
            
            # Save to CSV
            try:
                save_response(st.session_state.trip_data)
                # Reset map state for next time
                st.session_state.origin_coord = None
                st.session_state.dest_coord = None
                navigate_to('success_page')
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

    if st.button("Back to Start"):
        navigate_to('landing')
        st.rerun()

def show_success_page():
    st.balloons()
    st.title("✅ Thank You!")
    st.success("Your trip and coordinates have been saved successfully.")
    
    st.write("### Summary of your submission:")
    st.json(st.session_state.trip_data)

    if st.button("Record Another Trip"):
        st.session_state.trip_data = {}
        navigate_to('trip_form')
        st.rerun()

    if st.button("Exit to Landing Page"):
        st.session_state.trip_data = {}
        navigate_to('landing')
        st.rerun()

# --- Page Router ---

if st.session_state.current_page == 'landing':
    show_landing_page()
elif st.session_state.current_page == 'trip_form':
    show_trip_form()
elif st.session_state.current_page == 'success_page':
    show_success_page()
