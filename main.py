#!/usr/bin/env python
import sys
import os
import argparse
from travel_agent.src.travel_agent.crew import TravelAgentCrew

def run_crew(starting_point: str, destination: str, start_date: str, end_date: str):
    """
    Run the travel agent crew with the given parameters
    
    Args:
        starting_point: The starting location
        destination: The destination location
        start_date: The start date (YYYY-MM-DD)
        end_date: The end date (YYYY-MM-DD)
    """
    print(f"Planning a trip from {starting_point} to {destination} ({start_date} to {end_date})...")
    
    # Create inputs dictionary
    inputs = {
        'starting_point': starting_point,
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date
    }

    # Run the crew
    report_file = TravelAgentCrew().crew().kickoff(inputs=inputs)
    
    print(f"\nTravel plan generated successfully!")
    print(f"Report saved to: {report_file}")
    
    # Optional: Display the report
    if os.path.exists(report_file):
        print("\nWould you like to see the report? (y/n): ", end="")
        show_report = input().lower().strip()
        if show_report == 'y':
            with open(report_file, 'r') as f:
                print("\n" + f.read())

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Travel Agent Crew - Plan your trip using AI')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Plan trip command
    plan_parser = subparsers.add_parser('plan', help='Plan a new trip')
    plan_parser.add_argument('--from', dest='starting_point', required=True, help='Starting location')
    plan_parser.add_argument('--to', dest='destination', required=True, help='Destination')
    plan_parser.add_argument('--start', dest='start_date', required=True, help='Start date (YYYY-MM-DD)')
    plan_parser.add_argument('--end', dest='end_date', required=True, help='End date (YYYY-MM-DD)')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the crew')
    train_parser.add_argument('iterations', type=int, help='Number of training iterations')
    train_parser.add_argument('filename', help='Filename to save training data')
    
    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay a specific task')
    replay_parser.add_argument('task_id', help='Task ID to replay')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test the crew')
    test_parser.add_argument('iterations', type=int, help='Number of test iterations')
    test_parser.add_argument('model', help='Model to use for testing')
    
    return parser.parse_args()

def train(iterations, filename):
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "destination": "Paris",
        "starting_point": "New York",
        "start_date": "2025-05-15",
        "end_date": "2025-05-22"
    }
    try:
        TravelAgentCrew().crew().train(n_iterations=iterations, filename=filename, inputs=inputs)
        print(f"Training completed and saved to {filename}")

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay(task_id):
    """
    Replay the crew execution from a specific task.
    """
    try:
        result = TravelAgentCrew().crew().replay(task_id=task_id)
        print(f"Replay completed. Result: {result}")

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test(iterations, model):
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "destination": "Tokyo",
        "starting_point": "Los Angeles",
        "start_date": "2025-06-10",
        "end_date": "2025-06-20"
    }
    try:
        results = TravelAgentCrew().crew().test(n_iterations=iterations, model_name=model, inputs=inputs)
        print(f"Testing completed. Results: {results}")

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def interactive_mode():
    """Interactive mode for when no arguments are provided"""
    print("=== Travel Agent Crew - Interactive Mode ===")
    
    starting_point = input("Enter your starting point: ")
    destination = input("Enter your destination: ")
    start_date = input("Enter your start date (YYYY-MM-DD): ")
    end_date = input("Enter your end date (YYYY-MM-DD): ")
    
    run_crew(starting_point, destination, start_date, end_date)

def main():
    """Main entry point"""
    # Check if any arguments were provided
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    args = parse_arguments()
    
    if args.command == 'plan':
        run_crew(args.starting_point, args.destination, args.start_date, args.end_date)
    elif args.command == 'train':
        train(args.iterations, args.filename)
    elif args.command == 'replay':
        replay(args.task_id)
    elif args.command == 'test':
        test(args.iterations, args.model)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()