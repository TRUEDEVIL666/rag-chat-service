from typing import Annotated, List

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.agent.config import BotRetrievalConfig
from app.schemas.llm import LLMConfig


def add_documents(left: List[Document], right: List[Document]) -> List[Document]:
  """Custom reducer to append documents in parallel nodes."""
  return (left or []) + (right or [])


class GraphState(TypedDict):
  """
  Represents the state of the agent graph.
  """

  messages: Annotated[list[AnyMessage], add_messages]
  context: Annotated[List[Document], add_documents]
  llm_config: LLMConfig
  retrieval_config: BotRetrievalConfig

  user_id: str
  tenant_id: str
  access_token: str | None
  kb_ids: List[str]
  memori_context: str | None
  start_time: float | None
  planner_decision: dict | None

  retry_count: int
  is_grounded: bool
