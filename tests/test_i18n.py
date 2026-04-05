import sys
from unittest.mock import MagicMock

# Mock streamlit before importing src.i18n
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st

from src.i18n import TRANSLATIONS, t
import pytest

def test_translations_have_all_keys():
    en_keys = set(TRANSLATIONS['en'].keys())
    fr_keys = set(TRANSLATIONS['fr'].keys())
    
    assert en_keys == fr_keys, f"Missing keys in FR: {en_keys - fr_keys}. Missing keys in EN: {fr_keys - en_keys}"

def test_t_function(monkeypatch):
    # Mock streamlit session state
    mock_st.session_state = {'lang': 'en'}
    
    assert t("start_survey") == "Start Survey"
    
    mock_st.session_state['lang'] = 'fr'
    assert t("start_survey") == "Commencer l'enquête"

def test_t_function_with_kwargs(monkeypatch):
    mock_st.session_state = {'lang': 'en'}
    
    assert t("success_saved", count=5) == "All 5 trips have been saved successfully."
