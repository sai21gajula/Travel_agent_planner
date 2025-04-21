# travel_agent/tools/geoapify_tools.py
import os
import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List

# Store key in .env: GEOAPIFY_API_KEY=YOUR_KEY
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

class GeoapifyPOIInput(BaseModel):
    """Input schema for GeoapifyPOITool."""
    categories: List[str] = Field(..., description="List of Geoapify categories (e.g., ['tourism.attraction', 'catering.restaurant'])")
    latitude: float = Field(..., description="Latitude of the center point for the search (e.g., 48.8566)")
    longitude: float = Field(..., description="Longitude of the center point for the search (e.g., 2.3522)")
    radius: int = Field(5000, description="Search radius in meters (default 5000m)")
    limit: int = Field(10, description="Maximum number of results to return (default 10, max 100 usually)")

class GeoapifyPOITool(BaseTool):
    """
    Tool that searches for Points of Interest (POI) like restaurants, attractions, shops etc.,
    around specific coordinates (latitude, longitude) using the Geoapify Places API.
    Requires categories, latitude, and longitude. Returns names, addresses, and distances.
    Refer to Geoapify documentation for a full list of category names.
    """
    name: str = "geoapify_points_of_interest_search"
    description: str = """
    Searches for Points of Interest (POI) like restaurants, tourist attractions, shops etc.,
    around a specific location (latitude, longitude) using the Geoapify Places API.
    Requires a list of categories (e.g., 'tourism.attraction', 'catering.restaurant'), latitude, and longitude.
    Returns names, addresses, and distances.
    """
    args_schema: Type[BaseModel] = GeoapifyPOIInput

    def _run(self, categories: List[str], latitude: float, longitude: float, radius: int = 5000, limit: int = 10) -> str:
        """Executes the Geoapify POI search."""
        if not GEOAPIFY_API_KEY:
            return "Geoapify API key not configured in .env file."

        # Use the v2/places endpoint
        base_url = "https://api.geoapify.com/v2/places"
        # Ensure limit is within reasonable bounds (Geoapify might have its own max)
        limit = min(limit, 100)

        params = {
            'categories': ','.join(categories),
            'filter': f'circle:{longitude},{latitude},{radius}',
            'bias': f'proximity:{longitude},{latitude}', # Prioritize closer results
            'limit': limit,
            'apiKey': GEOAPIFY_API_KEY
        }

        try:
            print(f"Calling Geoapify Places API with params: {params}") # Debug print
            response = requests.get(base_url, params=params)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if not data or 'features' not in data or not data['features']:
                cat_str = ', '.join(categories)
                return f"No Geoapify POIs found for categories '{cat_str}' near ({latitude}, {longitude}). Check coordinates and categories."

            results_str = f"Geoapify POIs Found (Categories: {', '.join(categories)}):\n\n"
            for i, feature in enumerate(data['features'][:limit], 1):
                properties = feature.get('properties', {})
                # Try to get a meaningful name, fallback to address parts if needed
                name = properties.get('name', properties.get('address_line1', 'N/A'))
                address = properties.get('formatted', 'N/A')
                distance = properties.get('distance', 'N/A')
                poi_categories = properties.get('categories', [])

                results_str += f"{i}. Name: {name}\n"
                results_str += f"   Address: {address}\n"
                if distance != 'N/A':
                    results_str += f"   Distance: ~{distance}m\n"
                if poi_categories:
                    results_str += f"   Main Categories: {', '.join(poi_categories)}\n"
                results_str += "\n" # Add space between entries

            return results_str

        except requests.exceptions.RequestException as e:
            print(f"Error calling Geoapify API: {e}") # Log error
            return f"Error calling Geoapify API: {e}"
        except Exception as e:
            print(f"Unexpected error processing Geoapify POI search: {str(e)}") # Log error
            return f"Unexpected error processing Geoapify POI search: {str(e)}"

