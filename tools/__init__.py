# travel_agent/tools/__init__.py
"""
Tools package for the travel agent crew.
Includes Yelp, Geoapify, Transitland, Wikipedia, Weather, Serper, and Amadeus tools.
"""
import os

# --- Tool Imports ---
# Keep Yelp tools
try:
    from .yelp_tools import YelpRestaurantSearchTool, LocalFoodExperienceTool
    YELP_AVAILABLE = True
except ImportError:
    YelpRestaurantSearchTool, LocalFoodExperienceTool = None, None
    YELP_AVAILABLE = False
    print("Warning: Yelp tools not found or failed to import.")

# Keep Wikipedia tools
try:
    from .wikipedia_tools import HistoricalInfoTool, CulturalCustomsTool, FunFactsTool
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    HistoricalInfoTool, CulturalCustomsTool, FunFactsTool = None, None, None
    WIKIPEDIA_AVAILABLE = False
    print("Warning: Wikipedia tools not found or failed to import.")

# Keep Weather tools
try:
    from .weather_tools import WeatherForecastTool, ClothingRecommendationTool
    WEATHER_AVAILABLE = True
except ImportError:
    WeatherForecastTool, ClothingRecommendationTool = None, None
    WEATHER_AVAILABLE = False
    print("Warning: Weather tools not found or failed to import.")

# Import Geoapify and Transport tools
try:
    from .geoapify_tools import GeoapifyPOITool
    GEOAPIFY_AVAILABLE = True
except ImportError:
    GeoapifyPOITool = None
    GEOAPIFY_AVAILABLE = False
    print("Warning: Geoapify tools not found or failed to import.")

try:
    from .transport_tools import PublicTransportSearchTool, CityCodeLookupTool
    TRANSPORT_AVAILABLE = True
except ImportError:
    PublicTransportSearchTool, CityCodeLookupTool = None, None
    TRANSPORT_AVAILABLE = False
    print("Warning: Transport tools not found or failed to import.")

# Import Amadeus tools
try:
    from .amadeus_tools import AmadeusFlightSearchTool, AmadeusHotelSearchTool
    AMADEUS_AVAILABLE = True
except ImportError:
    AmadeusFlightSearchTool, AmadeusHotelSearchTool = None, None
    AMADEUS_AVAILABLE = False
    print("Warning: Amadeus tools not found or failed to import. Flight and hotel search will be limited.")

# Import Serper tool wrapper
try:
    from .serper_tool import SerperDevTool # Import the wrapper class
    SERPER_WRAPPER_AVAILABLE = True
except ImportError:
    SerperDevTool = None
    SERPER_WRAPPER_AVAILABLE = False
    print("Warning: Serper tool wrapper (serper_tool.py) not found or failed to import.")


# --- Tool Initialization ---
# Initialize tools, handling potential errors if dependencies/keys are missing

yelp_restaurant_tool = None
if YELP_AVAILABLE and YelpRestaurantSearchTool:
    try:
        yelp_restaurant_tool = YelpRestaurantSearchTool()
    except Exception as e:
        print(f"Warning: Failed to initialize YelpRestaurantSearchTool - {e}")

local_food_tool = None
if YELP_AVAILABLE and LocalFoodExperienceTool:
    try:
        local_food_tool = LocalFoodExperienceTool()
    except Exception as e:
        print(f"Warning: Failed to initialize LocalFoodExperienceTool - {e}")

# Wikipedia tools are generally safe if imported
historical_info_tool = HistoricalInfoTool() if WIKIPEDIA_AVAILABLE and HistoricalInfoTool else None
cultural_customs_tool = CulturalCustomsTool() if WIKIPEDIA_AVAILABLE and CulturalCustomsTool else None
fun_facts_tool = FunFactsTool() if WIKIPEDIA_AVAILABLE and FunFactsTool else None

# Weather tools
weather_forecast_tool = None
if WEATHER_AVAILABLE and WeatherForecastTool:
    try:
        weather_forecast_tool = WeatherForecastTool()
    except Exception as e:
        print(f"Warning: Failed to initialize WeatherForecastTool - {e}")

clothing_recommendation_tool = ClothingRecommendationTool() if WEATHER_AVAILABLE and ClothingRecommendationTool else None


# Geoapify
geoapify_poi_tool = None
if GEOAPIFY_AVAILABLE and GeoapifyPOITool:
    try:
        geoapify_poi_tool = GeoapifyPOITool()
    except Exception as e:
        print(f"Warning: Failed to initialize GeoapifyPOITool - {e}")

# Transport tools
public_transport_tool = None
if TRANSPORT_AVAILABLE and PublicTransportSearchTool:
    try:
        public_transport_tool = PublicTransportSearchTool()
    except Exception as e:
        print(f"Warning: Failed to initialize PublicTransportSearchTool - {e}")

city_code_lookup_tool = None
if TRANSPORT_AVAILABLE and CityCodeLookupTool:
    try:
        city_code_lookup_tool = CityCodeLookupTool()
    except Exception as e:
        print(f"Warning: Failed to initialize CityCodeLookupTool - {e}")

# Amadeus tools
amadeus_flight_tool = None
amadeus_hotel_tool = None
if AMADEUS_AVAILABLE:
    if AmadeusFlightSearchTool:
        try:
            amadeus_flight_tool = AmadeusFlightSearchTool()
            print("Initialized Amadeus Flight Search Tool")
        except Exception as e:
            print(f"Warning: Failed to initialize AmadeusFlightSearchTool - {e}")

    if AmadeusHotelSearchTool:
        try:
            amadeus_hotel_tool = AmadeusHotelSearchTool()
            print("Initialized Amadeus Hotel Search Tool")
        except Exception as e:
            print(f"Warning: Failed to initialize AmadeusHotelSearchTool - {e}")

# Serper tool
serper_dev_tool = None
if SERPER_WRAPPER_AVAILABLE and SerperDevTool:
    try:
        # The wrapper's __init__ handles underlying tool init and key checks
        serper_dev_tool_instance = SerperDevTool()
        # Check if the *underlying* original tool was successfully initialized within the wrapper
        if hasattr(serper_dev_tool_instance, 'original_tool') and serper_dev_tool_instance.original_tool:
            serper_dev_tool = serper_dev_tool_instance # Assign if successful
            print("Initialized Serper Web Search Tool")
        else:
            # This means the wrapper loaded, but the actual tool didn't init (likely missing key/dependency)
             print("Warning: Serper tool wrapper loaded, but underlying tool failed to initialize. Web search disabled.")
    except Exception as e:
        print(f"Warning: Failed to initialize SerperDevTool wrapper - {e}")


# --- Tool Groups for Agents (Updated & Filtered for None) ---
# Filter out any tools that failed to initialize

# General Web Search (if available) - can be added to multiple agents
web_search_tools = [t for t in [serper_dev_tool] if t is not None]

transport_planner_tools = [
    t for t in [
        public_transport_tool,
        city_code_lookup_tool,
        amadeus_flight_tool,
    ] + web_search_tools if t is not None # Add web search
]

accommodation_finder_tools = [
     t for t in [
        geoapify_poi_tool, # For finding hotels/lodging POIs
        city_code_lookup_tool,
        amadeus_hotel_tool,
    ] + web_search_tools if t is not None # Add web search
]

local_guide_tools = [
    t for t in [
        yelp_restaurant_tool,
        local_food_tool,
        geoapify_poi_tool, # For finding attractions, landmarks etc.
        historical_info_tool,
        cultural_customs_tool,
        fun_facts_tool
    ] + web_search_tools if t is not None # Add web search
]

weather_advisor_tools = [
    t for t in [
        weather_forecast_tool,
        clothing_recommendation_tool
    ] + web_search_tools if t is not None # Add web search
]

# --- Create combined list of unique tools ---
# Use a dictionary based on tool names to ensure uniqueness and avoid hashing issues
temp_tools_dict = {}
# Combine all potential tools into one list first
all_potential_tools = (
    [yelp_restaurant_tool, local_food_tool] +
    [historical_info_tool, cultural_customs_tool, fun_facts_tool] +
    [weather_forecast_tool, clothing_recommendation_tool] +
    [geoapify_poi_tool] +
    [public_transport_tool, city_code_lookup_tool] +
    [amadeus_flight_tool, amadeus_hotel_tool] +
    [serper_dev_tool] # Add serper tool here
)

for tool in all_potential_tools:
    # Ensure tool is not None, has a 'name' attribute, and hasn't been added yet
    if tool and hasattr(tool, 'name') and tool.name not in temp_tools_dict:
         temp_tools_dict[tool.name] = tool

# The final list of unique, successfully initialized tool instances
all_tools = list(temp_tools_dict.values())

# --- Print Initialized Tools ---
print("\n--- Tools Initialization Report ---")
print(f"Transport Planner Tools: {[t.name for t in transport_planner_tools]}")
print(f"Accommodation Finder Tools: {[t.name for t in accommodation_finder_tools]}")
print(f"Local Guide Tools: {[t.name for t in local_guide_tools]}")
print(f"Weather Advisor Tools: {[t.name for t in weather_advisor_tools]}")
print(f"Total Unique Tools Loaded: {[t.name for t in all_tools]}")
print("-----------------------------------\n")

