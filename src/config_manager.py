import json
import os
from src.config import SURVEY_SETTINGS_FILE

DEFAULT_MODES = ["Walk", "Bicycle", "Car (Driver)", "Car (Passenger)", "Public Transit", "Motorcycle", "Other"]
DEFAULT_PURPOSES = ["Work", "Education", "Shopping", "Social/Leisure", "Personal Business", "Other"]

def load_survey_settings():
    """Loads survey settings (modes and purposes) from local storage."""
    if os.path.exists(SURVEY_SETTINGS_FILE):
        try:
            with open(SURVEY_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return (
                    settings.get("modes", DEFAULT_MODES),
                    settings.get("purposes", DEFAULT_PURPOSES)
                )
        except Exception:
            pass
    return DEFAULT_MODES, DEFAULT_PURPOSES

def save_survey_settings(modes, purposes):
    """Saves survey settings to local storage."""
    settings = {
        "modes": modes,
        "purposes": purposes
    }
    try:
        os.makedirs(os.path.dirname(SURVEY_SETTINGS_FILE), exist_ok=True)
        with open(SURVEY_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True, "Settings saved successfully."
    except Exception as e:
        return False, f"Error saving settings: {str(e)}"
