from typing import AsyncGenerator, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class ChatService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "ChatService":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    # Dynamic imports to avoid circular dependencies
    from langgraph.checkpoint.memory import MemorySaver

    from app.agent.config import ChatConfigHelper
    from app.agent.graph import ChatGraphBuilder
    from app.agent.retrieval import ChatRetrievalHelper
    from app.repositories import (
      BotRepository,
      ChatMessageRepository,
      DocumentRepository,
      KnowledgeBaseRepository,
      SessionRepository,
    )
    from app.services import AiModelService, LLMService

    self.bot_repo = BotRepository.get_instance()
    self.chat_message_repo = ChatMessageRepository.get_instance()
    self.doc_repo = DocumentRepository.get_instance()
    self.kb_repo = KnowledgeBaseRepository.get_instance()
    self.session_repo = SessionRepository.get_instance()

    self.llm_service = LLMService.get_instance()
    self.ai_model_service = AiModelService.get_instance()
    self.config_helper = ChatConfigHelper(self.ai_model_service)

    self.retrieval_helper = ChatRetrievalHelper(
      llm_service=self.llm_service,
      kb_repo=self.kb_repo,
      doc_repo=self.doc_repo,
      config_helper=self.config_helper,
    )

    # Compile the agent graph once
    self.checkpointer = MemorySaver()
    self.graph_builder = ChatGraphBuilder(
      llm_service=self.llm_service,
      retrieval_helper=self.retrieval_helper,
      checkpointer=self.checkpointer,
    )
    self.graph = self.graph_builder.build_graph()

  async def chat(
    self,
    query: str,
    session_id: str,
    user_id: str,
    kb_id: Optional[str] = None,
  ) -> dict:
    session = await self.session_repo.get_session(session_id)
    if not session:
      raise ValueError("Session not found")
    bot_id = session.get("bot_id")
    tenant_id = session.get("tenant_id")

    bot_config = await self.bot_repo.get_bot_config(bot_id)
    if not bot_config:
      raise ValueError("Bot config not found")

    llm_config = await self.config_helper.resolve_model_config(bot_config)
    retrieval_config = self.config_helper.parse_bot_retrieval_config(bot_config)

    if kb_id:
      kb_ids = [kb_id]
    else:
      kb_ids = await self.bot_repo.get_bot_kb_ids(bot_id)

    history = self.chat_message_repo.get_history(
      session_id=session_id, user_id=user_id, bot_id=bot_id
    )
    messages = await history.aget_messages()

    from langchain_core.messages import HumanMessage

    user_message = HumanMessage(content=query)
    await history.aadd_messages([user_message])
    messages = messages + [user_message]

    initial_state = {
      "messages": messages,
      "context": [],
      "llm_config": llm_config,
      "retrieval_config": retrieval_config,
      "user_id": user_id,
      "tenant_id": tenant_id,
      "access_token": None,
      "kb_ids": kb_ids,
      "memori_context": None,
      "start_time": None,
      "planner_decision": None,
      "retry_count": 0,
      "is_grounded": True,
    }

    config = {"configurable": {"thread_id": session_id}}
    result_state = await self.graph.ainvoke(initial_state, config=config)

    from langchain_core.messages import AIMessage

    final_messages = result_state.get("messages", [])
    assistant_msg = None
    if final_messages and isinstance(final_messages[-1], AIMessage):
      assistant_msg = final_messages[-1]
      await history.aadd_messages([assistant_msg])

    return {
      "response": assistant_msg.content if assistant_msg else "",
      "session_id": session_id,
      "role": "assistant",
    }

  async def stream_chat(
    self,
    query: str,
    session_id: str,
    user_id: str,
    kb_id: Optional[str] = None,
  ) -> AsyncGenerator[dict, None]:
    session = await self.session_repo.get_session(session_id)
    if not session:
      yield {"type": "error", "text": "Session not found"}
      return
    bot_id = session.get("bot_id")
    tenant_id = session.get("tenant_id")

    bot_config = await self.bot_repo.get_bot_config(bot_id)
    if not bot_config:
      yield {"type": "error", "text": "Bot config not found"}
      return

    try:
      llm_config = await self.config_helper.resolve_model_config(bot_config)
      retrieval_config = self.config_helper.parse_bot_retrieval_config(bot_config)
    except Exception as e:
      yield {"type": "error", "text": f"Config resolution error: {e}"}
      return

    if kb_id:
      kb_ids = [kb_id]
    else:
      kb_ids = await self.bot_repo.get_bot_kb_ids(bot_id)

    history = self.chat_message_repo.get_history(
      session_id=session_id, user_id=user_id, bot_id=bot_id
    )
    messages = await history.aget_messages()

    from langchain_core.messages import HumanMessage

    user_message = HumanMessage(content=query)
    await history.aadd_messages([user_message])
    messages = messages + [user_message]

    initial_state = {
      "messages": messages,
      "context": [],
      "llm_config": llm_config,
      "retrieval_config": retrieval_config,
      "user_id": user_id,
      "tenant_id": tenant_id,
      "access_token": None,
      "kb_ids": kb_ids,
      "memori_context": None,
      "start_time": None,
      "planner_decision": None,
      "retry_count": 0,
      "is_grounded": True,
    }

    config = {"configurable": {"thread_id": session_id}}
    assistant_content = ""

    try:
      async for event in self.graph.astream_events(
        initial_state, config=config, version="v2"
      ):
        kind = event.get("event")

        if kind == "on_node_start":
          node_name = event.get("name")
          if node_name == "planner":
            yield {"type": "status", "text": "Planning search strategy..."}
          elif node_name == "memori_retrieve":
            yield {"type": "status", "text": "Recalling user memories..."}
          elif node_name == "rag_retrieve":
            yield {"type": "status", "text": "Searching knowledge bases..."}
          elif node_name == "agent":
            yield {"type": "status", "text": "Generating response..."}
          elif node_name == "check_hallucination":
            yield {"type": "status", "text": "Checking response grounding..."}
          elif node_name == "observe":
            yield {"type": "status", "text": "Saving conversation turn..."}

        elif kind == "on_chat_model_stream":
          node = event.get("metadata", {}).get("langgraph_node")
          if node == "agent":
            chunk_data = event.get("data", {}).get("chunk")
            if chunk_data and hasattr(chunk_data, "content") and chunk_data.content:
              assistant_content += chunk_data.content
              yield {
                "type": "content",
                "text": chunk_data.content,
                "session_id": session_id,
              }

      if assistant_content:
        from langchain_core.messages import AIMessage

        await history.aadd_messages([AIMessage(content=assistant_content)])

    except Exception as e:
      yield {"type": "error", "text": str(e)}

  async def get_history(self, session_id: str) -> list[dict]:
    return await self.chat_message_repo.get_messages_by_session(
      session_id, limit=20, sort_desc=False
    )
