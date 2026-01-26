import json
from typing import List, Optional
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm.prompt_templates import (
    QUERY_REWRITE_AND_DECOMPOSE_PROMPT
)
from app.schemas.llm import LLMConfig, QueryRefinement, KbRoutingOutput
from app.schemas.quiz import QuizOutput
from app.core.logger import get_logger
from langchain_core.output_parsers import StrOutputParser

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, Runnable
from langchain.agents import create_agent
from langchain_core.tools import Tool

logger = get_logger("llm_service")


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

  async def rewrite_and_decompose_query(self, history: str, query: str, config: LLMConfig) -> QueryRefinement:
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

  # ----------------------------------------------------------------------
  # LCEL CHAIN FACTORIES
  # ----------------------------------------------------------------------

  def get_rewrite_decompose_chain(self, config: LLMConfig):
    """Returns a chain for simultaneous rewriting and decomposition."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a search query optimizer. Return a JSON object matching the specified format."),
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

  def get_agent(self, config: LLMConfig, system_instruction: str, tools: List[Tool]) -> Runnable:
    """
    Creates a Tool Calling Agent using LangGraph (create_agent).
    """
    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url
    )

    if config.tool_choice:
      llm = llm.bind_tools(tools, tool_choice=config.tool_choice)

    return create_agent(model=llm, tools=tools, system_prompt=system_instruction)

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

  def supports_tools(self, provider: str, model: str, api_key: str = None, base_url: str = None) -> bool:
    """
    Detect if a model supports tool calling by attempting to invoke with tools.
    """
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
      return True
    except Exception as e:
      error_msg = str(e).lower()
      # Check if it's a tool-related error
      if "tool" in error_msg or "function" in error_msg or "400" in error_msg:
        logger.info(f"Model {provider}/{model} does not support tools: {e}")
        return False
      # Other errors might be network/auth issues, assume tools work
      logger.warning(
        f"Tool detection inconclusive for {provider}/{model}: {e}")
      return True


llm_service = LLMService()
