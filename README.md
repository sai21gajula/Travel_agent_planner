# Travel Agent Crew with LangChain Tools

A comprehensive AI-powered travel planning system using CrewAI with Gemini and Groq LLMs, enhanced with specialized LangChain tools for weather, attractions, dining, and more.

## Features

- **Multi-agent AI system** for comprehensive travel planning
- **Mixed LLM approach** using Google's Gemini and Groq's Llama/Mixtral models
- **LangChain tool integration** for specialized capabilities:
  - Weather forecasts and clothing recommendations
  - Restaurant and local food experience search
  - Attraction and activity recommendations
  - Historical and cultural information
  - Browser automation for travel websites
- **Hierarchical process** where specialized agents work under a manager agent
- **Markdown report generation** with all travel details

## Project Structure

```
travel_agent/
├── .env                        # Environment variables
├── main.py                     # Main entry point
├── src/
│   ├── __init__.py
│   ├── travel_agent/
│   │   ├── __init__.py
│   │   ├── crew.py             # Main crew implementation
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── browser_tools.py     # Browser tools for navigating websites
│   │   │   ├── places_tools.py      # Google Places API tools
│   │   │   ├── weather_tools.py     # OpenWeatherMap tools
│   │   │   ├── yelp_tools.py        # Yelp API tools
│   │   │   └── wikipedia_tools.py   # Wikipedia tools
│   │   └── config/
│   │       ├── agents.yaml     # Agent configurations
│   │       └── tasks.yaml      # Task configurations
├── reports/                    # Generated travel reports
└── requirements.txt            # Project dependencies
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/travel-agent-crew.git
   cd travel-agent-crew
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## API Keys Setup

Create a `.env` file in the root directory with the following keys:

```
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY_1=your_groq_api_key_1
GROQ_API_KEY_2=your_groq_api_key_2
SERPER_API_KEY=your_serper_api_key

# LangChain Tool APIs
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
GOOGLE_PLACES_API_KEY=your_google_places_api_key
YELP_API_KEY=your_yelp_api_key
```

### Where to get API keys:

- **Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Groq API Key**: [Groq Cloud](https://console.groq.com/keys)
- **Serper API Key**: [Serper.dev](https://serper.dev)
- **OpenWeatherMap API Key**: [OpenWeatherMap](https://openweathermap.org/api)
- **Google Places API Key**: [Google Cloud Console](https://console.cloud.google.com/)
- **Yelp API Key**: [Yelp Fusion](https://www.yelp.com/developers/documentation/v3/authentication)

## Usage

### Interactive Mode

Run the script without arguments to use interactive mode:

```bash
python main.py
```

This will prompt you for:
- Starting point
- Destination
- Start date
- End date

### Command Line Arguments

Plan a trip using command line arguments:

```bash
python main.py plan --from "New York" --to "Paris" --start "2025-05-15" --end "2025-05-25"
```

### Advanced Features

The system also supports CrewAI's training, testing, and replay features:

```bash
# Train the crew
python main.py train 5 training_data.json

# Replay a specific task
python main.py replay task_123456

# Test the crew
python main.py test 3 gemini-1.5-flash
```

## Agents and Tools

This travel planning system uses five specialized agents, each with dedicated tools:

1. **Transport Planner**
   - FlightSearchWebTool
   - TravelWebsiteNavigationTool
   - SerperDevTool (fallback)

2. **Accommodation Finder**
   - HotelSearchWebTool
   - GooglePlacesTool
   - SerperDevTool (fallback)

3. **Local Guide**
   - AttractionFinderTool
   - YelpRestaurantSearchTool
   - LocalFoodExperienceTool
   - HistoricalInfoTool
   - CulturalCustomsTool
   - FunFactsTool
   - SerperDevTool (fallback)

4. **Weather and Packing Advisor**
   - WeatherForecastTool
   - ClothingRecommendationTool
   - SerperDevTool (fallback)

5. **Report Compiler** (Manager Agent)
   - Synthesizes information from all other agents
   - Creates the final travel report

## Customization

You can customize the agents and tasks by modifying the YAML configuration files in the `config` directory:

- `agents.yaml`: Define agent roles, goals, and backstories
- `tasks.yaml`: Define task descriptions and expected outputs

## Output

The system generates a comprehensive travel report saved as a Markdown file in the `reports` directory. The report includes:

- Transportation options and recommendations
- Accommodation options
- Weather forecast and clothing advice
- Activities, attractions, and restaurants
- Local history and cultural information

## Requirements

- Python 3.9+
- CrewAI
- LangChain
- Google Gemini API key
- Groq API key
- Serper API key
- OpenWeatherMap API key
- Google Places API key
- Yelp API key

## Troubleshooting

- **API Key Issues**: Make sure all required API keys are correctly set in the `.env` file
- **Module Not Found Errors**: Ensure all required packages are installed
- **Browser Tool Errors**: Make sure Playwright is installed and properly configured
- **LLM Errors**: Check if the models (e.g., "gemini-1.5-flash", "llama3-70b-8192") are still available in the respective APIs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CrewAI](https://www.crewai.com/) for the multi-agent framework
- [LangChain](https://www.langchain.com/) for the tools ecosystem
- All the API providers that make this system possible