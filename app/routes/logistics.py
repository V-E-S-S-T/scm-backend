from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.logistics_service import LogisticsService

router = APIRouter()

class ShipmentCreate(BaseModel):
    destination: str = Field(..., description="Destination address")
    origin: Optional[str] = Field(None, description="Origin address")
    items_count: Optional[int] = Field(None, ge=1, description="Number of items")
    weight: Optional[float] = Field(None, ge=0.1, description="Total weight in kg")
    estimated_days: Optional[int] = Field(None, ge=1, le=30, description="Estimated delivery days")
    transport_mode: Optional[str] = Field('road', description="Transport mode: road, rail, air, sea")
    priority: Optional[str] = Field('standard', description="Priority: standard, express, urgent")
    items: Optional[List[Dict[str, Any]]] = Field([], description="List of items in shipment")
    notes: Optional[str] = Field('', description="Additional notes")

class ShipmentResponse(BaseModel):
    success: bool
    shipments: Optional[List[Dict[str, Any]]] = None
    shipment: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str = Field(..., description="New status")
    location: Optional[str] = Field(None, description="Current location")
    message: Optional[str] = Field(None, description="Status update message")

class LocationPair(BaseModel):
    origin: str
    destination: str

class EstimateRequest(BaseModel):
    origin: str
    destination: str
    originCoords: Optional[List[float]] = None
    destinationCoords: Optional[List[float]] = None
    weather: Optional[List[Dict[str, Any]]] = None

@router.get("/shipments", response_model=ShipmentResponse)
async def get_shipments(
    status: Optional[str] = None,
    transport_mode: Optional[str] = None,
    priority: Optional[str] = None
):
    """Get all shipments with enhanced filtering options"""
    try:
        logistics_service = LogisticsService()
        shipments = logistics_service.get_shipments(status, transport_mode, priority)
        return ShipmentResponse(
            success=True,
            shipments=shipments,
            message=f"Retrieved {len(shipments)} shipments"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve shipments",
                "message": str(e)
            }
        )

@router.post("/shipments", response_model=ShipmentResponse)
async def create_shipment(shipment: ShipmentCreate):
    """Create a new shipment"""
    try:
        logistics_service = LogisticsService()
        new_shipment = logistics_service.create_shipment(shipment.dict())
        return ShipmentResponse(
            success=True,
            shipment=new_shipment,
            message="Shipment created successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to create shipment",
                "message": str(e)
            }
        )

@router.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: str):
    """Get specific shipment details"""
    try:
        logistics_service = LogisticsService()
        shipment = logistics_service.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Shipment not found",
                    "message": f"Shipment with ID {shipment_id} not found"
                }
            )

        return {
            "success": True,
            "shipment": shipment,
            "message": "Shipment details retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve shipment",
                "message": str(e)
            }
        )

@router.put("/shipments/{shipment_id}/status")
async def update_shipment_status(shipment_id: str, update: StatusUpdate):
    """Update shipment status with enhanced tracking"""
    valid_statuses = ["Processing", "In Transit", "Out for Delivery", "Delivered", "Cancelled"]

    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid status",
                "message": f"Status must be one of: {', '.join(valid_statuses)}"
            }
        )

    try:
        logistics_service = LogisticsService()
        updated_shipment = logistics_service.update_shipment_status(
            shipment_id, update.status, update.location, update.message
        )

        if not updated_shipment:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Shipment not found",
                    "message": f"Shipment with ID {shipment_id} not found"
                }
            )

        return {
            "success": True,
            "shipment": updated_shipment,
            "message": f"Shipment status updated to {update.status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to update shipment status",
                "message": str(e)
            }
        )

@router.post("/routes/optimize")
async def optimize_routes(destinations: List[str]):
    """Optimize delivery routes for multiple destinations"""
    if not destinations or len(destinations) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid destinations",
                "message": "At least 2 destinations are required for route optimization"
            }
        )

    try:
        logistics_service = LogisticsService()
        optimized_routes = logistics_service.optimize_routes(destinations)
        return {
            "success": True,
            "routes": optimized_routes,
            "total_destinations": len(destinations),
            "estimated_savings": "15-25% time reduction",
            "message": "Routes optimized successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to optimize routes",
                "message": str(e)
            }
        )

@router.post('/shipments/estimate')
async def estimate_transport(data: dict):
    """Dynamic trip analysis with Gemini AI for distance, time, and cost estimation"""
    try:
        logistics_service = LogisticsService()
        
        origin = data.get('origin')
        destination = data.get('destination')
        
        if not origin or not destination:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': 'Missing origin or destination',
                    'message': 'Both origin and destination are required'
                }
            )
        
        # Get dynamic trip analysis using Gemini AI
        trip_analysis = logistics_service.get_dynamic_trip_analysis(origin, destination)
        
        # Get weather data
        origin_weather = logistics_service.fetch_weather_for_location(origin)
        dest_weather = logistics_service.fetch_weather_for_location(destination)
        
        # Combine analysis with weather data
        result = {
            **trip_analysis,
            'origin_weather': origin_weather,
            'destination_weather': dest_weather,
            'weather_points': [
                {'position': 'Origin', 'weather': origin_weather},
                {'position': 'Destination', 'weather': dest_weather}
            ],
            'warnings': ['Weather conditions analyzed for optimal delivery']
        }
        
        return {
            'success': True,
            'recommendation': result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                'success': False, 
                'error': 'Failed to estimate transport', 
                'message': str(e)
            }
        )

@router.post('/shipments/providers')
async def compare_providers(pair: LocationPair):
    """Compare logistics providers for a given origin/destination"""
    try:
        logistics_service = LogisticsService()
        comparisons = logistics_service.compare_logistics_providers(pair.origin, pair.destination)
        return {
            'success': True,
            'providers': comparisons
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                'success': False, 
                'error': 'Failed to compare providers', 
                'message': str(e)
            }
        )

@router.get('/weather')
async def get_weather(city: str = None, lat: float = None, lng: float = None):
    """Get current weather for a city or coordinates"""
    try:
        logistics_service = LogisticsService()
        if lat is not None and lng is not None:
            data = logistics_service.fetch_weather_by_coords(lat, lng)
        elif city:
            data = logistics_service.fetch_weather_for_location(city)
        else:
            raise HTTPException(
                status_code=400, 
                detail={
                    'success': False, 
                    'error': 'Missing parameters', 
                    'message': "Provide either 'city' or both 'lat' and 'lng'"
                }
            )
        return {'success': True, 'weather': data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                'success': False, 
                'error': 'Failed to fetch weather', 
                'message': str(e)
            }
        )

@router.post('/routes/weather-analysis')
async def get_route_weather_analysis(pair: LocationPair):
    """Get comprehensive route analysis with weather and AI insights"""
    try:
        logistics_service = LogisticsService()
        analysis = logistics_service.get_route_analysis_with_weather(pair.origin, pair.destination)
        
        if 'error' in analysis:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': analysis['error'],
                    'message': 'Failed to analyze route'
                }
            )
        
        return {
            'success': True,
            'analysis': analysis,
            'message': 'Route analysis completed successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Failed to analyze route weather',
                'message': str(e)
            }
        )

@router.get('/weather/route')
async def get_weather_along_route(origin: str, destination: str, samples: int = 5):
    """Get weather samples along a route with AI analysis"""
    try:
        logistics_service = LogisticsService()
        
        # Get coordinates
        origin_geo = logistics_service._geocode_place(origin)
        dest_geo = logistics_service._geocode_place(destination)
        
        if not origin_geo or not dest_geo:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': 'Geocoding failed',
                    'message': 'Could not find coordinates for origin or destination'
                }
            )
        
        weather_data = logistics_service.get_weather_along_route(
            origin_geo['lat'], origin_geo['lon'],
            dest_geo['lat'], dest_geo['lon'],
            samples=samples
        )
        
        return {
            'success': True,
            'route_weather': weather_data,
            'message': 'Route weather analysis completed'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Failed to fetch route weather',
                'message': str(e)
            }
        )

@router.get("/analytics")
async def get_logistics_analytics():
    """Get enhanced logistics performance analytics"""
    try:
        logistics_service = LogisticsService()
        analytics = logistics_service.get_analytics()
        return {
            "success": True,
            "analytics": analytics,
            "message": "Enhanced logistics analytics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve logistics analytics",
                "message": str(e)
            }
        )

@router.get("/shipments/{shipment_id}/tracking")
async def get_shipment_tracking(shipment_id: str):
    """Get detailed tracking information for a shipment"""
    try:
        logistics_service = LogisticsService()
        shipment = logistics_service.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Shipment not found",
                    "message": f"Shipment with ID {shipment_id} not found"
                }
            )
        
        return {
            "success": True,
            "tracking": shipment.get('tracking_info', {}),
            "shipment": shipment,
            "message": "Tracking information retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve tracking information",
                "message": str(e)
            }
        )

@router.post("/routes/precise-analysis")
async def get_precise_route_analysis(pair: LocationPair, transport_mode: str = 'road', weight: float = 10.0):
    """Get precise distance measurement and AI-powered time/cost predictions"""
    try:
        logistics_service = LogisticsService()
        analysis = logistics_service.get_precise_distance_and_predictions(
            pair.origin, pair.destination, transport_mode, weight
        )
        
        if 'error' in analysis:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': analysis['error'],
                    'message': 'Failed to analyze route precisely'
                }
            )
        
        return {
            'success': True,
            'analysis': analysis,
            'message': 'Precise route analysis completed successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Failed to perform precise route analysis',
                'message': str(e)
            }
        )

@router.get("/shipments/{shipment_id}/weather-analysis")
async def get_shipment_weather_analysis(shipment_id: str):
    """Get weather analysis for a specific shipment route"""
    try:
        logistics_service = LogisticsService()
        shipment = logistics_service.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Shipment not found",
                    "message": f"Shipment with ID {shipment_id} not found"
                }
            )
        
        # Get both weather analysis and precise distance data
        weather_analysis = logistics_service.get_route_analysis_with_weather(
            shipment['origin'], 
            shipment['destination']
        )
        
        precise_analysis = logistics_service.get_precise_distance_and_predictions(
            shipment['origin'], 
            shipment['destination'],
            shipment.get('transport_mode', 'road'),
            shipment.get('total_weight', 10.0)
        )
        
        if 'error' in weather_analysis:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': weather_analysis['error'],
                    'message': 'Failed to analyze shipment route'
                }
            )
        
        # Combine weather and precise analysis
        combined_analysis = weather_analysis.copy()
        if 'error' not in precise_analysis:
            combined_analysis['precise_distance'] = precise_analysis
        
        return {
            'success': True,
            'shipment_id': shipment_id,
            'analysis': combined_analysis,
            'message': f'Complete analysis completed for shipment {shipment_id}'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Failed to analyze shipment weather',
                'message': str(e)
            }
        )