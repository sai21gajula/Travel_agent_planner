from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os
import yaml

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')
serper_api_key = os.getenv('SERPER_API_KEY')

# Multiple Groq accounts
groq_account1 = os.getenv("GROQ_API_KEY_1", os.getenv("GROQ_API_KEY"))
groq_account2 = os.getenv("GROQ_API_KEY_2", groq_account1)

print("API Keys loaded:")
print(f"Gemini API Key: {gemini_api_key[:5]}..." if gemini_api_key else "Gemini API Key: Not found")
print(f"Groq Account 1: {groq_account1[:5]}..." if groq_account1 else "Groq Account 1: Not found")
print(f"Groq Account 2: {groq_account2[:5]}..." if groq_account2 else "Groq Account 2: Not found")
print(f"Serper API Key: {serper_api_key[:5]}..." if serper_api_key else "Serper API Key: Not found")

# Initialize specialized LLMs
gemini_travel_llm = LLM(
    provider="google",
    model="gemini-1.5-flash",
    api_key=gemini_api_key,
    temperature=0.2,
)

gemini_reporter_llm = LLM(
    provider="google",
    model="gemini-1.5-flash",
    api_key=gemini_api_key,
    temperature=0.7,
)

# Groq LLMs for different roles
groq_researcher_llm = LLM(
    provider="groq",
    model="llama3-70b-8192",
    api_key=groq_account1,
    temperature=0.3,
)

groq_planning_llm = LLM(
    provider="groq",
    model="mixtral-8x7b-32768",
    api_key=groq_account2,
    temperature=0.4,
)

# Load agent and task configurations
def load_configs():
    # Define base directory relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Attempt to load from config files
    try:
        with open(os.path.join(base_dir, 'configs', 'agents.yaml'), 'r') as file:
            agents_config = yaml.safe_load(file)
        
        with open(os.path.join(base_dir, 'configs', 'tasks.yaml'), 'r') as file:
            tasks_config = yaml.safe_load(file)
            
        return agents_config, tasks_config
    
    # Fall back to default configs if files not found
    except (FileNotFoundError, yaml.YAMLError):
        print("Warning: Could not load configuration files. Using default configurations.")
        
        # Default agent configurations
        agents_config = {
            'train_finder': {
                'role': 'Train Travel Specialist',
                'goal': 'Find the most convenient and cost-effective train options',
                'backstory': 'You are an expert in train travel with deep knowledge of routes, schedules, and pricing worldwide.'
            },
            'flight_finder': {
                'role': 'Flight Specialist',
                'goal': 'Find the best flight options considering price, duration, and convenience',
                'backstory': 'You are a seasoned travel agent specializing in finding optimal flight arrangements.'
            },
            'car_rental_finder': {
                'role': 'Car Rental Expert',
                'goal': 'Find the most suitable car rental options for travelers',
                'backstory': 'You have years of experience in the car rental industry and know how to find the best deals.'
            },
            'hotel_finder': {
                'role': 'Hotel Accommodation Specialist',
                'goal': 'Find the best hotel options that match travelers\' preferences and budget',
                'backstory': 'You have extensive experience in the hospitality industry and know how to match travelers with their ideal hotels.'
            },
            'airbnb_finder': {
                'role': 'Airbnb and Vacation Rental Specialist',
                'goal': 'Find the best vacation rental options for an authentic local experience',
                'backstory': 'You are an expert in finding unique and comfortable vacation rentals that provide authentic local experiences.'
            },
            'weatherman': {
                'role': 'Travel Meteorologist',
                'goal': 'Provide accurate weather forecasts for travel destinations',
                'backstory': 'You are a meteorologist specializing in travel weather forecasting, helping travelers prepare appropriately.'
            },
            'clothing_advisor': {
                'role': 'Travel Fashion Consultant',
                'goal': 'Recommend appropriate clothing based on destination, activities, and weather',
                'backstory': 'You are a fashion expert who specializes in practical and culturally appropriate travel attire.'
            },
            'museum_finder': {
                'role': 'Cultural Attractions Specialist',
                'goal': 'Find the most interesting museums and cultural sites',
                'backstory': 'You have a PhD in Art History and have visited museums all around the world.'
            },
            'restaurant_finder': {
                'role': 'Culinary Experience Expert',
                'goal': 'Find the best local dining experiences ranging from street food to fine dining',
                'backstory': 'You are a food critic and culinary expert who has dined at restaurants worldwide.'
            },
            'activity_finder': {
                'role': 'Activities and Experiences Coordinator',
                'goal': 'Find the most engaging activities and unique experiences',
                'backstory': 'You specialize in finding unique experiences that create memorable travel moments.'
            },
            'historian': {
                'role': 'Destination Historian',
                'goal': 'Provide rich historical context about travel destinations',
                'backstory': 'You are a historian with expertise in global history and cultural significance of tourist destinations.'
            },
            'reporter_agent': {
                'role': 'Travel Report Compiler',
                'goal': 'Create a comprehensive travel plan report that is informative and well-organized',
                'backstory': 'You are a travel writer known for creating detailed and engaging travel guides.'
            }
        }
        
        # Default task configurations
        tasks_config = {
            'find_transportation': {
                'description': 'Research and recommend the best transportation options from {starting_point} to {destination}, including flights, trains, and car rentals. Consider factors like cost, travel time, convenience, and luggage requirements. If multiple transportation modes are needed, plan the full journey with connections.',
                'expected_output': 'Detailed transportation plan with options, prices, durations, and booking information.'
            },
            'find_hotel': {
                'description': 'Find the best accommodation options in {destination} for a stay from {start_date} to {end_date}. Consider both hotels and vacation rentals. Include options for different budgets and preferences. Provide details on location, amenities, room types, and proximity to attractions.',
                'expected_output': 'List of recommended accommodations with descriptions, prices, and booking details.'
            },
            'get_weather': {
                'description': 'Research the typical weather conditions in {destination} during the period from {start_date} to {end_date}. Include temperature ranges, precipitation likelihood, and any seasonal considerations that might affect travel plans.',
                'expected_output': 'Weather forecast and seasonal considerations with clothing recommendations.'
            },
            'get_activities': {
                'description': 'Discover the best activities, attractions, and dining options in {destination}. Include museums, historical sites, natural attractions, tours, and local experiences. Also recommend restaurants representing local cuisine at various price points.',
                'expected_output': 'Comprehensive list of recommended activities and restaurants with descriptions and practical information.'
            },
            'get_history': {
                'description': 'Research the history and cultural background of {destination}. Include information about historical significance, cultural customs, local etiquette, and interesting facts that would enhance a visitor\'s understanding and appreciation of the destination.',
                'expected_output': 'Historical and cultural overview of the destination.'
            },
            'get_report': {
                'description': 'Compile all the research into a comprehensive travel plan for a trip to {destination}. Organize the information logically and include all relevant details for transportation, accommodation, weather, activities, and cultural context.',
                'expected_output': 'Complete travel plan document organized in a clear and user-friendly format.'
            }
        }
        
        return agents_config, tasks_config


@CrewBase
class TravelAgentCrew():
    def __init__(self):
        # Load configurations
        self.agents_config, self.tasks_config = load_configs()

    # CREATING ALL THE AGENTS

    @agent
    def train_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['train_finder'],
            tools=[SerperDevTool()],
            llm=groq_researcher_llm,
            verbose=True
        )
    
    @agent
    def flight_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['flight_finder'],
            tools=[SerperDevTool()],
            llm=groq_researcher_llm,
            verbose=True
        )
    
    
    @agent
    def car_rental_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['car_rental_finder'],
            tools=[SerperDevTool()],
            llm=groq_researcher_llm,
            verbose=True
        )
    
    @agent
    def hotel_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['hotel_finder'],
            tools=[SerperDevTool()],
            llm=gemini_travel_llm,
            verbose=True
        )
    
    @agent
    def airbnb_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['airbnb_finder'],
            tools=[SerperDevTool()],
            llm=gemini_travel_llm,
            verbose=True
        )
    
    @agent
    def weatherman(self) -> Agent:
        return Agent(
            config=self.agents_config['weatherman'],
            tools=[SerperDevTool()],
            llm=gemini_travel_llm,
            verbose=True
        )
    
    @agent
    def clothing_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['clothing_advisor'],
            tools=[SerperDevTool()],
            llm=gemini_travel_llm,
            verbose=True
        )
    
    @agent
    def museum_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['museum_finder'],
            tools=[SerperDevTool()],
            llm=groq_planning_llm,
            verbose=True
        )
    
    @agent
    def restaurant_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['restaurant_finder'],
            tools=[SerperDevTool()],
            llm=groq_planning_llm,
            verbose=True
        )
    
    @agent
    def activity_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['activity_finder'],
            tools=[SerperDevTool()],
            llm=groq_planning_llm,
            verbose=True
        )
    
    @agent
    def historian(self) -> Agent:
        return Agent(
            config=self.agents_config['historian'],
            tools=[SerperDevTool()],
            llm=groq_researcher_llm,
            verbose=True
        )
    
    @agent
    def reporter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['reporter_agent'],
            llm=gemini_reporter_llm,
            verbose=True
        )

    
    # CREATING ALL THE TASKS
    
    @task
    def find_transportation(self) -> Task:
        return Task(
            config=self.tasks_config['find_transportation'],
        )

    @task
    def find_hotel(self) -> Task:
        return Task(
            config=self.tasks_config['find_hotel'],
        )

    @task
    def get_weather(self) -> Task:
        return Task(
            config=self.tasks_config['get_weather'],
        )

    @task
    def get_activities(self) -> Task:
        return Task(
            config=self.tasks_config['get_activities'],
        )

    @task
    def get_history(self) -> Task:
        return Task(
            config=self.tasks_config['get_history'],
        )


    @task
    def get_report(self) -> Task:
        def aggregate_results(subtask_results):
            # Generate the report
            report = f"""
            # Travel Report for {self.crew().context.get('destination', 'Your Destination')}

            ## Transportation
            {subtask_results['find_transportation']}

            ## Accommodation
            {subtask_results['find_hotel']}

            ## Weather
            {subtask_results['get_weather']}

            ## Activities and Dining
            {subtask_results['get_activities']}

            ## Local History and Culture
            {subtask_results['get_history']}
            """

            # Create reports directory if it doesn't exist
            os.makedirs('reports', exist_ok=True)
            
            # Generate a filename based on the destination
            destination = self.crew().context.get('destination', 'destination').replace(' ', '_').lower()
            filename = f"reports/travel_plan_{destination}.md"
            
            with open(filename, 'w') as file:
                file.write(report)
            return filename

        return Task(
            config=self.tasks_config['get_report'],
            subtasks=[
                self.find_transportation(),
                self.find_hotel(),
                self.get_weather(),
                self.get_activities(),
                self.get_history(),
            ],
            action=aggregate_results,
            output_file='travel_report.md'
        )


    # CREATING ALL THE CREWS

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.train_finder(),
                self.flight_finder(),
                self.car_rental_finder(),
                self.hotel_finder(),
                self.airbnb_finder(),
                self.weatherman(),
                self.clothing_advisor(),
                self.museum_finder(),
                self.restaurant_finder(),
                self.activity_finder(),
                self.historian()
            ],
            tasks=[
                self.get_report(),
            ],
            verbose=True,
            manager_agent=self.reporter_agent(),
            manager_llm=gemini_reporter_llm,
            process=Process.hierarchical
        )