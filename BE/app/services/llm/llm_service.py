import json
from typing import List, Optional
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm.prompt_templates import (
    QUERY_REWRITE_PROMPT,
    QUERY_DECOMPOSITION_PROMPT
)
from app.schemas.llm import LLMConfig
from app.core.logger import get_logger
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

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
        **model_kwargs
    )

  async def rewrite_query(self, history: str, query: str, config: LLMConfig) -> str:
    """Rewrites the query using LCEL chain."""
    chain = self.get_rewrite_chain(config)
    result = await chain.ainvoke({"history": history, "query": query})
    return result.strip() if result else query

  async def decompose_query(self, query: str, config: LLMConfig) -> List[str]:
    """Decomposes the query using LCEL chain."""
    chain = self.get_decompose_chain(config)
    result = await chain.ainvoke({"query": query})
    return result if isinstance(result, list) else [query]

  async def route_query(self, user_prompt: str, system_instruction: str, config: LLMConfig) -> List[str]:
    """Routes the query using LCEL chain."""
    chain = self.get_route_chain(config, system_instruction)
    result = await chain.ainvoke({"input_text": user_prompt})
    return result if isinstance(result, list) else []

  # ----------------------------------------------------------------------
  # LCEL CHAIN FACTORIES
  # ----------------------------------------------------------------------

  def get_rewrite_chain(self, config: LLMConfig):
    """Returns a chain for query rewriting."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a query rewriting assistant."),
        ("human", QUERY_REWRITE_PROMPT)
    ])
    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0,
        api_key=config.api_key,
        base_url=config.base_url
    )
    return prompt | llm | StrOutputParser()

  def get_decompose_chain(self, config: LLMConfig):
    """Returns a chain for query decomposition."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a query decomposition assistant. Return ONLY a JSON array of strings."),
        ("human", QUERY_DECOMPOSITION_PROMPT)
    ])
    llm = self._get_llm(
        config.provider,
        config.model,
        temperature=0,
        api_key=config.api_key,
        base_url=config.base_url
    )
    return prompt | llm | JsonOutputParser()

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
    return prompt | llm | JsonOutputParser()


llm_service = LLMService()
