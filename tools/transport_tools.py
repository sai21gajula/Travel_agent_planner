# travel_agent/tools/transport_tools.py
import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List

# Store key in .env: TRANSITLAND_API_KEY=YOUR_KEY
TRANSITLAND_API_KEY = os.getenv("TRANSITLAND_API_KEY")

class PublicTransportInput(BaseModel):
    """Input schema for PublicTransportSearchTool."""
    latitude: float = Field(..., description="Latitude of the center point for the search")
    longitude: float = Field(..., description="Longitude of the center point for the search")
    radius: int = Field(1000, description="Search radius in meters (default 1000m) to find nearby stops/routes")
    vehicle_type: Optional[str] = Field(None, description="Optional: Filter by vehicle type (e.g., 'bus', 'train', 'subway', 'tram')")

class PublicTransportSearchTool(BaseTool):
    """
    Searches for public transport routes (bus, train, subway, etc.) near a specific
    location (latitude, longitude) using the Transitland API.
    Returns a list of nearby routes and their operators.
    Coverage depends on data availability in Transitland for the searched area.
    Does not provide real-time schedules.
    """
    name: str = "public_transport_route_search"
    description: str = """
    Searches for public transport routes (bus, train, subway, tram) and operators
    near a specific location defined by latitude and longitude.
    Useful for finding what public transit options are available in an area.
    Optionally filter by vehicle type (e.g., 'bus', 'train').
    """
    args_schema: Type[BaseModel] = PublicTransportInput

    def _run(self, latitude: float, longitude: float, radius: int = 1000, vehicle_type: Optional[str] = None) -> str:
        """Executes the Transitland route search."""
        if not TRANSITLAND_API_KEY:
            return "Transitland API key not configured in .env file."

        # Transitland API v2 endpoint for routes
        base_url = "https://transit.land/api/v2/routes"

        params = {
            'lat': latitude,
            'lon': longitude,
            'radius': radius,
            'per_page': 10 # Limit the number of results initially
            # 'include': 'operator' # Optionally include operator details directly
        }
        if vehicle_type:
            # Map common names to Transitland vehicle types if needed, or pass directly
            # Check Transitland docs for exact vehicle type values (e.g., 0: Tram, 1: Subway, 2: Rail, 3: Bus, 4: Ferry...)
            # For simplicity, we'll assume direct string matching might work for common types
            # A more robust implementation would map user input ('train') to the correct code ('2')
            params['vehicle_type'] = vehicle_type.lower() # Example, adjust based on API spec

        headers = {
            'ApiKey': TRANSITLAND_API_KEY,
            'Accept': 'application/json'
        }

        try:
            print(f"Calling Transitland Routes API with params: {params}") # Debug print
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if not data or 'routes' not in data or not data['routes']:
                filter_msg = f" of type '{vehicle_type}'" if vehicle_type else ""
                return f"No Transitland routes found{filter_msg} near ({latitude}, {longitude}) within {radius}m. Coverage may be limited."

            results_str = f"Nearby Public Transport Routes near ({latitude}, {longitude}):\n\n"
            seen_routes = set() # Avoid duplicates if API returns multiple entries for same route nearby
            count = 0
            max_display = 10 # Limit displayed results

            for route in data['routes']:
                if count >= max_display:
                    break

                route_id = route.get('onestop_id')
                if route_id in seen_routes:
                    continue # Skip duplicate

                props = route.get('properties', {})
                short_name = props.get('route_short_name', '')
                long_name = props.get('route_long_name', '')
                vehicle = props.get('vehicle_type', 'N/A') # Get vehicle type if available

                # Construct a display name
                display_name = f"{short_name} - {long_name}" if short_name and long_name else long_name or short_name or "Unnamed Route"

                # Extract operator info (might be nested differently, check API response)
                # This assumes operator info is directly in properties or relationships
                operator_name = "Unknown Operator"
                agency_info = props.get('agency', {}) # Check properties first
                if agency_info:
                    operator_name = agency_info.get('agency_name', operator_name)
                # Alternatively, check relationships if 'operator' was included
                # relationships = route.get('relationships', {}).get('operator', {}).get('data', {})
                # operator_onestop_id = relationships.get('id')
                # Need another API call to get operator details from ID usually, unless included

                results_str += f"{count+1}. Route: {display_name}\n"
                results_str += f"   Type: {vehicle}\n"
                results_str += f"   Operator: {operator_name}\n" # Operator info might require another call or 'include' param
                results_str += f"   Transitland ID: {route_id}\n\n"

                seen_routes.add(route_id)
                count += 1

            if count == 0:
                 filter_msg = f" of type '{vehicle_type}'" if vehicle_type else ""
                 return f"Found route data but could not parse details for routes{filter_msg} near ({latitude}, {longitude})."

            if 'meta' in data and data['meta'].get('next'):
                results_str += "(More routes might be available...)\n"

            return results_str

        except requests.exceptions.RequestException as e:
            print(f"Error calling Transitland API: {e}") # Log error
            # Check for common errors like 401 Unauthorized
            if e.response is not None and e.response.status_code == 401:
                 return "Error calling Transitland API: Unauthorized. Check your TRANSITLAND_API_KEY."
            return f"Error calling Transitland API: {e}"
        except Exception as e:
            print(f"Unexpected error processing Transitland route search: {str(e)}") # Log error
            return f"Unexpected error processing Transitland route search: {str(e)}"