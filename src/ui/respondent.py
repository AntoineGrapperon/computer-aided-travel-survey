import streamlit as st
import uuid
import folium
import polyline
import json
from datetime import datetime, time
from streamlit_folium import st_folium

from ..config import DEFAULT_LOCATION
from ..i18n import t
from ..data_manager import save_responses, check_overlap
from ..geo_utils import geocode_address, get_osrm_route, calculate_trip_stats
from ..gtfs_manager import load_transit_stops
from ..config_manager import load_survey_settings
from .common import navigate_to

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
    
    # Load survey settings
    settings = load_survey_settings()
    
    if 'demographic_persons' not in st.session_state:
        st.session_state.demographic_persons = [{
            "age_group": settings["age_groups"][min(2, len(settings["age_groups"])-1)],
            "gender": settings["genders"][0],
            "occupation": settings["occupations"][min(1, len(settings["occupations"])-1)],
            "driving_license": "Yes"
        }]
    
    if 'home_coord' not in st.session_state:
        st.session_state.home_coord = None
    if 'home_addr' not in st.session_state:
        st.session_state.home_addr = ""

    with st.expander(t("household_section"), expanded=True):
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            # Household size drives the number of persons
            current_p_count = len(st.session_state.demographic_persons)
            h_size = st.number_input(t("household_size"), min_value=1, max_value=20, value=current_p_count, key="h_size_input")
            
            # Sync demographic_persons with h_size
            if h_size > current_p_count:
                for _ in range(h_size - current_p_count):
                    st.session_state.demographic_persons.append({
                        "age_group": settings["age_groups"][min(2, len(settings["age_groups"])-1)], 
                        "gender": settings["genders"][0], 
                        "occupation": settings["occupations"][min(1, len(settings["occupations"])-1)], 
                        "driving_license": "Yes"
                    })
            elif h_size < current_p_count:
                st.session_state.demographic_persons = st.session_state.demographic_persons[:h_size]
        
        with col_h2:
            h_cars = st.number_input(t("number_of_cars"), min_value=0, max_value=10, value=1)

    with st.form("demographics_form"):
        # --- Income & Home ---
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            h_income = st.selectbox(t("household_income"), settings["income_brackets"])
        with col_i2:
            home_search = st.text_input("Home Address Search", placeholder="e.g., 10 Rue de Rivoli, Paris")

        # --- Persons Section ---
        st.subheader(t("persons_section"))
        
        updated_persons = []
        for i in range(len(st.session_state.demographic_persons)):
            p = st.session_state.demographic_persons[i]
            is_resp = t("is_respondent") if i == 0 else ""
            st.markdown(f"**{t('person_number', number=i+1)} {is_resp}**")
            
            c1, c2 = st.columns(2)
            with c1:
                # Use current value if possible, else index 2
                age_idx = 0
                if p["age_group"] in settings["age_groups"]:
                    age_idx = settings["age_groups"].index(p["age_group"])
                elif len(settings["age_groups"]) > 2:
                    age_idx = 2
                
                age = st.selectbox(t("age_group"), settings["age_groups"], index=age_idx, key=f"p_age_{i}")
                gender = st.selectbox(t("gender"), settings["genders"], key=f"p_gen_{i}")
            with c2:
                occ = st.selectbox(t("occupation"), settings["occupations"], key=f"p_occ_{i}")
                license = st.selectbox(t("driving_license"), ["Yes", "No"], key=f"p_lic_{i}")
            
            updated_persons.append({
                "age_group": age,
                "gender": gender,
                "occupation": occ,
                "driving_license": license
            })
            if i < len(st.session_state.demographic_persons) - 1:
                st.divider()

        submitted = st.form_submit_button(t("cont_to_diary"), type="primary", use_container_width=True)

    if submitted:
        # Geocode home address if provided and not already set
        if home_search and not st.session_state.home_coord:
            coords = geocode_address(home_search)
            if coords:
                st.session_state.home_coord = coords
                st.session_state.home_addr = home_search

        # Save to demographics
        resp = updated_persons[0]
        st.session_state.demographics = {
            "household_size": h_size,
            "household_income": h_income,
            "number_of_cars": h_cars,
            "home_lat": st.session_state.home_coord[0] if st.session_state.home_coord else None,
            "home_lon": st.session_state.home_coord[1] if st.session_state.home_coord else None,
            "home_addr": st.session_state.home_addr,
            "age_group": resp["age_group"],
            "gender": resp["gender"],
            "occupation": resp["occupation"],
            "driving_license": resp["driving_license"],
            "persons_json": json.dumps(updated_persons)
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

    # Load custom settings
    settings = load_survey_settings()
    mode_options = settings["modes"]
    purpose_options = settings["purposes"]

    # Define travel_mode early to avoid NameError
    travel_mode = st.session_state.get("last_selected_mode", mode_options[0])

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
    
    # --- GTFS Integration ---
    if travel_mode == "Public Transit":
        stops_df = load_transit_stops()
        if not stops_df.empty:
            # Add stops to map as small circles/markers
            for _, stop in stops_df.iterrows():
                # Check if this stop is already selected as origin or destination
                is_selected = False
                color = "blue"
                if st.session_state.origin_stop_id == stop['stop_id']:
                    is_selected = True
                    color = "green"
                elif st.session_state.dest_stop_id == stop['stop_id']:
                    is_selected = True
                    color = "red"
                
                folium.CircleMarker(
                    location=[stop['stop_lat'], stop['stop_lon']],
                    radius=5,
                    popup=f"Stop: {stop['stop_name']} ({stop['stop_id']})",
                    color=color,
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)

    route_coords = None
    osrm_dist = None
    route_poly = None
    
    if st.session_state.origin_coord and st.session_state.dest_coord:
        # Fetch route
        with st.spinner("Calculating route..."):
            route_coords, osrm_dist, route_poly = get_osrm_route(
                st.session_state.origin_coord, 
                st.session_state.dest_coord, 
                travel_mode
            )
            if route_coords:
                folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)
                # Zoom to fit route
                m.fit_bounds([st.session_state.origin_coord, st.session_state.dest_coord])

    if st.session_state.origin_coord:
        folium.Marker(st.session_state.origin_coord, popup="Origin", icon=folium.Icon(color='green', icon='play')).add_to(m)
    if st.session_state.dest_coord:
        folium.Marker(st.session_state.dest_coord, popup="Destination", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    output = st_folium(m, width="100%", height=300)

    # --- Click & Map Logic ---
    if output.get("last_clicked"):
        lat, lng = output["last_clicked"]["lat"], output["last_clicked"]["lng"]
        
        picked_stop = None
        if travel_mode == "Public Transit":
            stops_df = load_transit_stops()
            if not stops_df.empty:
                stops_df['dist'] = ((stops_df['stop_lat'] - lat)**2 + (stops_df['stop_lon'] - lng)**2)**0.5
                closest = stops_df.nsmallest(1, 'dist').iloc[0]
                if closest['dist'] < 0.001: 
                    picked_stop = closest

        if selection_mode == "Origin":
            if picked_stop is not None:
                st.session_state.origin_coord = [picked_stop['stop_lat'], picked_stop['stop_lon']]
                st.session_state.origin_stop_id = picked_stop['stop_id']
            else:
                if st.session_state.origin_coord != [lat, lng]:
                    st.session_state.origin_coord = [lat, lng]
                    st.session_state.origin_stop_id = None
            st.rerun()
        else:
            if picked_stop is not None:
                st.session_state.dest_coord = [picked_stop['stop_lat'], picked_stop['stop_lon']]
                st.session_state.dest_stop_id = picked_stop['stop_id']
            else:
                if st.session_state.dest_coord != [lat, lng]:
                    st.session_state.dest_coord = [lat, lng]
                    st.session_state.dest_stop_id = None
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

        # We use a key to store the mode in session state so the map logic can access it on the next run
        travel_mode = st.selectbox(t("how_travel"), options=mode_options, key="last_selected_mode")
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
                _, final_dist, final_poly = get_osrm_route(
                    st.session_state.origin_coord, 
                    st.session_state.dest_coord, 
                    travel_mode
                )
                
                if final_dist is None:
                    final_dist, _ = calculate_trip_stats(
                        st.session_state.origin_coord[0], st.session_state.origin_coord[1],
                        st.session_state.dest_coord[0], st.session_state.dest_coord[1],
                        dep_str, arr_str
                    )
                
                fmt = "%H:%M"
                start = datetime.strptime(dep_str, fmt)
                end = datetime.strptime(arr_str, fmt)
                dur_hrs = (end - start).total_seconds() / 3600.0
                final_speed = round(final_dist / dur_hrs, 1) if dur_hrs > 0 else 0
                
                trip_entry = {
                    "origin_name": origin_name,
                    "origin_lat": st.session_state.origin_coord[0],
                    "origin_lon": st.session_state.origin_coord[1],
                    "origin_stop_id": st.session_state.origin_stop_id,
                    "dest_name": destination_name,
                    "dest_lat": st.session_state.dest_coord[0],
                    "dest_lon": st.session_state.dest_coord[1],
                    "dest_stop_id": st.session_state.dest_stop_id,
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
                st.session_state.origin_stop_id = None
                st.session_state.dest_stop_id = None
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
