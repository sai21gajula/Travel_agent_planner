"""
Main crew implementation for the travel agent system using LangChain tools.
This version includes the fix for the Agent tool validation error.
"""
import os
import yaml
import datetime
import nest_asyncio
from dotenv import load_dotenv
import sys

# Apply nest_asyncio (important if any async tools are ever used, like Playwright)
nest_asyncio.apply()

# CrewAI imports
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Handle SerperDevTool import with a fallback mechanism
try:
    from crewai_tools.tools.search_tools import SerperDevTool
except ImportError:
    try:
        from crewai_tools import SerperDevTool
    except ImportError:
        print("Warning: SerperDevTool not available in installed crewai_tools package", file=sys.stderr)
        class SerperDevTool:
            __dummy__ = True
            def __init__(self, *args, **kwargs): print("Warning: Using dummy SerperDevTool (not functional)", file=sys.stderr)
            def __call__(self, *args, **kwargs): return "SerperDevTool not available"

# Import our *lists* of tools from tools/__init__.py
from tools import (
    transport_planner_tools,
    accommodation_finder_tools,
    local_guide_tools,
    weather_advisor_tools
)

# ********** FIX: Import the wrapper function **********
from tools.crewai_tools import wrap_tools

# LangChain imports for LLMs
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# --- Environment Variable Loading & Validation ---
gemini_api_key = os.getenv('GEMINI_API_KEY')
serper_api_key = os.getenv('SERPER_API_KEY')
groq_account1 = os.getenv("GROQ_API_KEY_1", os.getenv("GROQ_API_KEY"))
groq_account2 = os.getenv("GROQ_API_KEY_2", groq_account1) # Fallback for second key

def validate_api_key(key, name):
    """Validate API key exists and warn if missing."""
    if not key:
        print(f"Warning: {name} API Key not found in environment variables.", file=sys.stderr)
        return None
    return key

gemini_api_key = validate_api_key(gemini_api_key, "Gemini")
serper_api_key = validate_api_key(serper_api_key, "Serper")
groq_account1 = validate_api_key(groq_account1, "Groq Account 1")
groq_account2 = validate_api_key(groq_account2, "Groq Account 2")

print("--- Initializing Crew ---")
print("API Keys loaded status:")
print(f"Gemini API Key: {'Loaded' if gemini_api_key else 'Not found'}")
print(f"Serper API Key: {'Loaded' if serper_api_key else 'Not found'}")
print(f"Groq Account 1: {'Loaded' if groq_account1 else 'Not found'}")
print(f"Groq Account 2: {'Loaded' if groq_account2 else 'Not found'}")

# --- Tool Initialization (Serper Fallback) ---
serper_tool = None
if serper_api_key:
    try:
        if SerperDevTool.__name__ == "SerperDevTool" and not getattr(SerperDevTool, "__dummy__", False):
            serper_tool = SerperDevTool()
            print("Initialized SerperDevTool")
        else:
            print("Skipping initialization of dummy SerperDevTool", file=sys.stderr)
    except Exception as e:
         print(f"Error initializing SerperDevTool: {e}", file=sys.stderr)
else:
     print("Warning: SERPER_API_KEY not found. SerperDevTool not initialized.", file=sys.stderr)

# --- LLM Initialization ---
def create_llm(llm_type, api_key, model_name, temperature, max_tokens=None):
    """Creates an LLM instance with error handling."""
    try:
        if not api_key:
            print(f"Skipping {llm_type} LLM ({model_name}) initialization: API key missing.", file=sys.stderr)
            return None

        if llm_type == "gemini":
            llm_params = {
                "model": model_name,
                "google_api_key": api_key,
                "temperature": temperature,
                "convert_system_message_to_human": True
            }
            if max_tokens:
                llm_params["max_output_tokens"] = max_tokens
            print(f"Initializing Gemini: {model_name}, temp={temperature}, max_tokens={max_tokens}")
            return ChatGoogleGenerativeAI(**llm_params)

        elif llm_type == "groq":
            llm_params = {
                "model_name": model_name,
                "groq_api_key": api_key,
                "temperature": temperature
            }
            print(f"Initializing Groq: {model_name}, temp={temperature}")
            return ChatGroq(**llm_params)

        else:
            print(f"Error: Unknown LLM type '{llm_type}'", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error initializing {llm_type} LLM ({model_name}): {e}", file=sys.stderr)
        return None

# Initialize LLMs
print("Initializing LLMs...")
gemini_general_llm = create_llm("gemini", gemini_api_key, "gemini-1.5-flash", 0.3, max_tokens=1024)
groq_planning_llm = create_llm("groq", groq_account2, "mixtral-8x7b-32768", 0.4)
groq_researcher_llm = create_llm("groq", groq_account1, "llama3-70b-8192", 0.3)
gemini_reporter_llm = create_llm("gemini", gemini_api_key, "gemini-1.5-flash", 0.7, max_tokens=2048)
print("LLM Initialization complete.")

# --- Configuration Loading ---
def load_configs():
    """Loads agent and task configurations from YAML files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, 'config')
    agents_path = os.path.join(config_dir, 'agents.yaml')
    tasks_path = os.path.join(config_dir, 'tasks.yaml')

    print(f"Attempting to load configurations from: {agents_path} and {tasks_path}")

    if not os.path.isdir(config_dir):
        print(f"Configuration directory not found: {config_dir}. Using default configs.")
        return _get_default_configs()
    if not os.path.isfile(agents_path) or not os.path.isfile(tasks_path):
        print(f"Config files agents.yaml or tasks.yaml not found. Using default configs.")
        return _get_default_configs()

    try:
        with open(agents_path, 'r') as file: agents_config = yaml.safe_load(file)
        with open(tasks_path, 'r') as file: tasks_config = yaml.safe_load(file)
        if not agents_config or not tasks_config:
            print("Config files loaded but are empty/invalid. Using default configs.")
            return _get_default_configs()
        print("Successfully loaded configurations from YAML files.")
        return agents_config, tasks_config
    except Exception as e:
        print(f"Error loading configurations: {e}. Using default configs.", file=sys.stderr)
        return _get_default_configs()

def _get_default_configs():
    """Returns default configurations if loading from files fails."""
    # (Default configs omitted for brevity - assume they are defined as in the original file)
    print("Using default agent and task configurations (implementation omitted in this snippet).")
    # Placeholder return - replace with actual default dicts if needed
    return {}, {}


# --- Crew Definition ---
@CrewBase
class TravelAgentCrew():
    """TravelAgentCrew defines the crew responsible for planning trips."""
    agents_config: dict
    tasks_config: dict
    kickoff_inputs: dict = None # To store inputs from kickoff

    def __init__(self):
        """Initializes the TravelAgentCrew, loading configurations."""
        print("Initializing TravelAgentCrew class...")
        self.agents_config, self.tasks_config = load_configs()
        if not self.agents_config or not self.tasks_config:
             print("Warning: Agent or Task configurations are empty after loading.", file=sys.stderr)
        else:
             print("Configurations loaded successfully during crew initialization.")

        if not gemini_reporter_llm:
             print("CRITICAL Warning: Gemini Reporter LLM (for manager) failed to initialize.", file=sys.stderr)

    # --- Action Function (Instance Method) ---
    def aggregate_results(self, context: str):
        """
        Action function to process the final context (report) and save it to a file.
        Relies on self.kickoff_inputs being set before crew execution.
        """
        print("\n--- Aggregating Results Action Function ---")
        print(f"Context received (report content starts with):\n{context[:500]}...\n--------------------------")

        report_content = context

        destination = "UnknownDestination"
        start_date = "UnknownStartDate"
        end_date = "UnknownEndDate"

        if self.kickoff_inputs:
            destination = self.kickoff_inputs.get('destination', destination)
            start_date = self.kickoff_inputs.get('start_date', start_date)
            end_date = self.kickoff_inputs.get('end_date', end_date)
            print(f"Inputs retrieved for saving report: Dest={destination}, Start={start_date}, End={end_date}")
        else:
            print("Warning: kickoff_inputs not found on crew instance. Report filename will use defaults.", file=sys.stderr)

        reports_dir = 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_destination = "".join(c if c.isalnum() else "_" for c in destination)
        filename = os.path.join(reports_dir, f"travel_plan_{safe_destination}_{timestamp}.md")

        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(report_content)
            print(f"Report saved successfully to: {filename}")
        except IOError as e:
            print(f"Error saving report to file {filename}: {e}", file=sys.stderr)
            return report_content # Return content if save fails

        return filename

    # --- Agent Definitions ---

    @agent
    def transport_planner(self) -> Agent:
        if not gemini_general_llm: return None
        print("Creating transport_planner agent...")
        agent_tools_instances = list(transport_planner_tools) # Get instances from __init__
        if serper_tool: agent_tools_instances.append(serper_tool)
        # ********** FIX: Wrap the tool instances **********
        wrapped_agent_tools = wrap_tools(agent_tools_instances)
        print(f" -> Assigning tools: {[t['name'] for t in wrapped_agent_tools]}") # Print names from wrapped dicts
        return Agent(
            config=self.agents_config.get('transport_planner', {}),
            tools=wrapped_agent_tools, # Pass the wrapped tools
            llm=gemini_general_llm,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def accommodation_finder(self) -> Agent:
        if not groq_planning_llm: return None
        print("Creating accommodation_finder agent...")
        agent_tools_instances = list(accommodation_finder_tools)
        if serper_tool: agent_tools_instances.append(serper_tool)
        # ********** FIX: Wrap the tool instances **********
        wrapped_agent_tools = wrap_tools(agent_tools_instances)
        print(f" -> Assigning tools: {[t['name'] for t in wrapped_agent_tools]}")
        return Agent(
            config=self.agents_config.get('accommodation_finder', {}),
            tools=wrapped_agent_tools, # Pass the wrapped tools
            llm=groq_planning_llm,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def local_guide(self) -> Agent:
        if not groq_researcher_llm: return None
        print("Creating local_guide agent...")
        agent_tools_instances = list(local_guide_tools)
        if serper_tool: agent_tools_instances.append(serper_tool)
        # ********** FIX: Wrap the tool instances **********
        wrapped_agent_tools = wrap_tools(agent_tools_instances)
        print(f" -> Assigning tools: {[t['name'] for t in wrapped_agent_tools]}")
        return Agent(
            config=self.agents_config.get('local_guide', {}),
            tools=wrapped_agent_tools, # Pass the wrapped tools
            llm=groq_researcher_llm,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def packing_and_weather_advisor(self) -> Agent:
        if not gemini_general_llm: return None
        print("Creating packing_and_weather_advisor agent...")
        agent_tools_instances = list(weather_advisor_tools)
        if serper_tool: agent_tools_instances.append(serper_tool)
        # ********** FIX: Wrap the tool instances **********
        wrapped_agent_tools = wrap_tools(agent_tools_instances)
        print(f" -> Assigning tools: {[t['name'] for t in wrapped_agent_tools]}")
        return Agent(
            config=self.agents_config.get('packing_and_weather_advisor', {}),
            tools=wrapped_agent_tools, # Pass the wrapped tools
            llm=gemini_general_llm,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def report_compiler(self) -> Agent:
        if not gemini_reporter_llm: return None
        print("Creating report_compiler agent (Manager)...")
        # Manager typically doesn't need tools
        return Agent(
            config=self.agents_config.get('report_compiler', {}),
            llm=gemini_reporter_llm,
            verbose=True
        )

    # --- Task Definitions ---
    # No changes needed here, they use the agents which now have wrapped tools

    @task
    def find_transportation_task(self) -> Task:
        print("Defining find_transportation_task...")
        task_config = self.tasks_config.get('find_transportation')
        if not task_config: print("Error: 'find_transportation' task config missing."); return None
        planner = self.transport_planner()
        if not planner: print("Skipping task: transport_planner agent not available."); return None
        return Task(
            config=task_config,
            agent=planner,
            description=task_config.get('description', 'Find transportation.') + "\n\n[Debug Info] Current Inputs (if available): " + str(self.kickoff_inputs)
        )

    @task
    def find_accommodation_task(self) -> Task:
        print("Defining find_accommodation_task...")
        task_config = self.tasks_config.get('find_accommodation')
        if not task_config: print("Error: 'find_accommodation' task config missing."); return None
        finder = self.accommodation_finder()
        if not finder: print("Skipping task: accommodation_finder agent not available."); return None
        return Task(
            config=task_config,
            agent=finder,
            description=task_config.get('description', 'Find accommodation.') + "\n\n[Debug Info] Current Inputs (if available): " + str(self.kickoff_inputs)
        )

    @task
    def get_local_recommendations_task(self) -> Task:
        print("Defining get_local_recommendations_task...")
        task_config = self.tasks_config.get('get_local_recommendations')
        if not task_config: print("Error: 'get_local_recommendations' task config missing."); return None
        guide = self.local_guide()
        if not guide: print("Skipping task: local_guide agent not available."); return None
        return Task(
            config=task_config,
            agent=guide,
            description=task_config.get('description', 'Get local recommendations.') + "\n\n[Debug Info] Current Inputs (if available): " + str(self.kickoff_inputs)
        )

    @task
    def get_weather_and_packing_advice_task(self) -> Task:
        print("Defining get_weather_and_packing_advice_task...")
        task_config = self.tasks_config.get('get_weather_and_packing_advice')
        if not task_config: print("Error: 'get_weather_and_packing_advice' task config missing."); return None
        advisor = self.packing_and_weather_advisor()
        if not advisor: print("Skipping task: packing_and_weather_advisor agent not available."); return None
        return Task(
            config=task_config,
            agent=advisor,
            description=task_config.get('description', 'Get weather and packing advice.') + "\n\n[Debug Info] Current Inputs (if available): " + str(self.kickoff_inputs)
        )

    @task
    def compile_travel_report_task(self) -> Task:
        print("Defining compile_travel_report_task (Final Task)...")
        task_config = self.tasks_config.get('compile_travel_report')
        if not task_config: print("Error: 'compile_travel_report' task config missing."); return None
        compiler = self.report_compiler()
        if not compiler: print("Skipping task: report_compiler agent not available."); return None

        prerequisite_task_methods = [
             self.find_transportation_task,
             self.find_accommodation_task,
             self.get_local_recommendations_task,
             self.get_weather_and_packing_advice_task
        ]
        prerequisite_tasks = [task_method() for task_method in prerequisite_task_methods]
        valid_prerequisite_tasks = [task for task in prerequisite_tasks if task is not None]

        print(f"Number of valid prerequisite tasks for report: {len(valid_prerequisite_tasks)}")
        if not valid_prerequisite_tasks:
             print("Error: No prerequisite tasks initialized successfully. Cannot create compile_travel_report task.", file=sys.stderr)
             return None

        return Task(
            config=task_config,
            agent=compiler,
            context=valid_prerequisite_tasks,
            action=self.aggregate_results
        )

    # --- Main Crew Definition ---
    @crew
    def crew(self) -> Crew:
        """Creates and returns the Travel Agent Crew."""
        print("Assembling crew...")
        manager_agent_instance = self.report_compiler()
        if not manager_agent_instance:
             raise SystemExit("Critical Error: Manager agent (report_compiler) failed to initialize. Cannot create crew.")

        worker_agents = [
            self.transport_planner(),
            self.accommodation_finder(),
            self.local_guide(),
            self.packing_and_weather_advisor(),
        ]
        initialized_workers = [agent for agent in worker_agents if agent is not None]

        if not initialized_workers:
             raise SystemExit("Critical Error: No worker agents were successfully initialized. Cannot create crew.")
        print(f"Initialized {len(initialized_workers)} worker agents.")

        final_task = self.compile_travel_report_task()
        if not final_task:
             raise SystemExit("Critical Error: Final task 'compile_travel_report' could not be initialized.")

        if not manager_agent_instance.llm:
             raise SystemExit("Critical Error: Manager agent LLM is not initialized.")

        print("--- Crew Assembly Complete ---")
        return Crew(
            agents=initialized_workers,
            tasks=[final_task],
            process=Process.hierarchical,
            manager_llm=manager_agent_instance.llm,
            # manager_agent=manager_agent_instance, # Deprecated
            verbose=2,
        )

    def kickoff(self, inputs=None):
        """
        Kickoff the crew with the given inputs. Stores inputs and calls the crew's kickoff.
        """
        if inputs is None: raise ValueError("Inputs dictionary cannot be None for kickoff.")

        print(f"Starting travel planning with inputs: {inputs}")
        self.kickoff_inputs = inputs

        required_inputs = ['starting_point', 'destination', 'start_date', 'end_date']
        missing_inputs = [inp for inp in required_inputs if inp not in inputs]
        if missing_inputs: raise ValueError(f"Missing required inputs for kickoff: {', '.join(missing_inputs)}")

        try:
            crew_instance = self.crew()
        except SystemExit as e:
            print(f"Failed to assemble crew: {e}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Unexpected error during crew assembly: {e}", file=sys.stderr)
            raise

        report_result = crew_instance.kickoff(inputs=inputs)
        return report_result
