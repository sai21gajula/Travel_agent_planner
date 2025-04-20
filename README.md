Travel Agent Crew
A comprehensive AI-powered travel planning system using CrewAI with Gemini and Groq LLMs.

Features
Multi-agent AI system for complete travel planning
Uses a combination of Google's Gemini and Groq's LLMs for different specialized roles
Generates comprehensive travel reports including:
Transportation options (flights, trains, car rentals)
Accommodation recommendations
Weather forecasts and clothing advice
Activities, attractions, and restaurants
Local history and cultural context
Installation
Clone the repository:
bash
git clone https://github.com/yourusername/travel-agent-crew.git
cd travel-agent-crew
Create a virtual environment:
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:
bash
pip install -r requirements.txt
API Keys Setup
Create a .env file in the root directory with the following keys:

GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
GROQ_API_KEY_1=your_first_groq_api_key  # can be the same as GROQ_API_KEY
GROQ_API_KEY_2=your_second_groq_api_key  # optional, falls back to GROQ_API_KEY_1
SERPER_API_KEY=your_serper_api_key
Where to get API keys:
Gemini API Key: Visit Google AI Studio
Groq API Key: Visit Groq Cloud
Serper API Key: Visit Serper.dev to sign up
Usage
Interactive Mode
Run the script without arguments to use interactive mode:

bash
python main.py
This will prompt you for:

Starting point
Destination
Start date
End date
Command Line Arguments
Plan a trip using command line arguments:

bash
python main.py plan --from "New York" --to "Paris" --start "2025-05-15" --end "2025-05-25"
Output
The system will generate a comprehensive travel report saved as a Markdown file in the reports directory. The report includes:

Transportation options and recommendations
Accommodation options
Weather forecast and clothing advice
Activities, attractions, and restaurants
Local history and cultural information
Advanced Features
The system also supports CrewAI's training, testing, and replay features:

bash
# Train the crew
python main.py train 5 training_data.json

# Replay a specific task
python main.py replay task_123456

# Test the crew
python main.py test 3 gemini-1.5-flash
Project Structure
travel-agent-crew/
├── .env                      # Environment variables
├── main.py                   # Main entry point
├── requirements.txt          # Dependencies
├── reports/                  # Generated travel reports
└── travel_agent/
    └── src/
        └── travel_agent/
            ├── crew.py       # CrewAI implementation
            └── configs/      # Agent and task configurations
                ├── agents.yaml
                └── tasks.yaml
Customization
You can customize the agents and tasks by modifying the YAML configuration files in the configs directory:

agents.yaml: Define agent roles, goals, and backstories
tasks.yaml: Define task descriptions and expected outputs
Requirements
Python 3.9+
CrewAI
Gemini API key
Groq API key
Serper API key
