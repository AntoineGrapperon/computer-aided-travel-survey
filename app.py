import streamlit as st
import pandas as pd
import os
import folium
import plotly.express as px
import pydeck as pdk
import uuid
from streamlit_folium import st_folium
from datetime import datetime, time

# Set page configuration
st.set_page_config(
    page_title="CATS - City Travel Survey",
    page_icon="🏙️",
    layout="wide"
)

# Constants
CSV_FILE = "survey_responses.csv"
DEFAULT_LOCATION = [48.8566, 2.3522]  # Paris

# Initialize Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'trips' not in st.session_state:
    st.session_state.trips = []

if 'demographics' not in st.session_state:
    st.session_state.demographics = {}

if 'origin_coord' not in st.session_state:
    st.session_state.origin_coord = None

if 'dest_coord' not in st.session_state:
    st.session_state.dest_coord = None

def navigate_to(page):
    st.session_state.current_page = page

def save_responses(trips, demographics):
    """Saves multiple trips with demographic data to a local CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rows = []
    for trip in trips:
        row = trip.copy()
        row.update(demographics)
        row['session_id'] = st.session_state.session_id
        row['submission_timestamp'] = timestamp
        rows.append(row)
    
    new_df = pd.DataFrame(rows)
    
    if not os.path.isfile(CSV_FILE):
        new_df.to_csv(CSV_FILE, index=False)
    else:
        existing_df = pd.read_csv(CSV_FILE, nrows=0)
        if set(new_df.columns) != set(existing_df.columns):
            full_df = pd.read_csv(CSV_FILE)
            combined = pd.concat([full_df, new_df], ignore_index=True)
            combined.to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, mode='a', header=False, index=False)

def load_data():
    """Loads survey data from CSV."""
    if os.path.isfile(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()

# --- Navigation (Sidebar) ---
with st.sidebar:
    st.title("🏙️ CATS Admin")
    app_mode = st.radio("Choose Section:", ["Respondent (Survey)", "Admin (Dashboard)"])
    if app_mode == "Respondent (Survey)":
        if st.session_state.current_page == 'admin_dashboard':
            navigate_to('landing')
    else:
        navigate_to('admin_dashboard')

# --- Pages ---

def show_landing_page():
    st.title("🏙️ Welcome to the City Travel Survey")
    st.markdown("""
    Thank you for participating in our effort to improve urban mobility. 
    By sharing your daily travel habits, you help us design better infrastructure.

    ### How it works:
    1. Tell us a bit about yourself (optional demographics).
    2. Log all your trips for a single 24-hour period.
    3. Review and submit your Trip Diary.

    *Your data is anonymized and used exclusively for city planning purposes.*
    """)
    
    if st.button("Start Survey", type="primary"):
        navigate_to('demographics_form')

def show_demographics_form():
    st.title("👤 About You")
    st.write("This information helps us understand who is traveling and how.")
    
    with st.form("demographics_form"):
        age_group = st.selectbox("Age Group", ["Under 18", "18-24", "25-44", "45-64", "65+"])
        gender = st.selectbox("Gender", ["Woman", "Man", "Non-binary", "Prefer not to say"])
        occupation = st.selectbox("Primary Occupation", ["Student", "Employed", "Self-employed", "Retired", "Unemployed", "Other"])
        
        submitted = st.form_submit_button("Continue to Trip Diary", type="primary")
        
    if submitted:
        st.session_state.demographics = {
            "age_group": age_group,
            "gender": gender,
            "occupation": occupation
        }
        navigate_to('trip_diary')
        st.rerun()

def show_trip_diary():
    st.title("📋 Your Trip Diary")
    st.write("Please log all trips you made yesterday (or on a typical travel day).")
    
    if st.session_state.trips:
        st.subheader("Logged Trips")
        for i, trip in enumerate(st.session_state.trips):
            with st.expander(f"Trip {i+1}: {trip['origin_name']} ➔ {trip['destination_name']} ({trip['mode']})"):
                st.write(f"**From:** {trip['departure_time']} | **To:** {trip['arrival_time']}")
                st.write(f"**Purpose:** {trip['purpose']}")
                if st.button(f"Remove Trip {i+1}", key=f"remove_{i}"):
                    st.session_state.trips.pop(i)
                    st.rerun()
    else:
        st.info("No trips logged yet. Click 'Add a Trip' to begin.")
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add a Trip", type="primary"):
            navigate_to('trip_form')
            st.rerun()
            
    with col2:
        if st.session_state.trips:
            if st.button("🏁 Finish and Submit All Trips"):
                try:
                    save_responses(st.session_state.trips, st.session_state.demographics)
                    navigate_to('success_page')
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")

def show_trip_form():
    st.title("🚆 Record a Trip")
    st.write("Select your travel points on the map, then fill in the details.")

    # --- Mapping Section ---
    st.subheader("1. Where did you go?")
    selection_mode = st.radio("Select point to place on map:", ["Origin", "Destination"], horizontal=True)

    m = folium.Map(location=DEFAULT_LOCATION, zoom_start=12)
    if st.session_state.origin_coord:
        folium.Marker(st.session_state.origin_coord, popup="Origin", icon=folium.Icon(color='green', icon='play')).add_to(m)
    if st.session_state.dest_coord:
        folium.Marker(st.session_state.dest_coord, popup="Destination", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    output = st_folium(m, width=700, height=400)

    if output.get("last_clicked"):
        lat, lng = output["last_clicked"]["lat"], output["last_clicked"]["lng"]
        if selection_mode == "Origin":
            if st.session_state.origin_coord != [lat, lng]:
                st.session_state.origin_coord = [lat, lng]
                st.rerun()
        else:
            if st.session_state.dest_coord != [lat, lng]:
                st.session_state.dest_coord = [lat, lng]
                st.rerun()

    col_o, col_d = st.columns(2)
    with col_o:
        if st.session_state.origin_coord: st.success(f"✅ Origin Set")
        else: st.info("📍 Click map to set Origin")
    with col_d:
        if st.session_state.dest_coord: st.success(f"✅ Destination Set")
        else: st.info("📍 Click map to set Destination")

    # --- Details Section ---
    st.subheader("2. Trip Details")
    with st.form("trip_details_form"):
        col_orig_name, col_dest_name = st.columns(2)
        with col_orig_name:
            origin_name = st.text_input("Origin Name", placeholder="e.g., Home")
        with col_dest_name:
            destination_name = st.text_input("Destination Name", placeholder="e.g., Work")

        col1, col2 = st.columns(2)
        with col1:
            departure_time = st.time_input("Departure Time", value=time(8, 0))
        with col2:
            arrival_time = st.time_input("Arrival Time", value=time(8, 30))

        mode_options = ["Walk", "Bicycle", "Car (Driver)", "Car (Passenger)", "Public Transit", "Motorcycle", "Other"]
        travel_mode = st.selectbox("How did you travel?", options=mode_options)

        purpose_options = ["Work", "Education", "Shopping", "Social/Leisure", "Personal Business", "Other"]
        trip_purpose = st.selectbox("What was the purpose of this trip?", options=purpose_options)

        submitted = st.form_submit_button("Add Trip to Diary", type="primary")

    if submitted:
        if not st.session_state.origin_coord or not st.session_state.dest_coord:
            st.error("❌ Please select both Origin and Destination on the map.")
        elif arrival_time <= departure_time:
            st.error("❌ Arrival time must be after the departure time.")
        else:
            trip_entry = {
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
            st.session_state.trips.append(trip_entry)
            st.session_state.origin_coord = None
            st.session_state.dest_coord = None
            navigate_to('trip_diary')
            st.rerun()

    if st.button("Cancel - Back to Diary"):
        navigate_to('trip_diary')
        st.rerun()

def show_success_page():
    st.balloons()
    st.title("✅ Thank You!")
    st.success(f"All {len(st.session_state.trips)} trips have been saved successfully.")
    
    st.write("Thank you for contributing to your city's planning efforts!")

    if st.button("Start a New Diary"):
        st.session_state.trips = []
        st.session_state.demographics = {}
        st.session_state.session_id = str(uuid.uuid4())
        navigate_to('landing')
        st.rerun()

def show_admin_dashboard():
    st.title("📊 Admin Analytics Dashboard")
    df = load_data()
    
    if df.empty:
        st.warning("No survey responses found yet. Start collecting data to see analytics!")
        return

    # --- Metrics ---
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trips", len(df))
    col2.metric("Total Sessions", df['session_id'].nunique())
    col3.metric("Avg Trips/User", f"{len(df) / df['session_id'].nunique():.1f}")
    col4.metric("Most Common Mode", df['mode'].mode()[0])

    # --- Charts ---
    st.subheader("🚲 Travel Behavior")
    c1, c2 = st.columns(2)
    with c1:
        st.write("#### Modal Split")
        fig_mode = px.pie(df, names='mode', hole=0.4)
        st.plotly_chart(fig_mode, use_container_width=True)
    with c2:
        st.write("#### Trip Purpose")
        fig_purpose = px.bar(df['purpose'].value_counts())
        st.plotly_chart(fig_purpose, use_container_width=True)

    st.subheader("👤 Demographics")
    d1, d2 = st.columns(2)
    with d1:
        st.write("#### Age Group Distribution")
        fig_age = px.pie(df.drop_duplicates('session_id'), names='age_group')
        st.plotly_chart(fig_age, use_container_width=True)
    with d2:
        st.write("#### Occupation Distribution")
        fig_occ = px.bar(df.drop_duplicates('session_id')['occupation'].value_counts())
        st.plotly_chart(fig_occ, use_container_width=True)

    # --- Mapping ---
    st.subheader("🗺️ Trip Geography")
    origin_df = df[['origin_lat', 'origin_lon']].rename(columns={'origin_lat': 'lat', 'origin_lon': 'lon'})
    origin_df['color'] = '[0, 200, 0, 160]'
    dest_df = df[['dest_lat', 'dest_lon']].rename(columns={'dest_lat': 'lat', 'dest_lon': 'lon'})
    dest_df['color'] = '[200, 0, 0, 160]'
    points_df = pd.concat([origin_df, dest_df])

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(latitude=df['origin_lat'].mean(), longitude=df['origin_lon'].mean(), zoom=11),
        layers=[pdk.Layer('ScatterplotLayer', data=points_df, get_position='[lon, lat]', get_color='color', get_radius=200)],
    ))

    st.subheader("📄 Raw Data")
    st.dataframe(df)

# --- Page Router ---
if st.session_state.current_page == 'landing':
    show_landing_page()
elif st.session_state.current_page == 'demographics_form':
    show_demographics_form()
elif st.session_state.current_page == 'trip_diary':
    show_trip_diary()
elif st.session_state.current_page == 'trip_form':
    show_trip_form()
elif st.session_state.current_page == 'success_page':
    show_success_page()
elif st.session_state.current_page == 'admin_dashboard':
    show_admin_dashboard()
