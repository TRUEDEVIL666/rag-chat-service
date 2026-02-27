from typing import Literal, cast, List
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.logger import get_logger
from app.schemas.llm import LLMConfig
from app.schemas.quiz import QuizOutput
from app.rag.retrieval import ChatRetrievalHelper
from app.services.llm.llm_service import LLMService
from app.agent.state import GraphState


logger = get_logger(__name__)


class ChatGraphBuilder:
  """
  Builds the LangGraph for Chat Service using langchain.agents.create_agent.
  Includes Tool execution loop.
  """

  def __init__(
      self,
      llm_service: LLMService,
      retrieval_helper: ChatRetrievalHelper,
      tools: List[BaseTool] = None,
      checkpointer: BaseCheckpointSaver = None
  ):
    self.llm_service = llm_service
    self.retrieval_helper = retrieval_helper
    self.tools = tools or []
    self.checkpointer = checkpointer

  def build_graph(self):
    """
    Builds the compiled StateGraph.
    """
    workflow = StateGraph(GraphState)

    # Define Nodes
    workflow.add_node("agent", self.run_agent)
    workflow.add_node("check_hallucination", self.check_hallucination)

    if self.tools:
      workflow.add_node("tools", ToolNode(self.tools))

    # Define Edges
    workflow.add_edge(START, "agent")

    # Conditional Edge from Agent -> Tools OR Check Hallucination
    workflow.add_conditional_edges(
        "agent",
        self.route_agent_output,
        {
            "tools": "tools",
            "check_hallucination": "check_hallucination",
        }
    )

    if self.tools:
      # After tool execution, loop back to agent to read tool output
      workflow.add_edge("tools", "agent")

    # Conditional Edge: Check Hallucination -> End OR Retry
    workflow.add_conditional_edges(
        "check_hallucination",
        self.grade_generation,
        {
            "grounded": END,
            "hallucination": "agent",  # Loop back to agent to retry
            "max_retries": END
        }
    )

    # Compile
    return workflow.compile(checkpointer=self.checkpointer)

  def route_agent_output(self, state: GraphState) -> Literal["tools", "check_hallucination"]:
    """
    Determines if the agent invoked a tool or finished.
    """
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
      return "tools"

    return "check_hallucination"

  # ------------------------------------------------------------------
  # NODES
  # ------------------------------------------------------------------

  async def run_agent(self, state: GraphState):
    """
    Invokes the Agent using the new create_agent method.
    """
    logger.info("---RUN AGENT---")
    messages = state["messages"]
    context = state["context"]
    llm_config = state["llm_config"]

    context_str = "\n\n".join(
      [d.page_content for d in context]) if context else ""

    # Construct System Instruction
    instruction = self._prepare_system_instruction(
      llm_config, state.get("quiz_mode", False))

    if context_str:
      instruction += f"\n\nContext from Knowledge Base:\n{context_str}"

    # Determine Tools
    tools = self.tools if state.get(
      "supports_tools") and not state.get("quiz_mode") else []

    # 2. Get LLM
    llm = self.llm_service._get_llm(
        llm_config.provider,
        llm_config.model,
        llm_config.temperature,
        llm_config.api_key,
        llm_config.base_url
    )

    # 3. Create Agent
    # create_agent likely returns a compiled graph
    agent = create_agent(llm, tools, system_prompt=instruction)

    # 4. Invoke
    # Pass messages directly as expected by LangGraph-style agents
    result = await agent.ainvoke({"messages": messages})

    # 5. Extract Output
    # The result from a graph invocation usually contains the final state.
    # We expect 'messages' in the result.
    output_messages = result["messages"]
    last_message = output_messages[-1]

    # Wrap in AIMessage to be compatible with GraphState expected by next node
    return {
        "messages": [last_message],
        "retry_count": state.get("retry_count", 0)
    }

  async def check_hallucination(self, state: GraphState):
    """
    Check for hallucinations.
    """
    # Skip check if Quiz Mode or no context
    if state.get("quiz_mode"):
      return {"is_grounded": True}

    logger.info("---CHECK HALLUCINATION---")
    messages = state["messages"]
    last_message = messages[-1]

    if not isinstance(last_message, AIMessage):
      return {"is_grounded": True}

    # If it has tool calls, it shouldn't have stopped unless it hit max steps?
    if last_message.tool_calls:
      return {"is_grounded": True}

    generation = str(last_message.content)
    context = state.get("context", [])
    context_str = "\n\n".join(
      [d.page_content for d in context]) if context else ""
    llm_config = state["llm_config"]

    if not context_str:
      return {"is_grounded": True}

    score = await self.llm_service.check_hallucination(context_str, generation, llm_config)

    if score:
      return {"is_grounded": True}
    else:
      logger.warning(
        f"Hallucination detected. Retry count: {state.get('retry_count', 0)}")
      return {"is_grounded": False, "retry_count": state.get('retry_count', 0) + 1}

  # ------------------------------------------------------------------
  # EDGES
  # ------------------------------------------------------------------

  def grade_generation(self, state: GraphState) -> Literal["grounded", "hallucination", "max_retries"]:
    """
    Determines the next step based on hallucination check.
    """
    MAX_RETRIES = 2

    if state.get("is_grounded", True):
      logger.info("Generation is grounded.")
      return "grounded"

    if state.get("retry_count", 0) >= MAX_RETRIES:
      logger.warning("Max retries reached via self-correction.")
      return "max_retries"

    return "hallucination"

  # ------------------------------------------------------------------
  # HELPERS
  # ------------------------------------------------------------------

  def _prepare_system_instruction(self, config: LLMConfig, quiz_mode: bool) -> str:
    from app.services.llm.prompt_templates import EDUCATIONAL_GUARDRAIL_PROMPT, QUIZ_PROMPT
    base_instruction = config.system_prompt or "You are a helpful AI assistant."
    if quiz_mode:
      return f"{base_instruction}\n\n{QUIZ_PROMPT}"
    return f"{EDUCATIONAL_GUARDRAIL_PROMPT}\n\n{base_instruction}"

  def _get_standard_rag_chain(self, config: LLMConfig, instruction: str, quiz_mode: bool):
    # Resolve provider/model
    provider = config.provider
    model = config.model
    if "/" in config.model and provider != "ollama":
      provider, model = config.model.split("/", 1)

    llm = self.llm_service._get_llm(
        provider=provider,
        model=model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url
    )

    if quiz_mode:
      return self.llm_service.get_quiz_chain(config, instruction)

    prompt = ChatPromptTemplate.from_messages([
        ("system", instruction),
        ("human",
         "Here's the previous conversation:\n{history}\n\nContext from Knowledge Base:\n{context}\n\nUser Question:\n{query}")
    ])

    return prompt | llm | StrOutputParser()
