# travel_agent/tools/__init__.py
"""
Tools package for the travel agent crew.
Includes Yelp, Geoapify, Transitland, Wikipedia, Weather tools.
"""
# Keep Yelp tools
from .yelp_tools import YelpRestaurantSearchTool, LocalFoodExperienceTool

# Keep Wikipedia tools
from .wikipedia_tools import HistoricalInfoTool, CulturalCustomsTool, FunFactsTool

# Keep Weather tools (consider updating WeatherForecastTool internally)
from .weather_tools import WeatherForecastTool, ClothingRecommendationTool

# Import NEW Geoapify and Transport tools
from .geoapify_tools import GeoapifyPOITool
from .transport_tools import PublicTransportSearchTool

# --- Tool Initialization ---
# Initialize tools, handling potential errors if dependencies/keys are missing
try:
    yelp_restaurant_tool = YelpRestaurantSearchTool()
except Exception as e:
    print(f"Warning: Failed to initialize YelpRestaurantSearchTool - {e}")
    yelp_restaurant_tool = None

try:
    local_food_tool = LocalFoodExperienceTool()
except Exception as e:
    print(f"Warning: Failed to initialize LocalFoodExperienceTool - {e}")
    local_food_tool = None

# Wikipedia tools are generally safe
historical_info_tool = HistoricalInfoTool()
cultural_customs_tool = CulturalCustomsTool()
fun_facts_tool = FunFactsTool()

# Weather tools
try:
    weather_forecast_tool = WeatherForecastTool() # Assumes key/mock logic is handled inside
except Exception as e:
    print(f"Warning: Failed to initialize WeatherForecastTool - {e}")
    weather_forecast_tool = None

clothing_recommendation_tool = ClothingRecommendationTool() # Logic based, should be safe

# Geoapify
try:
    geoapify_poi_tool = GeoapifyPOITool()
except Exception as e:
    print(f"Warning: Failed to initialize GeoapifyPOITool - {e}")
    geoapify_poi_tool = None

# Transitland
try:
    public_transport_tool = PublicTransportSearchTool()
except Exception as e:
    print(f"Warning: Failed to initialize PublicTransportSearchTool - {e}")
    public_transport_tool = None


# --- Tool Groups for Agents (Updated & Filtered for None) ---
# Filter out any tools that failed to initialize

transport_planner_tools = [
    t for t in [
        public_transport_tool,
        # Add other relevant tools if needed
    ] if t is not None
]

accommodation_finder_tools = [
     t for t in [
        geoapify_poi_tool, # Can search for 'accommodation.hotel' category
        # Add AmadeusHotelSearchTool back here if needed and initialized
    ] if t is not None
]

local_guide_tools = [
    t for t in [
        yelp_restaurant_tool,    # Keep Yelp for specific restaurant/food focus
        local_food_tool,         # Keep Yelp for local food focus
        geoapify_poi_tool,       # Use Geoapify for attractions, shops, etc.
        historical_info_tool,    # Keep Wikipedia tools
        cultural_customs_tool,
        fun_facts_tool
    ] if t is not None
]

weather_advisor_tools = [
    t for t in [
        weather_forecast_tool,
        clothing_recommendation_tool
    ] if t is not None
]

# --- Create combined list of unique tools (FIXED) ---
# Use a dictionary based on tool names to ensure uniqueness and avoid hashing issues
temp_tools_dict = {}
for tool in (transport_planner_tools +
             accommodation_finder_tools +
             local_guide_tools +
             weather_advisor_tools):
    # Ensure tool is valid and has a name before adding
    if tool and hasattr(tool, 'name') and tool.name not in temp_tools_dict:
         temp_tools_dict[tool.name] = tool

# The final list of unique tool instances
all_tools = list(temp_tools_dict.values())


# --- Print Initialized Tools ---
print("--- Tools Initialized ---")
print(f"Transport Planner Tools: {[t.name for t in transport_planner_tools]}")
print(f"Accommodation Finder Tools: {[t.name for t in accommodation_finder_tools]}")
print(f"Local Guide Tools: {[t.name for t in local_guide_tools]}")
print(f"Weather Advisor Tools: {[t.name for t in weather_advisor_tools]}")
print(f"Total Unique Tools Loaded: {[t.name for t in all_tools]}")
