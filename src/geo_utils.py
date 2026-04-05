import requests
import polyline
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from datetime import datetime

# Initialize Geocoder
geolocator = Nominatim(user_agent="cats_travel_survey_app")

def geocode_address(address):
    """Converts a text address to [lat, lon] coordinates."""
    try:
        location = geolocator.geocode(address)
        if location:
            return [location.latitude, location.longitude]
    except Exception:
        pass
    return None

def get_osrm_route(origin, dest, mode):
    """Fetches route from OSRM public API."""
    # Map travel mode to OSRM profile
    profile = "car"
    if mode == "Walk": profile = "foot"
    elif mode == "Bicycle": profile = "cycling"
    
    # OSRM expects [lon, lat]
    url = f"http://router.project-osrm.org/route/v1/{profile}/{origin[1]},{origin[0]};{dest[1]},{dest[0]}?overview=full&geometries=polyline"
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("code") == "Ok":
            route = data["routes"][0]
            geometry = route["geometry"]
            distance_m = route["distance"]
            # Decode polyline to list of [lat, lon]
            coords = polyline.decode(geometry)
            return coords, round(distance_m / 1000.0, 2), geometry
    except Exception:
        pass
    
    return None, None, None

def calculate_trip_stats(origin_lat, origin_lon, dest_lat, dest_lon, departure_time_str, arrival_time_str):
    """Calculates distance in km and average speed in km/h using Haversine fallback."""
    dist_km = geodesic((origin_lat, origin_lon), (dest_lat, dest_lon)).kilometers
    
    fmt = "%H:%M"
    try:
        start = datetime.strptime(departure_time_str, fmt)
        end = datetime.strptime(arrival_time_str, fmt)
        duration_hrs = (end - start).total_seconds() / 3600.0
        speed_kmh = dist_km / duration_hrs if duration_hrs > 0 else 0
        return round(dist_km, 2), round(speed_kmh, 1)
    except Exception:
        return round(dist_km, 2), 0.0
