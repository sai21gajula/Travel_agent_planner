#!/usr/bin/env python
"""
Main entry point for the Travel Agent application.
Enhanced Streamlit interface with improved user experience and agent selection.
"""
import os
import sys
import time
import datetime
import re
import streamlit as st
from datetime import timedelta

# Ensure reports directory exists
reports_dir = 'reports'
os.makedirs(reports_dir, exist_ok=True)

try:
    # Import the crew
    from crew import TravelAgentCrew
    
    # Set page configuration
    st.set_page_config(
        page_title="AI Travel Planner",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.8rem;
            color: #0D47A1;
            margin-bottom: 1rem;
        }
        .section-header {
            font-size: 1.5rem;
            color: #1565C0;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        .info-box {
            background-color: #E3F2FD;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        .warning-box {
            background-color: #FFF8E1;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        .success-box {
            background-color: #E8F5E9;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        .error-box {
            background-color: #FFEBEE;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border-left: 4px solid #E53935;
        }
        .card {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .highlight {
            background-color: #BBDEFB;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            font-weight: 500;
        }
        .destination-tag {
            display: inline-block;
            background-color: #1E88E5;
            color: white;
            padding: 0.3rem 0.6rem;
            border-radius: 20px;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            cursor: pointer;
        }
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #EEEEEE;
            color: #757575;
            font-size: 0.9rem;
        }
        /* Enhanced section styling */
        h1 {
            color: #0D47A1;
            border-bottom: 2px solid #1E88E5;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        h2 {
            color: #1565C0;
            border-left: 4px solid #1E88E5;
            padding-left: 10px;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        h3 {
            color: #1976D2;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        ul {
            margin-bottom: 20px;
        }
        .report-container {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }
        .agent-selector {
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 15px;
        }
        .agent-header {
            font-weight: bold;
            color: #1565C0;
        }
        .agent-description {
            font-size: 0.9rem;
            color: #616161;
            margin-top: 5px;
        }
        .loading-animation {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'trip_planned' not in st.session_state:
        st.session_state.trip_planned = False
    if 'report_content' not in st.session_state:
        st.session_state.report_content = None
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None
    if 'planning_time' not in st.session_state:
        st.session_state.planning_time = None
    if 'trip_details' not in st.session_state:
        st.session_state.trip_details = {}
    if 'planning_error' not in st.session_state:
        st.session_state.planning_error = None
    if 'selected_destination' not in st.session_state:
        st.session_state.selected_destination = None
    
    # Header
    st.markdown("<h1 class='main-header'>✈️ AI Travel Planner</h1>", unsafe_allow_html=True)
    
    # Sidebar with information and popular destinations
    with st.sidebar:
        st.markdown("<h3>How It Works</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        This AI Travel Planner uses multiple specialized AI agents to create your personalized travel itinerary:
        
        • <b>Transport Planner</b>: Finds flights and local transport
        • <b>Accommodation Specialist</b>: Locates hotels and lodging
        • <b>Local Guide</b>: Recommends attractions with cultural context
        • <b>Yelp Dining Expert</b>: Finds restaurants and food experiences 
        • <b>Weather Advisor</b>: Provides packing suggestions
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h3>Popular Destinations</h3>", unsafe_allow_html=True)
        
        # Display popular destinations as clickable tags
        popular_destinations = [
            "Paris, France", "Tokyo, Japan", "Rome, Italy", "New York, USA", 
            "Barcelona, Spain", "London, UK", "Sydney, Australia", "Dubai, UAE",
            "Bali, Indonesia", "Rio de Janeiro, Brazil"
        ]
        
        # Create destination tags with JavaScript click handlers
        dest_html = "<div>"
        for dest in popular_destinations:
            dest_id = re.sub(r'[^a-zA-Z0-9]', '', dest)
            dest_html += f'<span class="destination-tag" onclick="selectDestination(\'{dest}\')" id="{dest_id}">{dest}</span>'
        dest_html += "</div>"
        
        # Add JavaScript to handle destination selection
        st.markdown(dest_html, unsafe_allow_html=True)
        st.markdown("""
        <script>
        function selectDestination(dest) {
            // Use Streamlit's component communication
            const data = {
                destination: dest
            };
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: data
            }, "*");
        }
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("<h3>Planning Tips</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="warning-box">
        • <b>Processing Time</b>: Planning takes 3-8 minutes due to extensive research
        • <b>Specific Locations</b>: More specific locations yield better results
        • <b>Date Range</b>: Allow at least 2-3 days for a comprehensive plan
        </div>
        """, unsafe_allow_html=True)
        
        # Add troubleshooting section
        st.markdown("<h3>Troubleshooting</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="error-box">
        If you encounter any issues:
        • Try refreshing the page
        • Use more specific destination names
        • Try again in a few minutes (service may be busy)
        • Check your internet connection
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    if not st.session_state.trip_planned:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 class='sub-header'>Plan Your Perfect Trip</h2>", unsafe_allow_html=True)
        
        # Create columns for form inputs
        col1, col2 = st.columns(2)
        
        # Calculate default dates (current date + 30 days for start, +37 days for end)
        default_start_date = datetime.datetime.now().date() + timedelta(days=30)
        default_end_date = default_start_date + timedelta(days=7)
        
        with col1:
            starting_point = st.text_input("Starting Location", "New York, USA")
            start_date = st.date_input("Start Date", default_start_date, min_value=datetime.datetime.now().date())
        
        with col2:
            # If a destination was selected from the sidebar, use it
            destination_placeholder = st.session_state.selected_destination or "Paris, France"
            destination = st.text_input("Destination", destination_placeholder)
            end_date = st.date_input("End Date", default_end_date, min_value=start_date)
        
        # Additional travel preferences
        st.markdown("<h3 class='section-header'>Travel Preferences</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            budget = st.select_slider(
                "Budget Range",
                options=["Budget", "Moderate", "Luxury"],
                value="Moderate"
            )
        
        with col2:
            travel_style = st.selectbox(
                "Travel Style",
                ["Sightseeing & Culture", "Relaxation & Leisure", "Adventure & Activities", 
                 "Food & Culinary", "Family-friendly", "Mix of Everything"],
                index=5
            )
        
        with col3:
            travelers = st.number_input("Number of Travelers", min_value=1, max_value=10, value=2)
        
        # Interests and accommodations
        col1, col2 = st.columns(2)
        
        with col1:
            interests = st.multiselect(
                "Interests (Select multiple)",
                ["Historical Sites", "Museums & Art", "Local Cuisine", "Shopping", 
                 "Nature & Outdoors", "Nightlife", "Family Activities", "Local Events"],
                ["Historical Sites", "Local Cuisine"]
            )
        
        with col2:
            accommodation_type = st.selectbox(
                "Preferred Accommodation",
                ["Any", "Hotel", "Vacation Rental", "Hostel", "Resort", "Boutique Hotel"],
                index=0
            )
        
        # Special requests
        special_requests = st.text_area(
            "Special Requests or Requirements (accessibility needs, dietary restrictions, etc.)",
            height=100
        )
        
        # Agent Selection Section
        st.markdown("<h3 class='section-header'>Choose Your Travel Planning Experts</h3>", unsafe_allow_html=True)
        st.markdown("Select which specialized AI agents you want to include in your travel planning team:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_transport = st.checkbox("Transport Planner", value=True)
            st.markdown("<div class='agent-description'>Researches flights, local transit options, and transportation logistics between your starting point and destination.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_accommodation = st.checkbox("Accommodation Specialist", value=True)
            st.markdown("<div class='agent-description'>Finds hotels, vacation rentals, and other lodging options across different neighborhoods and price points.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_local_guide = st.checkbox("Local Guide & Cultural Context", value=True)
            st.markdown("<div class='agent-description'>Recommends attractions, museums, and experiences with historical and cultural insights about the destination.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_dining = st.checkbox("Dining & Culinary Expert", value=True)
            st.markdown("<div class='agent-description'>Uses Yelp to find restaurants, cafes, food tours, and local dining experiences across different cuisines and price ranges.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_weather = st.checkbox("Weather & Packing Advisor", value=True)
            st.markdown("<div class='agent-description'>Analyzes typical weather for your dates and provides customized packing recommendations.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='agent-selector'>", unsafe_allow_html=True)
            use_evaluator = st.checkbox("Report Evaluator", value=True)
            st.markdown("<div class='agent-description'>Reviews the final travel plan for completeness, quality, and makes suggestions for improvement.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Action buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            plan_trip_button = st.button("✨ Plan My Trip", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("Clear Form", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("""
        <div class="footer">
        <p><b>Note:</b> This is a demonstration application and does not book actual travel arrangements.
        For real bookings, please use the recommendations to make reservations through appropriate travel services.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Handle the trip planning button click
        if plan_trip_button:
            # Validate dates
            if end_date <= start_date:
                st.error("End date must be after start date.")
            else:
                # Format dates as strings
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                # Create active_agents list based on checkboxes
                active_agents = []
                if use_transport:
                    active_agents.append('transport_planner')
                if use_accommodation:
                    active_agents.append('accommodation_finder')
                if use_local_guide:
                    active_agents.append('local_guide')
                if use_dining:
                    active_agents.append('yelp_dining_expert')
                if use_weather:
                    active_agents.append('packing_and_weather_advisor')
                if use_evaluator:
                    active_agents.append('report_evaluator')
                
                # Always include report compiler
                active_agents.append('report_compiler')
                
                # Make sure at least one agent is selected
                if len(active_agents) <= 1:  # Only report_compiler
                    st.error("Please select at least one planning expert.")
                    st.stop()
                
                # Initialize inputs
                inputs = {
                    'starting_point': starting_point,
                    'destination': destination,
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'budget': budget,
                    'travelers': travelers,
                    'interests': interests,
                    'accommodation': accommodation_type,
                    'travel_style': travel_style,
                    'special_requests': special_requests,
                    'active_agents': active_agents
                }
                
                # Save to session state
                st.session_state.trip_details = inputs
                
                # Progress messages for each agent
                progress_messages = {
                    'transport_planner': [
                        "Researching flight options...",
                        "Finding local transit routes...",
                        "Analyzing transportation logistics..."
                    ],
                    'accommodation_finder': [
                        "Finding accommodation options...",
                        "Comparing neighborhoods...",
                        "Analyzing hotel and lodging choices..."
                    ],
                    'local_guide': [
                        "Researching local attractions...",
                        "Finding cultural landmarks...",
                        "Discovering hidden gems and experiences..."
                    ],
                    'yelp_dining_expert': [
                        "Finding top restaurants...",
                        "Discovering local food specialties...",
                        "Locating unique culinary experiences..."
                    ],
                    'packing_and_weather_advisor': [
                        "Checking weather forecast...",
                        "Creating packing recommendations...",
                        "Finalizing preparation advice..."
                    ],
                    'report_compiler': [
                        "Compiling all research...",
                        "Creating your personalized travel plan...",
                        "Finalizing your travel itinerary..."
                    ]
                }
                
                # Create a list of all messages for active agents
                all_progress_messages = []
                for agent in active_agents:
                    if agent in progress_messages:
                        all_progress_messages.extend(progress_messages[agent])
                
                with st.spinner("AI agents are planning your trip..."):
                    # Create a progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Start time
                    start_time = time.time()
                    
                    try:
                        # Initialize the crew with the selected agents
                        crew_runner = TravelAgentCrew(active_agents=active_agents)
                        
                        # Display agent-specific progress messages while actually running the crew
                        for i, message in enumerate(all_progress_messages):
                            # Update progress
                            progress_value = (i + 1) / len(all_progress_messages)
                            progress_bar.progress(progress_value)
                            status_text.text(message)
                            
                            # Only in the first step do we actually run the crew
                            if i == 0:
                                # Run the crew with the inputs
                                report_path = crew_runner.kickoff(inputs=inputs)
                                
                                # Record planning time
                                end_time = time.time()
                                planning_time = round(end_time - start_time, 1)
                                st.session_state.planning_time = planning_time
                                
                                # Process the report
                                if report_path and os.path.exists(report_path):
                                    try:
                                        with open(report_path, 'r', encoding='utf-8') as file:
                                            report_content = file.read()
                                        st.session_state.report_content = report_content
                                        st.session_state.report_path = report_path
                                    except Exception as e:
                                        st.session_state.planning_error = f"Error reading report: {str(e)}"
                                else:
                                    st.session_state.planning_error = "Failed to generate a report file."
                            else:
                                # For the remaining steps, just add a short delay to show progress
                                time.sleep(0.3)
                        
                        # Mark as trip planned
                        st.session_state.trip_planned = True
                        
                        # Force rerun to display the report
                        st.rerun()
                        
                    except Exception as e:
                        error_message = f"An error occurred during planning: {str(e)}"
                        st.error(error_message)
                        st.session_state.planning_error = error_message
        
        # Clear the form
        if clear_button:
            # Reset values but keep the trip_planned state
            st.session_state.selected_destination = None
            st.rerun()
    
    else:
        # Display the generated trip plan
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Trip details header
        dest = st.session_state.trip_details.get('destination', 'your destination')
        start = st.session_state.trip_details.get('start_date', 'start date')
        end = st.session_state.trip_details.get('end_date', 'end date')
        
        st.markdown(f"<h2 class='sub-header'>Your Trip to {dest}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p>From {start} to {end}</p>", unsafe_allow_html=True)
        
        # Display any planning errors
        if st.session_state.planning_error:
            st.markdown(f"""
            <div class='error-box'>
            <b>Notice:</b> {st.session_state.planning_error}
            </div>
            """, unsafe_allow_html=True)
        
        # Planning stats
        if st.session_state.planning_time:
            st.markdown(f"""
            <div class='info-box'>
            <b>Planning Stats:</b> AI analyzed options in {st.session_state.planning_time} seconds to create your personalized itinerary.
            </div>
            """, unsafe_allow_html=True)
        
        # Report content
        if st.session_state.report_content:
            # Display the full report in a container
            st.markdown("<div class='report-container'>", unsafe_allow_html=True)
            st.markdown(st.session_state.report_content)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Add download button
            if st.session_state.report_path and os.path.exists(st.session_state.report_path):
                try:
                    with open(st.session_state.report_path, "rb") as file:
                        st.download_button(
                            label="Download Complete Itinerary",
                            data=file,
                            file_name=f"Travel_Plan_{dest.replace(' ', '_').replace(',', '')}.md",
                            mime="text/markdown",
                        )
                except Exception as e:
                    st.warning(f"Could not prepare download: {str(e)}")
        else:
            st.error("Could not load the itinerary content. Please try again.")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✨ Plan Another Trip", use_container_width=True):
                # Reset all session state
                st.session_state.trip_planned = False
                st.session_state.report_content = None
                st.session_state.report_path = None
                st.session_state.planning_time = None
                st.session_state.trip_details = {}
                st.session_state.planning_error = None
                st.session_state.selected_destination = None
                st.rerun()
        
        with col2:
            if st.session_state.report_path and os.path.exists(st.session_state.report_path):
                try:
                    with open(st.session_state.report_path, "rb") as file:
                        st.download_button(
                            label="Download Itinerary (MD)",
                            data=file,
                            file_name=f"Travel_Plan_{dest.replace(' ', '_').replace(',', '')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                except Exception as e:
                    st.warning(f"Could not prepare download: {str(e)}")
            else:
                st.warning("Download not available", icon="⚠️")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add feedback and help section
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section-header'>Help & Feedback</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="info-box">
            <b>Having issues?</b> Try these steps:
            <ul>
            <li>Refresh the page and try again</li>
            <li>Use more specific destination names</li>
            <li>Try a different browser</li>
            <li>Check your internet connection</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="warning-box">
            <b>Missing information?</b> Note that this demo:
            <ul>
            <li>Does not provide real-time booking or pricing</li>
            <li>Cannot access restricted travel information</li>
            <li>Works best with popular tourist destinations</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"An unexpected error occurred during application setup: {str(e)}")

    # Create a more user-friendly error message
    st.markdown("""
    <div class="error-box">
    <h3>Application Error</h3>
    <p>We're sorry, but the Travel Agent application encountered an unexpected error during startup.</p>
    
    <p><b>Possible solutions:</b></p>
    <ul>
    <li>Refresh the page and try again</li>
    <li>Check that all required API keys are set in your .env file</li>
    <li>Ensure all dependencies are installed correctly</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a restart button
    if st.button("Restart Application"):
        st.rerun()