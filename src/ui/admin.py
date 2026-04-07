import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import polyline
from datetime import datetime

from ..config import DEFAULT_LOCATION
from ..i18n import t
from ..auth import check_password
from ..data_manager import load_data, convert_to_geojson
from ..gtfs_manager import process_gtfs_zip
from ..config_manager import load_survey_settings, save_survey_settings
from .common import navigate_to

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

def show_admin_dashboard():
    st.title(t("admin_title"))
    df = load_data()
    
    if df.empty:
        st.info("No survey responses found yet. Analytics and exports will appear here once data is collected.")
    else:
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

    # --- Survey Configuration (Always Visible) ---
    st.divider()
    st.subheader("⚙️ Survey Configuration")
    with st.expander("Manage Survey Categories (Modes, Purposes, Demographics)"):
        settings = load_survey_settings()
        
        st.write("Edit the lists below (one item per line).")
        
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            new_modes_text = st.text_area("Travel Modes", value="\n".join(settings["modes"]), height=150)
            new_age_groups_text = st.text_area("Age Groups", value="\n".join(settings["age_groups"]), height=150)
            new_occupations_text = st.text_area("Occupations / Work Status", value="\n".join(settings["occupations"]), height=150)
        with col_cfg2:
            new_purposes_text = st.text_area("Trip Purposes", value="\n".join(settings["purposes"]), height=150)
            new_genders_text = st.text_area("Gender Options", value="\n".join(settings["genders"]), height=150)
            new_incomes_text = st.text_area("Household Income Brackets", value="\n".join(settings["income_brackets"]), height=150)
            
        if st.button("Save Survey Configuration", type="primary", use_container_width=True):
            def clean_list(text):
                return [x.strip() for x in text.split("\n") if x.strip()]
            
            new_settings = {
                "modes": clean_list(new_modes_text),
                "purposes": clean_list(new_purposes_text),
                "age_groups": clean_list(new_age_groups_text),
                "genders": clean_list(new_genders_text),
                "occupations": clean_list(new_occupations_text),
                "income_brackets": clean_list(new_incomes_text)
            }
            
            if any(not v for v in new_settings.values()):
                st.error("All category lists must contain at least one item.")
            else:
                success, msg = save_survey_settings(new_settings)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # --- GTFS Setup ---
    st.divider()
    st.subheader("🚌 GTFS Network Setup")
    with st.expander("Upload Transit Data (GTFS)"):
        st.write("Upload a city's GTFS .zip file to enable transit stop selection for respondents.")
        gtfs_file = st.file_uploader("Select GTFS Zip", type="zip")
        if gtfs_file:
            success, message = process_gtfs_zip(gtfs_file)
            if success:
                st.success(message)
            else:
                st.error(message)
