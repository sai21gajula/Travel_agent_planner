# travel_agent/tools/transport_tools.py
import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List, Dict, ClassVar

# Store key in .env: TRANSITLAND_API_KEY=YOUR_KEY
TRANSITLAND_API_KEY = os.getenv("TRANSITLAND_API_KEY")

class PublicTransportInput(BaseModel):
    """Input schema for PublicTransportSearchTool."""
    latitude: float = Field(..., description="Latitude of the center point for the search")
    longitude: float = Field(..., description="Longitude of the center point for the search")
    radius: int = Field(1000, description="Search radius in meters (default 1000m) to find nearby stops/routes")
    vehicle_type: Optional[str] = Field(None, description="Optional: Filter by vehicle type (e.g., 'bus', 'train', 'subway', 'tram')")
    location_name: Optional[str] = Field("this location", description="Name of the location being searched")

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

    def _run(self, latitude: float, longitude: float, radius: int = 1000, vehicle_type: Optional[str] = None, location_name: Optional[str] = "this location") -> str:
        """Executes the Transitland route search."""
        try:
            # Try to access the API directly through the REST endpoint instead of routes endpoint
            # This is an alternative approach that might work better
            base_url = "https://transit.land/api/v2/rest/stops"
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'radius': radius,
                'apikey': TRANSITLAND_API_KEY,  # Use apikey parameter as documented
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'TravelAgentCrew/1.0'
            }
            
            # Increase timeout from 10 to 20 seconds
            response = requests.get(base_url, params=params, headers=headers, timeout=20)
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                if 'stops' in data and data['stops']:
                    # Process the stops data to extract route information
                    stops_count = len(data['stops'])
                    routes_set = set()
                    
                    # Extract unique routes from the stops
                    for stop in data['stops']:
                        if 'routes' in stop:
                            for route in stop['routes']:
                                route_name = route.get('route_name', 'Unnamed Route')
                                agency_name = route.get('agency_name', 'Unknown Agency')
                                route_id = f"{route_name} ({agency_name})"
                                routes_set.add(route_id)
                    
                    # Format the results
                    results_str = f"Public Transport Options near {location_name} ({latitude}, {longitude}):\n\n"
                    results_str += f"Found {stops_count} transit stops within {radius}m.\n\n"
                    
                    if routes_set:
                        results_str += "Routes serving this area:\n"
                        for i, route in enumerate(sorted(list(routes_set)), 1):
                            results_str += f"{i}. {route}\n"
                    else:
                        results_str += "No specific route information available for these stops.\n"
                    
                    results_str += "\nNote: This information is based on available transit data and may not include all routes or recent changes."
                    return results_str
                else:
                    return f"No transit stops found near {location_name} ({latitude}, {longitude}) within {radius}m. The area may not have public transportation coverage in our database."
            else:
                # Handle API error
                print(f"API Error: {response.status_code} - {response.text}")
                return self._get_fallback_message(latitude, longitude, location_name)
                
        except requests.exceptions.Timeout:
            print(f"Timeout while accessing Transitland API for {location_name}")
            return self._get_fallback_message(latitude, longitude, location_name)
            
        except Exception as e:
            print(f"Error calling Transitland API: {str(e)}")
            return self._get_fallback_message(latitude, longitude, location_name)
    
    def _get_fallback_message(self, latitude, longitude, location_name):
        """Return a fallback message when API access fails."""
        return f"""
**Important Note:** Unable to retrieve public transportation data for {location_name} ({latitude}, {longitude}). This could be due to API limitations, coverage gaps, or temporary service issues.

For accurate public transportation information, please check these resources:
- Local transit authority websites
- Google Maps transit directions
- Transit apps like Citymapper, Moovit, or Transit
- Official tourism websites for the destination

For intercity travel, consider:
- Airlines for flights
- Rail services for long-distance train travel
- Bus companies for intercity coaches
- Ride-sharing services

I apologize for not being able to provide specific route details at this time.
"""

# City code lookup tool for Amadeus integration
class CityCodeLookupInput(BaseModel):
    """Input schema for CityCodeLookupTool."""
    city_name: str = Field(..., description="The name of the city to lookup the IATA code for")
    country_code: Optional[str] = Field(None, description="Optional: The two-letter ISO country code to refine the search")

class CityCodeLookupTool(BaseTool):
    """
    A simple tool to lookup IATA city codes for major cities.
    This is needed for Amadeus API calls which require city codes.
    """
    name: str = "city_code_lookup"
    description: str = """
    Looks up the IATA city code for a given city name.
    Useful when you need to convert a city name to its 3-letter IATA code for flight searches.
    """
    args_schema: Type[BaseModel] = CityCodeLookupInput
    
    # A small database of major city codes
    CITY_CODES: ClassVar[Dict[str, str]] = {
        "new york": "NYC",
        "paris": "PAR",
        "london": "LON",
        "tokyo": "TYO",
        "rome": "ROM",
        "barcelona": "BCN",
        "amsterdam": "AMS",
        "berlin": "BER",
        "singapore": "SIN",
        "hong kong": "HKG",
        "sydney": "SYD",
        "dubai": "DXB",
        "los angeles": "LAX",
        "chicago": "CHI",
        "miami": "MIA",
        "toronto": "YTO",
        "madrid": "MAD",
        "munich": "MUC",
        "bangkok": "BKK",
        "beijing": "BJS",
        "shanghai": "SHA",
        "delhi": "DEL",
        "mumbai": "BOM",
        "rio de janeiro": "RIO",
        "sao paulo": "SAO",
        "mexico city": "MEX",
        "cairo": "CAI",
        "johannesburg": "JNB",
        "moscow": "MOW",
        "istanbul": "IST",
        "athens": "ATH",
        "vienna": "VIE",
        "dublin": "DUB",
        "brussels": "BRU",
        "zurich": "ZRH",
        "geneva": "GVA",
        "stockholm": "STO",
        "oslo": "OSL",
        "copenhagen": "CPH",
        "helsinki": "HEL",
        "seoul": "SEL",
        "kuala lumpur": "KUL",
        "manila": "MNL",
        "jakarta": "JKT",
        "boston": "BOS",
        "san francisco": "SFO",
        "washington": "WAS",
        "seattle": "SEA",
        "vancouver": "YVR",
        "montreal": "YMQ",
        "melbourne": "MEL",
        "auckland": "AKL",
        "wellington": "WLG"
    }
    
    def _run(self, city_name: str, country_code: Optional[str] = None) -> str:
        """Find the IATA city code for the given city."""
        city_key = city_name.lower().strip()
        
        # First try direct match
        if city_key in self.CITY_CODES:
            return f"IATA city code for {city_name}: {self.CITY_CODES[city_key]}"
        
        # Try partial match
        for known_city, code in self.CITY_CODES.items():
            if city_key in known_city or known_city in city_key:
                return f"IATA city code for {city_name} (matched as {known_city}): {code}"
        
        # No match found
        return f"Could not find IATA city code for {city_name}. Please use a more common city name or specify a major nearby city. For flights, you may need to search for the nearest major airport code."