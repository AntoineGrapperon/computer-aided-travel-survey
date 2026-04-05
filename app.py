import streamlit as st
import pandas as pd
import folium
import plotly.express as px
import pydeck as pdk
import uuid
import polyline
from streamlit_folium import st_folium
from datetime import datetime, time

# Custom Modules
from src.config import DEFAULT_LOCATION
from src.i18n import t
from src.auth import check_password
from src.data_manager import save_responses, load_data, convert_to_geojson, check_overlap
from src.geo_utils import geocode_address, get_osrm_route, calculate_trip_stats

# Set page configuration
st.set_page_config(
    page_title="CATS - City Travel Survey",
    page_icon="🏙️",
    layout="wide"
)

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

if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

def navigate_to(page):
    st.session_state.current_page = page

# --- Navigation (Sidebar) ---
with st.sidebar:
    st.title("🏙️ CATS")
    
    # Language Selector
    lang_options = ["English", "Français"]
    current_lang_idx = 0 if st.session_state.lang == "en" else 1
    lang = st.selectbox("🌐 Language / Langue", lang_options, index=current_lang_idx)
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
            if check_password(password):
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
                save_responses(st.session_state.trips, st.session_state.demographics, st.session_state.session_id)
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
                "Car" 
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
