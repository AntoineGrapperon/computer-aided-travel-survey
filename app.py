import streamlit as st
import pandas as pd
import os
import folium
import plotly.express as px
import pydeck as pdk
import uuid
import json
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from datetime import datetime, time, timedelta

# Set page configuration
st.set_page_config(
    page_title="CATS - City Travel Survey",
    page_icon="🏙️",
    layout="wide"
)

# Constants
CSV_FILE = "survey_responses.csv"
DEFAULT_LOCATION = [48.8566, 2.3522]  # Paris
ADMIN_PASSWORD = "city_planning_2026"  # In a real app, use secrets or env vars

# Initialize Geocoder
geolocator = Nominatim(user_agent="cats_travel_survey_app")

# Initialize Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

if 'is_admin_authenticated' not in st.session_state:
    st.session_state.is_admin_authenticated = False

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

def geocode_address(address):
    """Converts a text address to [lat, lon] coordinates."""
    try:
        location = geolocator.geocode(address)
        if location:
            return [location.latitude, location.longitude]
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return None

def calculate_trip_stats(origin_lat, origin_lon, dest_lat, dest_lon, departure_time_str, arrival_time_str):
    """Calculates distance in km and average speed in km/h."""
    dist_km = geodesic((origin_lat, origin_lon), (dest_lat, dest_lon)).kilometers
    
    fmt = "%H:%M"
    start = datetime.strptime(departure_time_str, fmt)
    end = datetime.strptime(arrival_time_str, fmt)
    
    # Simple hour calculation
    duration_hrs = (end - start).total_seconds() / 3600.0
    speed_kmh = dist_km / duration_hrs if duration_hrs > 0 else 0
    
    return round(dist_km, 2), round(speed_kmh, 1)

def check_overlap(new_departure_str, new_arrival_str, existing_trips):
    """Checks if a new trip overlaps with any existing trips in the diary."""
    fmt = "%H:%M"
    new_start = datetime.strptime(new_departure_str, fmt).time()
    new_end = datetime.strptime(new_arrival_str, fmt).time()
    
    for trip in existing_trips:
        trip_start = datetime.strptime(trip['departure_time'], fmt).time()
        trip_end = datetime.strptime(trip['arrival_time'], fmt).time()
        
        # Standard time overlap check
        if (trip_start < new_end and new_start < trip_end):
            return True, trip
            
    return False, None

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
    """Loads survey data from CSV and ensures all expected columns exist."""
    expected_columns = [
        'origin_name', 'origin_lat', 'origin_lon', 
        'dest_name', 'dest_lat', 'dest_lon', 
        'departure_time', 'arrival_time', 'mode', 'purpose',
        'distance_km', 'speed_kmh',
        'age_group', 'gender', 'occupation', 'session_id', 'submission_timestamp'
    ]
    if os.path.isfile(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Ensure all expected columns are present (for backward compatibility)
        for col in expected_columns:
            if col not in df.columns:
                df[col] = None
        return df
    return pd.DataFrame(columns=expected_columns)

def convert_to_geojson(df):
    """Converts the DataFrame to a GeoJSON FeatureCollection (LineStrings)."""
    features = []
    for _, row in df.iterrows():
        if pd.notna(row['origin_lat']) and pd.notna(row['dest_lat']):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [float(row['origin_lon']), float(row['origin_lat'])],
                        [float(row['dest_lon']), float(row['dest_lat'])]
                    ]
                },
                "properties": {
                    "mode": row['mode'],
                    "purpose": row['purpose'],
                    "distance_km": row['distance_km'],
                    "age_group": row['age_group'],
                    "timestamp": row['submission_timestamp']
                }
            }
            features.append(feature)
    
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)

# --- Navigation (Sidebar) ---
with st.sidebar:
    st.title("🏙️ CATS Menu")
    app_mode = st.radio("Choose Section:", ["Respondent (Survey)", "Admin (Dashboard)"])
    
    if app_mode == "Respondent (Survey)":
        if st.session_state.current_page == 'admin_dashboard':
            navigate_to('landing')
    else:
        # Check authentication for Admin mode
        if not st.session_state.is_admin_authenticated:
            navigate_to('admin_login')
        else:
            navigate_to('admin_dashboard')
            if st.button("🔓 Logout Admin"):
                st.session_state.is_admin_authenticated = False
                navigate_to('landing')
                st.rerun()

# --- Pages ---

def show_admin_login():
    st.title("🔒 Admin Access")
    st.write("Please enter the administrative password to access the dashboard.")
    
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.is_admin_authenticated = True
                st.success("Authenticated successfully!")
                navigate_to('admin_dashboard')
                st.rerun()
            else:
                st.error("Incorrect password.")
    
    if st.button("Back to Survey"):
        navigate_to('landing')
        st.rerun()

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
            origin_label = trip.get('origin_name') or "Unknown Origin"
            dest_label = trip.get('destination_name') or "Unknown Destination"
            mode_label = trip.get('mode') or "Unknown Mode"
            
            with st.expander(f"Trip {i+1}: {origin_label} ➔ {dest_label} ({mode_label})"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.write(f"**From:** {trip.get('departure_time', '??')} | **To:** {trip.get('arrival_time', '??')}")
                    st.write(f"**Purpose:** {trip.get('purpose', 'Unknown')}")
                with col_t2:
                    st.write(f"**Distance:** {trip.get('distance_km', 0)} km")
                    speed = trip.get('speed_kmh', 0)
                    st.write(f"**Avg Speed:** {speed} km/h")
                    
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
    
    # Address Search
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        origin_addr = st.text_input("Search Origin Address", placeholder="e.g., 10 Downing St, London")
        if st.button("🔍 Find Origin"):
            if origin_addr:
                coords = geocode_address(origin_addr)
                if coords:
                    st.session_state.origin_coord = coords
                    st.success(f"Found: {coords}")
                    st.rerun()
                else:
                    st.error("Address not found.")
            else:
                st.warning("Please enter an address.")

    with col_search2:
        dest_addr = st.text_input("Search Destination Address", placeholder="e.g., Eiffel Tower, Paris")
        if st.button("🔍 Find Destination"):
            if dest_addr:
                coords = geocode_address(dest_addr)
                if coords:
                    st.session_state.dest_coord = coords
                    st.success(f"Found: {coords}")
                    st.rerun()
                else:
                    st.error("Address not found.")
            else:
                st.warning("Please enter an address.")

    selection_mode = st.radio("Select point to place on map manually:", ["Origin", "Destination"], horizontal=True)

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
        dep_str = departure_time.strftime("%H:%M")
        arr_str = arrival_time.strftime("%H:%M")
        
        # 1. Coordinate Validation
        if not st.session_state.origin_coord or not st.session_state.dest_coord:
            st.error("❌ Please select both Origin and Destination on the map.")
        
        # 2. Time Logic Validation
        elif arrival_time <= departure_time:
            st.error("❌ Arrival time must be after the departure time.")
            
        # 3. Overlap Validation
        else:
            is_overlap, overlapping_trip = check_overlap(dep_str, arr_str, st.session_state.trips)
            if is_overlap:
                st.error(f"❌ This trip overlaps with an existing entry ({overlapping_trip['departure_time']} - {overlapping_trip['arrival_time']}).")
            else:
                # 4. Speed Validation
                dist_km, speed_kmh = calculate_trip_stats(
                    st.session_state.origin_coord[0], st.session_state.origin_coord[1],
                    st.session_state.dest_coord[0], st.session_state.dest_coord[1],
                    dep_str, arr_str
                )
                
                # Basic speed thresholds (km/h)
                unrealistic = False
                if travel_mode == "Walk" and speed_kmh > 15: unrealistic = True
                if travel_mode == "Bicycle" and speed_kmh > 50: unrealistic = True
                if travel_mode in ["Car (Driver)", "Car (Passenger)"] and speed_kmh > 180: unrealistic = True
                
                if unrealistic:
                    st.warning(f"⚠️ The calculated speed ({speed_kmh} km/h) seems unrealistic for {travel_mode}. Please check your times and locations.")
                
                # Proceed to add
                trip_entry = {
                    "origin_name": origin_name,
                    "origin_lat": st.session_state.origin_coord[0],
                    "origin_lon": st.session_state.origin_coord[1],
                    "dest_name": destination_name,
                    "dest_lat": st.session_state.dest_coord[0],
                    "dest_lon": st.session_state.dest_coord[1],
                    "departure_time": dep_str,
                    "arrival_time": arr_str,
                    "mode": travel_mode,
                    "purpose": trip_purpose,
                    "distance_km": dist_km,
                    "speed_kmh": speed_kmh
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
    st.subheader("🗺️ Trip Geography & Flows")
    
    # Points for Scatterplot
    origin_df = df[['origin_lat', 'origin_lon']].rename(columns={'origin_lat': 'lat', 'origin_lon': 'lon'})
    origin_df['color'] = '[0, 200, 0, 160]'
    dest_df = df[['dest_lat', 'dest_lon']].rename(columns={'dest_lat': 'lat', 'dest_lon': 'lon'})
    dest_df['color'] = '[200, 0, 0, 160]'
    points_df = pd.concat([origin_df, dest_df])

    # Arcs for Flows
    # Pydeck ArcLayer expects [start_lon, start_lat, end_lon, end_lat]
    # Filter out any None coordinates
    flow_df = df.dropna(subset=['origin_lat', 'origin_lon', 'dest_lat', 'dest_lon'])

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=df['origin_lat'].mean() if not df.empty else DEFAULT_LOCATION[0], 
            longitude=df['origin_lon'].mean() if not df.empty else DEFAULT_LOCATION[1], 
            zoom=11,
            pitch=45
        ),
        layers=[
            # Arcs
            pdk.Layer(
                'ArcLayer',
                data=flow_df,
                get_source_position='[origin_lon, origin_lat]',
                get_target_position='[dest_lon, dest_lat]',
                get_source_color='[0, 200, 0, 80]',
                get_target_color='[200, 0, 0, 80]',
                get_width=2,
            ),
            # Points
            pdk.Layer(
                'ScatterplotLayer',
                data=points_df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=150,
            ),
        ],
    ))

    st.subheader("📄 Raw Data")
    st.dataframe(df)

    # --- Data Export ---
    st.subheader("📥 Export Data")
    col_ex1, col_ex2 = st.columns(2)
    
    with col_ex1:
        st.write("#### Download CSV")
        st.download_button(
            label="Download CSV Responses",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"cats_survey_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    
    with col_ex2:
        st.write("#### Export to GeoJSON (GIS)")
        geojson_data = convert_to_geojson(df)
        st.download_button(
            label="Download GeoJSON Flows",
            data=geojson_data,
            file_name=f"cats_survey_flows_{datetime.now().strftime('%Y%m%d')}.geojson",
            mime='application/json',
        )

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
elif st.session_state.current_page == 'admin_login':
    show_admin_login()
elif st.session_state.current_page == 'admin_dashboard':
    if st.session_state.is_admin_authenticated:
        show_admin_dashboard()
    else:
        navigate_to('admin_login')
        st.rerun()
