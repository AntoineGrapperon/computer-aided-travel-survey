import pandas as pd
import os
import json
from datetime import datetime
from src.config import CSV_FILE

def save_responses(trips, demographics, session_id):
    """Saves multiple trips with demographic data to a local CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rows = []
    for trip in trips:
        row = trip.copy()
        row.update(demographics)
        row['session_id'] = session_id
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
        'origin_name', 'origin_lat', 'origin_lon', 'origin_stop_id',
        'dest_name', 'dest_lat', 'dest_lon', 'dest_stop_id',
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

def check_overlap(new_departure_str, new_arrival_str, existing_trips):
    """Checks if a new trip overlaps with any existing trips in the diary."""
    fmt = "%H:%M"
    try:
        new_start = datetime.strptime(new_departure_str, fmt).time()
        new_end = datetime.strptime(new_arrival_str, fmt).time()
        
        for trip in existing_trips:
            trip_start = datetime.strptime(trip['departure_time'], fmt).time()
            trip_end = datetime.strptime(trip['arrival_time'], fmt).time()
            
            # Standard time overlap check
            if (trip_start < new_end and new_start < trip_end):
                return True, trip
    except Exception:
        pass
            
    return False, None
