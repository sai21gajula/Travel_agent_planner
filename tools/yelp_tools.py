"""
Enhanced Yelp tools for fetching restaurant and culinary experience information.
"""
import os
import re
import requests
from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool

class YelpRestaurantSearchTool(BaseTool):
    """Tool for searching restaurants using Yelp Fusion API."""
    name: str = "yelp_restaurant_search"
    description: str = "Search for restaurants, cafes, and bars using Yelp"
    
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or os.getenv('YELP_API_KEY')
        if not self.api_key:
            raise ValueError("Yelp API key is required.")
    
    def _run(self, query: str) -> str:
        """
        Search for restaurants on Yelp based on query string.
        
        Args:
            query: Search string (e.g., "Italian restaurants in New York")
            
        Returns:
            Formatted string with restaurant results
        """
        # Parse query to extract location and other parameters
        location = self._extract_location(query)
        term = self._clean_query(query, location)
        price = self._extract_price(query)
        sort_by = self._extract_sort(query)
        limit = self._extract_limit(query)
        
        if not location:
            return "Error: Location is required for restaurant search. Please specify a location (e.g., 'restaurants in Paris')."
        
        # Call Yelp API
        results = self._api_call(term, location, price, sort_by, limit)
        
        # Format results
        return self._format_results(results, location)
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query."""
        location_match = re.search(r'in\s+([^,\.]+(?:,\s*[^,\.]+)?)', query.lower())
        if location_match:
            return location_match.group(1).strip()
        return None
    
    def _clean_query(self, query: str, location: str) -> str:
        """Clean query by removing location and parameters."""
        if location:
            query = query.replace(f"in {location}", "").strip()
        
        # Remove price, sort, and limit parameters
        query = re.sub(r'price:?\s*\d+(?:,\s*\d+)*', '', query, flags=re.IGNORECASE)
        query = re.sub(r'sort:?\s*(?:rating|review_count|distance)', '', query, flags=re.IGNORECASE)
        query = re.sub(r'limit:?\s*\d+', '', query, flags=re.IGNORECASE)
        
        # Add keywords for better results if not present
        keywords = ["restaurant", "food", "dining", "eat"]
        if not any(keyword in query.lower() for keyword in keywords):
            query += " restaurant food"
            
        return query.strip()
    
    def _extract_price(self, query: str) -> Optional[str]:
        """Extract price parameter from query."""
        price_match = re.search(r'price:?\s*(\d+(?:,\s*\d+)*)', query, flags=re.IGNORECASE)
        if price_match:
            return price_match.group(1).replace(" ", "")
        return None
    
    def _extract_sort(self, query: str) -> str:
        """Extract sort parameter from query."""
        sort_match = re.search(r'sort:?\s*(rating|review_count|distance)', query, flags=re.IGNORECASE)
        if sort_match:
            return sort_match.group(1).lower()
        return "rating"  # Default
    
    def _extract_limit(self, query: str) -> int:
        """Extract limit parameter from query."""
        limit_match = re.search(r'limit:?\s*(\d+)', query, flags=re.IGNORECASE)
        if limit_match:
            return min(int(limit_match.group(1)), 50)  # Yelp API max is 50
        return 10  # Default
    
    def _api_call(self, term: str, location: str, price: Optional[str] = None, 
                 sort_by: str = "rating", limit: int = 10) -> Dict[str, Any]:
        """Call Yelp Fusion API."""
        endpoint = "https://api.yelp.com/v3/businesses/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "term": term,
            "location": location,
            "sort_by": sort_by,
            "limit": limit
        }
        if price:
            params["price"] = price
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error calling Yelp API: {str(e)}"}
    
    def _format_results(self, results: Dict[str, Any], location: str) -> str:
        """Format API results into readable text."""
        if "error" in results:
            return f"Error: {results['error']}"
        
        if "businesses" not in results or not results["businesses"]:
            return f"No restaurants found in {location} matching your criteria."
        
        businesses = results["businesses"]
        formatted_output = f"Top Restaurants in {location}:\n\n"
        
        for i, business in enumerate(businesses):
            name = business.get("name", "Unknown")
            rating = business.get("rating", "N/A")
            review_count = business.get("review_count", 0)
            price = business.get("price", "$")
            categories = ", ".join([cat.get("title", "") for cat in business.get("categories", [])])
            address = ", ".join(business.get("location", {}).get("display_address", ["Address unavailable"]))
            phone = business.get("display_phone", "Phone unavailable")
            
            formatted_output += f"🍽️ **{name}** ({categories}) - {price}\n"
            formatted_output += f"   Rating: {rating}/5.0 ({review_count} reviews)\n"
            formatted_output += f"   Address: {address}\n"
            formatted_output += f"   Phone: {phone}\n\n"
        
        return formatted_output

class YelpCulinaryExperienceTool(BaseTool):
    """Tool for finding unique culinary experiences using Yelp Fusion API."""
    name: str = "yelp_culinary_experiences"
    description: str = "Find food tours, cooking classes, markets and unique food experiences"
    
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or os.getenv('YELP_API_KEY')
        if not self.api_key:
            raise ValueError("Yelp API key is required.")
        
        # Define experience types and search terms
        self.experience_types = {
            "food_tour": "food tour culinary tour walking food tour",
            "cooking_class": "cooking class culinary class",
            "food_market": "food market farmers market",
            "street_food": "street food food stalls"
        }
    
    def _run(self, query: str) -> str:
        """
        Find culinary experiences on Yelp based on query string.
        
        Args:
            query: Search string (e.g., "food tours in Paris")
            
        Returns:
            Formatted string with culinary experience results
        """
        # Parse query
        location = self._extract_location(query)
        experience_type = self._extract_experience_type(query)
        
        if not location:
            return "Error: Location is required for culinary experience search. Please specify a location (e.g., 'food tours in Paris')."
        
        # Call Yelp API for each experience type
        if experience_type == "all":
            results = []
            for exp_type, search_term in self.experience_types.items():
                exp_results = self._api_call(search_term, location, limit=5)
                if "error" not in exp_results and "businesses" in exp_results and exp_results["businesses"]:
                    results.append((exp_type, exp_results))
        else:
            search_term = self.experience_types.get(experience_type, self.experience_types["food_tour"])
            api_results = self._api_call(search_term, location, limit=10)
            results = [(experience_type, api_results)]
        
        # Format results
        return self._format_results(results, location)
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query."""
        location_match = re.search(r'in\s+([^,\.]+(?:,\s*[^,\.]+)?)', query.lower())
        if location_match:
            return location_match.group(1).strip()
        return None
    
    def _extract_experience_type(self, query: str) -> str:
        """Extract experience type from query."""
        query_lower = query.lower()
        for exp_type in self.experience_types:
            if exp_type.replace("_", " ") in query_lower:
                return exp_type
        
        # Check for keywords
        if "tour" in query_lower:
            return "food_tour"
        elif "class" in query_lower:
            return "cooking_class"
        elif "market" in query_lower:
            return "food_market"
        elif "street" in query_lower:
            return "street_food"
        
        return "all"  # Default to all types
    
    def _api_call(self, term: str, location: str, limit: int = 10) -> Dict[str, Any]:
        """Call Yelp Fusion API."""
        endpoint = "https://api.yelp.com/v3/businesses/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "term": term,
            "location": location,
            "sort_by": "rating",
            "limit": limit
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error calling Yelp API: {str(e)}"}
    
    def _format_results(self, results: List[tuple], location: str) -> str:
        """Format API results into readable text."""
        if not results:
            return f"No culinary experiences found in {location}."
        
        formatted_output = f"Culinary Experiences in {location}:\n\n"
        
        for exp_type, api_results in results:
            if "error" in api_results:
                formatted_output += f"Error finding {exp_type.replace('_', ' ')}s: {api_results['error']}\n\n"
                continue
            
            if "businesses" not in api_results or not api_results["businesses"]:
                formatted_output += f"No {exp_type.replace('_', ' ')}s found in {location}.\n\n"
                continue
            
            # Add section header
            formatted_output += f"## {exp_type.replace('_', ' ').title()}s\n\n"
            
            # Add businesses
            for business in api_results["businesses"]:
                name = business.get("name", "Unknown")
                rating = business.get("rating", "N/A")
                review_count = business.get("review_count", 0)
                price = business.get("price", "$")
                categories = ", ".join([cat.get("title", "") for cat in business.get("categories", [])])
                address = ", ".join(business.get("location", {}).get("display_address", ["Address unavailable"]))
                
                formatted_output += f"🍳 **{name}** - {price}\n"
                formatted_output += f"   Rating: {rating}/5.0 ({review_count} reviews)\n"
                formatted_output += f"   Categories: {categories}\n"
                formatted_output += f"   Address: {address}\n\n"
        
        return formatted_output

class LocalFoodSpecialtiesTool(BaseTool):
    """Tool for finding local food specialties using Yelp Fusion API."""
    name: str = "local_food_specialties"
    description: str = "Find local and traditional food specialties in a destination"
    
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or os.getenv('YELP_API_KEY')
        if not self.api_key:
            raise ValueError("Yelp API key is required.")
    
    def _run(self, query: str) -> str:
        """
        Find local food specialties and where to try them.
        
        Args:
            query: Search string (e.g., "local food specialties in Tokyo")
            
        Returns:
            Formatted string with local food specialty results
        """
        # Parse query
        location = self._extract_location(query)
        
        if not location:
            return "Error: Location is required to find local food specialties. Please specify a destination (e.g., 'local food in Paris')."
        
        # Search for traditional and local food
        search_terms = [
            "traditional local food specialty",
            "famous local dish",
            "must try food",
            "local cuisine specialty"
        ]
        
        all_results = []
        for term in search_terms:
            results = self._api_call(f"{term} {location}", location, limit=5)
            if "error" not in results and "businesses" in results and results["businesses"]:
                all_results.extend(results["businesses"])
        
        # Remove duplicates
        unique_businesses = {}
        for business in all_results:
            business_id = business.get("id")
            if business_id and business_id not in unique_businesses:
                unique_businesses[business_id] = business
        
        # Format results
        return self._format_results(list(unique_businesses.values()), location)
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query."""
        location_match = re.search(r'in\s+([^,\.]+(?:,\s*[^,\.]+)?)', query.lower())
        if location_match:
            return location_match.group(1).strip()
        
        # Try to find location at the beginning
        location_match = re.search(r'^([a-zA-Z\s]+)\s+(?:food|dish|cuisine|specialties)', query.lower())
        if location_match:
            return location_match.group(1).strip()
            
        return None
    
    def _api_call(self, term: str, location: str, limit: int = 10) -> Dict[str, Any]:
        """Call Yelp Fusion API."""
        endpoint = "https://api.yelp.com/v3/businesses/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "term": term,
            "location": location,
            "sort_by": "rating",
            "limit": limit
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error calling Yelp API: {str(e)}"}
    
    def _format_results(self, businesses: List[Dict[str, Any]], location: str) -> str:
        """Format API results into readable text."""
        if not businesses:
            return f"No local food specialties found for {location}."
        
        formatted_output = f"Local Food Specialties in {location}:\n\n"
        
        # Group by categories
        category_businesses = {}
        for business in businesses:
            categories = business.get("categories", [])
            for category in categories:
                cat_title = category.get("title", "")
                if cat_title and cat_title not in ["Restaurants", "Food"]:
                    if cat_title not in category_businesses:
                        category_businesses[cat_title] = []
                    category_businesses[cat_title].append(business)
        
        # Output by category
        for category, cat_businesses in category_businesses.items():
            formatted_output += f"## {category}\n\n"
            
            for business in cat_businesses[:3]:  # Limit to 3 per category
                name = business.get("name", "Unknown")
                rating = business.get("rating", "N/A")
                price = business.get("price", "$")
                address = ", ".join(business.get("location", {}).get("display_address", ["Address unavailable"]))
                
                formatted_output += f"🥘 **{name}** - {price}\n"
                formatted_output += f"   Rating: {rating}/5.0\n"
                formatted_output += f"   Address: {address}\n\n"
        
        return formatted_output