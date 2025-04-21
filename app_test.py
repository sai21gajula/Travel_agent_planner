#!/usr/bin/env python
"""
Test file to diagnose CrewAI tool compatibility issues
"""
import os
from dotenv import load_dotenv
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.places_tools import GooglePlacesTool
from tools.crewai_tools import wrap_tools

# Load environment variables
load_dotenv()

def test_agent_with_tool():
    """Test agent initialization with a single tool"""
    try:
        # Create a simple agent with a single tool
        tool = GooglePlacesTool()
        print(f"Created tool: {tool}")
        print(f"Tool type: {type(tool)}")
        
        # Convert tool to CrewAI compatible format
        wrapped_tools = wrap_tools([tool])
        print(f"Wrapped tool: {wrapped_tools[0]}")
        
        # Initialize LLM
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Warning: GEMINI_API_KEY not found")
            return False
            
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.4,
            convert_system_message_to_human=True
        )
        
        # Try creating an agent with the wrapped tool
        agent = Agent(
            role="Test Agent",
            goal="Test if tools work properly",
            backstory="I'm a test agent to verify tool compatibility",
            verbose=True,
            tools=wrapped_tools,
            llm=llm
        )
        print("Agent created successfully with tool!")
        return True
    except Exception as e:
        print(f"Error creating agent with tool: {e}")
        return False

if __name__ == "__main__":
    test_agent_with_tool() 