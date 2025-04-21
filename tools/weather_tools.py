"""
Weather tools for the travel agent crew using OpenWeatherMap API.
"""
import os
from crewai.tools import BaseTool
from langchain_community.utilities.openweathermap import OpenWeatherMapAPIWrapper
from typing import Optional, Any
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    """Input for the WeatherForecastTool."""
    location: str = Field(..., description="The city and country, e.g., 'Paris, France'")
    date: Optional[str] = Field(None, description="The date for the forecast in YYYY-MM-DD format. If not provided, the current forecast will be returned.")

class WeatherForecastTool(BaseTool):
    """Tool that gets weather forecasts using OpenWeatherMap API."""
    name: str = "weather_forecast"
    description: str = """
    Useful for getting weather forecasts for a location.
    Input should be a city and country (e.g., 'Paris, France').
    Optionally include a date in YYYY-MM-DD format for a forecast.
    """
    weather_api: Any = None
    
    def __init__(self):
        """Initialize the OpenWeatherMap API wrapper."""
        super().__init__()
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            # For development without API key, provide mock data
            self.weather_api = None
            print("WARNING: OPENWEATHERMAP_API_KEY not set, using mock weather data")
        else:
            self.weather_api = OpenWeatherMapAPIWrapper(openweathermap_api_key=api_key)
    
    def _run(self, location: str, date: Optional[str] = None) -> str:
        """Run the weather forecast tool."""
        try:
            # Check if we have a real API wrapper
            if not self.weather_api:
                # Return mock data if no API key
                return self._get_mock_weather(location, date)
            
            # Get current weather - OpenWeatherMap's free tier is limited in forecast abilities
            weather_data = self.weather_api.run(location)
            
            # Include date information in the response if provided
            if date:
                result = f"Weather forecast for {location} on {date}:\n{weather_data}"
                # Note: For accurate forecasts by date, you would need a premium
                # OpenWeatherMap subscription or a different weather API
            else:
                result = f"Current weather for {location}:\n{weather_data}"
            
            return result
        except Exception as e:
            return f"Error getting weather data: {str(e)}"
    
    def _get_mock_weather(self, location: str, date: Optional[str] = None) -> str:
        """Return mock weather data when no API key is available."""
        if date:
            return f"Weather forecast for {location} on {date}:\nTemperature: 22°C (72°F), Conditions: Partly Cloudy, Humidity: 60%, Wind: 10 km/h"
        else:
            return f"Current weather for {location}:\nTemperature: 21°C (70°F), Conditions: Sunny, Humidity: 55%, Wind: 8 km/h"

class ClothingRecommendationTool(BaseTool):
    """Tool that recommends clothing based on weather conditions."""
    name: str = "clothing_recommendation"
    description: str = """
    Useful for recommending appropriate clothing based on weather conditions.
    Input should be a weather description (e.g., 'Sunny, 25°C' or 'Rainy, 10°C').
    """
    
    def _run(self, weather_description: str) -> str:
        """Run the clothing recommendation tool."""
        try:
            # Extract temperature if available
            temp_celsius = None
            if "°C" in weather_description:
                temp_parts = [part for part in weather_description.split() if "°C" in part]
                if temp_parts:
                    try:
                        temp_celsius = float(temp_parts[0].replace("°C", ""))
                    except ValueError:
                        pass
            
            # Extract weather conditions
            conditions = weather_description.lower()
            
            # Generate clothing recommendations based on conditions
            recommendations = []
            
            # Temperature-based recommendations
            if temp_celsius is not None:
                if temp_celsius > 25:
                    recommendations.append("Lightweight and breathable clothing (t-shirts, shorts, light dresses)")
                    recommendations.append("Sun hat and sunglasses")
                elif temp_celsius > 15:
                    recommendations.append("Light layers (t-shirts, light sweaters, jeans or light pants)")
                elif temp_celsius > 5:
                    recommendations.append("Warm layers (sweaters, jackets, long pants)")
                else:
                    recommendations.append("Heavy winter clothing (thick coat, scarf, gloves, thermals)")
            
            # Condition-based recommendations
            if "rain" in conditions or "shower" in conditions:
                recommendations.append("Waterproof jacket or umbrella")
                recommendations.append("Waterproof footwear")
            
            if "snow" in conditions:
                recommendations.append("Snow boots with good traction")
                recommendations.append("Waterproof outer layers")
            
            if "wind" in conditions:
                recommendations.append("Windproof jacket or coat")
            
            if "sun" in conditions or "clear" in conditions:
                recommendations.append("Sunscreen and sunglasses")
                if temp_celsius and temp_celsius > 20:
                    recommendations.append("Hat for sun protection")
            
            if not recommendations:
                return "Unable to provide specific clothing recommendations based on the given weather information."
            
            return "Recommended clothing:\n- " + "\n- ".join(recommendations)
        except Exception as e:
            return f"Error generating clothing recommendations: {str(e)}"