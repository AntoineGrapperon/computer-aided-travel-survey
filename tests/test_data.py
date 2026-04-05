import sys
from unittest.mock import MagicMock

# Mock pandas before importing src.data_manager
mock_pd = MagicMock()
sys.modules["pandas"] = mock_pd

from src.data_manager import check_overlap
import pytest

def test_check_overlap():
    existing_trips = [
        {"departure_time": "08:00", "arrival_time": "08:30"},
        {"departure_time": "12:00", "arrival_time": "13:00"}
    ]
    
    # No overlap
    is_overlap, _ = check_overlap("09:00", "10:00", existing_trips)
    assert not is_overlap
    
    # Overlap start
    is_overlap, trip = check_overlap("08:15", "08:45", existing_trips)
    assert is_overlap
    assert trip["departure_time"] == "08:00"
    
    # Overlap end
    is_overlap, trip = check_overlap("07:45", "08:15", existing_trips)
    assert is_overlap
    assert trip["departure_time"] == "08:00"
    
    # Entirely contained
    is_overlap, trip = check_overlap("08:10", "08:20", existing_trips)
    assert is_overlap
    
    # Entirely containing
    is_overlap, trip = check_overlap("07:00", "09:00", existing_trips)
    assert is_overlap
