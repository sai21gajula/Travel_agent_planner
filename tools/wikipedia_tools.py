"""
Wikipedia tools for the travel agent crew using the langchain Wikipedia API.
"""
from langchain.tools import BaseTool
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from typing import Optional, Any
from pydantic import BaseModel, Field

class HistoricalInfoInput(BaseModel):
    """Input for the HistoricalInfoTool."""
    query: str = Field(..., description="The search query, e.g., 'History of Paris'")
    num_results: Optional[int] = Field(2, description="Number of results to return (default 2)")

class HistoricalInfoTool(BaseTool):
    """Tool that gets historical information about a location using Wikipedia."""
    name: str = "historical_info"
    description: str = """
    Useful for finding historical information about a location or landmark.
    Input should be a place or landmark name (e.g., 'Colosseum, Rome' or 'Machu Picchu').
    """
    wiki_api: Any = None
    
    def __init__(self):
        """Initialize the Wikipedia API wrapper."""
        super().__init__()
        self.wiki_api = WikipediaAPIWrapper(top_k_results=2)
    
    def _run(self, query: str) -> str:
        """Run the historical info tool."""
        try:
            # Create a more specific query for historical information
            history_query = f"history of {query}"
            
            # Get information from Wikipedia
            wiki_result = self.wiki_api.run(history_query)
            
            # Format the response
            if not wiki_result:
                return f"No historical information found for {query}"
            
            # Extract main historical information
            result = f"Historical Information about {query}:\n\n"
            result += wiki_result[:1500] + "..." if len(wiki_result) > 1500 else wiki_result
            
            return result
        except Exception as e:
            return f"Error retrieving historical information: {str(e)}"

class CulturalCustomsTool(BaseTool):
    """Tool that provides information about cultural customs of a location."""
    name: str = "cultural_customs"
    description: str = """
    Useful for finding information about cultural customs, etiquette, and local practices.
    Input should be a location or country (e.g., 'Japan' or 'Morocco').
    """
    wiki_api: Any = None
    
    def __init__(self):
        """Initialize the Wikipedia API wrapper."""
        super().__init__()
        self.wiki_api = WikipediaAPIWrapper(top_k_results=2)
    
    def _run(self, location: str) -> str:
        """Run the cultural customs tool."""
        try:
            # Create a more specific query for cultural information
            culture_query = f"culture customs traditions etiquette of {location}"
            
            # Get information from Wikipedia
            wiki_result = self.wiki_api.run(culture_query)
            
            # Format the response
            if not wiki_result:
                return f"No cultural customs information found for {location}"
            
            # Extract main cultural information
            result = f"Cultural Customs in {location}:\n\n"
            result += wiki_result[:1500] + "..." if len(wiki_result) > 1500 else wiki_result
            
            return result
        except Exception as e:
            return f"Error retrieving cultural information: {str(e)}"

class FunFactsTool(BaseTool):
    """Tool that provides interesting facts about a location."""
    name: str = "fun_facts"
    description: str = """
    Useful for finding interesting and fun facts about a location.
    Input should be a location, landmark, or attraction (e.g., 'Paris' or 'Great Wall of China').
    """
    wiki_api: Any = None
    
    def __init__(self):
        """Initialize the Wikipedia API wrapper."""
        super().__init__()
        self.wiki_api = WikipediaAPIWrapper(top_k_results=1)
    
    def _run(self, query: str) -> str:
        """Run the fun facts tool."""
        try:
            # Get general information from Wikipedia
            wiki_result = self.wiki_api.run(query)
            
            # Format the response
            if not wiki_result:
                return f"No interesting facts found for {query}"
            
            # Extract a snippet for fun facts
            result = f"Interesting Facts about {query}:\n\n"
            
            # Just take the first paragraph as a "fun fact"
            # In a real implementation, you might want to use a more sophisticated
            # approach to extract actual interesting facts.
            paragraphs = wiki_result.split('\n\n')
            first_paragraph = paragraphs[0] if paragraphs else wiki_result[:500]
            
            result += first_paragraph
            result += "\n\nSource: Based on Wikipedia information"
            
            return result
        except Exception as e:
            return f"Error retrieving fun facts: {str(e)}"