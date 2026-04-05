import streamlit as st
import pandas as pd
import os
import folium
import plotly.express as px
import pydeck as pdk
import uuid
import json
import requests
import polyline
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

# Multilingual Support
TRANSLATIONS = {
    "en": {
        "landing_title": "🏙️ Welcome to the City Travel Survey",
        "landing_desc": "Thank you for participating in our effort to improve urban mobility. By sharing your daily travel habits, you help us design better infrastructure.",
        "how_it_works": "### How it works:",
        "step_1": "1. Tell us a bit about yourself (optional demographics).",
        "step_2": "2. Log all your trips for a single 24-hour period.",
        "step_3": "3. Review and submit your Trip Diary.",
        "anonymized": "*Your data is anonymized and used exclusively for city planning purposes.*",
        "start_survey": "Start Survey",
        "about_you_title": "👤 About You",
        "about_you_desc": "This information helps us understand who is traveling and how.",
        "age_group": "Age Group",
        "gender": "Gender",
        "occupation": "Primary Occupation",
        "cont_to_diary": "Continue to Trip Diary",
        "diary_title": "📋 Your Trip Diary",
        "diary_desc": "Please log all trips you made yesterday (or on a typical travel day).",
        "logged_trips": "Logged Trips",
        "no_trips": "No trips logged yet. Click 'Add a Trip' to begin.",
        "add_trip": "➕ Add a Trip",
        "finish_submit": "🏁 Finish and Submit All Trips",
        "record_trip_title": "🚆 Record a Trip",
        "record_trip_desc": "Select your travel points on the map, then fill in the details.",
        "where_go": "1. Where did you go?",
        "search_orig": "Search Origin Address",
        "search_dest": "Search Destination Address",
        "find_orig": "🔍 Find Origin",
        "find_dest": "🔍 Find Destination",
        "select_map_manual": "Select point to place on map manually:",
        "orig_set": "✅ Origin Set",
        "dest_set": "✅ Destination Set",
        "click_orig": "📍 Click map to set Origin",
        "click_dest": "📍 Click map to set Destination",
        "trip_details": "2. Trip Details",
        "orig_name": "Origin Name",
        "dest_name": "Destination Name",
        "dep_time": "Departure Time",
        "arr_time": "Arrival Time",
        "how_travel": "How did you travel?",
        "trip_purpose": "What was the purpose of this trip?",
        "add_to_diary": "Add Trip to Diary",
        "cancel_back": "Cancel - Back to Diary",
        "success_thanks": "✅ Thank You!",
        "success_saved": "All {count} trips have been saved successfully.",
        "success_city": "Thank you for contributing to your city's planning efforts!",
        "new_diary": "Start a New Diary",
        "admin_title": "📊 Admin Analytics Dashboard",
        "key_metrics": "📈 Key Metrics",
        "total_trips": "Total Trips",
        "total_sessions": "Total Sessions",
        "avg_trips": "Avg Trips/User",
        "common_mode": "Most Common Mode",
        "travel_behavior": "🚲 Travel Behavior",
        "modal_split": "Modal Split",
        "trip_purpose_chart": "Trip Purpose",
        "demographics_chart": "👤 Demographics",
        "age_dist": "Age Group Distribution",
        "occ_dist": "Occupation Distribution",
        "trip_geography": "🗺️ Trip Geography & Flows",
        "raw_data": "📄 Raw Data",
        "export_data": "📥 Export Data",
        "download_csv": "Download CSV Responses",
        "export_geojson": "Export to GeoJSON (GIS)",
        "admin_login": "🔒 Admin Access",
        "password": "Password",
        "login": "Log In",
        "logout": "🔓 Logout Admin"
    },
    "fr": {
        "landing_title": "🏙️ Bienvenue à l'enquête sur les déplacements urbains",
        "landing_desc": "Merci de participer à notre effort pour améliorer la mobilité urbaine. En partageant vos habitudes de voyage, vous nous aidez à concevoir de meilleures infrastructures.",
        "how_it_works": "### Comment ça marche :",
        "step_1": "1. Parlez-nous un peu de vous (démographie facultative).",
        "step_2": "2. Enregistrez tous vos trajets pour une période de 24 heures.",
        "step_3": "3. Vérifiez et soumettez votre carnet de voyage.",
        "anonymized": "*Vos données sont anonymisées et utilisées exclusivement à des fins de planification urbaine.*",
        "start_survey": "Commencer l'enquête",
        "about_you_title": "👤 À propos de vous",
        "about_you_desc": "Ces informations nous aident à comprendre qui se déplace et comment.",
        "age_group": "Groupe d'âge",
        "gender": "Genre",
        "occupation": "Occupation principale",
        "cont_to_diary": "Continuer vers le carnet de voyage",
        "diary_title": "📋 Votre carnet de voyage",
        "diary_desc": "Veuillez enregistrer tous les trajets que vous avez effectués hier (ou lors d'une journée de voyage typique).",
        "logged_trips": "Trajets enregistrés",
        "no_trips": "Aucun trajet enregistré. Cliquez sur 'Ajouter un trajet' pour commencer.",
        "add_trip": "➕ Ajouter un trajet",
        "finish_submit": "🏁 Terminer et soumettre tous les trajets",
        "record_trip_title": "🚆 Enregistrer un trajet",
        "record_trip_desc": "Sélectionnez vos points de voyage sur la carte, puis remplissez les détails.",
        "where_go": "1. Où êtes-vous allé ?",
        "search_orig": "Rechercher l'adresse d'origine",
        "search_dest": "Rechercher l'adresse de destination",
        "find_orig": "🔍 Trouver l'origine",
        "find_dest": "🔍 Trouver la destination",
        "select_map_manual": "Sélectionnez manuellement le point sur la carte :",
        "orig_set": "✅ Origine définie",
        "dest_set": "✅ Destination définie",
        "click_orig": "📍 Cliquez sur la carte pour définir l'origine",
        "click_dest": "📍 Cliquez sur la carte pour définir la destination",
        "trip_details": "2. Détails du trajet",
        "orig_name": "Nom de l'origine",
        "dest_name": "Nom de la destination",
        "dep_time": "Heure de départ",
        "arr_time": "Heure d'arrivée",
        "how_travel": "Comment avez-vous voyagé ?",
        "trip_purpose": "Quel était le but de ce trajet ?",
        "add_to_diary": "Ajouter le trajet au carnet",
        "cancel_back": "Annuler - Retour au carnet",
        "success_thanks": "✅ Merci !",
        "success_saved": "Tous les {count} trajets ont été enregistrés avec succès.",
        "success_city": "Merci de contribuer aux efforts de planification de votre ville !",
        "new_diary": "Commencer un nouveau carnet",
        "admin_title": "📊 Tableau de bord analytique",
        "key_metrics": "📈 Métriques clés",
        "total_trips": "Total des trajets",
        "total_sessions": "Total des sessions",
        "avg_trips": "Moy. trajets/utilisateur",
        "common_mode": "Mode le plus courant",
        "travel_behavior": "🚲 Comportement de voyage",
        "modal_split": "Répartition modale",
        "trip_purpose_chart": "But du trajet",
        "demographics_chart": "👤 Démographie",
        "age_dist": "Répartition par groupe d'âge",
        "occ_dist": "Répartition par occupation",
        "trip_geography": "🗺️ Géographie et flux des trajets",
        "raw_data": "📄 Données brutes",
        "export_data": "📥 Exporter les données",
        "download_csv": "Télécharger les réponses CSV",
        "export_geojson": "Exporter vers GeoJSON (GIS)",
        "admin_login": "🔒 Accès administrateur",
        "password": "Mot de passe",
        "login": "Se connecter",
        "logout": "🔓 Se déconnecter Admin"
    }
}

def t(key, **kwargs):
    """Helper function to get translated text."""
    lang = st.session_state.get('lang', 'en')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

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

def get_osrm_route(origin, dest, mode):
    """Fetches route from OSRM public API."""
    # Map travel mode to OSRM profile
    profile = "car"
    if mode == "Walk": profile = "foot"
    elif mode == "Bicycle": profile = "cycling"
    
    # OSRM expects [lon, lat]
    url = f"http://router.project-osrm.org/route/v1/{profile}/{origin[1]},{origin[0]};{dest[1]},{dest[0]}?overview=full&geometries=polyline"
    
    try:
        r = requests.get(url)
        data = r.json()
        if data.get("code") == "Ok":
            route = data["routes"][0]
            geometry = route["geometry"]
            distance_m = route["distance"]
            # Decode polyline to list of [lat, lon]
            coords = polyline.decode(geometry)
            return coords, round(distance_m / 1000.0, 2), geometry
    except Exception as e:
        st.warning(f"Routing error: {e}")
    
    return None, None, None

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
        'distance_km', 'speed_kmh', 'route_polyline',
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
    st.title("🏙️ CATS")
    
    # Language Selector
    lang = st.selectbox("🌐 Language / Langue", ["English", "Français"], index=0)
    st.session_state.lang = "en" if lang == "English" else "fr"
    
    st.divider()
    
    app_mode = st.radio("Menu", ["Respondent (Survey)", "Admin (Dashboard)"])
    
    if app_mode == "Respondent (Survey)":
        # Progress Bar for Survey
        pages = ['landing', 'demographics_form', 'trip_diary', 'trip_form', 'success_page']
        if st.session_state.current_page in pages:
            idx = pages.index(st.session_state.current_page)
            st.progress((idx + 1) / len(pages))
            
        if st.session_state.current_page == 'admin_dashboard' or st.session_state.current_page == 'admin_login':
            navigate_to('landing')
    else:
        # Check authentication for Admin mode
        if not st.session_state.is_admin_authenticated:
            navigate_to('admin_login')
        else:
            navigate_to('admin_dashboard')
            if st.button(t("logout")):
                st.session_state.is_admin_authenticated = False
                navigate_to('landing')
                st.rerun()

# --- Pages ---

def show_admin_login():
    st.title(t("admin_login"))
    st.write(t("admin_login_desc", default="Please enter the administrative password."))
    
    with st.form("login_form"):
        password = st.text_input(t("password"), type="password")
        submitted = st.form_submit_button(t("login"))
        
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.is_admin_authenticated = True
                st.success("Authenticated!")
                navigate_to('admin_dashboard')
                st.rerun()
            else:
                st.error("Incorrect password.")
    
    if st.button("Back to Survey"):
        navigate_to('landing')
        st.rerun()

def show_landing_page():
    st.title(t("landing_title"))
    st.markdown(f"""
    {t("landing_desc")}

    {t("how_it_works")}
    {t("step_1")}
    {t("step_2")}
    {t("step_3")}

    {t("anonymized")}
    """)
    
    if st.button(t("start_survey"), type="primary", use_container_width=True):
        navigate_to('demographics_form')
        st.rerun()

def show_demographics_form():
    st.title(t("about_you_title"))
    st.write(t("about_you_desc"))
    
    with st.form("demographics_form"):
        age_group = st.selectbox(t("age_group"), ["Under 18", "18-24", "25-44", "45-64", "65+"])
        gender = st.selectbox(t("gender"), ["Woman", "Man", "Non-binary", "Prefer not to say"])
        occupation = st.selectbox(t("occupation"), ["Student", "Employed", "Self-employed", "Retired", "Unemployed", "Other"])
        
        submitted = st.form_submit_button(t("cont_to_diary"), type="primary", use_container_width=True)
        
    if submitted:
        st.session_state.demographics = {
            "age_group": age_group,
            "gender": gender,
            "occupation": occupation
        }
        navigate_to('trip_diary')
        st.rerun()

def show_trip_diary():
    st.title(t("diary_title"))
    st.write(t("diary_desc"))
    
    if st.session_state.trips:
        st.subheader(t("logged_trips"))
        for i, trip in enumerate(st.session_state.trips):
            origin_label = trip.get('origin_name') or "Unknown Origin"
            dest_label = trip.get('destination_name') or "Unknown Destination"
            mode_label = trip.get('mode') or "Unknown Mode"
            
            with st.expander(f"Trip {i+1}: {origin_label} ➔ {dest_label} ({mode_label})"):
                col_t1, col_t2 = st.columns([2, 1])
                with col_t1:
                    st.write(f"**From:** {trip.get('departure_time', '??')} | **To:** {trip.get('arrival_time', '??')}")
                    st.write(f"**Purpose:** {trip.get('purpose', 'Unknown')}")
                with col_t2:
                    st.write(f"**Dist:** {trip.get('distance_km', 0)} km")
                    st.write(f"**Speed:** {trip.get('speed_kmh', 0)} km/h")
                    
                if st.button(f"🗑️ Remove", key=f"remove_{i}", use_container_width=True):
                    st.session_state.trips.pop(i)
                    st.rerun()
    else:
        st.info(t("no_trips"))
        
    st.divider()
    if st.button(t("add_trip"), type="primary", use_container_width=True):
        navigate_to('trip_form')
        st.rerun()
            
    if st.session_state.trips:
        if st.button(t("finish_submit"), type="secondary", use_container_width=True):
            try:
                save_responses(st.session_state.trips, st.session_state.demographics)
                navigate_to('success_page')
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

def show_trip_form():
    st.title(t("record_trip_title"))
    st.write(t("record_trip_desc"))

    # --- Mapping Section ---
    st.subheader(t("where_go"))
    
    # Address Search (Responsive columns)
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        origin_addr = st.text_input(t("search_orig"), placeholder="e.g., Gare du Nord, Paris")
        if st.button(t("find_orig"), use_container_width=True):
            if origin_addr:
                coords = geocode_address(origin_addr)
                if coords:
                    st.session_state.origin_coord = coords
                    st.rerun()
                else:
                    st.error("Not found.")

    with col_search2:
        dest_addr = st.text_input(t("search_dest"), placeholder="e.g., Louvre, Paris")
        if st.button(t("find_dest"), use_container_width=True):
            if dest_addr:
                coords = geocode_address(dest_addr)
                if coords:
                    st.session_state.dest_coord = coords
                    st.rerun()
                else:
                    st.error("Not found.")

    selection_mode = st.radio(t("select_map_manual"), ["Origin", "Destination"], horizontal=True)

    # Use a slightly smaller map for mobile compatibility
    m = folium.Map(location=DEFAULT_LOCATION, zoom_start=12)
    
    route_coords = None
    osrm_dist = None
    route_poly = None
    
    if st.session_state.origin_coord and st.session_state.dest_coord:
        # Fetch route
        with st.spinner("Calculating route..."):
            route_coords, osrm_dist, route_poly = get_osrm_route(
                st.session_state.origin_coord, 
                st.session_state.dest_coord, 
                "Car" # Default for map preview or use a session state if available
            )
            if route_coords:
                folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)
                # Zoom to fit route
                m.fit_bounds([st.session_state.origin_coord, st.session_state.dest_coord])

    if st.session_state.origin_coord:
        folium.Marker(st.session_state.origin_coord, popup="Origin", icon=folium.Icon(color='green', icon='play')).add_to(m)
    if st.session_state.dest_coord:
        folium.Marker(st.session_state.dest_coord, popup="Destination", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    output = st_folium(m, width="100%", height=300) # Reduced height for mobile

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
        if st.session_state.origin_coord: st.success(t("orig_set"))
        else: st.info(t("click_orig"))
    with col_d:
        if st.session_state.dest_coord: st.success(t("dest_set"))
        else: st.info(t("click_dest"))

    # --- Details Section ---
    st.subheader(t("trip_details"))
    with st.form("trip_details_form"):
        origin_name = st.text_input(t("orig_name"), placeholder="e.g., Home")
        destination_name = st.text_input(t("dest_name"), placeholder="e.g., Work")

        col_time1, col_time2 = st.columns(2)
        with col_time1:
            departure_time = st.time_input(t("dep_time"), value=time(8, 0))
        with col_time2:
            arrival_time = st.time_input(t("arr_time"), value=time(8, 30))

        mode_options = ["Walk", "Bicycle", "Car (Driver)", "Car (Passenger)", "Public Transit", "Motorcycle", "Other"]
        travel_mode = st.selectbox(t("how_travel"), options=mode_options)

        purpose_options = ["Work", "Education", "Shopping", "Social/Leisure", "Personal Business", "Other"]
        trip_purpose = st.selectbox(t("trip_purpose"), options=purpose_options)

        submitted = st.form_submit_button(t("add_to_diary"), type="primary", use_container_width=True)

    if submitted:
        dep_str = departure_time.strftime("%H:%M")
        arr_str = arrival_time.strftime("%H:%M")
        
        if not st.session_state.origin_coord or not st.session_state.dest_coord:
            st.error("❌ " + t("click_orig") + " / " + t("click_dest"))
        elif arrival_time <= departure_time:
            st.error("❌ " + t("arr_time") + " <= " + t("dep_time"))
        else:
            is_overlap, overlapping_trip = check_overlap(dep_str, arr_str, st.session_state.trips)
            if is_overlap:
                st.error(f"❌ Overlap: {overlapping_trip['departure_time']} - {overlapping_trip['arrival_time']}")
            else:
                # Get final route stats based on selected mode
                _, final_dist, final_poly = get_osrm_route(
                    st.session_state.origin_coord, 
                    st.session_state.dest_coord, 
                    travel_mode
                )
                
                # Fallback to geodesic if routing fails
                if final_dist is None:
                    final_dist, _ = calculate_trip_stats(
                        st.session_state.origin_coord[0], st.session_state.origin_coord[1],
                        st.session_state.dest_coord[0], st.session_state.dest_coord[1],
                        dep_str, arr_str
                    )
                
                # Recalculate speed with final distance
                fmt = "%H:%M"
                start = datetime.strptime(dep_str, fmt)
                end = datetime.strptime(arr_str, fmt)
                dur_hrs = (end - start).total_seconds() / 3600.0
                final_speed = round(final_dist / dur_hrs, 1) if dur_hrs > 0 else 0
                
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
                    "distance_km": final_dist,
                    "speed_kmh": final_speed,
                    "route_polyline": final_poly
                }
                st.session_state.trips.append(trip_entry)
                st.session_state.origin_coord = None
                st.session_state.dest_coord = None
                navigate_to('trip_diary')
                st.rerun()

    if st.button(t("cancel_back"), use_container_width=True):
        navigate_to('trip_diary')
        st.rerun()

def show_success_page():
    st.balloons()
    st.title(t("success_thanks"))
    st.success(t("success_saved", count=len(st.session_state.trips)))
    
    st.write(t("success_city"))

    if st.button(t("new_diary"), use_container_width=True):
        st.session_state.trips = []
        st.session_state.demographics = {}
        st.session_state.session_id = str(uuid.uuid4())
        navigate_to('landing')
        st.rerun()

def show_admin_dashboard():
    st.title(t("admin_title"))
    df = load_data()
    
    if df.empty:
        st.warning("No survey responses found yet.")
        return

    # --- Metrics ---
    st.subheader(t("key_metrics"))
    col1, col2 = st.columns(2)
    with col1:
        st.metric(t("total_trips"), len(df))
        st.metric(t("total_sessions"), df['session_id'].nunique())
    with col2:
        st.metric(t("avg_trips"), f"{len(df) / df['session_id'].nunique():.1f}")
        st.metric(t("common_mode"), df['mode'].mode()[0])

    # --- Charts ---
    st.subheader(t("travel_behavior"))
    
    st.write(f"#### {t('modal_split')}")
    fig_mode = px.pie(df, names='mode', hole=0.4)
    st.plotly_chart(fig_mode, use_container_width=True)
    
    st.write(f"#### {t('trip_purpose_chart')}")
    fig_purpose = px.bar(df['purpose'].value_counts())
    st.plotly_chart(fig_purpose, use_container_width=True)

    st.subheader(t("demographics_chart"))
    st.write(f"#### {t('age_dist')}")
    fig_age = px.pie(df.drop_duplicates('session_id'), names='age_group')
    st.plotly_chart(fig_age, use_container_width=True)
    
    st.write(f"#### {t('occ_dist')}")
    fig_occ = px.bar(df.drop_duplicates('session_id')['occupation'].value_counts())
    st.plotly_chart(fig_occ, use_container_width=True)

    # --- Mapping ---
    st.subheader(t("trip_geography"))
    
    # Points for Scatterplot
    origin_df = df[['origin_lat', 'origin_lon']].rename(columns={'origin_lat': 'lat', 'origin_lon': 'lon'})
    origin_df['color'] = '[0, 200, 0, 160]'
    dest_df = df[['dest_lat', 'dest_lon']].rename(columns={'dest_lat': 'lat', 'dest_lon': 'lon'})
    dest_df['color'] = '[200, 0, 0, 160]'
    points_df = pd.concat([origin_df, dest_df])

    # Arcs & Paths for Flows
    flow_df = df.dropna(subset=['origin_lat', 'origin_lon', 'dest_lat', 'dest_lon'])
    
    # Prepare Path data (decode polylines)
    paths = []
    for _, row in flow_df.iterrows():
        if pd.notna(row['route_polyline']):
            try:
                # Decode and swap lat/lon for Pydeck [lon, lat]
                coords = polyline.decode(row['route_polyline'])
                path = [[c[1], c[0]] for c in coords]
                paths.append({
                    "path": path,
                    "mode": row['mode'],
                    "color": [0, 100, 255, 150]
                })
            except:
                pass

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=df['origin_lat'].mean() if not df.empty else DEFAULT_LOCATION[0], 
            longitude=df['origin_lon'].mean() if not df.empty else DEFAULT_LOCATION[1], 
            zoom=10,
            pitch=45
        ),
        layers=[
            # Estimated Paths
            pdk.Layer(
                'PathLayer',
                data=paths,
                get_path='path',
                get_color='color',
                width_min_pixels=3,
            ),
            # Arcs (Fallback or for context)
            pdk.Layer(
                'ArcLayer',
                data=flow_df[flow_df['route_polyline'].isna()],
                get_source_position='[origin_lon, origin_lat]',
                get_target_position='[dest_lon, dest_lat]',
                get_source_color='[0, 200, 0, 80]',
                get_target_color='[200, 0, 0, 80]',
                get_width=2,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=points_df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=150,
            ),
        ],
    ))

    st.subheader(t("raw_data"))
    st.dataframe(df)

    # --- Data Export ---
    st.subheader(t("export_data"))
    st.download_button(
        label=t("download_csv"),
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"cats_survey_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )
    
    geojson_data = convert_to_geojson(df)
    st.download_button(
        label=t("export_geojson"),
        data=geojson_data,
        file_name=f"cats_survey_flows_{datetime.now().strftime('%Y%m%d')}.geojson",
        mime='application/json',
        use_container_width=True
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
