import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.logistics_service import LogisticsService


def test_get_distance_and_duration_basic():
    svc = LogisticsService()
    res = svc.get_distance_and_duration('Bangalore', 'Mumbai')
    assert 'distance_km' in res
    assert 'duration_hours' in res
    assert isinstance(res['distance_km'], (int, float))


def test_decide_transport_mode_structure():
    svc = LogisticsService()
    res = svc.decide_transport_mode('Bangalore', 'Delhi')
    assert 'recommended_mode' in res
    assert 'mode_scores' in res
    assert isinstance(res['mode_scores'], dict)


if __name__ == '__main__':
    pytest.main([__file__])
