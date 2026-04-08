import streamlit as st
import uuid
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Custom Modules
from src.i18n import t
from src.ui import (
    navigate_to,
    show_landing_page,
    show_demographics_form,
    show_trip_diary,
    show_trip_form,
    show_success_page,
    show_admin_login,
    show_admin_dashboard
)

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

if 'current_person_idx' not in st.session_state:
    st.session_state.current_person_idx = 0

if 'demographics' not in st.session_state:
    st.session_state.demographics = {}

if 'origin_coord' not in st.session_state:
    st.session_state.origin_coord = None

if 'dest_coord' not in st.session_state:
    st.session_state.dest_coord = None

if 'origin_stop_id' not in st.session_state:
    st.session_state.origin_stop_id = None

if 'dest_stop_id' not in st.session_state:
    st.session_state.dest_stop_id = None

if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

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
