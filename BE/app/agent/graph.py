import asyncio
import time
from typing import List, Literal

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.retrieval import ChatRetrievalHelper
from app.agent.state import GraphState
from app.core.logger import get_logger
from app.schemas.llm import LLMConfig
from app.services.llm.llm_service import LLMService
from app.services.memory.memory_service import memory_service

logger = get_logger(__name__)

# Constants
MAX_RETRIES = 2
MAX_OBSERVE_CHARS = 1000
CACHE_TIMEOUT_SECONDS = 300


class ChatGraphBuilder:
  """
  Builds LangGraph agent workflow.
  """

  def __init__(
      self,
      llm_service: LLMService,
      retrieval_helper: ChatRetrievalHelper,
      tools: List[BaseTool] | None = None,
      checkpointer: BaseCheckpointSaver | None = None
  ):
    self.llm_service = llm_service
    self.retrieval_helper = retrieval_helper
    self.tools = tools or []
    self.checkpointer = checkpointer

  def build_graph(self):
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", self.planner_node)
    workflow.add_node("kb_router", self.kb_router_node)
    workflow.add_node("query_rewrite", self.query_rewrite_node)
    workflow.add_node("hyde", self.hyde_node)
    workflow.add_node("memori_retrieve", self.memori_retrieve_node)
    workflow.add_node("rag_retrieve", self.rag_retrieve_node)
    workflow.add_node("agent", self.run_agent)
    workflow.add_node("check_hallucination", self.check_hallucination)
    workflow.add_node("observe", self.observe_node)

    if self.tools:
      workflow.add_node("tools", ToolNode(self.tools))

    workflow.add_edge(START, "planner")

    # Fan-out from Planner
    workflow.add_conditional_edges(
        "planner",
        self.route_planner,
        {
            "memori_retrieve": "memori_retrieve",
            "rag_retrieve": "kb_router",
            "tools": "tools",
            "agent": "agent"
        }
    )

    # KB Router fans out to Query Rewrite and HyDE (parallel)
    workflow.add_conditional_edges(
        "kb_router",
        self.route_kb_router,
        {
            "query_rewrite": "query_rewrite",
            "hyde": "hyde"
        }
    )

    # Fan-in to RAG Retrieve
    workflow.add_edge("query_rewrite", "rag_retrieve")
    workflow.add_edge("hyde", "rag_retrieve")

    # Fan-in to Agent
    workflow.add_edge("memori_retrieve", "agent")
    workflow.add_edge("rag_retrieve", "agent")
    if self.tools:
      workflow.add_edge("tools", "agent")

    workflow.add_conditional_edges(
        "agent",
        self.route_agent_output,
        {
            "tools": "tools",
            "check_hallucination": "check_hallucination",
        }
    )

    workflow.add_conditional_edges(
        "check_hallucination",
        self.grade_generation,
        {
            "grounded": "observe",
            "hallucination": "agent",
            "max_retries": "observe"
        }
    )

    workflow.add_edge("observe", END)

    return workflow.compile(checkpointer=self.checkpointer)

  def route_planner(self, state: GraphState) -> List[str]:
    """
    Determines which nodes to run in parallel based on the planner's decision.
    """
    messages = state.get("messages", [])
    if not messages:
      return ["agent"]

    last = messages[-1]
    # If we are looping back from tools, go back to agent
    if hasattr(last, "tool_calls") and last.tool_calls:
      return ["tools"]

    decision = state.get("planner_decision")
    if not decision:
      # Default to both if no decision is found (fallback)
      return ["memori_retrieve", "rag_retrieve"]

    targets = []
    if decision.get("use_memori"):
      targets.append("memori_retrieve")
    if decision.get("use_rag"):
      targets.append("rag_retrieve")

    return targets if targets else ["agent"]

  def route_kb_router(self, state: GraphState) -> List[str]:
    """
    Routes to query rewrite and/or HyDE based on configuration.
    """
    kb_router_decision = state.get("kb_router_decision", {})
    targets = []
    if kb_router_decision.get("use_query_rewrite"):
      targets.append("query_rewrite")
    if kb_router_decision.get("use_hyde"):
      targets.append("hyde")
    return targets if targets else ["query_rewrite"]  # default fallback

  async def kb_router_node(self, state: GraphState):
    """Route query to appropriate knowledge bases."""
    logger.info("---KB ROUTER---")
    messages = state.get("messages", [])
    if not messages:
      return {}

    user_query = messages[-1].content
    llm_config = state["llm_config"]

    # Use the subagent tool if available
    from app.agent.tools.subagents.kb_router_tool import route_to_knowledge_bases
    try:
      routed_kbs = await route_to_knowledge_bases(
        query=user_query,
        available_kb_ids=state.get("kb_ids", []),
        llm_config=llm_config
      )
      return {
        "kb_router_decision": {
          "use_query_rewrite": True,
          "use_hyde": True,
          "routed_kb_ids": routed_kbs
        },
        "routed_kb_ids": routed_kbs
      }
    except Exception as e:
      logger.warning(f"KB Router failed: {e}, using default")
      return {
        "kb_router_decision": {
          "use_query_rewrite": True,
          "use_hyde": True,
          "routed_kb_ids": state.get("kb_ids", [])
        },
        "routed_kb_ids": state.get("kb_ids", [])
      }

  async def query_rewrite_node(self, state: GraphState):
    """Rewrite user query for better retrieval."""
    logger.info("---QUERY REWRITE---")
    messages = state.get("messages", [])
    if not messages:
      return {}

    user_query = messages[-1].content
    llm_config = state["llm_config"]

    from app.agent.tools.subagents.query_optimizer_tool import rewrite_query
    try:
      rewritten_queries = await rewrite_query(
        query=user_query,
        llm_config=llm_config
      )
      return {"rewritten_queries": rewritten_queries}
    except Exception as e:
      logger.warning(f"Query rewrite failed: {e}")
      return {"rewritten_queries": [user_query]}

  async def hyde_node(self, state: GraphState):
    """Generate HyDE (Hypothetical Document Embeddings) for query."""
    logger.info("---HYDE---")
    messages = state.get("messages", [])
    if not messages:
      return {}

    user_query = messages[-1].content
    llm_config = state["llm_config"]

    from app.agent.tools.subagents.hyde_generator_tool import generate_hyde_documents
    try:
      hyde_queries = await generate_hyde_documents(
        query=user_query,
        llm_config=llm_config,
        num_docs=3
      )
      return {"hyde_queries": hyde_queries}
    except Exception as e:
      logger.warning(f"HyDE generation failed: {e}")
      return {"hyde_queries": [user_query]}

  async def planner_node(self, state: GraphState):
    logger.info("---PLANNER---")
    messages = state.get("messages", [])
    llm_config = state["llm_config"]
    
    if not messages:
      return {"start_time": time.time()}

    # Call LLM to decide on retrieval needs
    decision = await self.llm_service.plan_intent(messages, llm_config)
    
    return {
        "start_time": time.time(),
        "planner_decision": {
            "use_memori": decision.use_memori,
            "use_rag": decision.use_rag
        }
    }

  async def memori_retrieve_node(self, state: GraphState):
    """Fetch past memories."""
    logger.info("---MEMORI RETRIEVE---")
    
    if state.get("memori_context"):
      return {}

    user_id = state["user_id"]
    messages = state["messages"]
    if not messages:
      return {}

    user_query = messages[-1].content
    mem = await memory_service.get_memori()
    if not mem:
      return {}

    mem.attribution(entity_id=user_id, process_id="langgraph_agent")
    facts = mem.recall(user_query)
    lines = [
        f"- {f.get('content') or f.get('text')}"
        for f in facts
        if (f.get("content") or f.get("text"))
    ]

    if not lines:
      return {"memori_context": ""}

    context = (
        "<memori_context>\n"
        "Relevant facts about the user:\n"
        + "\n".join(lines)
        + "\n</memori_context>"
    )

    return {"memori_context": context}

  async def rag_retrieve_node(self, state: GraphState):
    """Fetch Knowledge Base documents using rewritten queries and HyDE."""
    logger.info("---RAG RETRIEVE---")

    if state.get("context"):
      return {}

    messages = state["messages"]
    if not messages:
      return {}

    user_query = messages[-1].content

    # Get all queries to search with: original, rewritten, and HyDE
    all_queries = [user_query]
    rewritten_queries = state.get("rewritten_queries", [])
    hyde_queries = state.get("hyde_queries", [])

    if rewritten_queries:
      all_queries.extend(rewritten_queries)
    if hyde_queries:
      all_queries.extend(hyde_queries)

    # Use routed KB IDs from kb_router, fallback to configured KBs
    kb_ids = state.get("routed_kb_ids") or state.get("kb_ids", [])

    # Use retrieval configuration from state, fallback to empty dict if missing
    retrieval_config = state.get("retrieval_config")
    if not retrieval_config:
      retrieval_config = self.retrieval_helper.config_helper.parse_bot_retrieval_config({})

    # Create search tasks for each query with the routed KB IDs
    search_tasks = [(q, kb_ids) for q in all_queries]

    docs = await self.retrieval_helper.search_knowledge_bases(
        search_tasks=search_tasks,
        tenant_id=state["tenant_id"],
        global_config=retrieval_config,
        access_token=state.get("access_token"),
        rerank_query=user_query  # Original query for reranking results
    )

    return {"context": docs}

  def route_agent_output(
      self,
      state: GraphState
  ) -> Literal["tools", "check_hallucination"]:

    messages = state["messages"]
    last = messages[-1]

    if hasattr(last, "tool_calls") and last.tool_calls:
      return "tools"

    return "check_hallucination"

  async def run_agent(self, state: GraphState):
    logger.info("---RUN AGENT---")
    llm_config: LLMConfig = state["llm_config"]

    llm = self.llm_service._get_llm(
        provider=llm_config.provider,
        model=llm_config.model,
        temperature=llm_config.temperature,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url
    )

    # 1. Gather all parallel contexts
    context = state.get("context", [])
    context_str = "\n\n".join(
        [d.page_content for d in context]
    ) if context else ""
    
    memori_context = state.get("memori_context", "")

    # 2. Always create agent fresh to avoid stale LLM instances
    instruction = self._prepare_system_instruction(llm_config)
    agent = create_agent(
        llm,
        self.tools,
        system_prompt=instruction
    )

    # 3. Build augmented message list
    extra_messages = []
    if memori_context:
      extra_messages.append(SystemMessage(content=memori_context))
    if context_str:
      extra_messages.append(SystemMessage(
        content=f"Knowledge Base Context:\n{context_str}"))

    agent_input = {"messages": extra_messages + state["messages"]}
    result = await agent.ainvoke(agent_input)

    return {
        "messages": result["messages"],
        "retry_count": state.get("retry_count", 0)
    }

  async def observe_node(self, state: GraphState):
    """Persist the conversation turn to Memori."""
    logger.info("---OBSERVE CONVERSATION---")
    messages = state["messages"]
    start_time = state.get("start_time") or time.time()
    
    if len(messages) < 2:
      return state

    # The last message is the AI response, the one before it should be the user message
    # In LangGraph with add_messages, we need to be careful about the order.
    # Usually, we find the last HumanMessage and the final AIMessage.
    
    ai_msg = messages[-1].content
    # Find the last user message in the accumulated list
    user_msg = ""
    from langchain_core.messages import HumanMessage
    for msg in reversed(messages[:-1]):
      if isinstance(msg, HumanMessage):
        user_msg = msg.content
        break
    
    if not user_msg:
      return state

    mem = await memory_service.get_memori()
    if not mem:
      return state

    # Clean/Truncate for embedding safety
    cleaned_ai_msg = ai_msg
    if len(ai_msg) > MAX_OBSERVE_CHARS:
      cleaned_ai_msg = ai_msg[:MAX_OBSERVE_CHARS] + "..."

    async def _save_to_memori(mem_instance, observe_payload):
      """Helper to run the blocking Memori execution in a thread."""
      from memori.memory._manager import Manager as MemoryManager
      try:
        await asyncio.to_thread(
          MemoryManager(mem_instance.config).execute, 
          observe_payload
        )
        return True
      except Exception as exc:
        # Check if it's a connection error (OperationalError)
        error_str = str(exc)
        markers = ["OperationalError", "closed the connection", "terminated abnormally"]
        if any(m in error_str for m in markers):
          logger.warning(f"Memori connection issue: {exc}. Retrying in 1s...")
          await asyncio.sleep(1)
          # Trigger a refresh for the next attempt
          new_mem = await memory_service.get_memori(force_refresh=True)
          if new_mem:
            await asyncio.to_thread(
              MemoryManager(new_mem.config).execute, 
              observe_payload
            )
            return True
        raise exc

    try:
      payload = {
        "attribution": {
          "entity": {"id": mem.config.entity_id},
          "process": {"id": mem.config.process_id},
        },
        "messages": [
          {"role": "user", "text": user_msg, "type": None},
          {"role": "assistant", "text": cleaned_ai_msg, "type": None}
        ],
        "session": {"uuid": str(mem.config.session_id)},
        "time": {"end": time.time(), "start": start_time},
      }
      await _save_to_memori(mem, payload)
      logger.info("Successfully recorded turn to Memori")
    except Exception as e:
      logger.error(f"Memori observation failed in node: {e}")

    return state

  async def check_hallucination(self, state: GraphState):
    logger.info("---CHECK HALLUCINATION---")

    messages = state["messages"]
    last = messages[-1]

    if not isinstance(last, AIMessage):
      return {"is_grounded": True}

    if getattr(last, "tool_calls", None):
      return {"is_grounded": True}

    generation = str(last.content)

    context = state.get("context", [])
    context_str = "\n\n".join(
        [d.page_content for d in context]
    ) if context else ""

    if not context_str:
      return {"is_grounded": True}

    llm_config = state["llm_config"]
    score = await self.llm_service.check_hallucination(
        context_str,
        generation,
        llm_config
    )

    if score:
      return {"is_grounded": True}

    retry = state.get("retry_count", 0) + 1
    logger.warning(f"Hallucination detected retry={retry}")

    return {
        "is_grounded": False,
        "retry_count": retry
    }

  def grade_generation(
      self,
      state: GraphState
  ) -> Literal["grounded", "hallucination", "max_retries"]:
    if state.get("is_grounded", True):
      return "grounded"
    if state.get("retry_count", 0) >= MAX_RETRIES:
      return "max_retries"
    return "hallucination"

  def _prepare_system_instruction(self, config: LLMConfig):
    from app.agent.prompt_templates import EDUCATIONAL_GUARDRAIL_PROMPT
    base = config.system_prompt or "You are a helpful AI assistant."
    return f"{EDUCATIONAL_GUARDRAIL_PROMPT}\n\n{base}"
