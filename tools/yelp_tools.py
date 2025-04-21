"""
Yelp API tools for the travel agent crew.
"""
import os
import json
from crewai.tools import BaseTool
from yelpapi import YelpAPI
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class YelpInput(BaseModel):
    """Input for the YelpSearchTool."""
    term: str = Field(..., description="The search term, e.g., 'restaurants' or 'Italian food'")
    location: str = Field(..., description="The location to search in, e.g., 'Paris, France'")
    price: Optional[str] = Field(None, description="Price level (1, 2, 3, 4) where 1 is $ and 4 is $$$$")
    limit: Optional[int] = Field(5, description="Number of results to return (default 5, max 10)")

class YelpRestaurantSearchTool(BaseTool):
    """Tool that searches for restaurants using Yelp API."""
    name: str = "yelp_restaurant_search"
    description: str = """
    Useful for finding restaurants, cafes, and other dining options.
    Input should include a search term (e.g., 'Italian restaurants') and a location (e.g., 'Rome, Italy').
    Optionally include a price level (1-4, where 1 is $ and 4 is $$$$) and the number of results to return.
    """
    yelp_api: Any = None
    
    def __init__(self):
        """Initialize the Yelp API client."""
        super().__init__()
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            # For development without API key, provide mock data
            self.yelp_api = None
            print("WARNING: YELP_API_KEY not set, using mock restaurant data")
        else:
            self.yelp_api = YelpAPI(api_key=api_key)
    
    def _run(self, term: str, location: str, price: Optional[str] = None, limit: Optional[int] = 5) -> str:
        """Run the Yelp restaurant search tool."""
        try:
            # Check if we have a real API client
            if not self.yelp_api:
                # Return mock data if no API key
                return self._get_mock_restaurants(term, location, price, limit)
                
            # Validate and process inputs
            if limit > 10:
                limit = 10  # Cap at 10 to avoid excessive results
            
            # Convert price string to Yelp format (comma-separated)
            price_filter = None
            if price:
                price_levels = [p.strip() for p in price.split(',')]
                price_filter = ','.join([p for p in price_levels if p in ['1', '2', '3', '4']])
            
            # Execute search
            search_params = {
                'term': term,
                'location': location,
                'limit': limit,
                'categories': 'restaurants,food'
            }
            if price_filter:
                search_params['price'] = price_filter
            
            response = self.yelp_api.search_query(**search_params)
            
            # Format results
            if not response or 'businesses' not in response or not response['businesses']:
                return f"No restaurants found for '{term}' in {location}"
            
            formatted_results = f"Restaurants found for '{term}' in {location}:\n\n"
            for i, business in enumerate(response['businesses'], 1):
                formatted_results += f"{i}. {business.get('name', 'Unknown')}\n"
                if 'price' in business:
                    formatted_results += f"   Price: {business['price']}\n"
                if 'rating' in business:
                    formatted_results += f"   Rating: {business['rating']}/5 ({business.get('review_count', 0)} reviews)\n"
                if 'categories' in business:
                    categories = [cat['title'] for cat in business['categories']]
                    formatted_results += f"   Categories: {', '.join(categories[:3])}\n"
                if 'location' in business and 'display_address' in business['location']:
                    formatted_results += f"   Address: {', '.join(business['location']['display_address'])}\n"
                if 'display_phone' in business:
                    formatted_results += f"   Phone: {business['display_phone']}\n"
                if 'url' in business:
                    formatted_results += f"   More info: {business['url']}\n"
                formatted_results += "\n"
            
            return formatted_results
        except Exception as e:
            return f"Error searching for restaurants: {str(e)}"
    
    def _get_mock_restaurants(self, term: str, location: str, price: Optional[str] = None, limit: Optional[int] = 5) -> str:
        """Return mock restaurant data when no API key is available."""
        # Generate mock restaurant data with the search parameters
        mock_restaurants = [
            {
                "name": f"Delicious {term.title()} Place",
                "price": "$$$" if price and int(price) > 2 else "$$",
                "rating": 4.5,
                "review_count": 123,
                "categories": ["Italian", "Pizza", "Pasta"],
                "address": f"123 Main St, {location}",
                "phone": "+1-123-456-7890"
            },
            {
                "name": f"Amazing {term.title()} Restaurant",
                "price": "$$" if price and int(price) > 2 else "$",
                "rating": 4.2,
                "review_count": 87,
                "categories": ["Italian", "Wine Bar"],
                "address": f"456 Oak Ave, {location}",
                "phone": "+1-234-567-8901"
            },
        ]
        
        # Format the mock results
        formatted_results = f"Restaurants found for '{term}' in {location}:\n\n"
        for i, business in enumerate(mock_restaurants[:limit], 1):
            formatted_results += f"{i}. {business['name']}\n"
            formatted_results += f"   Price: {business['price']}\n"
            formatted_results += f"   Rating: {business['rating']}/5 ({business['review_count']} reviews)\n"
            formatted_results += f"   Categories: {', '.join(business['categories'])}\n"
            formatted_results += f"   Address: {business['address']}\n"
            formatted_results += f"   Phone: {business['phone']}\n"
            formatted_results += "\n"
        
        return formatted_results

class LocalFoodExperienceTool(BaseTool):
    """Tool that finds local and authentic food experiences using Yelp API."""
    name: str = "find_local_food"
    description: str = """
    Useful for finding authentic, local food experiences that are popular with locals rather than tourists.
    Input should be a location (e.g., 'Kyoto, Japan').
    """
    yelp_api: Any = None
    
    def __init__(self):
        """Initialize the Yelp API client."""
        super().__init__()
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            # For development without API key, provide mock data
            self.yelp_api = None
            print("WARNING: YELP_API_KEY not set, using mock local food data")
        else:
            self.yelp_api = YelpAPI(api_key=api_key)
    
    def _run(self, location: str) -> str:
        """Run the local food experience tool."""
        try:
            # Check if we have a real API client
            if not self.yelp_api:
                # Return mock data if no API key
                return self._get_mock_local_food(location)
                
            # Search for highly-rated local food options
            search_params = {
                'term': 'local authentic food',
                'location': location,
                'limit': 5,
                'sort_by': 'rating',
                'attributes': 'hot_and_new',
                'categories': 'restaurants,food'
            }
            
            response = self.yelp_api.search_query(**search_params)
            
            # Try additional searches for better coverage
            local_terms = ["traditional food", "local cuisine"]
            all_businesses = []
            seen_ids = set()
            
            # Add initial results
            if response and 'businesses' in response:
                for business in response['businesses']:
                    if business['id'] not in seen_ids:
                        seen_ids.add(business['id'])
                        all_businesses.append(business)
            
            # Additional searches
            for term in local_terms:
                try:
                    additional_response = self.yelp_api.search_query(
                        term=term,
                        location=location,
                        limit=5,
                        sort_by='rating',
                        categories='restaurants,food'
                    )
                    
                    if additional_response and 'businesses' in additional_response:
                        for business in additional_response['businesses']:
                            if business['id'] not in seen_ids:
                                seen_ids.add(business['id'])
                                all_businesses.append(business)
                except:
                    continue
            
            # Sort by rating and review count
            all_businesses.sort(key=lambda x: (x.get('rating', 0), x.get('review_count', 0)), reverse=True)
            
            # Format results
            if not all_businesses:
                return f"No local food experiences found in {location}"
            
            formatted_results = f"Authentic Local Food Experiences in {location}:\n\n"
            for i, business in enumerate(all_businesses[:8], 1):  # Limit to top 8
                formatted_results += f"{i}. {business.get('name', 'Unknown')}\n"
                if 'price' in business:
                    formatted_results += f"   Price: {business['price']}\n"
                if 'rating' in business:
                    formatted_results += f"   Rating: {business['rating']}/5 ({business.get('review_count', 0)} reviews)\n"
                if 'categories' in business:
                    categories = [cat['title'] for cat in business['categories']]
                    formatted_results += f"   Cuisine: {', '.join(categories[:3])}\n"
                if 'location' in business and 'display_address' in business['location']:
                    formatted_results += f"   Address: {', '.join(business['location']['display_address'])}\n"
                formatted_results += "\n"
            
            return formatted_results
        except Exception as e:
            return f"Error finding local food experiences: {str(e)}"
    
    def _get_mock_local_food(self, location: str) -> str:
        """Return mock local food data when no API key is available."""
        # Generate mock local food data
        mock_local_foods = [
            {
                "name": f"Authentic {location} Kitchen",
                "price": "$$",
                "rating": 4.8,
                "review_count": 203,
                "categories": ["Local Cuisine", "Traditional"],
                "address": f"789 Local St, {location}"
            },
            {
                "name": f"Local's Favorite in {location}",
                "price": "$",
                "rating": 4.7,
                "review_count": 158,
                "categories": ["Street Food", "Regional"],
                "address": f"321 Hidden Alley, {location}"
            },
        ]
        
        # Format the mock results
        formatted_results = f"Authentic Local Food Experiences in {location}:\n\n"
        for i, business in enumerate(mock_local_foods, 1):
            formatted_results += f"{i}. {business['name']}\n"
            formatted_results += f"   Price: {business['price']}\n"
            formatted_results += f"   Rating: {business['rating']}/5 ({business['review_count']} reviews)\n"
            formatted_results += f"   Cuisine: {', '.join(business['categories'])}\n"
            formatted_results += f"   Address: {business['address']}\n"
            formatted_results += "\n"
        
        return formatted_results