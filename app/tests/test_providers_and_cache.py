import sys
import os
import time
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.logistics_service import LogisticsService
from app.services.providers import get_default_providers


def test_providers_adapter_quote():
    adapters = get_default_providers()
    assert len(adapters) >= 1
    q = adapters[0].quote('Bangalore', 'Mumbai', 980)
    assert 'estimated_time_hours' in q
    assert 'estimated_cost' in q


def test_cache_and_rate_limit():
    svc = LogisticsService()
    # Prime cache by calling geocode twice and ensure the second is cached (fast)
    a = svc._geocode_place('Mumbai')
    assert a is None or ('lat' in a and 'lon' in a)
    # Immediately call space expecting cache hit or rate-limited call
    b = svc._geocode_place('Mumbai')
    # Should not error and return same structure
    assert b is None or ('lat' in b and 'lon' in b)

    # Test allow_call rate limiting
    assert svc._allow_call('test_ep', 0.1) is True
    assert svc._allow_call('test_ep', 1.0) is False
    time.sleep(1.1)
    assert svc._allow_call('test_ep', 1.0) is True


if __name__ == '__main__':
    pytest.main([__file__])
