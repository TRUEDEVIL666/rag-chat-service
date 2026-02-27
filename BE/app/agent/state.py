from typing import Annotated, Any, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from app.schemas.llm import LLMConfig


class GraphState(TypedDict):
  """
  Represents the state of the agent graph.
  """
  # Messages in the conversation
  messages: Annotated[list[AnyMessage], add_messages]

  # Context retrieved from Knowledge Base
  context: List[Document]

  # The user's original query (or rewritten)
  query: str

  # Configuration for the LLM
  llm_config: LLMConfig

  # Metadata for the session
  session_id: str
  bot_id: str
  user_id: str
  access_token: Optional[str]

  # Retry count for self-correction
  retry_count: int
  is_grounded: bool

  # Whether tools are supported/used
  supports_tools: bool

  # Flags
  quiz_mode: bool
