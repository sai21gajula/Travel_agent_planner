"""
Main crew implementation for the travel agent system.
Uses specific LLM instances with separate API keys for each agent.
"""
import os
import yaml
import datetime
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

# Tool Imports - Import the tools directly
try: from tools.yelp_tools import YelpRestaurantSearchTool, LocalFoodExperienceTool
except ImportError: YelpRestaurantSearchTool, LocalFoodExperienceTool = None, None
try: from tools.wikipedia_tools import HistoricalInfoTool, CulturalCustomsTool, FunFactsTool
except ImportError: HistoricalInfoTool, CulturalCustomsTool, FunFactsTool = None, None, None
try: from tools.weather_tools import WeatherForecastTool, ClothingRecommendationTool
except ImportError: WeatherForecastTool, ClothingRecommendationTool = None, None
try: from tools.geoapify_tools import GeoapifyPOITool
except ImportError: GeoapifyPOITool = None
try: from tools.transport_tools import PublicTransportSearchTool
except ImportError: PublicTransportSearchTool = None

# Handle SerperDevTool import
try:
    from crewai_tools import SerperDevTool as OriginalSerperDevTool
    
    # Create a wrapper class that extends CrewAI's BaseTool
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

# --- Environment Variables ---
# Individual API keys for separate LLMs
gemini_api_key_1 = os.getenv('GEMINI_API_KEY')
gemini_api_key_2 = os.getenv('GEMINI_API_KEY_2')
gemini_api_key_3 = os.getenv('GEMINI_API_KEY_3')
groq_api_key_1 = os.getenv('GROQ_API_KEY_1')
groq_api_key_2 = os.getenv('GROQ_API_KEY_2')
serper_api_key = os.getenv('SERPER_API_KEY')

# --- Configuration Loading ---
def load_configs():
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
    # Default configs (unchanged from the original)
    agents_config = { 
        'transport_planner': {
            'role': 'Public Transport Route Finder', 
            'goal': 'Identify available public transportation routes (bus, train, subway, tram)\nnear the origin and destination points for the user\'s trip between {starting_point}\nto {destination} between {start_date} and {end_date}. Provide information on routes\nand operators based on available data.\nNote: Does not provide real-time schedules or flight/car rental booking.\n', 
            'backstory': 'You are a logistics expert specializing in public transit. You use available data feeds\n(like Transitland) to discover existing bus, train, and other public transport routes\nserving the specified locations to help users understand their ground transport options.\n'
        }, 
        'accommodation_finder': {
            'role': 'Accommodation Location Specialist', 
            'goal': 'Identify potential accommodation locations (hotels, hostels, etc.)\nin {destination} for the stay from {start_date} to {end_date} using Point of Interest searches.\nProvide a list including names, addresses, and general location/neighbourhood based on available POI data.\nNote: Does not provide real-time prices or booking availability.\n', 
            'backstory': 'You specialize in finding potential lodging locations using geographic searches.\nYou identify hotels and other accommodation types based on their location and category,\nproviding users with a starting list for further investigation.\n'
        }, 
        'local_guide': {
            'role': 'Destination Expert & Local Guide', 
            'goal': 'Research and recommend key activities, attractions, dining options (using Yelp), and notable museums\n(using Geoapify POI search) in {destination} suitable for a tourist visiting between {start_date} and {end_date}.\nProvide a concise historical overview and fun facts (using Wikipedia). List diverse recommendations\nfor activities/sights and dining (restaurants/cafes/bars), including names, brief descriptions,\ngeneral location, and estimated cost/price range where available from Yelp or POI data.\n', 
            'backstory': 'You are an enthusiastic local guide for {destination}, passionate about sharing the best\nexperiences, food (leveraging Yelp), culture, and history (leveraging Wikipedia) with visitors.\nYou use POI searches (Geoapify) to find attractions and other points of interest, providing curated recommendations\nto make their trip memorable.\n'
        }, 
        'packing_and_weather_advisor': {
            'role': 'Travel Preparation Advisor', 
            'goal': 'Provide a summarized weather forecast for {destination} covering the period {start_date}\nto {end_date} (including temperature ranges, precipitation chance). Based on this forecast,\nrecommend appropriate clothing types and essential items to pack.\n', 
            'backstory': 'You help travelers prepare for their trips by providing essential weather insights for\n{destination} and practical packing advice tailored to the forecast and typical tourist activities.\n(No change needed for this agent\'s role based on tool updates).\n'
        }, 
        'report_compiler': {
            'role': 'Lead Travel Report Compiler (Manager)', 
            'goal': 'Compile the research findings from the Transport Planner, Accommodation Specialist, Local Guide,\nand Packing Advisor into a comprehensive, well-organized, and engaging travel report\nfor the user\'s trip to {destination} from {start_date} to {end_date}.\n', 
            'backstory': 'You are the lead editor responsible for structuring and presenting the final travel plan.\nYour role is to synthesize the information from specialist agents into a cohesive and\nuser-friendly guide, ensuring all requested sections are included.\n(No change needed for this agent\'s role).\n'
        } 
    }
    
    tasks_config = { 
        'find_transportation': {
            'description': 'Research available public transportation routes (bus, train, subway, tram) near the\nstarting point {starting_point} and destination {destination} relevant for travel\nbetween {start_date} and {end_date}. Use the public transport search tool.\nFocus on identifying route names/numbers and operating agencies based on available data (e.g., Transitland).\nNote: This task does NOT search for flights, car rentals, or provide real-time schedules/booking.\n', 
            'expected_output': 'A summary of potential public transport routes found near the origin and destination.\nInclude route names/numbers (e.g., "Bus 5", "Red Line"), vehicle types (bus, train, etc.),\nand the names of the operating agencies, if available in the data. Mention coverage limitations if no routes are found.\n'
        }, 
        'find_accommodation': {
            'description': 'Search for potential accommodation locations (hotels, hostels, guesthouses)\nin {destination} suitable for the period {start_date} to {end_date}.\nUse the Point of Interest search tool (Geoapify) with relevant categories (e.g., \'accommodation.hotel\').\nFocus on identifying names and locations.\nNote: This task does NOT provide real-time pricing, availability, or booking links.\n', 
            'expected_output': 'A list presenting 3-5 potential accommodation locations found via POI search.\nFor each, include the Name, Address, general location/neighbourhood, and main category type (e.g., Hotel, Hostel)\nif available in the POI data. Explicitly state that prices and availability were not searched.\n'
        }, 
        'get_local_recommendations': {
            'description': 'Research and identify top recommendations for tourists visiting {destination} between\n{start_date} and {end_date}. Use Yelp tools for dining/drinking spots. Use the POI search tool (Geoapify)\nfor activities, attractions (category \'tourism.attraction\'), and museums (category \'entertainment.museum\').\nUse Wikipedia tools for a brief historical overview and fun facts.\n', 
            'expected_output': 'Four distinct sections:\n1. Brief History & Fun Facts: A concise summary (1-2 paragraphs) of {destination}\'s history and interesting facts (from Wikipedia).\n2. Top 3-5 Activities/Attractions: List from Geoapify POI search (category \'tourism.attraction\', etc.) with Name, Address/Location.\n3. Top 3 Museums: List from Geoapify POI search (category \'entertainment.museum\') with Name, Address/Location.\n4. Top 3-5 Dining/Drinking spots: List from Yelp search with Name, Cuisine/Type, Price Range [$,$$,$$$], Address/Location, Rating.\n'
        }, 
        'get_weather_and_packing_advice': {
            'description': 'Provide a summarized weather forecast for {destination} between {start_date} and {end_date}\n(including daily temperature ranges, precipitation chance). Based on this forecast, recommend\nappropriate clothing types and essential items (e.g., umbrella, sunscreen) to pack.\n', 
            'expected_output': 'A concise weather summary section covering the trip duration (e.g., "Expect daily highs around X°C, lows around Y°C, with a medium chance of rain mid-week.").\nFollowed by a bulleted list of recommended packing items (e.g., "- Layers (T-shirts, sweaters) - Waterproof jacket - Comfortable walking shoes").\n'
        }, 
        'compile_travel_report': {
            'description': 'Compile all gathered information from previous tasks (public transport options, potential accommodation locations,\nweather/packing, local recommendations) into a single, comprehensive travel report document\nfor the trip to {destination} from {start_date} to {end_date}. Organize the information logically and ensure clarity,\nnoting any limitations (e.g., lack of real-time pricing for accommodation).\n', 
            'expected_output': 'A well-structured markdown document containing all the synthesized information\nfrom the previous research tasks. The structure should follow standard travel itinerary sections\n(e.g., Transportation (Public Transit), Accommodation (Locations), Local Guide, Weather/Packing).\nAcknowledge where information like real-time pricing or booking details were not available due to tool limitations.\n', 
            'agent_assigned': 'report_compiler'
        } 
    }
    
    return agents_config, tasks_config

@CrewBase
class TravelAgentCrew():
    """TravelAgentCrew defines the crew responsible for planning trips."""
    
    def __init__(self, active_agents=None):
        """
        Initializes the TravelAgentCrew with multiple LLMs.
        
        Args:
            active_agents (List[str], optional): List of agent names to activate.
                                               If None, all agents are activated.
                                               Possible values: ['transport_planner', 'accommodation_finder',
                                                                'local_guide', 'packing_and_weather_advisor',
                                                                'report_compiler']
        """
        # Store active agents configuration
        self.active_agents = active_agents or ['transport_planner', 'accommodation_finder', 
                                              'local_guide', 'packing_and_weather_advisor', 
                                              'report_compiler']
        
        # Load configs
        self.agents_config, self.tasks_config = load_configs()
        self.kickoff_inputs = None
        
        # Initialize LLMs dictionary
        self.llms = {}
        
        # Initialize Gemini LLM 1 (for Transport Planner)
        if 'transport_planner' in self.active_agents:
            if gemini_api_key_1:
                try:
                    # Direct API initialization for Gemini
                    self.llms['gemini_1'] = LLM(
                        model="gemini/gemini-2.0-flash",  # Using OpenAI as fallback
                        api_key=gemini_api_key_1,
                        max_tokens=1024
                    )
                    print("Initialized Gemini LLM 1 for Transport Planner")
                except Exception as e:
                    print(f"Error initializing Gemini LLM 1: {str(e)}")
            else:
                print("Warning: Gemini API Key 1 not found - Transport Planner will be disabled")
        
        # Initialize Groq LLM 1 (for Accommodation Finder)
        if 'accommodation_finder' in self.active_agents:
            if gemini_api_key_3:
                try:
                    # Direct initialization for Groq
                    self.llms['groq_2'] = LLM(
                        model="gemini/gemini-2.0-flash",  # Properly formatted provider/model
                        api_key=gemini_api_key_3,
                        max_tokens=512

                    )
                    print("Initialized Groq LLM 1 for Accommodation Finder")
                except Exception as e:
                    print(f"Error initializing Groq LLM 1: {str(e)}")
            else:
                print("Warning: Groq API Key 1 not found - Accommodation Finder will be disabled")
        
        # Initialize Gemini LLM 2 (for Local Guide)
        if 'local_guide' in self.active_agents:
            if gemini_api_key_2:
                try:
                    # Direct API initialization for Gemini
                    self.llms['gemini_2'] = LLM(
                        model="gemini/gemini-2.0-flash",  # Using OpenAI as fallback
                        api_key=gemini_api_key_2,
                        max_tokens=1024

                    )
                    print("Initialized Gemini LLM 2 for Local Guide")
                except Exception as e:
                    print(f"Error initializing Gemini LLM 2: {str(e)}")
            else:
                print("Warning: Gemini API Key 2 not found - Local Guide will be disabled")
        
        # Initialize Groq LLM 2 (for Weather Advisor)
        if 'packing_and_weather_advisor' in self.active_agents:
            if groq_api_key_2:
                try:
                    # Direct initialization for Groq
                    self.llms['groq_2'] = LLM(
                        model="gemini/gemini-2.0-flash",  # Using OpenAI as fallback
                        api_key=gemini_api_key_3,
                        max_tokens=512

                    )
                    print("Initialized Groq LLM 2 for Weather Advisor")
                except Exception as e:
                    print(f"Error initializing Groq LLM 2: {str(e)}")
            else:
                print("Warning: Groq API Key 2 not found - Weather Advisor will be disabled")
        
        # Initialize tools
        self.tools = {}
        
        # Initialize all tools directly
        if YelpRestaurantSearchTool:
            try:
                self.tools['yelp_restaurant'] = YelpRestaurantSearchTool()
            except Exception as e:
                print(f"Error initializing YelpRestaurantSearchTool: {str(e)}")
                self.tools['yelp_restaurant'] = None
                
        if LocalFoodExperienceTool:
            try:
                self.tools['local_food'] = LocalFoodExperienceTool()
            except Exception as e:
                print(f"Error initializing LocalFoodExperienceTool: {str(e)}")
                self.tools['local_food'] = None
                
        if HistoricalInfoTool:
            try:
                self.tools['historical_info'] = HistoricalInfoTool()
            except Exception as e:
                print(f"Error initializing HistoricalInfoTool: {str(e)}")
                self.tools['historical_info'] = None
                
        if CulturalCustomsTool:
            try:
                self.tools['cultural_customs'] = CulturalCustomsTool()
            except Exception as e:
                print(f"Error initializing CulturalCustomsTool: {str(e)}")
                self.tools['cultural_customs'] = None
                
        if FunFactsTool:
            try:
                self.tools['fun_facts'] = FunFactsTool()
            except Exception as e:
                print(f"Error initializing FunFactsTool: {str(e)}")
                self.tools['fun_facts'] = None
                
        if WeatherForecastTool:
            try:
                self.tools['weather_forecast'] = WeatherForecastTool()
            except Exception as e:
                print(f"Error initializing WeatherForecastTool: {str(e)}")
                self.tools['weather_forecast'] = None
                
        if ClothingRecommendationTool:
            try:
                self.tools['clothing_recommendation'] = ClothingRecommendationTool()
            except Exception as e:
                print(f"Error initializing ClothingRecommendationTool: {str(e)}")
                self.tools['clothing_recommendation'] = None
                
        if GeoapifyPOITool:
            try:
                self.tools['geoapify_poi'] = GeoapifyPOITool()
            except Exception as e:
                print(f"Error initializing GeoapifyPOITool: {str(e)}")
                self.tools['geoapify_poi'] = None
                
        if PublicTransportSearchTool:
            try:
                self.tools['public_transport'] = PublicTransportSearchTool()
            except Exception as e:
                print(f"Error initializing PublicTransportSearchTool: {str(e)}")
                self.tools['public_transport'] = None
                
        if serper_api_key:
            try:
                self.tools['serper'] = SerperDevTool(api_key=serper_api_key)
            except Exception as e:
                print(f"Error initializing SerperDevTool: {str(e)}")
                self.tools['serper'] = None

    def get_tools_for_agent(self, agent_type):
        """Get the appropriate tools for an agent type."""
        tools = []
        
        if agent_type == 'transport_planner':
            if self.tools.get('public_transport'): tools.append(self.tools['public_transport'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'accommodation_finder':
            if self.tools.get('geoapify_poi'): tools.append(self.tools['geoapify_poi'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'local_guide':
            if self.tools.get('yelp_restaurant'): tools.append(self.tools['yelp_restaurant'])
            if self.tools.get('local_food'): tools.append(self.tools['local_food'])
            if self.tools.get('geoapify_poi'): tools.append(self.tools['geoapify_poi'])
            if self.tools.get('historical_info'): tools.append(self.tools['historical_info'])
            if self.tools.get('cultural_customs'): tools.append(self.tools['cultural_customs'])
            if self.tools.get('fun_facts'): tools.append(self.tools['fun_facts'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        elif agent_type == 'packing_and_weather_advisor':
            if self.tools.get('weather_forecast'): tools.append(self.tools['weather_forecast'])
            if self.tools.get('clothing_recommendation'): tools.append(self.tools['clothing_recommendation'])
            if self.tools.get('serper'): tools.append(self.tools['serper'])
        
        # Return only non-None tools
        valid_tools = [t for t in tools if t is not None]
        print(f"Assigned {len(valid_tools)} tools to {agent_type}")
        return valid_tools

    def aggregate_results(self, context):
        """Aggregate results and save the report."""
        # Extract report content - handle different object types
        try:
            if isinstance(context, str): 
                final_report_content = context
            elif isinstance(context, dict) and 'result' in context: 
                final_report_content = str(context['result'])
            elif hasattr(context, 'result') and context.result is not None:  # For CrewOutput objects
                final_report_content = str(context.result)
            elif hasattr(context, 'outputs') and context.outputs:  # Another CrewOutput format
                outputs = context.outputs
                if isinstance(outputs, list) and outputs:
                    final_report_content = str(outputs[-1])  # Use the last output
                else:
                    final_report_content = str(outputs)
            elif hasattr(context, '__str__'): 
                final_report_content = str(context)
            else:
                final_report_content = "Error: Could not extract final report content."
            
            # Save the report
            destination = self.kickoff_inputs.get('destination', "UnknownDestination")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_destination = "".join(c if c.isalnum() else "_" for c in destination)
            reports_dir = 'reports'
            os.makedirs(reports_dir, exist_ok=True)
            filename = os.path.join(reports_dir, f"travel_plan_{safe_destination}_{timestamp}.md")
            
            # Log what we're doing
            print(f"Saving report to {filename}")
            print(f"Report content type: {type(final_report_content)}")
            
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(final_report_content)
            
            # Return the path as a string
            return filename
        except Exception as e:
            print(f"Error in aggregate_results: {str(e)}")
            # Create an emergency report file
            emergency_file = os.path.join('reports', f"emergency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            try:
                with open(emergency_file, 'w', encoding='utf-8') as file:
                    file.write(f"Error generating report: {str(e)}\n\nOriginal context: {str(context)}")
                return emergency_file
            except:
                return "Error: Could not save report file"

    @agent
    def transport_planner(self):
        """Defines the Transport Planner agent using Gemini LLM 1."""
        if 'transport_planner' not in self.active_agents:
            return None
            
        if 'gemini_1' not in self.llms:
            print("Transport Planner agent requires Gemini LLM 1, which is not available")
            return None
            
        config = self.agents_config.get('transport_planner', {})
        tools = self.get_tools_for_agent('transport_planner')
        
        return Agent(
            role=config.get('role', 'Public Transport Route Finder'),
            goal=config.get('goal', 'Find transportation routes.'),
            backstory=config.get('backstory', 'Transport expert.'),
            llm=self.llms['gemini_1'],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def accommodation_finder(self):
        """Defines the Accommodation Finder agent using Groq LLM 1."""
        if 'accommodation_finder' not in self.active_agents:
            return None
            
        if 'gemini_1' not in self.llms:
            print("Accommodation Finder agent requires Groq LLM 1, which is not available")
            return None
            
        config = self.agents_config.get('accommodation_finder', {})
        tools = self.get_tools_for_agent('accommodation_finder')
        
        return Agent(
            role=config.get('role', 'Accommodation Location Specialist'),
            goal=config.get('goal', 'Find accommodations.'),
            backstory=config.get('backstory', 'Accommodation expert.'),
            llm=self.llms['gemini_1'],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def local_guide(self):
        """Defines the Local Guide agent using Gemini LLM 2."""
        if 'local_guide' not in self.active_agents:
            return None
            
        if 'gemini_2' not in self.llms:
            print("Local Guide agent requires Gemini LLM 2, which is not available")
            return None
            
        config = self.agents_config.get('local_guide', {})
        tools = self.get_tools_for_agent('local_guide')
        
        return Agent(
            role=config.get('role', 'Destination Expert & Local Guide'),
            goal=config.get('goal', 'Provide local recommendations.'),
            backstory=config.get('backstory', 'Local guide.'),
            llm=self.llms['gemini_2'],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def packing_and_weather_advisor(self):
        """Defines the Packing and Weather Advisor agent using Groq LLM 2."""
        if 'packing_and_weather_advisor' not in self.active_agents:
            return None
            
        if 'groq_2' not in self.llms:
            print("Weather Advisor agent requires Groq LLM 2, which is not available")
            return None
            
        config = self.agents_config.get('packing_and_weather_advisor', {})
        tools = self.get_tools_for_agent('packing_and_weather_advisor')
        
        return Agent(
            role=config.get('role', 'Travel Preparation Advisor'),
            goal=config.get('goal', 'Provide weather and packing advice.'),
            backstory=config.get('backstory', 'Weather expert.'),
            llm=self.llms['groq_2'],
            tools=tools,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def report_compiler(self):
        """Defines the Report Compiler agent using any available LLM from the active ones."""
        if 'report_compiler' not in self.active_agents:
            return None
        
        # Use any available LLM for the report compiler
        available_llm_keys = list(self.llms.keys())
        if not available_llm_keys:
            print("Report Compiler agent requires at least one LLM, but none are available")
            return None
        
        # Choose the first available LLM (preferring Gemini if available)
        gemini_keys = [k for k in available_llm_keys if k.startswith('gemini')]
        llm_key = gemini_keys[0] if gemini_keys else available_llm_keys[0]
        
        config = self.agents_config.get('report_compiler', {})
        
        return Agent(
            role=config.get('role', 'Lead Travel Report Compiler'),
            goal=config.get('goal', 'Compile travel report.'),
            backstory=config.get('backstory', 'Report editor.'),
            llm=self.llms[llm_key],
            verbose=True
        )

    @task
    def find_transportation_task(self):
        """Defines the task for finding transportation."""
        if 'transport_planner' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('find_transportation')
        if not task_config:
            return None
            
        planner = self.transport_planner()
        if not planner:
            return None
            
        description = task_config.get('description', 'Find transportation.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        # Add the expected_output parameter
        expected_output = task_config.get('expected_output', 'A summary of available transportation options.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=planner
        )

    @task
    def find_accommodation_task(self):
        """Defines the task for finding accommodation."""
        if 'accommodation_finder' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('find_accommodation')
        if not task_config:
            return None
            
        finder = self.accommodation_finder()
        if not finder:
            return None
            
        description = task_config.get('description', 'Find accommodation.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        # Add the expected_output parameter
        expected_output = task_config.get('expected_output', 'A list of potential accommodations.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=finder
        )

    @task
    def get_local_recommendations_task(self):
        """Defines the task for getting local recommendations."""
        if 'local_guide' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('get_local_recommendations')
        if not task_config:
            return None
            
        guide = self.local_guide()
        if not guide:
            return None
            
        description = task_config.get('description', 'Get local recommendations.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        # Add the expected_output parameter
        expected_output = task_config.get('expected_output', 'A list of local recommendations including attractions and dining options.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=guide
        )

    @task
    def get_weather_and_packing_advice_task(self):
        """Defines the task for getting weather and packing advice."""
        if 'packing_and_weather_advisor' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('get_weather_and_packing_advice')
        if not task_config:
            return None
            
        advisor = self.packing_and_weather_advisor()
        if not advisor:
            return None
            
        description = task_config.get('description', 'Get weather and packing advice.') + f"\n\n[Input Data]: {self.kickoff_inputs}"
        # Add the expected_output parameter
        expected_output = task_config.get('expected_output', 'A weather forecast and packing recommendations.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=advisor
        )

    @task
    def compile_travel_report_task(self):
        """Defines the final task for compiling the report."""
        if 'report_compiler' not in self.active_agents:
            return None
            
        task_config = self.tasks_config.get('compile_travel_report')
        if not task_config:
            return None
            
        compiler = self.report_compiler()
        if not compiler:
            return None

        # Create context from prerequisite tasks
        tasks = []
        if 'transport_planner' in self.active_agents:
            task = self.find_transportation_task()
            if task: tasks.append(task)
            
        if 'accommodation_finder' in self.active_agents:
            task = self.find_accommodation_task()
            if task: tasks.append(task)
            
        if 'local_guide' in self.active_agents:
            task = self.get_local_recommendations_task()
            if task: tasks.append(task)
            
        if 'packing_and_weather_advisor' in self.active_agents:
            task = self.get_weather_and_packing_advice_task()
            if task: tasks.append(task)
        
        description = task_config.get('description', 'Compile travel report.')
        # Add the expected_output parameter
        expected_output = task_config.get('expected_output', 'A comprehensive travel report document compiled from all previous tasks.')
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=compiler,
            context=tasks,
            action=self.aggregate_results
        )

    @crew
    def crew(self):
        """Creates and returns the assembled Travel Agent Crew."""
        # Create all tasks for active agents
        tasks = []
        
        if 'transport_planner' in self.active_agents:
            task = self.find_transportation_task()
            if task: tasks.append(task)
            
        if 'accommodation_finder' in self.active_agents:
            task = self.find_accommodation_task()
            if task: tasks.append(task)
            
        if 'local_guide' in self.active_agents:
            task = self.get_local_recommendations_task()
            if task: tasks.append(task)
            
        if 'packing_and_weather_advisor' in self.active_agents:
            task = self.get_weather_and_packing_advice_task()
            if task: tasks.append(task)
            
        if 'report_compiler' in self.active_agents:
            task = self.compile_travel_report_task()
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

        # Create and run the crew
        crew_instance = self.crew()
        return crew_instance.kickoff(inputs=inputs)