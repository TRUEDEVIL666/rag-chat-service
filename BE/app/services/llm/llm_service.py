from typing import List, Optional
import time

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import Tool

from app.core.logger import get_logger
from app.schemas.llm import HallucinationGrade, KbRoutingOutput, LLMConfig, QueryRefinement
from app.schemas.quiz import QuizOutput
from app.services.llm.prompt_templates import (
    QUERY_REWRITE_AND_DECOMPOSE_PROMPT
)

logger = get_logger(__name__)


class LLMService:
  def _get_model_kwargs(self, provider: str, api_key: str = None, base_url: str = None):
    kwargs = {}
    if api_key:
      if provider == "openai":
        kwargs["api_key"] = api_key
      elif provider == "google_genai":
        kwargs["google_api_key"] = api_key
      elif provider == "huggingface":
        kwargs["huggingfacehub_api_token"] = api_key

    if base_url:
      if provider == "openai":
        kwargs["base_url"] = base_url
      elif provider == "ollama":
        kwargs["base_url"] = base_url

    return kwargs

  def _get_llm(
      self,
      provider: str,
      model: str,
      temperature: float = 0.7,
      api_key: str = None,
      base_url: str = None
  ):
    langchain_provider = provider.lower()
    if langchain_provider == "google":
      langchain_provider = "google_genai"
    model_kwargs = self._get_model_kwargs(
      langchain_provider, api_key, base_url)

    return init_chat_model(
        model,
        model_provider=langchain_provider,
        temperature=temperature,
        timeout=120,  # Enforce 2-minute timeout
        **model_kwargs
    )

  async def rewrite_and_decompose_query(self, history: List[BaseMessage], query: str, config: LLMConfig) -> QueryRefinement:
    """Rewrites and Decomposes the query in one go."""
    chain = self.get_rewrite_decompose_chain(config)
    result = await chain.ainvoke({"history": history, "query": query})
    return result

  async def route_query(self, user_prompt: str, system_instruction: str, config: LLMConfig) -> List[str]:
    """Routes the query using LCEL chain."""
    chain = self.get_route_chain(config, system_instruction)
    try:
      result = await chain.ainvoke({"input_text": user_prompt})
      return result.kb_ids
    except Exception as e:
      logger.error(f"Routing chain failed: {e}")
      return []

  async def generate_hyde_doc(self, query: str, config: LLMConfig) -> str:
    """Generates a hypothetical document for HyDE retrieval."""
    chain = self.get_hyde_chain(config)
    try:
      result = await chain.ainvoke({"query": query})
      return result
    except Exception as e:
      logger.error(f"HyDE chain failed: {e}")
      return query  # Fallback to original query

  # ----------------------------------------------------------------------
  # LCEL CHAIN FACTORIES
  # ----------------------------------------------------------------------

  def get_rewrite_decompose_chain(self, config: LLMConfig):
    """Returns a chain for simultaneous rewriting and decomposition."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a search query optimizer. Return a JSON object matching the specified format."),
        MessagesPlaceholder(variable_name="history"),
        ("human", QUERY_REWRITE_AND_DECOMPOSE_PROMPT)
    ])
    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0,
        api_key=config.api_key,
        base_url=config.base_url
    )

    # Use standard structured output (supports OpenAI Tools, pure JSON mode, etc.)
    structured_llm = llm.with_structured_output(QueryRefinement)

    return prompt | structured_llm

  def get_route_chain(self, config: LLMConfig, system_instruction: str):
    """Returns a chain for KB routing."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{input_text}")
    ])

    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0,
        api_key=config.api_key,
        base_url=config.base_url
    )

    structured_llm = llm.with_structured_output(KbRoutingOutput)

    return prompt | structured_llm

  def get_bound_model(self, config: LLMConfig, system_instruction: str, tools: List[Tool]) -> Runnable:
    """
    Returns the LLM bound with tools (for native LangGraph tool calling).
    """
    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url
    )

    if tools:
      llm = llm.bind_tools(tools)

    return llm

  def get_quiz_chain(self, config: LLMConfig, system_instruction: str):
    """Returns a chain for Quiz generation."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human",
         "Here's the previous conversation:\n{history}\n\nContext from Knowledge Base:\n{context}\n\nUser Question:\n{query}")
    ])

    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url
    )

    structured_llm = llm.with_structured_output(QuizOutput)

    return prompt | structured_llm

  def get_hyde_chain(self, config: LLMConfig):
    """Returns a chain for HyDE generation."""
    from app.services.llm.prompt_templates import HYDE_PROMPT

    prompt = ChatPromptTemplate.from_messages([
        ("human", HYDE_PROMPT)
    ])

    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0.7,  # Higher temp for creativity in hallucinating answers
        api_key=config.api_key,
        base_url=config.base_url
    )

    return prompt | llm | StrOutputParser()

  async def check_hallucination(self, documents: str, generation: str, config: LLMConfig) -> bool:
    """
    Checks if the generation is grounded in the documents.
    Returns True (grounded) or False (hallucination).
    """
    chain = self.get_grader_chain(config)
    try:
      score_obj = await chain.ainvoke({"documents": documents, "generation": generation})
      return score_obj.score
    except Exception as e:
      logger.error(f"Hallucination check failed: {e}")
      return True  # Fallback to true to allow response on error

  def get_grader_chain(self, config: LLMConfig):
    """Returns a chain for Hallucination Grading."""
    from app.services.llm.prompt_templates import HALLUCINATION_GRADER_PROMPT

    prompt = ChatPromptTemplate.from_messages([
        ("system", HALLUCINATION_GRADER_PROMPT),
        ("human", "Facts:\n{documents}\n\nAnswer:\n{generation}")
    ])

    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0,  # Strict grading
        api_key=config.api_key,
        base_url=config.base_url
    )

    return prompt | llm.with_structured_output(HallucinationGrade)

  # Cache for tool support detection to avoid repeated calls
  _tool_support_cache = {}

  def supports_tools(self, provider: str, model: str, api_key: str = None, base_url: str = None) -> bool:
    """
    Detect if a model supports tool calling by attempting to invoke with tools.
    Results are cached to avoid repeated expensive checks.

    For known providers/models, we can short-circuit the detection.
    """
    # Create cache key
    cache_key = f"{provider}:{model}:{api_key}:{base_url}"

    # Check cache first
    if cache_key in self._tool_support_cache:
      cached_result, timestamp = self._tool_support_cache[cache_key]
      # Cache for 1 hour
      if time.time() - timestamp < 3600:
        return cached_result

    try:
      from langchain_core.tools import tool as tool_decorator
      from langchain_core.messages import HumanMessage

      # Create a real tool
      @tool_decorator
      def test_tool(query: str) -> str:
        """Test tool for capability detection."""
        return "test"

      llm = self._get_llm(provider, model, api_key=api_key, base_url=base_url)
      llm_with_tools = llm.bind_tools([test_tool])

      # Try a minimal invocation - this will fail for non-tool models
      # Use invoke instead of stream to get immediate error
      llm_with_tools.invoke([HumanMessage(content="test")])

      logger.info(f"Model {provider}/{model} supports tools")
      result = True
    except Exception as e:
      error_msg = str(e).lower()
      # Check if it's a tool-related error
      if "tool" in error_msg or "function" in error_msg or "400" in error_msg:
        logger.info(f"Model {provider}/{model} does not support tools: {e}")
        result = False
      # Network/auth errors - assume tools might work and retry later
      elif "timeout" in error_msg or "connection" in error_msg or "auth" in error_msg:
        logger.warning(
          f"Network/Auth error during tool detection for {provider}/{model}: {e}")
        result = True
      else:
        # Other errors might be network/auth issues, assume tools work
        logger.warning(
          f"Tool detection inconclusive for {provider}/{model}: {e}")
        result = True

    # Cache the result
    self._tool_support_cache[cache_key] = (result, time.time())
    return result


llm_service = LLMService()
