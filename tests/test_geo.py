from src.geo_utils import calculate_trip_stats, get_osrm_route
import pytest
from unittest.mock import patch, MagicMock

def test_calculate_trip_stats():
    # Paris to nearby (approx coordinates)
    # 48.8566, 2.3522 to 48.8566, 2.3622 is about 0.73km
    dist, speed = calculate_trip_stats(48.8566, 2.3522, 48.8566, 2.3622, "08:00", "08:06")
    
    assert dist > 0
    assert speed > 0
    # 0.73km in 6 mins (0.1 hrs) => 7.3 km/h
    assert 7.0 <= speed <= 8.0

@patch("requests.get")
def test_get_osrm_route_mock(mock_get):
    # Mock OSRM response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": "Ok",
        "routes": [{
            "geometry": "polyline_string",
            "distance": 1500.0
        }]
    }
    mock_get.return_value = mock_response
    
    with patch("polyline.decode", return_value=[[48.8, 2.3], [48.81, 2.31]]):
        coords, dist, poly = get_osrm_route([48.8, 2.3], [48.81, 2.31], "Walk")
        
        assert coords == [[48.8, 2.3], [48.81, 2.31]]
        assert dist == 1.5
        assert poly == "polyline_string"
