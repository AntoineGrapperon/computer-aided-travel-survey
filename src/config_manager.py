import json
import os
from .config import SURVEY_SETTINGS_FILE

DEFAULT_MODES = ["Walk", "Bicycle", "Car (Driver)", "Car (Passenger)", "Public Transit", "Motorcycle", "Other"]
DEFAULT_PURPOSES = ["Work", "Education", "Shopping", "Social/Leisure", "Personal Business", "Other"]
DEFAULT_AGE_GROUPS = ["Under 18", "18-24", "25-44", "45-64", "65+"]
DEFAULT_GENDERS = ["Woman", "Man", "Non-binary", "Prefer not to say"]
DEFAULT_OCCUPATIONS = ["Student", "Employed", "Self-employed", "Retired", "Unemployed", "Other"]
DEFAULT_INCOMES = ["Under €20,000", "€20,000 - €40,000", "€40,000 - €60,000", "€60,000 - €100,000", "Over €100,000", "Prefer not to say"]

def load_survey_settings():
    """Loads all survey settings from local storage."""
    if os.path.exists(SURVEY_SETTINGS_FILE):
        try:
            with open(SURVEY_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return {
                    "modes": settings.get("modes", DEFAULT_MODES),
                    "purposes": settings.get("purposes", DEFAULT_PURPOSES),
                    "age_groups": settings.get("age_groups", DEFAULT_AGE_GROUPS),
                    "genders": settings.get("genders", DEFAULT_GENDERS),
                    "occupations": settings.get("occupations", DEFAULT_OCCUPATIONS),
                    "income_brackets": settings.get("income_brackets", DEFAULT_INCOMES)
                }
        except Exception:
            pass
    return {
        "modes": DEFAULT_MODES,
        "purposes": DEFAULT_PURPOSES,
        "age_groups": DEFAULT_AGE_GROUPS,
        "genders": DEFAULT_GENDERS,
        "occupations": DEFAULT_OCCUPATIONS,
        "income_brackets": DEFAULT_INCOMES
    }

def save_survey_settings(settings_dict):
    """Saves survey settings to local storage."""
    try:
        os.makedirs(os.path.dirname(SURVEY_SETTINGS_FILE), exist_ok=True)
        with open(SURVEY_SETTINGS_FILE, 'w') as f:
            json.dump(settings_dict, f, indent=2)
        return True, "Settings saved successfully."
    except Exception as e:
        return False, f"Error saving settings: {str(e)}"
