from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.inventory_service import InventoryService

router = APIRouter()


class InventoryItem(BaseModel):
    name: str = Field(..., description="Item name")
    category: str = Field(..., description="Item category")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    current_stock: int = Field(..., ge=0, description="Current stock level")
    min_stock_level: int = Field(..., ge=0, description="Minimum stock level")
    max_stock_level: int = Field(..., ge=1, description="Maximum stock level")
    unit_cost: Optional[float] = Field(None, ge=0, description="Unit cost in INR")
    selling_price: Optional[float] = Field(
        None, ge=0, description="Selling price in INR"
    )
    supplier: Optional[str] = Field(None, description="Supplier name")


class InventoryResponse(BaseModel):
    success: bool
    inventory: Optional[List[Dict[str, Any]]] = None
    item: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


@router.get("/", response_model=InventoryResponse)
async def get_inventory(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by stock status"),
    search: Optional[str] = Query(None, description="Search term"),
):
    """
    Get inventory items with optional filtering
    """

    try:
        inventory_service = InventoryService()

        filters = {"category": category, "status": status, "search": search}

        inventory_items = inventory_service.get_inventory(filters)

        return InventoryResponse(
            success=True,
            inventory=inventory_items,
            message=f"Retrieved {len(inventory_items)} inventory items",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve inventory",
                "message": str(e),
            },
        )


@router.post("/", response_model=InventoryResponse)
async def add_inventory_item(item: InventoryItem):
    """
    Add new inventory item
    """

    try:
        inventory_service = InventoryService()

        new_item = inventory_service.add_item(item.dict())

        return InventoryResponse(
            success=True, item=new_item, message="Inventory item added successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to add inventory item",
                "message": str(e),
            },
        )


@router.put("/{item_id}")
async def update_inventory_item(item_id: int, item: InventoryItem):
    """
    Update existing inventory item
    """

    try:
        inventory_service = InventoryService()

        updated_item = inventory_service.update_item(item_id, item.dict())

        if not updated_item:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Item not found",
                    "message": f"Inventory item with ID {item_id} not found",
                },
            )

        return {
            "success": True,
            "item": updated_item,
            "message": "Inventory item updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to update inventory item",
                "message": str(e),
            },
        )


@router.delete("/{item_id}")
async def delete_inventory_item(item_id: int):
    """
    Delete inventory item
    """

    try:
        inventory_service = InventoryService()

        deleted = inventory_service.delete_item(item_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Item not found",
                    "message": f"Inventory item with ID {item_id} not found",
                },
            )

        return {"success": True, "message": "Inventory item deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to delete inventory item",
                "message": str(e),
            },
        )


@router.get("/low-stock")
async def get_low_stock_items():
    """
    Get items with low stock levels
    """

    try:
        inventory_service = InventoryService()

        low_stock_items = inventory_service.get_low_stock_items()

        return {
            "success": True,
            "items": low_stock_items,
            "count": len(low_stock_items),
            "message": f"Found {len(low_stock_items)} items with low stock",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve low stock items",
                "message": str(e),
            },
        )


@router.get("/analytics")
async def get_inventory_analytics():
    """
    Get inventory analytics and insights
    """

    try:
        inventory_service = InventoryService()

        analytics = inventory_service.get_analytics()

        return {
            "success": True,
            "analytics": analytics,
            "message": "Inventory analytics retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve inventory analytics",
                "message": str(e),
            },
        )
