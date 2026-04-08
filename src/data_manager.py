import pandas as pd
import os
import json
from datetime import datetime
from .config import CSV_FILE

def save_responses(trips_per_person, demographics, session_id):
    """
    Saves trips for multiple persons with their specific demographics.
    trips_per_person: list of lists of trips.
    demographics: dict containing household info and 'persons_json'.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    persons = json.loads(demographics.get('persons_json', '[]'))
    
    rows = []
    for p_idx, trips in enumerate(trips_per_person):
        if p_idx < len(persons):
            p_demog = persons[p_idx]
            for trip in trips:
                row = trip.copy()
                # Household info
                row['household_size'] = demographics.get('household_size')
                row['household_income'] = demographics.get('household_income')
                row['number_of_cars'] = demographics.get('number_of_cars')
                row['home_lat'] = demographics.get('home_lat')
                row['home_lon'] = demographics.get('home_lon')
                row['home_addr'] = demographics.get('home_addr')
                
                # Person info
                row['person_idx'] = p_idx
                row['age_group'] = p_demog.get('age_group')
                row['gender'] = p_demog.get('gender')
                row['occupation'] = p_demog.get('occupation')
                row['driving_license'] = p_demog.get('driving_license')
                
                row['session_id'] = session_id
                row['submission_timestamp'] = timestamp
                rows.append(row)
    
    if not rows:
        return
        
    new_df = pd.DataFrame(rows)
    
    if not os.path.isfile(CSV_FILE):
        new_df.to_csv(CSV_FILE, index=False)
    else:
        existing_df = pd.read_csv(CSV_FILE, nrows=0)
        # Ensure 'person_idx' exists in existing file or handle merge
        if 'person_idx' not in existing_df.columns:
            full_df = pd.read_csv(CSV_FILE)
            full_df['person_idx'] = 0 # Default for old data
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
        'age_group', 'gender', 'occupation', 'session_id', 'submission_timestamp',
        'household_size', 'household_income', 'number_of_cars', 'home_lat', 'home_lon', 'home_addr',
        'driving_license', 'persons_json', 'person_idx'
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
