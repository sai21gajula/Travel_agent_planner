import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional

# Define the input schema for the Serper tool
class SerperDevToolSchema(BaseModel):
    """Input schema for SerperDevTool."""
    query: str = Field(..., description="The search query string.")

# Handle SerperDevTool import gracefully
try:
    # Attempt to import the original tool from crewai_tools
    from crewai_tools import SerperDevTool as OriginalSerperDevTool
    SERPER_AVAILABLE = True
except ImportError:
    # Set flag if the import fails
    SERPER_AVAILABLE = False
    # Define the original tool as None to avoid errors later
    OriginalSerperDevTool = None
    print("Warning: crewai_tools.SerperDevTool not found. Serper search will not be available.")

# Define the wrapper tool class
class SerperDevTool(BaseTool):
    """
    A wrapper tool for searching the web using the Serper.dev API.
    Requires the SERPER_API_KEY environment variable to be set if crewai_tools is installed.
    """
    name: str = "serper_search"
    description: str = "Search the web for information based on a query using Serper.dev API."
    # Define the expected arguments using the Pydantic schema
    args_schema: Type[BaseModel] = SerperDevToolSchema
    original_tool: Optional[OriginalSerperDevTool] = None # Store the original tool instance

    def __init__(self, **kwargs):
        """
        Initializes the SerperDevTool wrapper.
        If the original SerperDevTool is available, it initializes it.
        The original tool handles fetching the SERPER_API_KEY from environment variables if not provided.
        """
        super().__init__(**kwargs)
        if SERPER_AVAILABLE and OriginalSerperDevTool:
            try:
                # Initialize the original tool. It will look for SERPER_API_KEY env var.
                self.original_tool = OriginalSerperDevTool()
                print("SerperDevTool initialized successfully.")
            except Exception as e:
                # Handle potential errors during original tool initialization (e.g., invalid key structure if passed)
                print(f"Warning: Failed to initialize original SerperDevTool: {e}. Serper search might not work.")
                self.original_tool = None # Ensure it's None if init fails
        else:
            # If the import failed, ensure original_tool is None
            self.original_tool = None

    def _run(self, **kwargs) -> str:
        """
        Runs the web search using the Serper.dev API after validating the query.
        """
        # Check if the original tool is available and initialized
        if not self.original_tool:
            return "SerperDevTool is not available or failed to initialize. Cannot perform search."

        try:
            # Validate the input arguments using the schema
            validated_args = SerperDevToolSchema(**kwargs)
            query = validated_args.query
        except Exception as e: # Catch validation errors or other issues
            return f"Input validation error for Serper search: {str(e)}"

        try:
            # Execute the search using the initialized original tool's _run method
            # The original tool's _run likely expects the query directly
            result = self.original_tool._run(search_query=query) # Note: Original tool might expect 'search_query' kwarg
            return result
        except Exception as e:
            # Catch errors during the API call
            print(f"Error during Serper search API call: {type(e).__name__} - {str(e)}")
            return f"An error occurred while searching with Serper: {str(e)}"

# --- Example Usage (Optional - for testing) ---
if __name__ == '__main__':
    # Make sure to set SERPER_API_KEY environment variable for this test
    if os.getenv("SERPER_API_KEY"):
        try:
            search_tool = SerperDevTool()
            # Test with valid input
            results = search_tool._run(query="Latest news on CrewAI")
            print("\n--- Search Results ---")
            print(results)

            # Test with invalid input (missing query - should raise validation error)
            # results_invalid = search_tool._run(location="Boston") # This would fail validation
            # print("\n--- Invalid Input Test ---")
            # print(results_invalid)

        except Exception as e:
            print(f"\nError during testing: {e}")
    else:
        print("\nSkipping SerperDevTool test: SERPER_API_KEY environment variable not set.")
        # Test the dummy behavior if key is not set
        try:
             search_tool_no_key = SerperDevTool() # Init might still work if import succeeded
             results_no_key = search_tool_no_key._run(query="test")
             print("\n--- No API Key Test ---")
             print(results_no_key) # Should indicate tool not available or init failed
        except Exception as e:
             print(f"\nError testing without API key: {e}")

