from typing import Dict, List, Any, Optional
from datetime import datetime

class InventoryService:
    """Service for inventory management and optimization"""

    def __init__(self): 
        # In a real application, this would connect to database
        self._mock_inventory = self._get_mock_inventory()

    def get_inventory(self, filters: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
        """Get inventory items with optional filtering"""

        inventory = self._mock_inventory.copy()

        # Apply filters
        if filters.get("category"):
            inventory = [
                item for item in inventory if item["category"] == filters["category"]
            ]

        if filters.get("status"):
            inventory = [
                item for item in inventory if item["status"] == filters["status"]
            ]

        if filters.get("search"):
            search_term = filters["search"].lower()
            inventory = [
                item
                for item in inventory
                if search_term in item["name"].lower()
                or search_term in item.get("sku", "").lower()
            ]

        return inventory

    def add_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new inventory item"""

        # Validate stock levels
        if item_data["min_stock_level"] >= item_data["max_stock_level"]:
            raise ValueError(
                "Minimum stock level must be less than maximum stock level"
            )

        # Generate new item
        new_item = {
            "id": len(self._mock_inventory) + 1,
            "name": item_data["name"],
            "category": item_data["category"],
            "sku": item_data.get("sku", f"SKU-{len(self._mock_inventory) + 1:04d}"),
            "current_stock": item_data["current_stock"],
            "min_stock_level": item_data["min_stock_level"],
            "max_stock_level": item_data["max_stock_level"],
            "unit_cost": item_data.get("unit_cost"),
            "selling_price": item_data.get("selling_price"),
            "supplier": item_data.get("supplier"),
            "status": self._calculate_status(
                item_data["current_stock"],
                item_data["min_stock_level"],
                item_data["max_stock_level"],
            ),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self._mock_inventory.append(new_item)
        return new_item

    def update_item(self, item_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing inventory item"""

        for i, item in enumerate(self._mock_inventory):
            if item["id"] == item_id:
                # Update fields
                for key, value in item_data.items():
                    if key != "id":  # Don't update ID
                        item[key] = value

                # Recalculate status
                item["status"] = self._calculate_status(
                    item["current_stock"],
                    item["min_stock_level"],
                    item["max_stock_level"],
                )

                item["updated_at"] = datetime.now().isoformat()
                return item

        return None

    def delete_item(self, item_id: int) -> bool:
        """Delete inventory item"""

        for i, item in enumerate(self._mock_inventory):
            if item["id"] == item_id:
                del self._mock_inventory[i]
                return True

        return False

    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items with low or critical stock levels"""

        return [
            item
            for item in self._mock_inventory
            if item["status"] in ["low", "critical"]
        ]

    def get_analytics(self) -> Dict[str, Any]:
        """Get inventory analytics and insights"""

        total_items = len(self._mock_inventory)
        total_value = sum(
            (item.get("unit_cost", 0) * item["current_stock"])
            for item in self._mock_inventory
        )

        # Status breakdown
        status_counts = {}
        for item in self._mock_inventory:
            status = item["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Category breakdown
        category_breakdown = {}
        for item in self._mock_inventory:
            category = item["category"]
            if category not in category_breakdown:
                category_breakdown[category] = {"items": 0, "value": 0}

            category_breakdown[category]["items"] += 1
            category_breakdown[category]["value"] += (
                item.get("unit_cost", 0) * item["current_stock"]
            )

        return {
            "total_items": total_items,
            "total_value": total_value,
            "status_breakdown": status_counts,
            "category_breakdown": category_breakdown,
            "turnover_rate": 6.4,  # Mock calculation
            "carrying_cost": total_value * 0.1,  # 10% carrying cost
            "reorder_alerts": len(self.get_low_stock_items()),
            "top_categories": sorted(
                category_breakdown.items(), key=lambda x: x[1]["value"], reverse=True
            )[:5],
        }

    def _calculate_status(self, current_stock: int, min_level: int, max_level: int) -> str:
        """Calculate stock status based on levels"""

        if current_stock <= min_level * 0.5:
            return "critical"
        elif current_stock <= min_level:
            return "low"
        elif current_stock >= max_level:
            return "overstock"
        else:
            return "normal"

    def _get_mock_inventory(self) -> List[Dict[str, Any]]:
        """Get mock inventory data"""

        return [
            {
                "id": 1,
                "name": "Wireless Headphones",
                "category": "Electronics",
                "sku": "SKU-0001",
                "current_stock": 45,
                "min_stock_level": 20,
                "max_stock_level": 100,
                "unit_cost": 2500.0,
                "selling_price": 4999.0,
                "supplier": "TechCorp Ltd",
                "status": "normal",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-20T14:45:00",
            },
            {
                "id": 2,
                "name": "Cotton T-Shirt",
                "category": "Clothing",
                "sku": "SKU-0002",
                "current_stock": 8,
                "min_stock_level": 15,
                "max_stock_level": 80,
                "unit_cost": 300.0,
                "selling_price": 799.0,
                "supplier": "Fashion Hub",
                "status": "critical",
                "created_at": "2024-01-10T09:15:00",
                "updated_at": "2024-01-22T11:20:00",
            },
            {
                "id": 3,
                "name": "Office Chair",
                "category": "Furniture",
                "sku": "SKU-0003",
                "current_stock": 12,
                "min_stock_level": 10,
                "max_stock_level": 30,
                "unit_cost": 8000.0,
                "selling_price": 15999.0,
                "supplier": "Comfort Seating",
                "status": "normal",
                "created_at": "2024-01-08T16:00:00",
                "updated_at": "2024-01-18T13:30:00",
            },
            {
                "id": 4,
                "name": "Smartphone Case",
                "category": "Electronics",
                "sku": "SKU-0004",
                "current_stock": 150,
                "min_stock_level": 50,
                "max_stock_level": 120,
                "unit_cost": 150.0,
                "selling_price": 499.0,
                "supplier": "Mobile Accessories Inc",
                "status": "overstock",
                "created_at": "2024-01-12T12:45:00",
                "updated_at": "2024-01-21T10:15:00",
            },
            {
                "id": 5,
                "name": "Coffee Mug",
                "category": "Home & Kitchen",
                "sku": "SKU-0005",
                "current_stock": 25,
                "min_stock_level": 30,
                "max_stock_level": 100,
                "unit_cost": 200.0,
                "selling_price": 599.0,
                "supplier": "Kitchen Essentials",
                "status": "low",
                "created_at": "2024-01-14T08:20:00",
                "updated_at": "2024-01-19T15:10:00",
            },
        ]