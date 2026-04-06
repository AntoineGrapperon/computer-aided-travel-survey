import pandas as pd
import zipfile
import os
from .config import GTFS_STOPS_FILE

def process_gtfs_zip(uploaded_file):
    """Extracts stops from a GTFS zip file and saves them to a local CSV."""
    try:
        with zipfile.ZipFile(uploaded_file) as z:
            if 'stops.txt' not in z.namelist():
                return False, "GTFS zip must contain stops.txt"
            
            with z.open('stops.txt') as f:
                stops_df = pd.read_csv(f)
                
                # Required columns for our mapping
                required = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
                missing = [col for col in required if col not in stops_df.columns]
                
                if missing:
                    return False, f"stops.txt is missing required columns: {', '.join(missing)}"
                
                # Keep only what we need to save space
                simplified_df = stops_df[required].copy()
                
                # Create directory if missing
                os.makedirs(os.path.dirname(GTFS_STOPS_FILE), exist_ok=True)
                
                simplified_df.to_csv(GTFS_STOPS_FILE, index=False)
                return True, f"Successfully imported {len(simplified_df)} transit stops."
                
    except Exception as e:
        return False, f"Error processing GTFS: {str(e)}"

def load_transit_stops():
    """Loads processed transit stops from local storage."""
    if os.path.exists(GTFS_STOPS_FILE):
        try:
            return pd.read_csv(GTFS_STOPS_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()
