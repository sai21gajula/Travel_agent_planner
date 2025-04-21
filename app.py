#!/usr/bin/env python
"""
Main entry point for the Travel Agent application.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Import the crew
    from crew import TravelAgentCrew
    
    # Import the tools wrapper (in case we need it directly)
    from tools.crewai_tools import wrap_tools
    
    print("--- Travel Agent Application Starting ---")
    print("Initializing crew components...")
    
    # Initialize the crew
    crew_runner = TravelAgentCrew()
    
    # Launch Streamlit interface
    print("Starting Streamlit web interface...")
    
    # Use Streamlit to run the app
    import streamlit as st
    
    st.title("AI Travel Agent")
    
    with st.form("travel_form"):
        st.header("Enter Your Travel Details")
        
        starting_point = st.text_input("Starting location", "New York, USA")
        destination = st.text_input("Destination", "Paris, France")
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
        
        submit_button = st.form_submit_button("Plan My Trip")
    
    if submit_button:
        st.write("Planning your trip... This may take several minutes.")
        
        try:
            # Format dates as strings
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Initialize inputs
            inputs = {
                'starting_point': starting_point,
                'destination': destination,
                'start_date': start_date_str,
                'end_date': end_date_str
            }
            
            # Run the crew with the inputs
            with st.spinner("AI agents are planning your trip..."):
                report_path = crew_runner.kickoff(inputs=inputs)
            
            # Display success
            st.success(f"Trip planning completed! Report saved to: {report_path}")
            
            # Read and display the report
            try:
                with open(report_path, 'r') as file:
                    report_content = file.read()
                st.markdown(report_content)
            except:
                st.error("Could not read the generated report file.")
                
        except Exception as e:
            st.error(f"An error occurred during planning: {str(e)}")
    
except Exception as e:
    print(f"An unexpected error occurred during initial setup: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)