"""
CrewAI-compatible tool wrappers
"""
from typing import List, Dict, Any, Callable, Optional
from langchain.tools import BaseTool
from crewai.tools import BaseTool as CrewAIBaseTool

class ToolWrapper(CrewAIBaseTool):
    """Wrapper for LangChain tools to make them compatible with CrewAI"""
    
    def __init__(self, tool):
        """Initialize with a LangChain tool"""
        self.name = getattr(tool, "name", str(tool))
        self.description = getattr(tool, "description", "")
        self.tool = tool
    
    def _run(self, *args, **kwargs):
        """Run the wrapped tool"""
        # Call the tool's _run method with arguments
        if hasattr(self.tool, "_run"):
            return self.tool._run(*args, **kwargs)
        # Fallback if the tool has a run method instead
        elif hasattr(self.tool, "run"):
            return self.tool.run(*args, **kwargs)
        else:
            return "Tool doesn't have _run or run method"

def wrap_tool(tool) -> CrewAIBaseTool:
    """
    Wrap a single LangChain tool as a CrewAI tool
    
    Args:
        tool: A LangChain BaseTool instance
        
    Returns:
        CrewAI-compatible tool
    """
    return ToolWrapper(tool)

def wrap_tools(tools: List[Any]) -> List[CrewAIBaseTool]:
    """
    Convert a list of LangChain tools to CrewAI-compatible tools
    
    Args:
        tools: List of LangChain BaseTool instances
        
    Returns:
        List of CrewAI-compatible tools
    """
    return [wrap_tool(tool) for tool in tools] 