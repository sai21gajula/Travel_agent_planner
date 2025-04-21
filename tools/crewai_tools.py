# tools/crewai_tools.py
from typing import List, Any
from crewai.tools import BaseTool as CrewAIBaseTool # Import CrewAI's BaseTool
import traceback
import sys

# --- ToolWrapper Class (Adapts LangChain/Custom Tools to CrewAI's BaseTool) ---
class ToolWrapper(CrewAIBaseTool):
    """Wrapper to make LangChain/Custom tools compatible with CrewAI Agent."""
    name: str
    description: str
    tool_instance: Any # Store the original tool instance

    def __init__(self, tool_instance: Any):
        """Initialize with the original tool instance."""
        if not tool_instance:
             raise ValueError("Tool instance cannot be None")
             
        self.name = getattr(tool_instance, "name", str(tool_instance.__class__.__name__))
        self.description = getattr(tool_instance, "description", "No description provided.")
        self.tool_instance = tool_instance
        # Initialize the Pydantic model fields for CrewAIBaseTool
        # Ensure args_schema is handled correctly if present on original tool
        args_schema = getattr(tool_instance, 'args_schema', None)
        super().__init__(name=self.name, description=self.description, args_schema=args_schema)
        print(f"[DEBUG] ToolWrapper initialized for: {self.name}", file=sys.stderr)

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the wrapped tool's execution method."""
        print(f"[DEBUG] ToolWrapper executing tool: {self.name} with args={args}, kwargs={kwargs}", file=sys.stderr)
        try:
            # Prioritize using the _run method of the original instance
            if hasattr(self.tool_instance, "_run") and callable(self.tool_instance._run):
                 # CrewAI might pass arguments differently depending on the tool's args_schema
                 # If there's an args_schema, Pydantic likely parsed kwargs based on it.
                 # If no schema, it might pass a single string arg.
                 if kwargs:
                     # If kwargs are present, pass them directly (likely from args_schema)
                     return self.tool_instance._run(**kwargs)
                 elif args:
                     # If only args are present, pass them positionally 
                     # (might need adjustment based on specific tool needs)
                     return self.tool_instance._run(*args) 
                 else:
                     # Handle tools that take no arguments
                     return self.tool_instance._run()
            # Fallback to 'run' method if '_run' is not available
            elif hasattr(self.tool_instance, "run") and callable(self.tool_instance.run):
                 if kwargs:
                     return self.tool_instance.run(**kwargs)
                 elif args:
                    return self.tool_instance.run(*args)
                 else:
                    return self.tool_instance.run()
            else:
                 error_msg = f"Tool '{self.name}' has no callable '_run' or 'run' method."
                 print(f"[ERROR] {error_msg}", file=sys.stderr)
                 return error_msg
                 
        except Exception as e:
            error_msg = f"Error executing tool '{self.name}': {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return error_msg # Return error message on failure

# --- wrap_tools Function (Returns List of CrewAI-compatible BaseTools) ---
def wrap_tools(tools_list: List[Any]) -> List[CrewAIBaseTool]:
    """
    Convert a list of tool instances (custom, LangChain, CrewAI Tools) into 
    a list of CrewAI-compatible BaseTool instances using ToolWrapper.
    Always wrap to ensure uniform type in the list passed to the Agent.
    """
    wrapped_list = []
    print(f"[DEBUG] Entering wrap_tools with {len(tools_list)} tools", file=sys.stderr)
    for tool_instance in tools_list:
        if tool_instance:
            try:
                # ALWAYS wrap the tool instance using ToolWrapper
                wrapped_tool = ToolWrapper(tool_instance=tool_instance)
                wrapped_list.append(wrapped_tool)
                print(f"[DEBUG] Successfully wrapped '{getattr(tool_instance, 'name', 'unknown')}' using ToolWrapper", file=sys.stderr)
            except Exception as e:
                tool_name_err = getattr(tool_instance, 'name', str(type(tool_instance)))
                print(f"[ERROR] Failed to wrap tool instance '{tool_name_err}' with ToolWrapper: {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
        else:
             print("[WARN] Skipping None tool instance in wrap_tools", file=sys.stderr)
             
    print(f"[DEBUG] wrap_tools finished. Returning {len(wrapped_list)} CrewAI-compatible wrapped tools.", file=sys.stderr)
    return wrapped_list