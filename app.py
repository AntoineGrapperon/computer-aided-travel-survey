import streamlit as st
import pandas as pd
import os
from datetime import datetime, time

# Set page configuration
st.set_page_config(
    page_title="CATS - City Travel Survey",
    page_icon="🏙️",
    layout="centered"
)

# Constants
CSV_FILE = "survey_responses.csv"

# Initialize Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

if 'trip_data' not in st.session_state:
    st.session_state.trip_data = {}

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
    2. Enter details for a single trip you've taken recently.
    3. Submit your response.

    *Your data is anonymized and used exclusively for city planning purposes.*
    """)
    
    if st.button("Start Survey", type="primary"):
        navigate_to('trip_form')

def show_trip_form():
    st.title("🚆 Record Your Trip")
    st.write("Please provide details for one of your recent trips.")

    with st.form("trip_form"):
        # Origin and Destination
        col_orig, col_dest = st.columns(2)
        with col_orig:
            origin = st.text_input("Origin", placeholder="e.g., Home, Work, 123 Main St")
        with col_dest:
            destination = st.text_input("Destination", placeholder="e.g., Grocery Store, Park")

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
        if not origin or not destination:
            st.error("❌ Please provide both an Origin and a Destination.")
        elif arrival_time <= departure_time:
            st.error("❌ Arrival time must be after the departure time. Please check your inputs.")
        else:
            # Prepare data
            st.session_state.trip_data = {
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time.strftime("%H:%M"),
                "arrival_time": arrival_time.strftime("%H:%M"),
                "mode": travel_mode,
                "purpose": trip_purpose
            }
            
            # Save to CSV
            try:
                save_response(st.session_state.trip_data)
                navigate_to('success_page')
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save response: {e}")

    if st.button("Back to Start"):
        navigate_to('landing')
        st.rerun()

def show_success_page():
    st.balloons()
    st.title("✅ Thank You!")
    st.success("Your trip response has been recorded and saved successfully.")
    
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
