from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import requests
import os
try:
    import google.generativeai as genai
except Exception:
    genai = None

import threading
import time

# API keys (loaded from environment where possible)
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '27e521566a6e46a597ba8bdc6f74a86a')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'a84144b278bdeac6c181b514a15e5db3')  # Will use Open-Meteo as fallback
ORS_API_KEY = os.getenv('ORS_API_KEY', '')
# Gemini defaults (use provided key if env not set)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCkIfYPDPy2Cid027BAEyAXcfnC84DA_l0')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

# configure genai if available
if genai is not None:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"✅ Gemini configured with model: {GEMINI_MODEL}")
    except Exception as e:
        print(f"❌ Gemini configuration failed: {e}")
        genai = None

class LogisticsService:
    """Service for logistics and shipment management"""

    def __init__(self): 
        # In a real application, this would connect to database
        self._mock_shipments = self._get_mock_shipments()
        # Simple in-memory cache for external calls
        self._cache = {}
        self._cache_lock = threading.Lock()
        # Simple per-endpoint last-call timestamps for rudimentary rate-limiting
        self._last_called = {}

    def get_shipments(self, status_filter: Optional[str] = None, transport_mode: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all shipments with enhanced filtering options"""

        shipments = self._mock_shipments.copy()

        if status_filter:
            shipments = [
                shipment for shipment in shipments 
                if shipment['status'].lower() == status_filter.lower()
            ]
        
        if transport_mode:
            shipments = [
                shipment for shipment in shipments 
                if shipment.get('transport_mode', '').lower() == transport_mode.lower()
            ]
        
        if priority:
            shipments = [
                shipment for shipment in shipments 
                if shipment.get('priority', '').lower() == priority.lower()
            ]

        return shipments

    def create_shipment(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shipment with enhanced validation and features"""

        # Validate required fields
        if not shipment_data.get('destination'):
            raise ValueError("Destination is required")
        
        # Generate shipment ID
        shipment_id = f"SHP-{uuid.uuid4().hex[:8].upper()}"

        # Calculate estimated delivery with transport mode consideration
        transport_mode = shipment_data.get('transport_mode', 'road')
        estimated_days = self._calculate_delivery_time(transport_mode, shipment_data.get('estimated_days', 4))
        estimated_delivery = (datetime.now() + timedelta(days=estimated_days)).date()

        # Calculate costs with mode-specific pricing
        weight = shipment_data.get('weight', 10.0)
        items_count = shipment_data.get('items_count', 1)
        origin = shipment_data.get('origin', 'Bangalore Distribution Center')
        destination = shipment_data['destination']
        
        # Get precise distance and AI predictions
        precise_data = self.get_precise_distance_and_predictions(origin, destination, transport_mode, weight)
        
        if 'error' not in precise_data:
            shipping_cost = precise_data['ai_predictions']['estimated_cost_inr']
            estimated_days = max(1, int(precise_data['ai_predictions']['estimated_time_hours'] / 24))
        else:
            # Fallback to original calculation
            distance_cost = self._calculate_distance_cost(origin, destination)
            shipping_cost = self._calculate_shipping_cost(weight, items_count, distance_cost, transport_mode)
        
        # Priority handling
        priority = shipment_data.get('priority', 'standard')
        if priority == 'express':
            shipping_cost *= 1.5
            estimated_days = max(1, estimated_days - 1)
        elif priority == 'urgent':
            shipping_cost *= 2.0
            estimated_days = max(1, estimated_days - 2)

        new_shipment = {
            'id': shipment_id,
            'origin': origin,
            'destination': destination,
            'status': 'Processing',
            'items_count': items_count,
            'total_weight': weight,
            'cost': shipping_cost,
            'transport_mode': transport_mode,
            'priority': priority,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'shipped_date': None,
            'eta': estimated_delivery.strftime('%Y-%m-%d'),
            'actual_delivery': None,
            'items': shipment_data.get('items', []),
            'notes': shipment_data.get('notes', ''),
            'tracking_info': {
                'last_update': datetime.now().isoformat(),
                'location': origin,
                'next_checkpoint': self._get_next_checkpoint(origin, destination),
                'progress_percentage': 0,
                'status_history': [{
                    'status': 'Processing',
                    'timestamp': datetime.now().isoformat(),
                    'location': origin,
                    'message': 'Shipment created and processing'
                }]
            }
        }

        self._mock_shipments.append(new_shipment)
        return new_shipment

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict[str, Any]]:
        """Get specific shipment by ID with enhanced details"""

        for shipment in self._mock_shipments:
            if shipment['id'] == shipment_id:
                # Add real-time updates for in-transit shipments
                if shipment['status'] == 'In Transit':
                    # Simulate progress updates
                    created = datetime.strptime(shipment['created_date'], '%Y-%m-%d')
                    eta = datetime.strptime(shipment['eta'], '%Y-%m-%d')
                    now = datetime.now()
                    
                    total_duration = (eta - created).days
                    elapsed_duration = (now.date() - created.date()).days
                    
                    if total_duration > 0:
                        progress = min(90, max(10, (elapsed_duration / total_duration) * 100))
                        shipment['tracking_info']['progress_percentage'] = int(progress)
                
                return shipment

        return None

    def update_shipment_status(self, shipment_id: str, new_status: str, location: str = None, message: str = None) -> Optional[Dict[str, Any]]:
        """Update shipment status with enhanced tracking"""

        for shipment in self._mock_shipments:
            if shipment['id'] == shipment_id:
                old_status = shipment['status']
                shipment['status'] = new_status

                # Update dates based on status
                now = datetime.now()

                if new_status == 'In Transit' and old_status == 'Processing':
                    shipment['shipped_date'] = now.strftime('%Y-%m-%d')
                elif new_status == 'Delivered':
                    shipment['actual_delivery'] = now.strftime('%Y-%m-%d')

                # Update progress percentage
                progress_map = {
                    'Processing': 10,
                    'In Transit': 50,
                    'Out for Delivery': 90,
                    'Delivered': 100,
                    'Cancelled': 0
                }
                
                # Update tracking info
                tracking_info = shipment.get('tracking_info', {})
                tracking_info['last_update'] = now.isoformat()
                tracking_info['progress_percentage'] = progress_map.get(new_status, 50)
                
                if location:
                    tracking_info['location'] = location
                
                # Add to status history
                if 'status_history' not in tracking_info:
                    tracking_info['status_history'] = []
                
                tracking_info['status_history'].append({
                    'status': new_status,
                    'timestamp': now.isoformat(),
                    'location': location or tracking_info.get('location', 'Unknown'),
                    'message': message or f'Status updated to {new_status}'
                })
                
                shipment['tracking_info'] = tracking_info
                return shipment

        return None

    def optimize_routes(self, destinations: List[str]) -> Dict[str, Any]:
        """Optimize delivery routes for multiple destinations"""

        # Simple route optimization algorithm
        # In a real application, this would use sophisticated routing algorithms

        optimized_order = self._simple_route_optimization(destinations)

        total_distance = self._calculate_total_distance(optimized_order)
        estimated_time = self._calculate_total_time(optimized_order)
        
        return {
            'optimized_order': optimized_order,
            'total_distance_km': total_distance,
            'estimated_time_hours': estimated_time,
            'fuel_savings': f'{total_distance * 0.15:.1f}L',
            'cost_savings': f'₹{total_distance * 12:.0f}'
        }

    def get_dynamic_trip_analysis(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get dynamic trip analysis using Gemini AI for distance, time, and cost estimation"""
        try:
            if not genai:
                return self._fallback_trip_analysis(origin, destination)
            
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            prompt = f"""
You are a logistics expert. Analyze the route from {origin} to {destination} and provide precise estimates.

Consider:
- Real-world distance between these locations
- Current traffic patterns and road conditions
- Fuel costs (₹100/L diesel, 12km/L efficiency)
- Driver wages (₹500/day)
- Toll charges on highways
- Vehicle maintenance costs
- Weather impact on delivery time
- Regional logistics challenges

Provide response in this exact JSON format:
{{
  "distance_km": <actual_distance_number>,
  "estimated_hours": <realistic_travel_time>,
  "estimated_cost_inr": <total_cost_including_all_factors>,
  "fuel_cost": <fuel_cost_only>,
  "other_costs": <tolls_driver_maintenance>,
  "risk_level": "low|medium|high",
  "summary": "Brief explanation of the route and cost factors"
}}

Be realistic and accurate for Indian logistics.
"""
            
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            import json
            import re
            
            text = response.text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        'distance_info': {
                            'distance_km': result.get('distance_km', 500),
                            'duration_hours': result.get('estimated_hours', 8)
                        },
                        'stats': {
                            'distance': int(result.get('distance_km', 500)),
                            'estimated_hours': int(result.get('estimated_hours', 8)),
                            'average_cost': int(result.get('estimated_cost_inr', 4000)),
                            'risk_level': result.get('risk_level', 'low')
                        },
                        'gemini_summary': result.get('summary', f'Route analysis for {origin} to {destination}'),
                        'cost_breakdown': {
                            'fuel_cost': result.get('fuel_cost', 2000),
                            'other_costs': result.get('other_costs', 2000)
                        }
                    }
                except json.JSONDecodeError:
                    pass
            
            return self._fallback_trip_analysis(origin, destination)
            
        except Exception as e:
            print(f"Gemini trip analysis error: {e}")
            return self._fallback_trip_analysis(origin, destination)
    
    def _fallback_trip_analysis(self, origin: str, destination: str) -> Dict[str, Any]:
        """Fallback trip analysis when Gemini is unavailable"""
        # Simple distance estimation based on coordinates
        origin_coords = self._geocode_place(origin)
        dest_coords = self._geocode_place(destination)
        
        if origin_coords and dest_coords:
            distance_km = self._haversine_distance(
                origin_coords['lat'], origin_coords['lon'],
                dest_coords['lat'], dest_coords['lon']
            )
        else:
            distance_km = 500  # Default
        
        # Calculate estimates
        hours = max(4, distance_km / 60)  # 60 km/h average
        fuel_cost = (distance_km / 12) * 100  # 12km/L, ₹100/L
        other_costs = distance_km * 3 + 1000  # Tolls, driver, maintenance
        total_cost = fuel_cost + other_costs
        
        return {
            'distance_info': {
                'distance_km': round(distance_km, 1),
                'duration_hours': round(hours, 1)
            },
            'stats': {
                'distance': int(distance_km),
                'estimated_hours': int(hours),
                'average_cost': int(total_cost),
                'risk_level': 'low'
            },
            'gemini_summary': f'Route from {origin} to {destination}: {distance_km:.0f}km, estimated {hours:.1f}h travel time.',
            'cost_breakdown': {
                'fuel_cost': int(fuel_cost),
                'other_costs': int(other_costs)
            }
        }

    def get_precise_distance_and_predictions(self, origin: str, destination: str, transport_mode: str = 'road', weight: float = 10.0) -> Dict[str, Any]:
        """Get precise distance using mapping API and AI predictions for time/cost"""
        try:
            # Get coordinates
            origin_coords = self._geocode_place(origin)
            dest_coords = self._geocode_place(destination)
            
            if not origin_coords or not dest_coords:
                return {'error': 'Could not geocode locations'}
            
            # Get precise distance using OpenRouteService or fallback
            distance_data = self._get_precise_route_distance(origin_coords, dest_coords, transport_mode)
            
            # Use Gemini AI for intelligent predictions
            ai_predictions = self._get_ai_transport_predictions(origin, destination, distance_data, transport_mode, weight)
            
            return {
                'distance_km': distance_data['distance_km'],
                'duration_hours': distance_data['duration_hours'],
                'route_geometry': distance_data.get('geometry'),
                'ai_predictions': ai_predictions,
                'transport_mode': transport_mode,
                'weight_kg': weight
            }
            
        except Exception as e:
            print(f"Error in precise distance calculation: {e}")
            return {'error': str(e)}
    
    def _get_precise_route_distance(self, origin_coords: Dict, dest_coords: Dict, transport_mode: str) -> Dict[str, Any]:
        """Get precise route distance using mapping services"""
        try:
            # Try OpenRouteService first if API key available
            if ORS_API_KEY:
                return self._get_ors_route_data(origin_coords, dest_coords, transport_mode)
            
            # Fallback to Haversine distance with estimated duration
            distance_km = self._haversine_distance(
                origin_coords['lat'], origin_coords['lon'],
                dest_coords['lat'], dest_coords['lon']
            )
            
            # Estimate duration based on transport mode
            speed_map = {'road': 60, 'rail': 80, 'air': 500, 'sea': 25}
            avg_speed = speed_map.get(transport_mode, 60)
            duration_hours = distance_km / avg_speed
            
            return {
                'distance_km': round(distance_km, 2),
                'duration_hours': round(duration_hours, 2),
                'method': 'haversine_fallback'
            }
            
        except Exception as e:
            print(f"Route distance calculation error: {e}")
            return {'distance_km': 500, 'duration_hours': 8, 'method': 'fallback'}
    
    def _get_ors_route_data(self, origin_coords: Dict, dest_coords: Dict, transport_mode: str) -> Dict[str, Any]:
        """Get route data from OpenRouteService"""
        try:
            profile_map = {
                'road': 'driving-car',
                'rail': 'driving-car',  # Approximate with car
                'air': 'driving-car',   # Direct distance
                'sea': 'driving-car'    # Approximate
            }
            
            profile = profile_map.get(transport_mode, 'driving-car')
            
            url = f"https://api.openrouteservice.org/v2/directions/{profile}"
            headers = {'Authorization': ORS_API_KEY}
            
            data = {
                'coordinates': [
                    [origin_coords['lon'], origin_coords['lat']],
                    [dest_coords['lon'], dest_coords['lat']]
                ],
                'format': 'json'
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                route = result['routes'][0]
                
                return {
                    'distance_km': round(route['summary']['distance'] / 1000, 2),
                    'duration_hours': round(route['summary']['duration'] / 3600, 2),
                    'geometry': route.get('geometry'),
                    'method': 'openrouteservice'
                }
            
        except Exception as e:
            print(f"ORS API error: {e}")
        
        # Fallback to Haversine
        return self._get_precise_route_distance(origin_coords, dest_coords, transport_mode)
    
    def _get_ai_transport_predictions(self, origin: str, destination: str, distance_data: Dict, transport_mode: str, weight: float) -> Dict[str, Any]:
        """Use Gemini AI to predict transport time and cost"""
        try:
            if not genai:
                return self._fallback_transport_predictions(distance_data, transport_mode, weight)
            
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            prompt = f"""
As a logistics expert, analyze this shipment and provide precise predictions:

Route: {origin} to {destination}
Distance: {distance_data['distance_km']} km
Transport Mode: {transport_mode}
Weight: {weight} kg
Base Duration: {distance_data.get('duration_hours', 'unknown')} hours

Provide predictions in this exact JSON format:
{{
  "estimated_time_hours": <number>,
  "estimated_cost_inr": <number>,
  "fuel_cost_inr": <number>,
  "driver_cost_inr": <number>,
  "toll_cost_inr": <number>,
  "risk_factors": ["factor1", "factor2"],
  "cost_breakdown_explanation": "brief explanation",
  "time_factors": "factors affecting delivery time"
}}

Consider:
- Indian road conditions and traffic
- Fuel prices (₹100/L diesel)
- Driver wages (₹500/day)
- Toll charges
- Weight impact on speed and fuel
- Seasonal factors
- Route complexity
"""
            
            response = model.generate_content(prompt)
            
            # Try to extract JSON from response
            import json
            import re
            
            text = response.text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                try:
                    predictions = json.loads(json_match.group())
                    return predictions
                except json.JSONDecodeError:
                    pass
            
            # If JSON parsing fails, use fallback
            return self._fallback_transport_predictions(distance_data, transport_mode, weight)
            
        except Exception as e:
            print(f"AI prediction error: {e}")
            return self._fallback_transport_predictions(distance_data, transport_mode, weight)
    
    def _fallback_transport_predictions(self, distance_data: Dict, transport_mode: str, weight: float) -> Dict[str, Any]:
        """Fallback predictions when AI is unavailable"""
        distance_km = distance_data.get('distance_km', 500)
        
        # Base calculations
        fuel_efficiency = max(8, 12 - (weight / 1000))  # km/L, decreases with weight
        fuel_needed = distance_km / fuel_efficiency
        fuel_cost = fuel_needed * 100  # ₹100/L
        
        # Driver cost (₹500/day, assuming 8 hours driving per day)
        driving_hours = distance_data.get('duration_hours', distance_km / 60)
        driver_cost = (driving_hours / 8) * 500
        
        # Toll cost (approximate ₹2/km for highways)
        toll_cost = distance_km * 2
        
        # Total cost
        total_cost = fuel_cost + driver_cost + toll_cost + (weight * 5)  # ₹5/kg handling
        
        return {
            'estimated_time_hours': round(driving_hours * 1.2, 1),  # 20% buffer
            'estimated_cost_inr': round(total_cost),
            'fuel_cost_inr': round(fuel_cost),
            'driver_cost_inr': round(driver_cost),
            'toll_cost_inr': round(toll_cost),
            'risk_factors': ['traffic_delays', 'weather_conditions'],
            'cost_breakdown_explanation': f'Fuel: ₹{fuel_cost:.0f}, Driver: ₹{driver_cost:.0f}, Tolls: ₹{toll_cost:.0f}',
            'time_factors': 'Traffic conditions and route complexity considered'
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _geocode_place(self, place_name: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a place name using Nominatim (free)"""
        try:
            cache_key = f"geocode_{place_name.lower()}"
            
            with self._cache_lock:
                if cache_key in self._cache:
                    return self._cache[cache_key]
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': place_name,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'in'  # Restrict to India
            }
            
            headers = {'User-Agent': 'SCM-Logistics/1.0'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = {
                        'lat': float(data[0]['lat']),
                        'lon': float(data[0]['lon'])
                    }
                    
                    with self._cache_lock:
                        self._cache[cache_key] = result
                    
                    return result
            
        except Exception as e:
            print(f"Geocoding error for {place_name}: {e}")
        
        return Nonelate_total_time(optimized_order)
        estimated_cost = self._calculate_route_cost(optimized_order)

        return {
            'optimized_route': optimized_order,
            'total_destinations': len(destinations),
            'total_distance_km': total_distance,
            'estimated_time_hours': estimated_time,
            'estimated_cost': estimated_cost,
            'savings': {
                'distance_saved_km': total_distance * 0.15,  # 15% optimization
                'time_saved_hours': estimated_time * 0.20,   # 20% time saving
                'cost_saved': estimated_cost * 0.15          # 15% cost saving
            },
            'route_details': [
                {
                    'sequence': i + 1,
                    'destination': dest,
                    'estimated_arrival': self._calculate_arrival_time(i, optimized_order),
                    'distance_from_previous': self._get_distance_between(
                        optimized_order[i-1] if i > 0 else 'Origin',
                        dest
                    )
                }
                for i, dest in enumerate(optimized_order)
            ]
        }

    # New integrations and helper methods
    def fetch_latest_news(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """Fetch latest news related to a query using NewsAPI-compatible endpoint"""
        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'pageSize': page_size,
                'apiKey': NEWS_API_KEY,
                'sortBy': 'publishedAt',
                'language': 'en'
            }
            # Cache key and short TTL
            cache_key = f"news:{query}:{page_size}"
            cached = self._get_cache(cache_key)
            if cached:
                return cached

            # Basic rate-limit: 1 call per 1 second per endpoint
            if not self._allow_call('news', 1.0):
                return []

            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get('articles', [])
            simplified = [
                {
                    'title': a.get('title'),
                    'source': a.get('source', {}).get('name'),
                    'publishedAt': a.get('publishedAt'),
                    'description': a.get('description'),
                    'url': a.get('url')
                }
                for a in articles
            ]
            self._set_cache(cache_key, simplified, ttl=60)
            return simplified
        except Exception:
            return []

    def fetch_weather_for_location(self, city: str) -> Dict[str, Any]:
        """Fetch current weather for a given city using Open-Meteo API (free)"""
        try:
            cache_key = f"weather:{city}"
            cached = self._get_cache(cache_key)
            if cached:
                return cached

            if not self._allow_call('weather', 1.0):
                return self._get_mock_weather(city)

            # Always use Open-Meteo (free, no API key required)
            return self._fetch_weather_open_meteo(city)
            
        except Exception as e:
            print(f"Weather fetch error for {city}: {e}")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """Generate mock weather data for demo purposes"""
        import random
        
        conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Sunny']
        descriptions = ['clear sky', 'few clouds', 'scattered clouds', 'light rain', 'sunny']
        
        temp = random.randint(15, 35)
        condition_idx = random.randint(0, len(conditions) - 1)
        
        return {
            'city': city,
            'temp_c': temp,
            'feels_like': temp + random.randint(-3, 3),
            'humidity': random.randint(40, 80),
            'pressure': random.randint(1000, 1020),
            'weather': conditions[condition_idx],
            'description': descriptions[condition_idx],
            'wind_speed': random.randint(2, 15),
            'wind_deg': random.randint(0, 360),
            'visibility': random.randint(8, 15),
            'clouds': random.randint(0, 100),
            'source': 'mock'
        }
    
    def _fetch_weather_open_meteo(self, city: str) -> Dict[str, Any]:
        """Fallback weather using Open-Meteo API"""
        try:
            # Geocode city first
            geo_url = 'https://nominatim.openstreetmap.org/search'
            geo_params = {'q': city, 'format': 'json', 'limit': 1}
            geo_resp = requests.get(geo_url, params=geo_params, headers={'User-Agent': 'scm-app/1.0'}, timeout=6)
            geo_data = geo_resp.json()
            
            if not geo_data:
                return {'city': city, 'error': 'geocode_failed', 'source': 'open-meteo'}
            
            lat, lon = float(geo_data[0]['lat']), float(geo_data[0]['lon'])
            
            # Get weather from Open-Meteo
            weather_url = 'https://api.open-meteo.com/v1/forecast'
            weather_params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': 'true',
                'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m',
                'timezone': 'auto'
            }
            
            weather_resp = requests.get(weather_url, params=weather_params, timeout=8)
            weather_data = weather_resp.json()
            
            current = weather_data.get('current_weather', {})
            return {
                'city': city,
                'temp_c': current.get('temperature'),
                'weather': self._weather_code_to_description(current.get('weathercode', 0)),
                'description': self._weather_code_to_description(current.get('weathercode', 0)),
                'wind_speed': current.get('windspeed'),
                'wind_deg': current.get('winddirection'),
                'source': 'open-meteo'
            }
            
        except Exception as e:
            return {'city': city, 'error': 'weather_fetch_failed', 'detail': str(e), 'source': 'error'}
    
    def _weather_code_to_description(self, code: int) -> str:
        """Convert WMO weather code to description"""
        codes = {
            0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Fog', 48: 'Depositing rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
            55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
            71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow', 80: 'Light rain showers',
            81: 'Moderate rain showers', 82: 'Heavy rain showers', 95: 'Thunderstorm'
        }
        return codes.get(code, f'Weather code {code}')

    def fetch_weather_by_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch current weather for given coordinates using Open-Meteo API (free)"""
        try:
            cache_key = f"weather:{lat}:{lon}"
            cached = self._get_cache(cache_key)
            if cached:
                return cached

            if not self._allow_call('weather_coords', 1.0):
                return self._get_mock_weather_coords(lat, lon)

            # Use Open-Meteo API (free)
            return self._fetch_weather_coords_open_meteo(lat, lon)
            
        except Exception as e:
            print(f"Weather fetch error for coords {lat},{lon}: {e}")
            return self._get_mock_weather_coords(lat, lon)
    
    def _get_mock_weather_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """Generate mock weather data for coordinates"""
        import random
        
        conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Sunny']
        descriptions = ['clear sky', 'few clouds', 'scattered clouds', 'light rain', 'sunny']
        
        temp = random.randint(15, 35)
        condition_idx = random.randint(0, len(conditions) - 1)
        
        return {
            'lat': lat,
            'lon': lon,
            'location': f'Location {lat:.2f},{lon:.2f}',
            'temp_c': temp,
            'feels_like': temp + random.randint(-3, 3),
            'humidity': random.randint(40, 80),
            'pressure': random.randint(1000, 1020),
            'weather': conditions[condition_idx],
            'description': descriptions[condition_idx],
            'wind_speed': random.randint(2, 15),
            'wind_deg': random.randint(0, 360),
            'visibility': random.randint(8, 15),
            'clouds': random.randint(0, 100),
            'source': 'mock'
        }
    
    def _fetch_weather_coords_open_meteo(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fallback weather by coordinates using Open-Meteo"""
        try:
            url = 'https://api.open-meteo.com/v1/forecast'
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': 'true',
                'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m',
                'timezone': 'auto'
            }
            
            resp = requests.get(url, params=params, timeout=8)
            data = resp.json()
            
            current = data.get('current_weather', {})
            return {
                'lat': lat,
                'lon': lon,
                'temp_c': current.get('temperature'),
                'weather': self._weather_code_to_description(current.get('weathercode', 0)),
                'description': self._weather_code_to_description(current.get('weathercode', 0)),
                'wind_speed': current.get('windspeed'),
                'wind_deg': current.get('winddirection'),
                'source': 'open-meteo'
            }
            
        except Exception as e:
            return {'lat': lat, 'lon': lon, 'error': 'weather_fetch_failed', 'detail': str(e), 'source': 'error'}

    def decide_transport_mode(self, origin: str, destination: str) -> Dict[str, Any]:
        """Decide optimal transport mode based on simple rules using weather and news"""
        # Gather simple weather and news signals for origin and destination
        origin_weather = self.fetch_weather_for_location(origin)
        dest_weather = self.fetch_weather_for_location(destination)

        # Basic scoring for modes
        mode_scores = {
            'road': 0,
            'rail': 0,
            'air': 0,
            'sea': 0
        }

        # Favor air for long distances
        # Try to get a better distance estimate using ORS if available
        dist_info = self.get_distance_and_duration(origin, destination)
        distance = dist_info.get('distance_km', self._get_distance_between(origin, destination))
        if distance >= 1000:
            mode_scores['air'] += 3
            mode_scores['rail'] += 1
        else:
            mode_scores['road'] += 2
            mode_scores['rail'] += 1

        # Weather penalties (severe weather reduces mode score)
        def weather_penalty(w):
            if not w or 'error' in w:
                return 0
            condition = (w.get('weather') or '').lower()
            if any(x in condition for x in ['storm', 'rain', 'snow', 'thunder']):
                return 2
            if 'cloud' in condition or 'mist' in condition:
                return 1
            return 0

        penalty = weather_penalty(origin_weather) + weather_penalty(dest_weather)
        # air affected more by storms
        mode_scores['air'] -= penalty
        mode_scores['road'] -= max(0, penalty - 1)

        # Check news for major incidents
        news_origin = self.fetch_latest_news(origin, page_size=3)
        news_dest = self.fetch_latest_news(destination, page_size=3)

        def news_penalty(articles):
            score = 0
            for a in articles:
                t = (a.get('title') or '').lower()
                if any(k in t for k in ['strike', 'protest', 'flood', 'blocked', 'accident', 'closure', 'cyclone']):
                    score += 2
                elif any(k in t for k in ['delay', 'traffic', 'storm', 'warning']):
                    score += 1
            return score

        npen = news_penalty(news_origin) + news_penalty(news_dest)
        # penalize road and rail more for strikes and protests
        mode_scores['road'] -= npen
        mode_scores['rail'] -= npen

        # Choose best mode
        best_mode = max(mode_scores.items(), key=lambda x: x[1])[0]
        base_result = {
            'origin_weather': origin_weather,
            'destination_weather': dest_weather,
            'origin_news_count': len(news_origin),
            'destination_news_count': len(news_dest),
            'mode_scores': mode_scores,
            'recommended_mode': best_mode,
            'notes': 'Recommendations based on weather and recent news headlines (simplified)'
        }

        # Attempt to attach a Gemini-generated short explanation; fall back to a deterministic summary if generation fails
        try:
            prompt = (
                f"You are an expert logistics assistant. Recommend the best transport mode from {origin} to {destination}. "
                f"Mode scores: {mode_scores}. Recommended: {best_mode}. "
                f"Origin weather: {origin_weather}. Destination weather: {dest_weather}. "
                f"Provide a concise (1-2 sentence) explanation and any cautions."
            )
            gemini_text = None
            try:
                gemini_text = self._generate_gemini_text(prompt)
            except Exception as gi:
                # ensure any exception in the SDK path doesn't crash the flow
                gemini_text = None

            # If Gemini returned a usable text, use it; otherwise synthesize a short fallback summary
            if gemini_text and isinstance(gemini_text, str) and not any(k in gemini_text.lower() for k in ['failed', 'unavailable', 'error']):
                base_result['gemini_summary'] = gemini_text
            else:
                # Build a concise fallback summarizing why the mode was chosen
                origin_cond = (origin_weather.get('weather') or origin_weather.get('error') or 'unknown') if isinstance(origin_weather, dict) else 'unknown'
                dest_cond = (dest_weather.get('weather') or dest_weather.get('error') or 'unknown') if isinstance(dest_weather, dict) else 'unknown'
                score = mode_scores.get(best_mode, 0)
                fallback = f"Recommend {best_mode.upper()} (score {score}). Origin weather: {origin_cond}. Destination weather: {dest_cond}."
                base_result['gemini_summary'] = fallback
        except Exception:
            # final safety net
            origin_cond = (origin_weather.get('weather') or origin_weather.get('error') or 'unknown') if isinstance(origin_weather, dict) else 'unknown'
            dest_cond = (dest_weather.get('weather') or dest_weather.get('error') or 'unknown') if isinstance(dest_weather, dict) else 'unknown'
            score = mode_scores.get(best_mode, 0)
            base_result['gemini_summary'] = f"Recommend {best_mode.upper()} (score {score}). Origin weather: {origin_cond}. Destination weather: {dest_cond}."

        return base_result

    def compare_logistics_providers(self, origin: str, destination: str) -> List[Dict[str, Any]]:
        """Compare mock logistics providers with approximate time and cost between two locations"""
        # This is a mocked comparator; in production integrate provider APIs
        dist_info = self.get_distance_and_duration(origin, destination)
        distance = dist_info.get('distance_km', self._get_distance_between(origin, destination))


        # Use provider adapters to generate quotes (allows swapping real provider integrations later)
        from app.services.providers import get_default_providers

        adapters = get_default_providers()
        results = []
        for adapter in adapters:
            q = adapter.quote(origin, destination, distance)
            # Enrich with live signals
            provider_news = self.fetch_latest_news(q.get('provider'), page_size=2)
            provider_weather_origin = self.fetch_weather_for_location(origin)
            provider_weather_dest = self.fetch_weather_for_location(destination)
            q['notes'] = f"weather_origin={provider_weather_origin.get('weather')}, weather_dest={provider_weather_dest.get('weather')}, recent_news={len(provider_news)}, distance_used_km={distance}"
            results.append(q)

        # Sort by estimated_time then cost
        results.sort(key=lambda x: (x['estimated_time_hours'], x['estimated_cost']))
        # Try to attach a Gemini summary about providers
        try:
            provider_prompt = (
                f"You are a logistics analyst. For shipment from {origin} to {destination}, compare providers: "
                f"{[{'provider': r.get('provider'), 'mode': r.get('mode'), 'time_h': r.get('estimated_time_hours'), 'cost': r.get('estimated_cost')} for r in results]}. "
                "Provide a short recommendation (1-2 sentences) naming the top provider and why."
            )
            gemini_text = None
            try:
                gemini_text = self._generate_gemini_text(provider_prompt)
            except Exception:
                gemini_text = None

            if gemini_text and isinstance(gemini_text, str) and not any(k in gemini_text.lower() for k in ['failed', 'unavailable', 'error']):
                return {'providers': results, 'gemini_summary': gemini_text}
            else:
                # Fallback deterministic recommendation: pick the provider with lowest cost (tie break by time)
                top = sorted(results, key=lambda x: (x.get('estimated_cost', 1e9), x.get('estimated_time_hours', 1e9)))[0]
                fallback = f"Recommend {top.get('provider')} ({top.get('mode')}) based on lowest estimated cost and acceptable transit time."
                return {'providers': results, 'gemini_summary': fallback}
        except Exception:
            # Last-resort fallback
            top = sorted(results, key=lambda x: (x.get('estimated_cost', 1e9), x.get('estimated_time_hours', 1e9)))[0]
            fallback = f"Recommend {top.get('provider')} ({top.get('mode')}) based on lowest estimated cost and acceptable transit time."
            return {'providers': results, 'gemini_summary': fallback}

    def _geocode_place(self, place: str) -> Optional[Dict[str, float]]:
        """Try to geocode a place name using Nominatim"""
        try:
            cache_key = f"geocode:{place}"
            cached = self._get_cache(cache_key)
            if cached:
                return cached

            if not self._allow_call('geocode', 1.0):
                return None

            url = 'https://nominatim.openstreetmap.org/search'
            params = {'q': place, 'format': 'jsonv2', 'limit': 1}
            headers = {'User-Agent': 'AISupplyChain/1.0'}
            r = requests.get(url, params=params, headers=headers, timeout=6)
            r.raise_for_status()
            data = r.json()
            if data:
                geo = {'lat': float(data[0]['lat']), 'lon': float(data[0]['lon'])}
                self._set_cache(cache_key, geo, ttl=3600)
                return geo
        except Exception:
            return None
        return None

    def get_route_analysis_with_weather(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get comprehensive route analysis with weather and AI insights"""
        try:
            print(f"Starting route analysis: {origin} -> {destination}")
            
            # Get basic route info
            route_info = self.get_distance_and_duration(origin, destination)
            print(f"Route info: {route_info}")
            
            # Get coordinates for weather analysis
            origin_geo = self._geocode_place(origin)
            dest_geo = self._geocode_place(destination)
            
            if not origin_geo or not dest_geo:
                print(f"Geocoding failed: origin={origin_geo}, dest={dest_geo}")
                # Return basic analysis without weather
                return {
                    'route_info': route_info,
                    'weather_analysis': {
                        'points': [],
                        'weather_summary': [],
                        'ai_analysis': 'Weather data unavailable. Using standard delivery estimates.',
                        'route_conditions': {'risk_level': 'low', 'delay_factor': 1.0}
                    },
                    'delivery_estimate': {
                        'base_hours': route_info.get('duration_hours', 24),
                        'weather_adjusted_hours': route_info.get('duration_hours', 24),
                        'delay_factor': 1.0,
                        'estimated_delivery': self._calculate_delivery_window(route_info.get('duration_hours', 24))
                    },
                    'ai_insights': 'Route analysis completed with standard parameters.',
                    'recommendations': ['Standard delivery conditions expected', 'Monitor traffic conditions']
                }
            
            print(f"Geocoding successful: {origin_geo}, {dest_geo}")
            
            # Get weather along route
            weather_analysis = self.get_weather_along_route(
                origin_geo['lat'], origin_geo['lon'],
                dest_geo['lat'], dest_geo['lon'],
                samples=5
            )
            
            print(f"Weather analysis: {weather_analysis.get('route_conditions', {})}")
            
            # Calculate adjusted delivery time with weather impact
            base_hours = route_info.get('duration_hours', 24)
            weather_delay_factor = weather_analysis.get('route_conditions', {}).get('delay_factor', 1.0)
            adjusted_hours = base_hours * weather_delay_factor
            
            # Generate comprehensive analysis
            prompt = f"Analyze logistics route {origin} to {destination}: {route_info.get('distance_km', 0)}km, {base_hours}h base time. Weather: {weather_analysis.get('route_conditions', {}).get('risk_level', 'unknown')} risk. Provide delivery recommendations."
            
            ai_insights = self._generate_gemini_text(prompt, 400)
            
            result = {
                'route_info': route_info,
                'weather_analysis': weather_analysis,
                'delivery_estimate': {
                    'base_hours': base_hours,
                    'weather_adjusted_hours': round(adjusted_hours, 1),
                    'delay_factor': weather_delay_factor,
                    'estimated_delivery': self._calculate_delivery_window(adjusted_hours)
                },
                'ai_insights': ai_insights,
                'recommendations': self._generate_route_recommendations(weather_analysis, route_info)
            }
            
            print("Route analysis completed successfully")
            return result
            
        except Exception as e:
            print(f"Route analysis error: {e}")
            return {
                'error': f'Route analysis failed: {str(e)}',
                'route_info': {'distance_km': 0, 'duration_hours': 24, 'source': 'error'},
                'weather_analysis': {
                    'points': [],
                    'weather_summary': [],
                    'ai_analysis': 'Analysis unavailable due to technical issues.',
                    'route_conditions': {'risk_level': 'unknown', 'delay_factor': 1.0}
                },
                'delivery_estimate': {
                    'base_hours': 24,
                    'weather_adjusted_hours': 24,
                    'delay_factor': 1.0,
                    'estimated_delivery': self._calculate_delivery_window(24)
                },
                'ai_insights': 'Technical issues prevented detailed analysis. Using standard estimates.',
                'recommendations': ['Use standard delivery procedures', 'Monitor conditions manually']
            }
    
    def _calculate_delivery_window(self, hours: float) -> Dict[str, str]:
        """Calculate delivery time window"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        estimated_delivery = now + timedelta(hours=hours)
        
        return {
            'earliest': (now + timedelta(hours=hours * 0.9)).strftime('%Y-%m-%d %H:%M'),
            'latest': (now + timedelta(hours=hours * 1.1)).strftime('%Y-%m-%d %H:%M'),
            'estimated': estimated_delivery.strftime('%Y-%m-%d %H:%M')
        }
    
    def _generate_route_recommendations(self, weather_analysis: Dict, route_info: Dict) -> List[str]:
        """Generate route recommendations based on conditions"""
        recommendations = []
        
        conditions = weather_analysis.get('route_conditions', {})
        risk_level = conditions.get('risk_level', 'low')
        
        if risk_level == 'high':
            recommendations.extend([
                'Consider delaying shipment until weather improves',
                'Use covered transport vehicles',
                'Add extra packaging protection',
                'Monitor weather updates closely'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Proceed with caution',
                'Ensure vehicle maintenance is up to date',
                'Consider alternative routes if available'
            ])
        else:
            recommendations.append('Favorable conditions for delivery')
        
        # Distance-based recommendations
        distance = route_info.get('distance_km', 0)
        if distance > 1000:
            recommendations.append('Consider air transport for faster delivery')
        elif distance > 500:
            recommendations.append('Rail transport may be more cost-effective')
        
        return recommendations
    
    def get_distance_and_duration(self, origin: str, destination: str) -> Dict[str, Any]:
        """Return distance and duration between two places"""
        try:
            cache_key = f"route:{origin}:{destination}"
            cached = self._get_cache(cache_key)
            if cached:
                return cached

            origin_geo = self._geocode_place(origin)
            dest_geo = self._geocode_place(destination)
            
            if origin_geo and dest_geo:
                # Use haversine distance calculation
                distance_km = self.get_distance_and_duration_by_coords(
                    origin_geo['lat'], origin_geo['lon'],
                    dest_geo['lat'], dest_geo['lon']
                )['distance_km']
                
                # Estimate duration based on distance and transport mode
                duration_hours = distance_km / 60.0  # Assume 60 km/h average
                
                result = {
                    'distance_km': round(distance_km, 1),
                    'duration_hours': round(duration_hours, 2),
                    'source': 'calculated'
                }
                
                self._set_cache(cache_key, result, ttl=3600)
                return result
            
            # Fallback to internal mapping
            km = self._get_distance_between(origin, destination)
            hrs = round(km / 60.0, 1)
            return {'distance_km': km, 'duration_hours': hrs, 'source': 'internal'}
            
        except Exception:
            return {'distance_km': 0, 'duration_hours': 0, 'source': 'error'}

    def get_distance_and_duration_by_coords(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
        """Compute approximate distance (km) and duration (hours) between two coordinate points using haversine."""
        try:
            # haversine formula
            from math import radians, sin, cos, asin, sqrt

            R = 6371.0  # Earth radius in km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = R * c

            # simple travel estimate using average speed 60 km/h
            hrs = round(km / 60.0, 2) if km > 0 else 0

            res = {'distance_km': round(km, 2), 'duration_hours': hrs, 'source': 'coords'}
            return res
        except Exception:
            return {'distance_km': 0, 'duration_hours': 0, 'source': 'coords_error'}

    def get_weather_along_route(self, lat1: float, lon1: float, lat2: float, lon2: float, samples: int = 3) -> Dict[str, Any]:
        """Sample weather at N points along route with analysis"""
        try:
            if samples < 2:
                samples = 2
            
            points = []
            weather_data = []
            
            for i in range(samples):
                t = i / (samples - 1)
                lat = lat1 + (lat2 - lat1) * t
                lon = lon1 + (lon2 - lon1) * t
                w = self.fetch_weather_by_coords(lat, lon)
                points.append({'lat': lat, 'lon': lon, 'weather': w, 'position': f'Point {i+1}'})
                
                if w and 'error' not in w:
                    weather_data.append({
                        'position': f'Point {i+1}',
                        'temp': w.get('temp_c', 20),
                        'weather': w.get('weather', 'Clear'),
                        'description': w.get('description', 'Clear sky'),
                        'wind_speed': w.get('wind_speed', 5),
                        'visibility': w.get('visibility', 10)
                    })
            
            # Generate analysis (with or without Gemini)
            if weather_data:
                prompt = f"Analyze route weather for delivery: {weather_data}. Provide brief logistics analysis."
                analysis = self._generate_gemini_text(prompt, 200)
                
                return {
                    'points': points,
                    'weather_summary': weather_data,
                    'ai_analysis': analysis,
                    'route_conditions': self._assess_route_conditions(weather_data)
                }
            
            # Fallback when no weather data
            return {
                'points': points, 
                'weather_summary': [], 
                'ai_analysis': 'Weather data temporarily unavailable. Using standard delivery estimates.',
                'route_conditions': {'risk_level': 'low', 'delay_factor': 1.0, 'risk_score': 0}
            }
            
        except Exception as e:
            print(f"Weather route error: {e}")
            return {
                'points': [], 
                'error': str(e),
                'weather_summary': [],
                'ai_analysis': 'Weather analysis unavailable. Proceeding with standard delivery estimates.',
                'route_conditions': {'risk_level': 'unknown', 'delay_factor': 1.0, 'risk_score': 0}
            }
    
    def _assess_route_conditions(self, weather_data: List[Dict]) -> Dict[str, Any]:
        """Assess overall route conditions"""
        if not weather_data:
            return {'risk_level': 'unknown', 'delay_factor': 1.0}
        
        risk_factors = 0
        delay_factor = 1.0
        
        for point in weather_data:
            weather = point.get('weather', '').lower()
            wind_speed = point.get('wind_speed', 0)
            visibility = point.get('visibility', 10)
            
            # Assess risk factors
            if any(condition in weather for condition in ['rain', 'storm', 'snow']):
                risk_factors += 2
                delay_factor += 0.15
            elif any(condition in weather for condition in ['cloud', 'fog']):
                risk_factors += 1
                delay_factor += 0.05
            
            if wind_speed > 10:  # High wind
                risk_factors += 1
                delay_factor += 0.1
            
            if visibility < 5:  # Poor visibility
                risk_factors += 2
                delay_factor += 0.2
        
        # Determine risk level
        if risk_factors >= 6:
            risk_level = 'high'
        elif risk_factors >= 3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'delay_factor': min(delay_factor, 2.0),  # Cap at 100% delay
            'risk_score': risk_factors
        }

    def _generate_gemini_text(self, prompt: str, max_output_tokens: int = 256) -> str:
        """Generate text using Gemini AI with fallback"""
        if genai is None:
            return self._generate_fallback_analysis(prompt)

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_output_tokens,
                    temperature=0.7
                )
            )
            return response.text if response.text else self._generate_fallback_analysis(prompt)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._generate_fallback_analysis(prompt)
    
    def _generate_fallback_analysis(self, prompt: str) -> str:
        """Generate fallback analysis when Gemini is unavailable"""
        if 'route weather' in prompt.lower():
            return "Route analysis: Weather conditions appear favorable for delivery. Monitor for any sudden weather changes. Estimated delivery time may vary by 10-15% based on current conditions. Recommend standard precautions for road transport."
        elif 'transport mode' in prompt.lower():
            return "Transport recommendation: Road transport is suitable for this route. Consider weather conditions and traffic patterns. Rail transport may be more cost-effective for longer distances."
        elif 'provider' in prompt.lower():
            return "Provider analysis: Multiple logistics providers available for this route. Compare based on cost, reliability, and delivery time. Consider weather impact on different transport modes."
        else:
            return "Analysis completed using statistical models. Weather and route conditions have been assessed for optimal delivery planning."

    # Simple cache helpers
    def _get_cache(self, key: str):
        with self._cache_lock:
            item = self._cache.get(key)
            if not item:
                return None
            value, expires = item
            if time.time() > expires:
                del self._cache[key]
                return None
            return value

    def _set_cache(self, key: str, value, ttl: int = 60):
        with self._cache_lock:
            self._cache[key] = (value, time.time() + ttl)

    def _allow_call(self, endpoint: str, min_interval: float) -> bool:
        """Allow a call to an external endpoint if min_interval seconds have passed since last call."""
        now = time.time()
        last = self._last_called.get(endpoint, 0)
        if now - last < min_interval:
            return False
        self._last_called[endpoint] = now
        return True

    def get_analytics(self) -> Dict[str, Any]:
        """Get enhanced logistics performance analytics"""

        total_shipments = len(self._mock_shipments)

        # Status breakdown
        status_counts = {}
        for shipment in self._mock_shipments:
            status = shipment['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        # Transport mode breakdown
        mode_counts = {}
        mode_costs = {}
        for shipment in self._mock_shipments:
            mode = shipment.get('transport_mode', 'road')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            mode_costs[mode] = mode_costs.get(mode, 0) + shipment.get('cost', 0)

        # Priority breakdown
        priority_counts = {}
        for shipment in self._mock_shipments:
            priority = shipment.get('priority', 'standard')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Calculate on-time delivery rate
        delivered_shipments = [s for s in self._mock_shipments if s['status'] == 'Delivered']
        on_time_count = 0

        for shipment in delivered_shipments:
            if shipment.get('actual_delivery') and shipment.get('eta'):
                actual = datetime.strptime(shipment['actual_delivery'], '%Y-%m-%d').date()
                expected = datetime.strptime(shipment['eta'], '%Y-%m-%d').date()
                if actual <= expected:
                    on_time_count += 1

        on_time_rate = (on_time_count / len(delivered_shipments) * 100) if delivered_shipments else 0

        # Calculate average delivery time
        total_delivery_days = 0
        for shipment in delivered_shipments:
            if shipment.get('shipped_date') and shipment.get('actual_delivery'):
                shipped = datetime.strptime(shipment['shipped_date'], '%Y-%m-%d').date()
                delivered = datetime.strptime(shipment['actual_delivery'], '%Y-%m-%d').date()
                total_delivery_days += (delivered - shipped).days

        avg_delivery_time = (total_delivery_days / len(delivered_shipments)) if delivered_shipments else 4.2

        # Cost analytics
        total_cost = sum(shipment.get('cost', 0) for shipment in self._mock_shipments)
        avg_cost_per_shipment = total_cost / total_shipments if total_shipments > 0 else 0
        
        # Calculate cost efficiency by mode
        cost_efficiency = {}
        for mode, cost in mode_costs.items():
            count = mode_counts.get(mode, 1)
            cost_efficiency[mode] = round(cost / count, 2)

        return {
            'total_shipments': total_shipments,
            'status_breakdown': status_counts,
            'transport_mode_breakdown': mode_counts,
            'priority_breakdown': priority_counts,
            'on_time_delivery_rate': round(on_time_rate, 1),
            'average_delivery_time_days': round(avg_delivery_time, 1),
            'total_shipping_cost': total_cost,
            'average_cost_per_shipment': round(avg_cost_per_shipment, 2),
            'cost_efficiency_by_mode': cost_efficiency,
            'performance_trends': {
                'last_30_days': {
                    'shipments': total_shipments,
                    'on_time_rate': round(on_time_rate, 1),
                    'avg_cost': round(avg_cost_per_shipment, 2)
                }
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate logistics recommendations based on current data"""
        recommendations = []
        
        # Analyze delivery performance
        delivered = [s for s in self._mock_shipments if s['status'] == 'Delivered']
        if delivered:
            on_time = sum(1 for s in delivered if s.get('actual_delivery') and s.get('eta') and 
                         datetime.strptime(s['actual_delivery'], '%Y-%m-%d').date() <= 
                         datetime.strptime(s['eta'], '%Y-%m-%d').date())
            rate = (on_time / len(delivered)) * 100
            
            if rate < 80:
                recommendations.append("Consider optimizing delivery routes to improve on-time performance")
            if rate > 95:
                recommendations.append("Excellent delivery performance - maintain current standards")
        
        # Analyze transport modes
        modes = {}
        for s in self._mock_shipments:
            mode = s.get('transport_mode', 'road')
            modes[mode] = modes.get(mode, 0) + 1
        
        if modes.get('road', 0) > len(self._mock_shipments) * 0.8:
            recommendations.append("Consider diversifying transport modes for better cost efficiency")
        
        return recommendations[:3]  # Return top 3 recommendations

    def _calculate_distance_cost(self, origin: str, destination: str) -> float:
        """Calculate distance-based cost"""

        # Simplified distance calculation
        distance_map = {
            ('Bangalore', 'Mumbai'): 980,
            ('Bangalore', 'Delhi'): 2150,
            ('Bangalore', 'Chennai'): 350,
            ('Bangalore', 'Hyderabad'): 570,
            ('Bangalore', 'Pune'): 840,
            ('Bangalore', 'Kolkata'): 1880,
        }

        key = (origin, destination)
        reverse_key = (destination, origin)

        distance = distance_map.get(key) or distance_map.get(reverse_key, 500)

        # ₹5 per km base rate
        return distance * 5.0

    def _calculate_shipping_cost(self, weight: float, items_count: int, distance_cost: float, transport_mode: str = 'road') -> float:
        """Calculate total shipping cost with transport mode consideration"""

        base_cost = 100  # Base handling charge
        weight_cost = weight * 15  # ₹15 per kg
        item_cost = items_count * 25  # ₹25 per item
        
        # Transport mode multipliers
        mode_multipliers = {
            'road': 1.0,
            'rail': 0.8,
            'air': 2.5,
            'sea': 0.6
        }
        
        mode_multiplier = mode_multipliers.get(transport_mode, 1.0)
        total_cost = (base_cost + weight_cost + item_cost + distance_cost) * mode_multiplier

        return round(total_cost, 2)
    
    def _calculate_delivery_time(self, transport_mode: str, base_days: int) -> int:
        """Calculate delivery time based on transport mode"""
        
        mode_factors = {
            'road': 1.0,
            'rail': 1.2,
            'air': 0.3,
            'sea': 2.0
        }
        
        factor = mode_factors.get(transport_mode, 1.0)
        return max(1, int(base_days * factor))

    def _get_next_checkpoint(self, origin: str, destination: str) -> str:
        """Get next checkpoint for shipment"""

        route_map = {
            ('Bangalore', 'Mumbai'): 'Pune Hub',
            ('Bangalore', 'Delhi'): 'Hyderabad Hub',
            ('Bangalore', 'Chennai'): 'Direct Route',
            ('Bangalore', 'Hyderabad'): 'Direct Route',
            ('Bangalore', 'Pune'): 'Mumbai Hub',
            ('Bangalore', 'Kolkata'): 'Hyderabad Hub',
        }

        key = (origin, destination)
        return route_map.get(key, 'Regional Hub')

    def _simple_route_optimization(self, destinations: List[str]) -> List[str]:
        """Simple route optimization algorithm"""

        # For demo purposes, just sort alphabetically with some logic
        # In reality, this would use sophisticated algorithms like TSP solvers

        priority_cities = ['Mumbai', 'Delhi', 'Chennai', 'Hyderabad']

        prioritized = []
        others = []

        for dest in destinations:
            if any(city in dest for city in priority_cities):
                prioritized.append(dest)
            else:
                others.append(dest)

        # Sort prioritized cities by distance (simplified)
        prioritized.sort()
        others.sort()

        return prioritized + others

    def _calculate_total_distance(self, route: List[str]) -> float:
        """Calculate total distance for route"""

        total = 0
        previous = 'Bangalore'  # Starting point

        for destination in route:
            total += self._get_distance_between(previous, destination)
            previous = destination

        return round(total, 1)

    def _calculate_total_time(self, route: List[str]) -> float:
        """Calculate total time for route"""

        total_distance = self._calculate_total_distance(route)
        # Average speed of 60 km/h including stops
        return round(total_distance / 60, 1)

    def _calculate_route_cost(self, route: List[str]) -> float:
        """Calculate total cost for route"""

        total_distance = self._calculate_total_distance(route)
        return round(total_distance * 8 + len(route) * 200, 2)  # ₹8/km + ₹200/stop

    def _get_distance_between(self, origin: str, destination: str) -> float:
        """Get distance between two cities"""

        distance_map = {
            ('Bangalore', 'Mumbai'): 980,
            ('Bangalore', 'Delhi'): 2150,
            ('Bangalore', 'Chennai'): 350,
            ('Bangalore', 'Hyderabad'): 570,
            ('Bangalore', 'Pune'): 840,
            ('Bangalore', 'Kolkata'): 1880,
            ('Mumbai', 'Delhi'): 1400,
            ('Mumbai', 'Chennai'): 1340,
            ('Delhi', 'Chennai'): 2180,
            ('Delhi', 'Hyderabad'): 1580,
        }

        key = (origin, destination)
        reverse_key = (destination, origin)

        return distance_map.get(key) or distance_map.get(reverse_key, 500)

    def _calculate_arrival_time(self, index: int, route: List[str]) -> str:
        """Calculate estimated arrival time for destination"""

        # Start at 9:00 AM, add time for each previous destination
        start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        total_hours = 0
        previous = 'Bangalore'

        for i in range(index + 1):
            destination = route[i]
            distance = self._get_distance_between(previous, destination)
            hours = distance / 60  # 60 km/h average
            total_hours += hours + 0.5  # Add 30 minutes for each stop
            previous = destination

        arrival_time = start_time + timedelta(hours=total_hours)
        return arrival_time.strftime('%H:%M on %Y-%m-%d')

    def _get_mock_shipments(self) -> List[Dict[str, Any]]:
        """Get mock shipment data"""

        return [
            {
                'id': 'SHP-A1B2C3D4',
                'origin': 'Bangalore Distribution Center',
                'destination': 'Mumbai',
                'status': 'Delivered',
                'items_count': 25,
                'total_weight': 45.5,
                'cost': 4250.0,
                'transport_mode': 'road',
                'priority': 'standard',
                'created_date': '2025-09-08',
                'shipped_date': '2025-09-09',
                'eta': '2025-09-12',
                'actual_delivery': '2025-09-11',
                'items': [
                    {'description': 'Electronics Package', 'quantity': 15, 'weight': 30.0},
                    {'description': 'Textile Items', 'quantity': 10, 'weight': 15.5}
                ],
                'notes': 'Handle with care - fragile items',
                'tracking_info': {
                    'last_update': '2025-09-11T18:30:00',
                    'location': 'Mumbai',
                    'progress_percentage': 100,
                    'status_history': [
                        {'status': 'Processing', 'timestamp': '2025-09-08T10:00:00', 'location': 'Bangalore', 'message': 'Order received'},
                        {'status': 'In Transit', 'timestamp': '2025-09-09T08:00:00', 'location': 'Bangalore Hub', 'message': 'Shipment dispatched'},
                        {'status': 'In Transit', 'timestamp': '2025-09-10T14:30:00', 'location': 'Pune Hub', 'message': 'In transit via Pune'},
                        {'status': 'Delivered', 'timestamp': '2025-09-11T18:30:00', 'location': 'Mumbai', 'message': 'Successfully delivered'}
                    ]
                }
            },
            {
                'id': 'SHP-E5F6G7H8',
                'origin': 'Bangalore Distribution Center',
                'destination': 'Chennai',
                'status': 'In Transit',
                'items_count': 12,
                'total_weight': 20.0,
                'cost': 1950.0,
                'transport_mode': 'road',
                'priority': 'express',
                'created_date': '2025-09-11',
                'shipped_date': '2025-09-11',
                'eta': '2025-09-13',
                'actual_delivery': None,
                'items': [
                    {'description': 'Medical Supplies', 'quantity': 8, 'weight': 12.0},
                    {'description': 'Documents', 'quantity': 4, 'weight': 8.0}
                ],
                'notes': 'Express delivery - time sensitive',
                'tracking_info': {
                    'last_update': '2025-09-12T14:20:00',
                    'location': 'En Route to Chennai',
                    'next_checkpoint': 'Chennai Hub',
                    'progress_percentage': 65,
                    'status_history': [
                        {'status': 'Processing', 'timestamp': '2025-09-11T09:00:00', 'location': 'Bangalore', 'message': 'Express order received'},
                        {'status': 'In Transit', 'timestamp': '2025-09-11T11:00:00', 'location': 'Bangalore Hub', 'message': 'Dispatched for express delivery'},
                        {'status': 'In Transit', 'timestamp': '2025-09-12T14:20:00', 'location': 'Highway Checkpoint', 'message': 'En route to Chennai'}
                    ]
                }
            },
            {
                'id': 'SHP-I9J0K1L2',
                'origin': 'Bangalore Distribution Center',
                'destination': 'Delhi',
                'status': 'Processing',
                'items_count': 35,
                'total_weight': 80.0,
                'cost': 6500.0,
                'transport_mode': 'rail',
                'priority': 'standard',
                'created_date': '2025-09-12',
                'shipped_date': None,
                'eta': '2025-09-16',
                'actual_delivery': None,
                'items': [
                    {'description': 'Bulk Grocery Items', 'quantity': 20, 'weight': 50.0},
                    {'description': 'Household Products', 'quantity': 15, 'weight': 30.0}
                ],
                'notes': 'Bulk shipment - rail transport for cost efficiency',
                'tracking_info': {
                    'last_update': '2025-09-12T10:00:00',
                    'location': 'Bangalore Warehouse',
                    'next_checkpoint': 'Railway Station',
                    'progress_percentage': 15,
                    'status_history': [
                        {'status': 'Processing', 'timestamp': '2025-09-12T10:00:00', 'location': 'Bangalore Warehouse', 'message': 'Order received - packaging in progress'}
                    ]
                }
            },
            {
                'id': 'SHP-M3N4O5P6',
                'origin': 'Bangalore Distribution Center',
                'destination': 'Hyderabad',
                'status': 'Delivered',
                'items_count': 18,
                'total_weight': 30.5,
                'cost': 2850.0,
                'transport_mode': 'road',
                'priority': 'urgent',
                'created_date': '2025-09-09',
                'shipped_date': '2025-09-09',
                'eta': '2025-09-11',
                'actual_delivery': '2025-09-10',
                'items': [
                    {'description': 'Pharmaceutical Products', 'quantity': 10, 'weight': 15.0},
                    {'description': 'Medical Equipment', 'quantity': 8, 'weight': 15.5}
                ],
                'notes': 'Urgent medical supplies - priority delivery',
                'tracking_info': {
                    'last_update': '2025-09-10T16:45:00',
                    'location': 'Hyderabad',
                    'progress_percentage': 100,
                    'status_history': [
                        {'status': 'Processing', 'timestamp': '2025-09-09T08:00:00', 'location': 'Bangalore', 'message': 'Urgent order received'},
                        {'status': 'In Transit', 'timestamp': '2025-09-09T10:00:00', 'location': 'Bangalore Hub', 'message': 'Priority dispatch'},
                        {'status': 'Delivered', 'timestamp': '2025-09-10T16:45:00', 'location': 'Hyderabad', 'message': 'Delivered ahead of schedule'}
                    ]
                }
            },
            {
                'id': 'SHP-Q7R8S9T0',
                'origin': 'Bangalore Distribution Center',
                'destination': 'Kolkata',
                'status': 'In Transit',
                'items_count': 22,
                'total_weight': 55.0,
                'cost': 8750.0,
                'transport_mode': 'air',
                'priority': 'express',
                'created_date': '2025-09-13',
                'shipped_date': '2025-09-13',
                'eta': '2025-09-14',
                'actual_delivery': None,
                'items': [
                    {'description': 'Electronic Components', 'quantity': 12, 'weight': 25.0},
                    {'description': 'Precision Instruments', 'quantity': 10, 'weight': 30.0}
                ],
                'notes': 'Air freight - high value items',
                'tracking_info': {
                    'last_update': '2025-09-13T16:00:00',
                    'location': 'In Flight',
                    'next_checkpoint': 'Kolkata Airport',
                    'progress_percentage': 75,
                    'status_history': [
                        {'status': 'Processing', 'timestamp': '2025-09-13T08:00:00', 'location': 'Bangalore', 'message': 'Express air shipment processed'},
                        {'status': 'In Transit', 'timestamp': '2025-09-13T12:00:00', 'location': 'Bangalore Airport', 'message': 'Loaded for air transport'},
                        {'status': 'In Transit', 'timestamp': '2025-09-13T16:00:00', 'location': 'In Flight', 'message': 'En route to Kolkata'}
                    ]
                }
            }
        ]