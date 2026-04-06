import streamlit as st

def navigate_to(page):
    """Updates the current page in session state."""
    st.session_state.current_page = page
