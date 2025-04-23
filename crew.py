"""
Enhanced crew implementation for the travel agent system.
Uses specialized agents with distinct tasks including a dedicated Yelp dining expert.
"""
import os
import yaml
import datetime
import re
import nest_asyncio
from dotenv import load_dotenv
import sys
from typing import Optional, Dict, List, Any

# Apply nest_asyncio
nest_asyncio.apply()

# CrewAI imports
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.llm import LLM
from crewai.tools import BaseTool

# Import tools
try: 
    from tools.yelp_tools import YelpRestaurantSearchTool, YelpCulinaryExperienceTool, LocalFoodSpecialtiesTool
except ImportError: 
    YelpRestaurantSearchTool = YelpCulinaryExperienceTool = LocalFoodSpecialtiesTool = None

try: 
    from tools.wikipedia_tools import HistoricalInfoTool, CulturalCustomsTool, FunFactsTool
except ImportError: 
    HistoricalInfoTool = CulturalCustomsTool = FunFactsTool = None

try: 
    from tools.weather_tools import WeatherForecastTool, ClothingRecommendationTool
except ImportError: 
    WeatherForecastTool = ClothingRecommendationTool = None

try: 
    from tools.geoapify_tools import GeoapifyPOITool
except ImportError: 
    GeoapifyPOITool = None

try: 
    from tools.transport_tools import PublicTransportSearchTool, CityCodeLookupTool
except ImportError: 
    PublicTransportSearchTool = CityCodeLookupTool = None

try: 
    from tools.amadeus_tools import AmadeusFlightSearchTool, AmadeusHotelSearchTool
except ImportError: 
    AmadeusFlightSearchTool = AmadeusHotelSearchTool = None

# Handle SerperDevTool import
try:
    from crewai_tools import SerperDevTool as OriginalSerperDevTool
    
    class SerperDevTool(BaseTool):
        name: str = "serper_search"
        description: str = "Search the web using Serper.dev API"
        
        def __init__(self, api_key=None):
            super().__init__()
            self.api_key = api_key
            self.original_tool = OriginalSerperDevTool(api_key=api_key)
        
        def _run(self, query: str) -> str:
            """Run the web search using Serper.dev API"""
            try:
                return self.original_tool._run(query)
            except Exception as e:
                return f"Error searching with Serper: {str(e)}"
                
except ImportError:
    class SerperDevTool(BaseTool):
        name: str = "dummy_serper_dev_tool"
        description: str = "Dummy SerperDevTool (not available)"
        
        def __init__(self, *args, **kwargs):
            super().__init__()
        
        def _run(self, *args, **kwargs) -> str:
            return "SerperDevTool not available"

# Load environment variables
load_dotenv()

# Environment Variables
gemini_api_key_1 = os.getenv('GEMINI_API_KEY')
gemini_api_key_2 = os.getenv('GEMINI_API_KEY_2')
gemini_api_key_3 = os.getenv('GEMINI_API_KEY_3')
groq_api_key_1 = os.getenv('GROQ_API_KEY_1')
groq_api_key_2 = os.getenv('GROQ_API_KEY_2')
serper_api_key = os.getenv('SERPER_API_KEY')
yelp_api_key = os.getenv('YELP_API_KEY')

# Configuration Loading
def load_configs():
    """Load agent and task configurations from YAML files."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, 'config')
        if not os.path.isdir(config_dir): config_dir = base_dir
        agents_path = os.path.join(config_dir, 'agents.yaml')
        tasks_path = os.path.join(config_dir, 'tasks.yaml')
        
        if not os.path.isfile(agents_path) or not os.path.isfile(tasks_path):
            return _get_default_configs()
            
        with open(agents_path, 'r', encoding='utf-8') as file: 
            agents_config = yaml.safe_load(file)
        with open(tasks_path, 'r', encoding='utf-8') as file: 
            tasks_config = yaml.safe_load(file)
            
        if not agents_config or not tasks_config:
            return _get_default_configs()
            
        return agents_config, tasks_config
    except:
        return _get_default_configs()

def _get_default_configs():
    """Provide default configurations if YAML files are not found."""
    agents_config = { 
        'transport_planner': {
            'role': 'Transport & Flight Planner', 
            'goal': 'Research and identify comprehensive transportation options between {starting_point} and {destination}\nfor the period {start_date} to {end_date}. This includes flight options using Amadeus flight API,\ntrains, buses, and local transit options at the destination. Analyze options based on price,\nduration, convenience, and schedule. Provide specific route codes, service providers,\nand connection details.', 
            'backstory': 'You are a travel logistics expert specializing in both air travel and ground transportation.\nYou have deep knowledge of flight routing, train and bus services, and local transit systems.\nYour expertise helps travelers understand all transportation options for their journey from\nstart to finish, finding the most efficient and appropriate options for their needs.'
        }, 
        'accommodation_finder': {
            'role': 'Accommodation & Local Stay Specialist', 
            'goal': 'Identify diverse accommodation options in {destination} for the stay from {start_date} to {end_date}.\nUse both Amadeus Hotel API for traditional hotels and Geoapify POI searches for unique local\naccommodations (guesthouses, homestays, boutique hotels). Provide analysis of neighborhoods,\nproximity to attractions, and accommodation styles that match the traveler\'s preferences.\nInclude price estimates when available.', 
            'backstory': 'You are an accommodation expert who understands both mainstream hotel options and unique local\nstays. You have extensive knowledge of different neighborhoods and can match travelers with\nthe perfect place to stay based on their preferences, whether they want luxury hotels, authentic\nlocal experiences, or budget-friendly options. You help travelers find accommodations that enhance\ntheir overall trip experience.'
        }, 
        'local_guide': {
            'role': 'Destination Expert & Cultural Context Provider', 
            'goal': 'Research and provide comprehensive information about {destination} for travelers visiting between\n{start_date} and {end_date}. Create a guide that includes historical context, cultural insights,\ntop attractions, local hidden gems, and practical visitor information. Use Wikipedia tools for\nhistorical research and Geoapify POI search for attractions and points of interest. Focus on both\npopular sites and authentic local experiences, with special attention to the cultural context that\nwill enrich the traveler\'s understanding of the destination.', 
            'backstory': 'You are a destination expert with deep knowledge of both the historical significance and modern\nculture of travel destinations. You blend factual information with cultural context to help\ntravelers understand the places they visit more deeply. Your recommendations balance must-see\nattractions with authentic local experiences that provide a more complete picture of a destination.'
        }, 
        'yelp_dining_expert': {
            'role': 'Culinary & Dining Experience Specialist', 
            'goal': 'Research and recommend outstanding dining experiences in {destination} for travelers visiting between\n{start_date} and {end_date}. Use Yelp tools to find a diverse range of options including restaurants,\ncafes, food markets, and unique culinary experiences. Recommendations should cover various price points,\ncuisine types, and dining styles from high-end restaurants to authentic local eateries. Include specific\ndetails on signature dishes, atmosphere, price range, location, and cultural significance of recommended\nestablishments.', 
            'backstory': 'You are a culinary specialist with extensive knowledge of global cuisine and dining cultures. You\nunderstand that food is a crucial part of the travel experience and can provide deep insight into\nlocal culture. Your recommendations help travelers discover memorable dining experiences at all price\npoints, from sophisticated restaurants to hidden local gems, food markets, and street food. You have\na particular talent for identifying authentic local specialties and unique food experiences that\nbecome highlights of a trip.'
        }, 
        'packing_and_weather_advisor': {
            'role': 'Travel Preparation & Weather Specialist', 
            'goal': 'Provide comprehensive travel preparation guidance for {destination} from {start_date} to {end_date}:\n1) Detailed weather analysis including temperature ranges, precipitation, and seasonal considerations\n2) Customized packing recommendations based on weather, planned activities, and destination culture\n3) Essential items specific to the region (adapters, special clothing, health items)\n4) Items better purchased at the destination versus packed\n5) Tips for dealing with specific environmental conditions (altitude, humidity, etc.)', 
            'backstory': 'You are a travel preparation expert who understands how proper planning enhances the travel experience.\nYou combine weather analysis with practical knowledge of what travelers need in different environments\nand cultures. Your customized recommendations help travelers pack efficiently while ensuring they\nhave everything needed for comfort and to fully enjoy their destination. You also know what\'s better\npurchased locally versus brought from home, helping travelers prepare wisely.'
        }, 
        'report_compiler': {
            'role': 'Lead Travel Report Compiler', 
            'goal': 'Compile the research findings from all specialist agents into a comprehensive, well-organized,\nand engaging travel report for the user\'s trip to {destination} from {start_date} to {end_date}.\nIntegrate information from the Transport Planner, Accommodation Specialist, Local Guide,\nCulinary Expert, and Weather Advisor into a cohesive document structured for easy reference.\nEnsure all aspects of the trip are covered while maintaining a consistent voice and highlighting\nkey recommendations.', 
            'backstory': 'You are the lead editor responsible for structuring and presenting the final travel plan.\nYour role is to synthesize specialized information from multiple experts into a cohesive and\nuser-friendly guide that gives travelers a complete picture of their upcoming journey. You\nexcel at organizing complex information into clear sections, maintaining consistency, and ensuring\nall aspects of travel planning are addressed in the final report.'
        } 
    }
    
    tasks_config = { 
        'find_transportation': {
            'description': 'Research comprehensive transportation options between {starting_point} and {destination}\nfor the period {start_date} to {end_date}. If these are different cities/countries,\nuse the Amadeus flight search tool to find flight options (first use city_code_lookup\nto find IATA codes). For local transportation within the destination, use the public\ntransport search tool to identify transit routes, operators, and key information.\nAdditionally, research any notable train or bus options for longer distances. For each\ntransportation type, provide details on routes, estimated costs, travel times, frequency,\nand any special considerations.', 
            'expected_output': 'A comprehensive transportation section including:\n1) Flight Options (if applicable): List 3-5 flight options with airlines, estimated prices,\n   flight duration, number of stops, and general schedules. Include any notes about airport\n   transportation.\n2) Local Public Transit: Available types (metro, bus, tram, etc.), key routes for tourists,\n   transit pass options, and approximate costs. Include operating hours and frequency information\n   if available.\n3) Regional Transportation: Notable train or bus routes to/from nearby destinations, with\n   service providers and general schedule information.\nConclude with practical transportation tips specific to the destination.'
        }, 
        'find_accommodation': {
            'description': 'Search for diverse accommodation options in {destination} suitable for the period {start_date}\nto {end_date}. Use both the Amadeus hotel search API for traditional accommodations and the\nGeoapify POI search tool for local stays and unique options (using categories like \'accommodation.hotel\',\n\'accommodation.guest_house\', etc.). For each area/neighborhood, identify a mix of accommodation\ntypes at different price points. Include specific details on location, approximate pricing (when\navailable), amenities, and the character of surrounding neighborhoods. Consider the traveler\'s\npreferences ({budget}, {travel_style}, and {accommodation}) when making recommendations.', 
            'expected_output': 'A well-structured accommodation section with:\n1) Overview of 2-3 recommended neighborhoods/areas to stay in {destination}, with brief\n   descriptions of each area\'s character, benefits, and drawbacks.\n2) For each area, 2-4 specific accommodation recommendations spanning different types and price points:\n   - Traditional Hotels: Names, star ratings, price range, notable amenities\n   - Local/Unique Stays: Guesthouses, boutique hotels, or other distinctive options with\n     descriptions of what makes them special\n   - Budget Options: Hostels or affordable hotels when applicable\n3) General advice about accommodation in {destination}, including booking tips and important\n   considerations for travelers.'
        }, 
        'get_local_context': {
            'description': 'Research and provide comprehensive destination information for {destination}, focusing on\nhistorical context, cultural insights, practical visitor information, and attractions.\nUse Wikipedia tools for historical research and cultural background. Use Geoapify POI search\nto identify key attractions (category \'tourism.attraction\'), museums (category \'entertainment.museum\'),\nand other points of interest. Create a guide that balances factual information with cultural\ncontext to help travelers understand and appreciate the destination more deeply. Consider\nthe traveler\'s interests ({interests}) and travel style ({travel_style}) when highlighting\nattractions.', 
            'expected_output': 'A comprehensive local guide section with:\n1) Historical & Cultural Context (1-2 paragraphs): Brief historical overview highlighting\n   key events and influences that shaped {destination}, important cultural aspects, and\n   any significant current context visitors should understand.\n2) Must-See Attractions & Sights: List of 5-7 major attractions with brief descriptions,\n   locations, estimated time needed, and any practical visitor information.\n3) Museums & Cultural Sites: 3-5 noteworthy museums or cultural institutions with focus/specialty,\n   location, and recommended for which types of travelers.\n4) Hidden Gems & Local Experiences: 3-4 lesser-known but worthwhile attractions or experiences\n   that provide authentic local flavor.\n5) Practical Information: Local customs, tipping practices, business hours, and other practical\n   tips specific to the destination.'
        }, 
        'get_dining_recommendations': {
            'description': 'Using Yelp tools, research and recommend outstanding dining experiences in {destination} for\ntravelers visiting between {start_date} and {end_date}. Find diverse options including fine dining,\nmid-range restaurants, casual eateries, food markets, and unique culinary experiences. Recommendations\nshould cover various cuisine types with special emphasis on local specialties and authentic food\nexperiences. For each recommendation, include cuisine type, price range, signature dishes, atmosphere,\nlocation, and why it\'s worth visiting. Consider the traveler\'s preferences ({budget}, {travel_style})\nand any mentioned food interests or dietary needs.', 
            'expected_output': 'A well-structured dining section with:\n1) Local Cuisine Overview: Brief description of the destination\'s culinary traditions and\n   signature dishes travelers should try.\n2) Top Dining Recommendations: 5-7 specific restaurants across different categories:\n   - Fine Dining (1-2 options if applicable)\n   - Mid-Range Restaurants (2-3 options)\n   - Authentic Local Eateries (2-3 options)\n   - Quick/Casual Options (1-2 options)\n   For each, include: Name, Cuisine type, Price range [$-$$$$], Signature dishes,\n   Address/Neighborhood, Yelp rating if available, and brief description.\n3) Food Experiences: 2-3 unique food-related experiences such as markets, food tours,\n   cooking classes, or street food areas.\n4) Practical Dining Tips: Reservation customs, tipping practices, meal times, and any other\n   useful information for dining in this destination.'
        }, 
        'get_weather_and_packing_advice': {
            'description': 'Provide comprehensive travel preparation guidance for {destination} for the period {start_date} to {end_date}.\nResearch typical weather patterns including temperature ranges, precipitation likelihood, and any\nseasonal considerations. Based on weather expectations, planned activities, and destination-specific\nfactors, create detailed packing recommendations. Include essential items specifically relevant to\nthis destination (appropriate clothing, accessories, electronics, health items), suggestions for what\nto purchase locally rather than pack, and tips for dealing with any special environmental conditions\n(altitude, humidity, etc.).', 
            'expected_output': 'A detailed weather and packing section with:\n1) Weather Analysis: Comprehensive overview of expected weather during the travel period, \n   including daily temperature ranges, precipitation probability, significant weather events\n   typical for this time of year, and other relevant climate factors.\n2) Essential Packing List: Categorized recommendations including:\n   - Clothing: Specific items appropriate for the expected weather and activities\n   - Footwear: Appropriate options based on terrain and planned activities\n   - Accessories: Weather-appropriate and culturally-appropriate items\n   - Electronics: Necessary adapters, chargers, and devices\n   - Health & Toiletries: Destination-specific health items, medications, or toiletries\n   - Documents & Money: Required travel documents and payment recommendations\n3) Destination-Specific Advice: Items particularly important for this location, suggested items\n   to purchase locally, and tips for dealing with any unique environmental conditions.'
        }, 
        'compile_travel_report': {
            'description': 'Compile all gathered information from specialist agents (transportation, accommodation, local guide,\ndining expert, and weather/packing advisor) into a single, comprehensive travel report document\nfor the trip to {destination} from {start_date} to {end_date}. Organize the information in a logical\nflow that guides the traveler through planning and experiencing their trip. Ensure all sections are\nwell-integrated while maintaining the detailed insights from each specialist area. Add an executive\nsummary at the beginning highlighting key recommendations across all categories.', 
            'expected_output': 'A well-structured markdown document containing all the synthesized information from the previous\nresearch tasks. The document should follow this structure:\n1) Trip Overview: Basic trip details and executive summary of key recommendations\n2) Transportation: Complete information on getting to and around the destination\n3) Accommodation: Recommended areas to stay and specific accommodation options\n4) Destination Guide: Historical context, cultural insights, and attractions\n5) Dining & Culinary Experiences: Restaurant recommendations and food experiences\n6) Weather & Packing: Weather expectations and detailed packing recommendations\n7) Practical Information: Additional useful tips for the destination\n\nThe final report should be comprehensive yet readable, with clear headings and logical organization.', 
            'agent_assigned': 'report_compiler'
        } 
    }
    
    return agents_config, tasks_config

@CrewBase
class TravelAgentCrew():
    """Enhanced TravelAgentCrew with specialized agents and detailed tasks."""
    
    def __init__(self, active_agents=None):
        """
        Initializes the TravelAgentCrew with multiple LLMs.
        
        Args:
            active_agents (List[str], optional): List of agent names to activate.
                                               If None, all agents are activated.
                                               Possible values: ['transport_planner', 'accommodation_finder',
                                                                'local_guide', 'yelp_dining_expert',
                                                                'packing_and_weather_advisor', 'report_compiler']
        """
        # Store active agents configuration
        self.active_agents = active_agents or ['transport_planner', 'accommodation_finder', 
                                              'local_guide', 'yelp_dining_expert',
                                              'packing_and_weather_advisor', 'report_compiler','report_evaluator']
        
        # Load configs
        self.agents_config, self.tasks_config = load_configs()
        self.kickoff_inputs = None
        
        # Initialize LLMs dictionary
        self.llms = {}
        
        # Initialize Gemini LLM 1 (for Transport Planner)
        if 'transport_planner' in self.active_agents:
            if gemini_api_key_1:
                try:
                    self.llms['gemini_1'] = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=gemini_api_key_1,
                        max_tokens=1024
                    )
                    print("Initialized Gemini LLM 1 for Transport Planner")
                except Exception as e:
                    print(f"Error initializing Gemini LLM 1: {str(e)}")
        
        # Initialize Gemini LLM 3 (for Accommodation Finder)
        if 'accommodation_finder' in self.active_agents:
            if gemini_api_key_3:
                try:
                    self.llms['gemini_3'] = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=gemini_api_key_3,
                        max_tokens=1024
                    )
                    print("Initialized Gemini LLM 3 for Accommodation Finder")
                except Exception as e:
                    print(f"Error initializing Gemini LLM 3: {str(e)}")
        
        # Initialize Gemini LLM 2 (for Local Guide)
        if 'local_guide' in self.active_agents:
            if gemini_api_key_2:
                try:
                    self.llms['gemini_2'] = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=gemini_api_key_2,
                        max_tokens=1024
                    )
                    print("Initialized Gemini LLM 2 for Local Guide")
                except Exception as e:
                    print(f"Error initializing Gemini LLM 2: {str(e)}")
        
        # Initialize a model for Yelp Dining Expert
        if 'yelp_dining_expert' in self.active_agents:
            if gemini_api_key_1:
                try:
                    self.llms['yelp_expert'] = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=gemini_api_key_1,
                        max_tokens=1024
                    )
                    print("Initialized LLM for Yelp Dining Expert")
                except Exception as e:
                    print(f"Error initializing LLM for Yelp Expert: {str(e)}")
        
        # Initialize a model for Weather Advisor
        if 'packing_and_weather_advisor' in self.active_agents:
            if gemini_api_key_2:
                try:
                    self.llms['weather_advisor'] = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=gemini_api_key_2,
                        max_tokens=1024
                    )
                    print("Initialized LLM for Weather Advisor")
                except Exception as e:
                    print(f"Error initializing LLM for Weather Advisor: {str(e)}")
        
        # Initialize tools
        self.tools = {}
        
        # Initialize standard tools
        if YelpRestaurantSearchTool:
            try:
                self.tools['yelp_restaurant'] = YelpRestaurantSearchTool(api_key=yelp_api_key)
                print("Initialized Yelp Restaurant Search Tool")
            except Exception as e:
                print(f"Error initializing YelpRestaurantSearchTool: {str(e)}")
                
        if YelpCulinaryExperienceTool:
            try:
                self.tools['yelp_culinary'] = YelpCulinaryExperienceTool(api_key=yelp_api_key)
                print("Initialized Yelp Culinary Experience Tool")
            except Exception as e:
                print(f"Error initializing YelpCulinaryExperienceTool: {str(e)}")
                
        if LocalFoodSpecialtiesTool:
            try:
                self.tools['local_food_specialties'] = LocalFoodSpecialtiesTool(api_key=yelp_api_key)
                print("Initialized Local Food Specialties Tool")
            except Exception as e:
                print(f"Error initializing LocalFoodSpecialtiesTool: {str(e)}")
                
        if HistoricalInfoTool:
            try:
                self.tools['historical_info'] = HistoricalInfoTool()
                print("Initialized Historical Info Tool")
            except Exception as e:
                print(f"Error initializing HistoricalInfoTool: {str(e)}")
                
        if CulturalCustomsTool:
            try:
                self.tools['cultural_customs'] = CulturalCustomsTool()
                print("Initialized Cultural Customs Tool")
            except Exception as e:
                print(f"Error initializing CulturalCustomsTool: {str(e)}")
                
        if FunFactsTool:
            try:
                self.tools['fun_facts'] = FunFactsTool()
                print("Initialized Fun Facts Tool")
            except Exception as e:
                print(f"Error initializing FunFactsTool: {str(e)}")
                
        if WeatherForecastTool:
            try:
                self.tools['weather_forecast'] = WeatherForecastTool()
                print("Initialized Weather Forecast Tool")
            except Exception as e:
                print(f"Error initializing WeatherForecastTool: {str(e)}")
                
        if ClothingRecommendationTool:
            try:
                self.tools['clothing_recommendation'] = ClothingRecommendationTool()
                print("Initialized Clothing Recommendation Tool")
            except Exception as e:
                print(f"Error initializing ClothingRecommendationTool: {str(e)}")
                
        if GeoapifyPOITool:
            try:
                self.tools['geoapify_poi'] = GeoapifyPOITool()
                print("Initialized Geoapify POI Tool")
            except Exception as e:
                print(f"Error initializing GeoapifyPOITool: {str(e)}")
                
        if PublicTransportSearchTool:
            try:
                self.tools['public_transport'] = PublicTransportSearchTool()
                print("Initialized Public Transport Search Tool")
            except Exception as e:
                print(f"Error initializing PublicTransportSearchTool: {str(e)}")
        
        # Add City Code Lookup Tool
        if CityCodeLookupTool:
            try:
                self.tools['city_code_lookup'] = CityCodeLookupTool()
                print("Initialized City Code Lookup Tool")
            except Exception as e:
                print(f"Error initializing CityCodeLookupTool: {str(e)}")
        
        # Add Amadeus tools
        if AmadeusFlightSearchTool:
            try:
                self.tools['amadeus_flight'] = AmadeusFlightSearchTool()
                print("Initialized Amadeus Flight Search Tool")
            except Exception as e:
                print(f"Error initializing AmadeusFlightSearchTool: {str(e)}")
                
        if AmadeusHotelSearchTool:
            try:
                self.tools['amadeus_hotel'] = AmadeusHotelSearchTool()
                print("Initialized Amadeus Hotel Search Tool")
            except Exception as e:
                print(f"Error initializing AmadeusHotelSearchTool: {str(e)}")
                
        if serper_api_key:
            try:
                self.tools['serper'] = SerperDevTool(api_key=serper_api_key)
                print("Initialized Serper Dev Tool")
            except Exception as e:
                print(f"Error initializing SerperDevTool: {str(e)}")

    def get_tools_for_agent(self, agent_type):
        """Get the appropriate tools for an agent type with kickoff_inputs context."""
        tools = []
        
        if agent_type == 'transport_planner':
            # Transport Planner tools
            if self.tools.get('amadeus_flight'): tools.append(self.tools['amadeus_flight'])
            if self.tools.get('public_transport'): tools.append(self.tools['public_transport'])
            if self.tools.get('city_code_lookup'): tools.append(self.tools['city_code_lookup'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'accommodation_finder':
            # Accommodation Finder tools
            if self.tools.get('amadeus_hotel'): tools.append(self.tools['amadeus_hotel'])
            if self.tools.get('geoapify_poi'): tools.append(self.tools['geoapify_poi'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'local_guide':
            # Local Guide tools
            if self.tools.get('historical_info'): tools.append(self.tools['historical_info'])
            if self.tools.get('cultural_customs'): tools.append(self.tools['cultural_customs'])
            if self.tools.get('fun_facts'): tools.append(self.tools['fun_facts'])
            if self.tools.get('geoapify_poi'): tools.append(self.tools['geoapify_poi'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'yelp_dining_expert':
            # Specialized Yelp Dining Expert tools
            if self.tools.get('yelp_restaurant'): 
                # Pass kickoff_inputs to the tool if it has a setter method
                if hasattr(self.tools['yelp_restaurant'], 'set_kickoff_inputs'):
                    self.tools['yelp_restaurant'].set_kickoff_inputs(self.kickoff_inputs)
                tools.append(self.tools['yelp_restaurant'])
            
            if self.tools.get('yelp_culinary'):
                # Pass kickoff_inputs to the tool if it has a setter method
                if hasattr(self.tools['yelp_culinary'], 'set_kickoff_inputs'):
                    self.tools['yelp_culinary'].set_kickoff_inputs(self.kickoff_inputs)
                tools.append(self.tools['yelp_culinary'])
                
            if self.tools.get('local_food_specialties'):
                # Pass kickoff_inputs to the tool if it has a setter method
                if hasattr(self.tools['local_food_specialties'], 'set_kickoff_inputs'):
                    self.tools['local_food_specialties'].set_kickoff_inputs(self.kickoff_inputs)
                tools.append(self.tools['local_food_specialties'])
                
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'packing_and_weather_advisor':
            # Weather and Packing Advisor tools
            if self.tools.get('weather_forecast'): tools.append(self.tools['weather_forecast'])
            if self.tools.get('clothing_recommendation'): tools.append(self.tools['clothing_recommendation'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        elif agent_type == 'report_evaluator':          # ← add this block
            tools = list(self.tools.values())
        # Return only non-None tools
        valid_tools = [t for t in tools if t is not None]
        print(f"Assigned {len(valid_tools)} tools to {agent_type}")
        return valid_tools

    def _generate_fallback_report(self):
        """Generate a fallback report with basic information when full report generation fails."""
        inputs = self.kickoff_inputs
        destination = inputs.get('destination', "your destination")
        start_date = inputs.get('start_date', "your start date")
        end_date = inputs.get('end_date', "your end date")
        
        report = f"""# Your Travel Plan to {destination}

## Trip Overview
- **Destination**: {destination}
- **Dates**: {start_date} to {end_date}
- **Starting Point**: {inputs.get('starting_point', 'Not specified')}

## Transportation
For transportation options between {inputs.get('starting_point', 'your starting point')} and {destination}, we recommend checking:
- Major airlines for flights
- Public transportation websites specific to {destination}
- Ride-sharing and car rental services

## Accommodation
When staying in {destination}, consider these popular areas:
- City center locations for convenience to attractions
- Authentic neighborhoods for local experience
- Accommodations with good public transport connections

## Local Attractions
{destination} is known for its unique attractions and experiences. Popular activities include:
- Visiting historical and cultural landmarks
- Exploring local cuisine and markets
- Taking guided tours to better understand the destination

## Weather and Packing
Research the typical weather for {destination} during your travel dates ({start_date} to {end_date}) and pack accordingly.

*This is a basic travel plan. For a more detailed itinerary, please try again.*
"""
        return report

    def aggregate_results(self, context):
        """Aggregate results and save the report."""
        try:
            # Extract report content based on the context type
            if hasattr(context, 'tasks_output') and context.tasks_output:
                # Reconstruct the full report from individual task outputs
                final_report_content = f"# Your Travel Plan to {self.kickoff_inputs.get('destination', 'Your Destination')}\n\n"

                # Add trip overview
                final_report_content += "## Trip Overview\n"
                final_report_content += f"- **Destination**: {self.kickoff_inputs.get('destination', 'Your Destination')}\n"
                final_report_content += f"- **Dates**: {self.kickoff_inputs.get('start_date', 'Start Date')} to {self.kickoff_inputs.get('end_date', 'End Date')}\n"
                final_report_content += f"- **Starting Point**: {self.kickoff_inputs.get('starting_point', 'Starting Point')}\n"
                final_report_content += f"- **Travelers**: {self.kickoff_inputs.get('travelers', '1')}\n"
                final_report_content += f"- **Budget**: {self.kickoff_inputs.get('budget', 'Not specified')}\n"

                if 'interests' in self.kickoff_inputs and self.kickoff_inputs['interests']:
                    final_report_content += f"- **Interests**: {', '.join(self.kickoff_inputs['interests'])}\n\n"
                else:
                    final_report_content += "\n"

                # Process transportation task output
                transport_tasks = [t for t in context.tasks_output if 'transport' in t.name.lower() or 'flight' in t.name.lower()]
                if transport_tasks:
                    transport_content = transport_tasks[0].raw
                    transport_content = transport_content.replace('```markdown', '').replace('```', '')
                    final_report_content += "## Transportation\n\n"
                    final_report_content += transport_content + "\n\n"

                # Process accommodation task output
                accomm_tasks = [t for t in context.tasks_output if 'accommodation' in t.name.lower() or 'hotel' in t.name.lower()]
                if accomm_tasks:
                    accomm_content = accomm_tasks[0].raw
                    accomm_content = accomm_content.replace('```markdown', '').replace('```', '')
                    final_report_content += "## Accommodation\n\n"
                    final_report_content += accomm_content + "\n\n"

                # Process local guide task output
                local_tasks = [t for t in context.tasks_output if 'local' in t.name.lower() or 'context' in t.name.lower()]
                if local_tasks:
                    local_content = local_tasks[0].raw
                    local_content = local_content.replace('```markdown', '').replace('```', '')
                    final_report_content += "## Destination Guide\n\n"
                    final_report_content += local_content + "\n\n"

                # Process dining recommendations task output
                dining_tasks = [t for t in context.tasks_output if 'dining' in t.name.lower() or 'food' in t.name.lower()]
                if dining_tasks:
                    dining_content = dining_tasks[0].raw
                    dining_content = dining_content.replace('```markdown', '').replace('```', '')
                    final_report_content += "## Dining & Culinary Experiences\n\n"
                    final_report_content += dining_content + "\n\n"

                # Process weather and packing advice
                weather_tasks = [t for t in context.tasks_output if 'weather' in t.name.lower() or 'packing' in t.name.lower()]
                if weather_tasks:
                    weather_content = weather_tasks[0].raw
                    weather_content = weather_content.replace('```markdown', '').replace('```', '')
                    final_report_content += "## Weather & Packing\n\n"
                    final_report_content += weather_content + "\n\n"

                # Add Practical Information section
                final_report_content += "## Practical Information\n\n"
                final_report_content += "### Important Notes\n"
                final_report_content += "- This travel plan provides recommendations based on available information at the time of creation.\n"
                final_report_content += "- Prices, availability, and schedules may change; always verify current information before booking.\n"
                final_report_content += "- For real-time pricing and booking, please visit the official websites of the recommended services.\n\n"

                # Verify the content is complete by checking for missing sections
                sections_to_check = ['Transportation', 'Accommodation', 'Destination Guide', 'Dining', 'Weather']
                missing_sections = []
                for section in sections_to_check:
                    if section.lower() not in final_report_content.lower():
                        missing_sections.append(section)

                if missing_sections:
                    final_report_content += "\n\n---\n*Note: This report may be incomplete. The following sections are missing: "
                    final_report_content += ", ".join(missing_sections) + ".*"
            
            else:
                final_report_content = self._generate_fallback_report()

            # Save the report
            destination = self.kickoff_inputs.get('destination', "UnknownDestination")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_destination = "".join(c if c.isalnum() else "_" for c in destination)
            reports_dir = 'reports'
            os.makedirs(reports_dir, exist_ok=True)
            filename = os.path.join(reports_dir, f"travel_plan_{safe_destination}_{timestamp}.md")

            with open(filename, 'w', encoding='utf-8') as file:
                file.write(final_report_content)

            # Return the path as a string
            return filename
            
        except Exception as e:
            # Create an emergency report file
            emergency_file = os.path.join('reports', f"emergency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            with open(emergency_file, 'w', encoding='utf-8') as file:
                emergency_content = self._generate_fallback_report()
                file.write(emergency_content)
            return emergency_file
    
    def kickoff(self, inputs=None):
        """Kick off the crew with the given inputs."""
        if inputs is None:
            raise ValueError("Inputs dictionary cannot be None for kickoff.")

        self.kickoff_inputs = inputs

        # Validate required inputs
        required_inputs = ['starting_point', 'destination', 'start_date', 'end_date']
        missing_inputs = [inp for inp in required_inputs if inp not in inputs]
        if missing_inputs:
            raise ValueError(f"Missing required inputs for kickoff: {', '.join(missing_inputs)}")

        # Get active agents override from inputs if provided
        if 'active_agents' in inputs:
            self.active_agents = inputs['active_agents']
            if not self.active_agents or not isinstance(self.active_agents, list):
                # Fall back to default if invalid
                self.active_agents = ['transport_planner', 'accommodation_finder', 
                                     'local_guide', 'yelp_dining_expert',
                                     'packing_and_weather_advisor', 'report_compiler']
            
            # Ensure report_compiler is always included
            if 'report_compiler' not in self.active_agents:
                self.active_agents.append('report_compiler')

        # Create and run the crew
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        
        # Create a report filename
        destination = inputs.get('destination', "UnknownDestination")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_destination = "".join(c if c.isalnum() else "_" for c in destination)
        reports_dir = 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        filename = os.path.join(reports_dir, f"travel_plan_{safe_destination}_{timestamp}.md")
        
        # If result is already a file path, return it
        if isinstance(result, str) and os.path.exists(result):
            return result
            
        # Otherwise generate from context
        if hasattr(result, 'tasks_output') and result.tasks_output:
            return self.aggregate_results(result)
        
        return self.aggregate_results(None)  # Use fallback report

    @agent
    def transport_planner(self):
        """Defines the enhanced Transport Planner agent."""
        if 'transport_planner' not in self.active_agents:
            return None

        # Use any available LLM
        available_llm_keys = [k for k in self.llms.keys() if k.startswith('gemini')]
        if not available_llm_keys:
            return None

        config = self.agents_config.get('transport_planner', {})
        tools = self.get_tools_for_agent('transport_planner')

        return Agent(
            role=config.get('role', 'Transport & Flight Planner'),
            goal=config.get('goal', 'Find comprehensive transportation options.'),
            backstory=config.get('backstory', 'Transport expert.'),
            llm=self.llms[available_llm_keys[0]],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def accommodation_finder(self):
        """Defines the enhanced Accommodation & Local Stay Specialist agent."""
        if 'accommodation_finder' not in self.active_agents:
            return None

        # Use any available LLM
        available_llm_keys = [k for k in self.llms.keys() if k.startswith('gemini')]
        if not available_llm_keys:
            return None

        config = self.agents_config.get('accommodation_finder', {})
        tools = self.get_tools_for_agent('accommodation_finder')

        return Agent(
            role=config.get('role', 'Accommodation & Local Stay Specialist'),
            goal=config.get('goal', 'Find diverse accommodation options.'),
            backstory=config.get('backstory', 'Accommodation expert.'),
            llm=self.llms[available_llm_keys[0]],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def local_guide(self):
        """Defines the enhanced Local Guide agent."""
        if 'local_guide' not in self.active_agents:
            return None

        # Use any available LLM
        available_llm_keys = [k for k in self.llms.keys() if k.startswith('gemini')]
        if not available_llm_keys:
            return None
            
        config = self.agents_config.get('local_guide', {})
        tools = self.get_tools_for_agent('local_guide')
        
        return Agent(
            role=config.get('role', 'Destination Expert & Cultural Context Provider'),
            goal=config.get('goal', 'Provide comprehensive destination information.'),
            backstory=config.get('backstory', 'Destination expert.'),
            llm=self.llms[available_llm_keys[0]],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def yelp_dining_expert(self):
        """Defines the specialized Yelp Dining Expert agent."""
        if 'yelp_dining_expert' not in self.active_agents:
            return None
            
        # Use any available LLM
        llm_to_use = None
        if 'yelp_expert' in self.llms:
            llm_to_use = 'yelp_expert'
        else:
            available_llm_keys = [k for k in self.llms.keys() if k.startswith('gemini')]
            if not available_llm_keys:
                return None
            llm_to_use = available_llm_keys[0]
            
        config = self.agents_config.get('yelp_dining_expert', {})
        tools = self.get_tools_for_agent('yelp_dining_expert')
        
        return Agent(
            role=config.get('role', 'Culinary & Dining Experience Specialist'),
            goal=config.get('goal', 'Recommend outstanding dining experiences.'),
            backstory=config.get('backstory', 'Culinary expert.'),
            llm=self.llms[llm_to_use],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def packing_and_weather_advisor(self):
        """Defines the enhanced Weather and Packing Advisor agent."""
        if 'packing_and_weather_advisor' not in self.active_agents:
            return None
            
        # Use any available LLM
        llm_to_use = None
        if 'weather_advisor' in self.llms:
            llm_to_use = 'weather_advisor'
        else:
            available_llm_keys = [k for k in self.llms.keys() if k.startswith('gemini')]
            if not available_llm_keys:
                return None
            llm_to_use = available_llm_keys[0]
            
        config = self.agents_config.get('packing_and_weather_advisor', {})
        tools = self.get_tools_for_agent('packing_and_weather_advisor')
        
        return Agent(
            role=config.get('role', 'Travel Preparation & Weather Specialist'),
            goal=config.get('goal', 'Provide comprehensive travel preparation guidance.'),
            backstory=config.get('backstory', 'Travel preparation expert.'),
            llm=self.llms[llm_to_use],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def report_compiler(self):
        """Defines the Report Compiler agent using any available LLM from the active ones."""
        if 'report_compiler' not in self.active_agents:
            return None
        
        # Use any available LLM
        available_llm_keys = list(self.llms.keys())
        if not available_llm_keys:
            return None
        
        # Choose the first available LLM (preferring Gemini if available)
        gemini_keys = [k for k in available_llm_keys if k.startswith('gemini')]
        llm_key = gemini_keys[0] if gemini_keys else available_llm_keys[0]
        
        config = self.agents_config.get('report_compiler', {})
        
        return Agent(
            role=config.get('role', 'Lead Travel Report Compiler'),
            goal=config.get('goal', 'Compile comprehensive travel report.'),
            backstory=config.get('backstory', 'Report editor.'),
            llm=self.llms[llm_key],
            verbose=True
        )
    @agent
    def report_evaluator(self):
        """QA agent that scores the final itinerary."""
        if 'report_evaluator' not in self.active_agents:
            return None

        # pick any available LLM
        llm_key = next(iter(self.llms)) if self.llms else None
        if not llm_key:
            return None

        cfg = self.agents_config.get('report_evaluator', {})
        return Agent(
            role       = cfg.get('role', 'Travel-Report Quality Evaluator'),
            goal       = cfg.get('goal', 'Evaluate itinerary quality.'),
            backstory  = cfg.get('backstory', 'QA expert.'),
            llm        = self.llms[llm_key],
            tools      = self.get_tools_for_agent('report_evaluator'),
            verbose    = True,
            allow_delegation = False
        )

    @task
    def evaluate_report_task(self):
        """Task: score the compiled report with a rubric."""
        if 'report_evaluator' not in self.active_agents:
            return None

        cfg = self.tasks_config.get('evaluate_report')
        if not cfg:
            return None

        evaluator = self.report_evaluator()
        if not evaluator:
            return None

        description = cfg['description'] + f"\n\n[meta] {self.kickoff_inputs}"
        return Task(
            description     = description,
            expected_output = cfg['expected_output'],
            agent           = evaluator,
            # context is the compiled report task itself
            context         = [self.compile_travel_report_task()]
        )

    @task
    def find_transportation_task(self):
        """Defines the enhanced task for finding transportation."""
        if 'transport_planner' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('find_transportation')
        if not task_config:
            return None
            
        planner = self.transport_planner()
        if not planner:
            return None
            
        description = task_config.get('description', 'Find transportation.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        expected_output = task_config.get('expected_output', 'A comprehensive transportation section.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=planner
        )

    @task
    def find_accommodation_task(self):
        """Defines the enhanced task for finding accommodation."""
        if 'accommodation_finder' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('find_accommodation')
        if not task_config:
            return None
            
        finder = self.accommodation_finder()
        if not finder:
            return None
            
        description = task_config.get('description', 'Find accommodation.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        expected_output = task_config.get('expected_output', 'A well-structured accommodation section.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=finder
        )

    @task
    def get_local_context_task(self):
        """Defines the enhanced task for getting local context and attractions."""
        if 'local_guide' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('get_local_context')
        if not task_config:
            return None
            
        guide = self.local_guide()
        if not guide:
            return None
            
        description = task_config.get('description', 'Get local context.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        expected_output = task_config.get('expected_output', 'A comprehensive local guide section.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=guide
        )

    @task
    def get_dining_recommendations_task(self):
        """Defines the specialized task for getting dining recommendations."""
        if 'yelp_dining_expert' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('get_dining_recommendations')
        if not task_config:
            return None
            
        expert = self.yelp_dining_expert()
        if not expert:
            return None
        
        # Extract relevant parameters from kickoff_inputs
        destination = self.kickoff_inputs.get('destination', '')
        budget = self.kickoff_inputs.get('budget', 'Moderate')
        
        # Map budget preference to Yelp price tiers (1=$, 2=$$, 3=$$$, 4=$$$$)
        price_map = {
            'Budget': '1,2',
            'Moderate': '2,3',
            'Luxury': '3,4'
        }
        price_tier = price_map.get(budget, '1,2,3,4')
        
        # Include these parameters in the task description
        enhanced_description = task_config.get('description', 'Get dining recommendations.') + f"""
        
[Input Data]: {self.kickoff_inputs}

Additional Yelp Search Parameters:
- Location: {destination}
- Price Range: {price_tier} (based on budget preference: {budget})
- Search for diverse options including local specialties and famous restaurants
"""
            
        expected_output = task_config.get('expected_output', 'A well-structured dining section.')
        
        return Task(
            description=enhanced_description,
            expected_output=expected_output,
            agent=expert
        )

    @task
    def get_weather_and_packing_advice_task(self):
        """Defines the enhanced task for getting weather and packing advice."""
        if 'packing_and_weather_advisor' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('get_weather_and_packing_advice')
        if not task_config:
            return None
            
        advisor = self.packing_and_weather_advisor()
        if not advisor:
            return None
            
        description = task_config.get('description', 'Get weather and packing advice.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        expected_output = task_config.get('expected_output', 'A detailed weather and packing section.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=advisor
        )

    @task
    def compile_travel_report_task(self):
        """Defines the final task for compiling the comprehensive report."""
        if 'report_compiler' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('compile_travel_report')
        if not task_config:
            return None
            
        compiler = self.report_compiler()
        if not compiler:
            return None

        # Create context from all prerequisite tasks
        tasks = []
        
        # Only include tasks for active agents
        if 'transport_planner' in self.active_agents:
            task = self.find_transportation_task()
            if task: tasks.append(task)
            
        if 'accommodation_finder' in self.active_agents:
            task = self.find_accommodation_task()
            if task: tasks.append(task)
            
        if 'local_guide' in self.active_agents:
            task = self.get_local_context_task()
            if task: tasks.append(task)
            
        if 'yelp_dining_expert' in self.active_agents:
            task = self.get_dining_recommendations_task()
            if task: tasks.append(task)
            
        if 'packing_and_weather_advisor' in self.active_agents:
            task = self.get_weather_and_packing_advice_task()
            if task: tasks.append(task)
        
        description = task_config.get('description', 'Compile travel report.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        expected_output = task_config.get('expected_output', 'A well-structured travel report document.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=compiler,
            context=tasks,
            output_file="temp_report.md",
            action=self.aggregate_results
        )
    
    def crew(self):
        """Creates and returns the assembled Travel Agent Crew with specialized agents."""
        # Create all tasks for active agents
        tasks = []
        
        # Only include tasks for active agents
        if 'transport_planner' in self.active_agents:
            task = self.find_transportation_task()
            if task: tasks.append(task)
            
        if 'accommodation_finder' in self.active_agents:
            task = self.find_accommodation_task()
            if task: tasks.append(task)
            
        if 'local_guide' in self.active_agents:
            task = self.get_local_context_task()
            if task: tasks.append(task)
            
        if 'yelp_dining_expert' in self.active_agents:
            task = self.get_dining_recommendations_task()
            if task: tasks.append(task)
            
        if 'packing_and_weather_advisor' in self.active_agents:
            task = self.get_weather_and_packing_advice_task()
            if task: tasks.append(task)
            
        if 'report_compiler' in self.active_agents:
            task = self.compile_travel_report_task()
            if task: tasks.append(task)

        if 'report_evaluator' in self.active_agents:
            task = self.evaluate_report_task()
            if task: tasks.append(task)
        # Filter out None tasks
        valid_tasks = [t for t in tasks if t is not None]
        
        if not valid_tasks:
            raise ValueError("No valid tasks could be created. Check active_agents and API keys.")
        
        # Get all agents used in valid tasks
        agents = set()
        for task in valid_tasks:
            if task.agent:
                agents.add(task.agent)
        
        if not agents:
            raise ValueError("No valid agents for the crew.")
        
        return Crew(
            agents=list(agents),
            tasks=valid_tasks,
            process=Process.sequential,
            verbose=True
        )