from typing import Dict, Any, List


class ProviderAdapter:
    """Base class for provider adapters. Implement `quote` method to return estimated time and cost."""

    def quote(self, origin: str, destination: str, distance_km: float) -> Dict[str, Any]:
        raise NotImplementedError()


class MockProviderAdapter(ProviderAdapter):
    def __init__(self, name: str, mode: str, speed_kmph: float, cost_per_km: float, handling_hours: float):
        self.name = name
        self.mode = mode
        self.speed_kmph = speed_kmph
        self.cost_per_km = cost_per_km
        self.handling_hours = handling_hours

    def quote(self, origin: str, destination: str, distance_km: float) -> Dict[str, Any]:
        hours = distance_km / self.speed_kmph if self.speed_kmph > 0 else float('inf')
        est_time_hours = round(hours + self.handling_hours, 1)
        est_cost = round(distance_km * self.cost_per_km + self.handling_hours * 50 + 200, 2)
        return {
            'provider': self.name,
            'mode': self.mode,
            'estimated_time_hours': est_time_hours,
            'estimated_cost': est_cost,
            'notes': f'mock provider {self.name}'
        }


def get_default_providers() -> List[ProviderAdapter]:
    return [
        MockProviderAdapter('FastShip', 'air', 800, 12, 2),
        MockProviderAdapter('EcoRoad', 'road', 60, 6, 6),
        MockProviderAdapter('RailLink', 'rail', 70, 5, 6),
        MockProviderAdapter('SeaCargo', 'sea', 30, 3, 12),
    ]
