from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.core.logger import get_logger
from app.schemas.llm import HallucinationGrade, LLMConfig

logger = get_logger(__name__)


class LLMService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "LLMService":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def _get_model_kwargs(
    self, provider: str, api_key: str = None, base_url: str = None
  ) -> dict:
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
    base_url: str = None,
  ) -> BaseChatModel:
    langchain_provider = provider.lower()
    if langchain_provider == "google":
      langchain_provider = "google_genai"
    model_kwargs = self._get_model_kwargs(langchain_provider, api_key, base_url)

    return init_chat_model(
      model,
      model_provider=langchain_provider,
      temperature=temperature,
      timeout=120,
      **model_kwargs,
    )

  async def check_hallucination(
    self, documents: str, generation: str, config: LLMConfig
  ) -> bool:
    """
    Checks if the generation is grounded in the documents.
    Returns True (grounded) or False (hallucination).
    """
    from app.agent.prompt_templates import HALLUCINATION_GRADER_PROMPT

    prompt = ChatPromptTemplate.from_messages(
      [
        ("system", HALLUCINATION_GRADER_PROMPT),
        ("human", "Facts:\n{documents}\n\nAnswer:\n{generation}"),
      ]
    )

    llm = self._get_llm(
      config.provider,
      config.model,
      temperature=0,
      api_key=config.api_key,
      base_url=config.base_url,
    )

    chain = prompt | llm.with_structured_output(HallucinationGrade)
    try:
      score_obj = await chain.ainvoke(
        {"documents": documents, "generation": generation}
      )
      return score_obj.score
    except Exception as e:
      logger.error(f"Hallucination check failed: {e}")
      return True

  async def plan_intent(self, messages: List[any], config: LLMConfig) -> any:
    """
    Decides which retrieval systems are needed based on the conversation history.
    """
    from app.agent.prompt_templates import PLANNER_SYSTEM_PROMPT

    from app.schemas.llm import PlannerOutput

    prompt = ChatPromptTemplate.from_messages(
      [("system", PLANNER_SYSTEM_PROMPT), ("human", "{history}")]
    )

    llm = self._get_llm(
      config.provider,
      config.model,
      temperature=0,
      api_key=config.api_key,
      base_url=config.base_url,
    )

    # Convert messages to a readable format for the planner
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-5:]])

    chain = prompt | llm.with_structured_output(PlannerOutput)
    try:
      return await chain.ainvoke({"history": history_str})
    except Exception as e:
      logger.error(f"Planning failed: {e}")
      # Default to both on failure for robustness
      return PlannerOutput(use_memori=True, use_rag=True, use_tools=False, direct=False)


llm_service = LLMService()
