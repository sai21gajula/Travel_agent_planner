---
title: AI Travel Planner
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.35.0"
app_file: app.py
pinned: false
python_version: "3.11"
---
link to live demo: https://huggingface.co/spaces/bharath21gaju/Ai-Travel-Planner. 
You can access the report genrated in report and evalaution pipleine evaluation json files for each of the query. 
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
├── app.py                      # Streamlit application
├── crew.py                     # Main crew implementation
├── tools/
│   ├── __init__.py
│   ├── crewai_tools.py         # Tools compatibility layer
│   ├── geoapify_tools.py       # Geoapify POI search tools
│   ├── transport_tools.py      # Public transport search tools
│   ├── weather_tools.py        # OpenWeatherMap tools
│   ├── yelp_tools.py           # Yelp API tools
│   └── wikipedia_tools.py      # Wikipedia tools
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
GEMINI_API_KEY_2=your_gemini_api_key_2
GROQ_API_KEY_1=your_groq_api_key_1
GROQ_API_KEY_2=your_groq_api_key_2
SERPER_API_KEY=your_serper_api_key

# LangChain Tool APIs
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
TRANSITLAND_API_KEY=your_transitland_api_key
YELP_API_KEY=your_yelp_api_key
```

### Where to get API keys:

- **Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Groq API Key**: [Groq Cloud](https://console.groq.com/keys)
- **Serper API Key**: [Serper.dev](https://serper.dev)
- **OpenWeatherMap API Key**: [OpenWeatherMap](https://openweathermap.org/api)
- **Geoapify API Key**: [Geoapify](https://www.geoapify.com/)
- **Transitland API Key**: [Transitland](https://www.transit.land/)
- **Yelp API Key**: [Yelp Fusion](https://www.yelp.com/developers/documentation/v3/authentication)

## Usage

### Interactive Web Interface

Run the Streamlit application:

```bash
streamlit run app.py
```

This will open a web interface where you can:
- Enter your starting point and destination
- Set travel dates
- Specify preferences and interests
- Generate a comprehensive travel plan

### Direct Python Usage

You can also use the TravelAgentCrew class directly in Python:

```python
from crew import TravelAgentCrew

# Initialize the crew
crew = TravelAgentCrew()

# Define your trip details
trip_details = {
    'starting_point': 'New York, USA',
    'destination': 'Paris, France',
    'start_date': '2025-05-21',
    'end_date': '2025-05-28',
    'budget': 'Moderate',
    'travelers': 2,
    'interests': ['Historical Sites', 'Local Cuisine'],
    'accommodation': 'Hotel',
    'travel_style': 'Mix of Everything'
}

# Generate the travel plan
report_path = crew.kickoff(inputs=trip_details)

# The report is saved as a markdown file
print(f"Travel plan saved to: {report_path}")
```

## Agents and Tools

This travel planning system uses five specialized agents, each with dedicated tools:

1. **Transport Planner**
   - PublicTransportSearchTool (Transitland API)
   - SerperDevTool (fallback)

2. **Accommodation Finder**
   - GeoapifyPOITool (for hotels and accommodation)
   - SerperDevTool (fallback)

3. **Local Guide**
   - YelpRestaurantSearchTool
   - LocalFoodExperienceTool
   - GeoapifyPOITool (for attractions)
   - HistoricalInfoTool (Wikipedia)
   - CulturalCustomsTool (Wikipedia)
   - FunFactsTool (Wikipedia)
   - SerperDevTool (fallback)

4. **Weather and Packing Advisor**
   - WeatherForecastTool
   - ClothingRecommendationTool
   - SerperDevTool (fallback)

5. **Report Compiler** (Manager Agent)
   - Synthesizes information from all other agents
   - Creates the final travel report

## Customization

You can customize which agents to use by passing a list to the TravelAgentCrew constructor:

```python
# Use only specific agents
crew = TravelAgentCrew(active_agents=[
    'transport_planner',
    'local_guide',
    'report_compiler'
])
```

## Known Issues

- Transitland API may return 403 Forbidden errors for some locations
- Rate limits on Groq API may cause failures during complex planning
- Gemini authentication requires proper API key formatting

## Requirements

- Python 3.9+
- CrewAI
- LangChain
- Google Gemini API key
- Groq API key
- Serper API key (optional)
- OpenWeatherMap API key
- Geoapify API key
- Yelp API key

## Troubleshooting

- **API Key Issues**: Make sure all required API keys are correctly set in the `.env` file
- **Module Not Found Errors**: Ensure all required packages are installed
- **LLM Errors**: Check if you're hitting rate limits on your API providers
- **Transport API Errors**: The Transitland API may not have coverage for all areas

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CrewAI](https://www.crewai.com/) for the multi-agent framework
- [LangChain](https://www.langchain.com/) for the tools ecosystem
- All the API providers that make this system possible

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
