# #!/usr/bin/env python
# """
# Main entry point for the Travel Agent application.
# """
# import os
# import sys
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# try:
#     # Import the crew
#     from crew import TravelAgentCrew
    
#     # Import the tools wrapper (in case we need it directly)
#     from tools.crewai_tools import wrap_tools
    
#     print("--- Travel Agent Application Starting ---")
#     print("Initializing crew components...")
    
#     # Initialize the crew
#     crew_runner = TravelAgentCrew()
    
#     # Launch Streamlit interface
#     print("Starting Streamlit web interface...")
    
#     # Use Streamlit to run the app
#     import streamlit as st
    
#     st.title("AI Travel Agent")
    
#     with st.form("travel_form"):
#         st.header("Enter Your Travel Details")
        
#         starting_point = st.text_input("Starting location", "New York, USA")
#         destination = st.text_input("Destination", "Paris, France")
#         start_date = st.date_input("Start date")
#         end_date = st.date_input("End date")
        
#         submit_button = st.form_submit_button("Plan My Trip")
    
#     if submit_button:
#         st.write("Planning your trip... This may take several minutes.")
        
#         try:
#             # Format dates as strings
#             start_date_str = start_date.strftime("%Y-%m-%d")
#             end_date_str = end_date.strftime("%Y-%m-%d")
            
#             # Initialize inputs
#             inputs = {
#                 'starting_point': starting_point,
#                 'destination': destination,
#                 'start_date': start_date_str,
#                 'end_date': end_date_str
#             }
            
#             # Run the crew with the inputs
#             with st.spinner("AI agents are planning your trip..."):
#                 report_path = crew_runner.kickoff(inputs=inputs)
            
#             # Display success
#             st.success(f"Trip planning completed! Report saved to: {report_path}")
            
#             # Read and display the report
#             try:
#                 with open(report_path, 'r') as file:
#                     report_content = file.read()
#                 st.markdown(report_content)
#             except:
#                 st.error("Could not read the generated report file.")
                
#         except Exception as e:
#             st.error(f"An error occurred during planning: {str(e)}")
    
# except Exception as e:
#     print(f"An unexpected error occurred during initial setup: {str(e)}", file=sys.stderr)
#     import traceback
#     traceback.print_exc()
#     sys.exit(1)


#!/usr/bin/env python
#!/usr/bin/env python
"""
Main entry point for the Travel Agent application.
Enhanced interactive Streamlit interface with improved user experience.
"""
import os
import sys
import time
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure reports directory exists and is writable
reports_dir = 'reports'
try:
    os.makedirs(reports_dir, exist_ok=True)
    test_file = os.path.join(reports_dir, 'test_write.txt')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"Reports directory {reports_dir} exists and is writable")
except Exception as e:
    print(f"Error with reports directory: {str(e)}")
    # Try to use a different directory
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    try:
        os.makedirs(reports_dir, exist_ok=True)
        print(f"Using alternative reports directory: {reports_dir}")
    except:
        print("Unable to create reports directory")

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
    from datetime import timedelta
    import random
    
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
        }
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #EEEEEE;
            color: #757575;
            font-size: 0.9rem;
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
    
    # Header
    st.markdown("<h1 class='main-header'>✈️ AI Travel Planner</h1>", unsafe_allow_html=True)
    
    # Sidebar with information and popular destinations
    with st.sidebar:
        st.markdown("<h3>How It Works</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        This AI Travel Planner uses multiple specialized AI agents to create your personalized travel itinerary:
        
        • <b>Transport Planner</b>: Finds public transport options
        • <b>Accommodation Specialist</b>: Locates hotels and lodging
        • <b>Local Guide</b>: Recommends attractions and dining
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
        
        st.markdown("<div>", unsafe_allow_html=True)
        for dest in popular_destinations:
            st.markdown(f"<span class='destination-tag'>{dest}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
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
            destination = st.text_input("Destination", "Paris, France")
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
                    'special_requests': special_requests
                }
                
                # Save to session state
                st.session_state.trip_details = inputs
                
                # Progress bar with messages
                progress_messages = [
                    "Researching transportation options...",
                    "Finding accommodation suggestions...",
                    "Discovering local attractions and activities...",
                    "Checking weather and creating packing list...",
                    "Generating personalized recommendations...",
                    "Compiling your custom travel plan...",
                    "Adding final touches to your itinerary..."
                ]
                
                with st.spinner("AI agents are planning your trip..."):
                    # Create a progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Start time
                    start_time = time.time()
                    
                    try:
                        # Simulate progress while actually running the crew
                        for i, message in enumerate(progress_messages):
                            # Update status message
                            status_text.text(message)
                            
                            # Update progress bar
                            progress_value = (i + 1) / len(progress_messages)
                            progress_bar.progress(progress_value)
                            
                            if i == 0:  # Only in the first step do we actually run the crew
                                # Run the crew with the inputs
                                report_path = crew_runner.kickoff(inputs=inputs)
                                
                                # Record planning time
                                end_time = time.time()
                                planning_time = round(end_time - start_time, 1)
                                st.session_state.planning_time = planning_time
                                
                                # Check for error conditions
                                if report_path == "ERROR_GENERATING_REPORT" or report_path == "ERROR_DURING_KICKOFF":
                                    st.session_state.planning_error = "Failed to generate a complete travel report. Please try again later."
                                    # Create a fallback report path
                                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    emergency_file = os.path.join('reports', f"error_report_{timestamp}.md")
                                    dest = inputs.get('destination', 'destination')
                                    start = inputs.get('start_date', 'start_date')
                                    end = inputs.get('end_date', 'end_date')
                                    
                                    with open(emergency_file, 'w', encoding='utf-8') as file:
                                        file.write(f"""# Your Travel Plan to {dest}

## Trip Overview
- **Destination**: {dest}
- **Dates**: {start} to {end}
- **Starting Point**: {inputs.get('starting_point', 'Not specified')}

## What Happened?
Our AI travel agents encountered technical difficulties while creating your detailed itinerary.

Please try again in a few minutes. Our system is continuously improving to better serve your travel planning needs.

*This is an automatically generated fallback plan due to technical limitations.*
""")
                                    report_path = emergency_file
                                
                                # Read the report content
                                try:
                                    with open(report_path, 'r', encoding='utf-8') as file:
                                        report_content = file.read()
                                    
                                    # Check if content is empty or just whitespace
                                    if not report_content or report_content.strip() == "":
                                        st.session_state.planning_error = "The generated report appears to be empty. This might be due to API rate limits or temporary issues with external services."
                                        # Create a minimal report
                                        dest = inputs.get('destination', 'destination')
                                        start = inputs.get('start_date', 'start_date')
                                        end = inputs.get('end_date', 'end_date')
                                        report_content = f"# Your Trip to {dest}\n\n**From {start} to {end}**\n\nI'm sorry, but we couldn't generate a detailed report at this time. Please try again later."
                                    
                                    # Store in session state
                                    st.session_state.report_content = report_content
                                    st.session_state.report_path = report_path
                                    
                                    # Add debugging information
                                    print(f"Successfully read report file: {report_path}")
                                    print(f"Report content length: {len(report_content)}")
                                except Exception as e:
                                    error_msg = f"Could not read the generated report file: {str(e)}"
                                    st.session_state.planning_error = error_msg
                                    print(error_msg)
                                    print(f"Report path: {report_path}")
                                    print(f"Report path exists: {os.path.exists(report_path) if report_path else 'N/A'}")
                                    
                                    # Create a fallback report
                                    dest = inputs.get('destination', 'destination')
                                    start = inputs.get('start_date', 'start_date')
                                    end = inputs.get('end_date', 'end_date')
                                    st.session_state.report_content = f"# Your Trip to {dest}\n\n**From {start} to {end}**\n\nI'm sorry, but we couldn't generate a detailed report at this time. Please try again later."
                                    report_content = st.session_state.report_content
                            else:
                                # For the remaining steps, just add a short delay to show progress
                                time.sleep(0.5)
                        
                        # Mark as trip planned
                        st.session_state.trip_planned = True
                        
                        # Force rerun to display the report
                        st.rerun()
                        
                    except Exception as e:
                        error_message = f"An error occurred during planning: {str(e)}"
                        st.error(error_message)
                        print(error_message)
                        st.session_state.planning_error = error_message
        
        # Clear the form
        if clear_button:
            # Reset values but keep the trip_planned state
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
            <br><br>
            We've created a basic travel outline below. For a more detailed plan, please try again later.
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
            # Add tabs to organize the information
            tabs = st.tabs(["Complete Itinerary", "Transportation", "Accommodations", "Activities", "Packing List"])
            
            with tabs[0]:
                # Display the full report
                st.markdown(st.session_state.report_content)
                
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
            
            # These tabs would ideally extract just the relevant sections from the report
            # For now, they show notes about what they would contain
            with tabs[1]:
                st.info("This tab would extract and display only the transportation information from your itinerary.")
                st.markdown("### Transportation Highlights")
                # Here we would ideally parse and extract just the transportation section from the report
                st.markdown("To see your transportation details, please refer to the Complete Itinerary tab.")
            
            with tabs[2]:
                st.info("This tab would extract and display only the accommodation information from your itinerary.")
                st.markdown("### Accommodation Suggestions")
                # Here we would ideally parse and extract just the accommodation section from the report
                st.markdown("To see your accommodation details, please refer to the Complete Itinerary tab.")
            
            with tabs[3]:
                st.info("This tab would extract and display only the activities and attractions from your itinerary.")
                st.markdown("### Recommended Activities")
                # Here we would ideally parse and extract just the activities section from the report
                st.markdown("To see your recommended activities, please refer to the Complete Itinerary tab.")
            
            with tabs[4]:
                st.info("This tab would extract and display only the packing list from your itinerary.")
                st.markdown("### Packing Recommendations")
                # Here we would ideally parse and extract just the packing list from the report
                st.markdown("To see your packing recommendations, please refer to the Complete Itinerary tab.")
        
        else:
            st.error("Could not load the itinerary content. Please try again.")
        
        # Action buttons
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
    print(f"An unexpected error occurred during initial setup: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    
    # Create a more user-friendly error page
    st.markdown("<h1 class='main-header'>✈️ AI Travel Planner</h1>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>System Temporarily Unavailable</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="error-box">
    <p>We're sorry, but the AI Travel Planner is currently unavailable. Our team has been notified and is working to resolve the issue.</p>
    
    <p><b>Possible reasons:</b></p>
    <ul>
    <li>Server maintenance</li>
    <li>High system demand</li>
    <li>Network connectivity issues</li>
    </ul>
    
    <p><b>What you can do:</b></p>
    <ul>
    <li>Try refreshing the page</li>
    <li>Come back in a few minutes</li>
    <li>Clear your browser cache and try again</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Refresh Page", type="primary"):
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)