from app.core.logger import get_logger
from typing import List, Callable, Dict, Any
from langchain_core.tools import tool, Tool
from langchain_community.tools import DuckDuckGoSearchResults

logger = get_logger(__name__)


class ToolService:
  def __init__(self):
    self._tools: Dict[str, Tool] = {}
    self._initialize_default_tools()

  def _initialize_default_tools(self):
    """Register default tools available to the system."""
    try:
      self.register_tool(self._create_web_search_tool())
    except Exception as e:
      logger.error(f"Failed to initialize default tools: {e}")

  def register_tool(self, tool_instance: Tool):
    """Register a new tool instance."""
    if tool_instance.name in self._tools:
      logger.warning(f"Tool {tool_instance.name} is being overwritten.")
    self._tools[tool_instance.name] = tool_instance
    logger.info(f"Registered tool: {tool_instance.name}")

  def get_tools(self, tool_names: List[str] = None) -> List[Tool]:
    """
    Get a list of tools. If tool_names is provided, return only those.
    Otherwise return all registered tools.
    """
    if not tool_names:
      return list(self._tools.values())

    return [self._tools[name] for name in tool_names if name in self._tools]

  def _create_web_search_tool(self) -> Tool:
    """
    Creates and returns the DuckDuckGo web search tool.
    """
    search = DuckDuckGoSearchResults()

    @tool("web_search")
    def web_search(query: str) -> str:
      """
      Useful for when you need to answer questions about current events or look up real-time information.
      Input should be a search query. returns a JSON string of results.
      """
      try:
        # DuckDuckGoSearchResults returns a formatted string of results
        return search.run(query)
      except Exception as e:
        logger.error(f"Error executing web search: {e}")
        return f"Error executing search: {str(e)}"

    return web_search
