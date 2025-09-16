import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock
from datetime import datetime

# Patchable service import
from app.services.demand_service import DemandService

# Import the FastAPI app
from app.main import app

# Test client
client = TestClient(app)


class TestDemandEndpoints:
    """Test demand forecasting endpoints"""

    def test_forecast_window_and_season_coverage(self, monkeypatch):
        """12-month window should include cross-year seasons and expose forecast window."""
        fixed_now = datetime(2025, 9, 14, 10, 0, 0)
        monkeypatch.setattr(DemandService, "_now", lambda self: fixed_now)

        request_data = {
            "businessName": "Test Electronics",
            "businessType": "Electronics Store",
            "businessScale": "Small",
            "location": "Karnataka",
            "currentSales": 50000,
            "forecastPeriod": 12,
        }

        resp = client.post("/api/demand/forecast", json=request_data)
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["success"] is True
        forecast = payload["forecast"]

        # Window assertions
        assert forecast["forecast_start"] == "2025-09-14"
        assert forecast["forecast_end"] == "2026-09-13"

        # Seasonal coverage: expect 5 overlapping seasons in this window
        seasonal_chart = forecast["seasonal_demands"]["chart"]
        assert len(seasonal_chart) >= 5
        labels = [row["season"] for row in seasonal_chart]
        joined = " ".join(labels)
        for expected in ["Autumn", "Winter", "Spring", "Summer", "Monsoon"]:
            assert expected in joined

    def test_forecast_festivals_count(self, monkeypatch):
        """Festival list should include all in-range festivals (>5 for this 12-month window)."""
        fixed_now = datetime(2025, 9, 14, 10, 0, 0)
        monkeypatch.setattr(DemandService, "_now", lambda self: fixed_now)

        request_data = {
            "businessType": "Grocery Store",
            "businessScale": "Micro",
            "location": "Maharashtra",
            "currentSales": 30000,
            "forecastPeriod": 12,
        }

        resp = client.post("/api/demand/forecast", json=request_data)
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["success"] is True
        chart = payload["forecast"]["festival_demands"]["chart"]
        assert len(chart) > 5

    def test_forecast_endpoint_valid_request(self):
        """Test forecast endpoint with valid request"""

        request_data = {
            "businessName": "Test Electronics",
            "businessType": "Electronics Store",
            "businessScale": "Small",
            "location": "Karnataka",
            "currentSales": 50000,
        }

        response = client.post("/api/demand/forecast", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "forecast" in data
        assert data["forecast"] is not None

    def test_forecast_endpoint_invalid_business_type(self):
        """Test forecast endpoint with invalid business type"""

        request_data = {
            "businessType": "Invalid Store Type",
            "businessScale": "Small",
            "location": "Karnataka",
            "currentSales": 50000,
        }

        response = client.post("/api/demand/forecast", json=request_data)
        assert response.status_code == 400

    def test_forecast_endpoint_missing_required_fields(self):
        """Test forecast endpoint with missing required fields"""

        request_data = {
            "businessName": "Test Store"
            # Missing required fields
        }

        response = client.post("/api/demand/forecast", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_seasonal_patterns_endpoint(self):
        """Test seasonal patterns endpoint"""

        response = client.get(
            "/api/demand/seasonal-patterns?type=Grocery Store&location=Karnataka"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "patterns" in data

    def test_festival_calendar_endpoint(self):
        """Test festival calendar endpoint"""

        response = client.get("/api/demand/festival-calendar?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "calendar" in data
        assert data["year"] == 2025

    def test_business_types_endpoint(self):
        """Test business types endpoint"""

        response = client.get("/api/demand/business-types")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "business_types" in data
        assert "business_scales" in data
        assert "locations" in data


class TestInventoryEndpoints:
    """Test inventory management endpoints"""

    def test_get_inventory_endpoint(self):
        """Test get inventory endpoint"""

        response = client.get("/api/inventory/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "inventory" in data

    def test_get_inventory_with_filters(self):
        """Test get inventory with filters"""

        response = client.get("/api/inventory/?category=Electronics&status=low")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_add_inventory_item_valid(self):
        """Test adding valid inventory item"""

        item_data = {
            "name": "Test Product",
            "category": "Electronics",
            "current_stock": 100,
            "min_stock_level": 20,
            "max_stock_level": 200,
            "unit_cost": 500.0,
            "selling_price": 750.0,
        }

        response = client.post("/api/inventory/", json=item_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "item" in data

    def test_add_inventory_item_invalid(self):
        """Test adding invalid inventory item"""

        item_data = {
            "name": "",  # Invalid empty name
            "category": "Electronics",
            "current_stock": -5,  # Invalid negative stock
            "min_stock_level": 20,
            "max_stock_level": 200,
        }

        response = client.post("/api/inventory/", json=item_data)
        assert response.status_code == 422  # Validation error

    def test_low_stock_items_endpoint(self):
        """Test low stock items endpoint"""

        response = client.get("/api/inventory/low-stock")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data


class TestLogisticsEndpoints:
    """Test logistics management endpoints"""

    def test_get_shipments_endpoint(self):
        """Test get shipments endpoint"""

        response = client.get("/api/logistics/shipments")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "shipments" in data

    def test_create_shipment_valid(self):
        """Test creating valid shipment"""

        shipment_data = {"destination": "Mumbai", "items_count": 10, "weight": 25.5}

        response = client.post("/api/logistics/shipments", json=shipment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "shipment" in data

    def test_create_shipment_invalid(self):
        """Test creating invalid shipment"""

        shipment_data = {
            "destination": "",  # Invalid empty destination
            "items_count": -1,  # Invalid negative count
        }

        response = client.post("/api/logistics/shipments", json=shipment_data)
        assert response.status_code == 422

    def test_optimize_routes_endpoint(self):
        """Test route optimization endpoint"""

        destinations = ["Mumbai", "Delhi", "Chennai", "Kolkata"]

        response = client.post("/api/logistics/routes/optimize", json=destinations)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "routes" in data


class TestScenariosEndpoints:
    """Test scenario analysis endpoints"""

    def test_analyze_scenario_valid(self):
        """Test scenario analysis with valid data"""

        scenario_data = {
            "baseSales": 100000,
            "priceChange": -10,
            "marketingSpend": 25000,
            "seasonalFactor": 1.2,
            "competitorAction": "aggressive",
        }

        response = client.post("/api/scenarios/analyze", json=scenario_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data

    def test_analyze_scenario_invalid(self):
        """Test scenario analysis with invalid data"""

        scenario_data = {
            "baseSales": -1000,  # Invalid negative sales
            "priceChange": 200,  # Invalid price change > 100%
            "competitorAction": "invalid_action",  # Invalid action
        }

        response = client.post("/api/scenarios/analyze", json=scenario_data)
        assert response.status_code == 400

    def test_scenario_templates_endpoint(self):
        """Test scenario templates endpoint"""

        response = client.get("/api/scenarios/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "templates" in data


class TestReportsEndpoints:
    """Test reporting endpoints"""

    def test_executive_summary_endpoint(self):
        """Test executive summary endpoint"""

        response = client.get("/api/reports/executive-summary")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data

    def test_sales_report_endpoint(self):
        """Test sales report endpoint"""

        response = client.get("/api/reports/sales?period=monthly")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data

    def test_inventory_report_endpoint(self):
        """Test inventory report endpoint"""

        response = client.get("/api/reports/inventory")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data

    def test_forecast_accuracy_report_endpoint(self):
        """Test forecast accuracy report endpoint"""

        response = client.get("/api/reports/forecast-accuracy")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data


class TestHealthEndpoints:
    """Test health and status endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "AI Supply Chain Management Platform"

    def test_health_endpoint(self):
        """Test health check endpoint"""

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoint(self):
        """Test accessing invalid endpoint"""

        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test method not allowed"""

        response = client.delete("/api/demand/forecast")
        assert response.status_code == 405

    def test_invalid_json_data(self):
        """Test sending invalid JSON data"""

        response = client.post(
            "/api/demand/forecast",
            data="invalid json data",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestAIModelIntegration:
    """Test AI model integration"""

    @patch("app.models.ai_models.GeminiAIModel.generate_demand_forecast")
    def test_gemini_ai_integration(self, mock_generate):
        """Test Gemini AI integration with mock"""

        # Mock AI response
        mock_generate.return_value = {
            "seasonal_analysis": "Test analysis",
            "festival_impact": "Test impact",
            "monthly_projections": [
                {"month": "Oct 2025", "sales": 60000, "growth": "+20%"}
            ],
            "recommendations": ["Test recommendation"],
            "confidence_score": 0.85,
        }

        request_data = {
            "businessType": "Electronics Store",
            "businessScale": "Small",
            "location": "Karnataka",
            "currentSales": 50000,
        }

        response = client.post("/api/demand/forecast", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["forecast"]["confidence_score"] == 0.85

    def test_ai_fallback_system(self):
        """Test AI fallback when Gemini is unavailable"""

        with patch.object(client.app.state, "gemini_available", False):
            request_data = {
                "businessType": "Grocery Store",
                "businessScale": "Micro",
                "location": "Maharashtra",
                "currentSales": 30000,
            }

            response = client.post("/api/demand/forecast", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # Should use fallback statistical model


# Test fixtures and utilities
@pytest.fixture
def sample_business_data():
    """Sample business data for testing"""
    return {
        "businessName": "Test Business",
        "businessType": "Electronics Store",
        "businessScale": "Small",
        "location": "Karnataka",
        "currentSales": 75000,
    }


@pytest.fixture
def sample_inventory_item():
    """Sample inventory item for testing"""
    return {
        "name": "Test Product",
        "category": "Electronics",
        "sku": "TEST-001",
        "current_stock": 50,
        "min_stock_level": 10,
        "max_stock_level": 100,
        "unit_cost": 200.0,
        "selling_price": 300.0,
        "supplier": "Test Supplier",
    }


@pytest.fixture
def sample_shipment_data():
    """Sample shipment data for testing"""
    return {
        "destination": "Delhi",
        "origin": "Bangalore",
        "items_count": 15,
        "weight": 30.5,
        "estimated_days": 5,
    }


# Performance tests
class TestPerformance:
    """Test API performance"""

    def test_forecast_response_time(self, sample_business_data):
        """Test forecast generation response time"""

        import time

        start_time = time.time()
        response = client.post("/api/demand/forecast", json=sample_business_data)
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 30  # Should respond within 30 seconds

    def test_multiple_concurrent_requests(self, sample_business_data):
        """Test handling multiple concurrent requests"""

        import concurrent.futures

        def make_request():
            return client.post("/api/demand/forecast", json=sample_business_data)

        # Test 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

        # All requests should succeed
        for result in results:
            assert result.status_code == 200


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""

    def test_complete_forecast_workflow(self, sample_business_data):
        """Test complete forecasting workflow"""

        # Step 1: Get business types
        response = client.get("/api/demand/business-types")
        assert response.status_code == 200

        # Step 2: Generate forecast
        response = client.post("/api/demand/forecast", json=sample_business_data)
        assert response.status_code == 200
        forecast_data = response.json()

        # Step 3: Get forecast history
        response = client.get("/api/demand/forecast-history")
        assert response.status_code == 200

        # Verify workflow completed successfully
        assert forecast_data["success"] is True

    def test_inventory_management_workflow(self, sample_inventory_item):
        """Test complete inventory management workflow"""

        # Step 1: Add inventory item
        response = client.post("/api/inventory/", json=sample_inventory_item)
        assert response.status_code == 200
        item_data = response.json()

        # Step 2: Get all inventory
        response = client.get("/api/inventory/")
        assert response.status_code == 200

        # Step 3: Check low stock items
        response = client.get("/api/inventory/low-stock")
        assert response.status_code == 200

        # Step 4: Get analytics
        response = client.get("/api/inventory/analytics")
        assert response.status_code == 200

        assert item_data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
