# app/services/bot/bot_service.py
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator
from app.services.llm.llm_service import LLMService
from app.services.supabase.supabase_client import supabase
from app.services.indexer.vector_store import VectorRepository
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from app.services.supabase.bot_repository import BotRepository
# from app.config import Settings
import httpx
from cachetools import TTLCache, cached

# Cache for 1 hour (3600 seconds), max 100 items
bot_cache = TTLCache(maxsize=100, ttl=3600)


class BotService:
  def __init__(self, vector_repo: VectorRepository, llm_service: LLMService):
    self.vector_repo = vector_repo
    self.llm_service = llm_service
    self.bot_repo = BotRepository()

  @staticmethod
  def create_bot(data: BotCreateRequest, tenant_id: str, user_id: str):
    repo = BotRepository()
    return repo.create_bot(data, tenant_id, user_id)

  @staticmethod
  def update_config(bot_id: str, tenant_id: str, request: BotUpdateConfigRequest):
    repo = BotRepository()
    return repo.update_config(bot_id, tenant_id, request)

  @staticmethod
  def list_bots(tenant_id: str):
    repo = BotRepository()
    return repo.list_bots(tenant_id)

  @staticmethod
  @cached(cache=bot_cache)
  def get_bot(bot_id: str, tenant_id: str):
    repo = BotRepository()
    return repo.get_bot(bot_id, tenant_id)

  @staticmethod
  def delete_bot(bot_id: str, tenant_id: str):
    repo = BotRepository()
    return repo.delete_bot(bot_id, tenant_id)

  async def ask_bot(self, bot_id: str, query: str, tenant_id: str) -> str:
    bot = self.get_bot(bot_id, tenant_id)
    if not bot:
      raise ValueError(f"Bot {bot_id} not found")

    kb_ids = bot.get("kb_ids")
    if not kb_ids:
      return "Bot is not configured with any knowledge bases."

    config_model = bot.get("config_model")
    if not config_model:
      # Provide default model and temperature if not configured
      model = "gpt-3.5-turbo"
      temperature = 0.7
    else:
      model = config_model.get("model", "gpt-3.5-turbo")
      temperature = config_model.get("temperature", 0.7)

    results = self.vector_repo.search(
        query=query,
        k=5,
        kb_ids=kb_ids,
        score_threshold=0.1,
    )

    if not results:
      return "Xin lỗi, tôi không tìm thấy câu trả lời phù hợp."

    context = "\n".join([r["text"] for r in results])

    result = self._call_llm(
        query=query,
        context=context,
        model=model,
        temperature=temperature
    )

    return result

  async def ask_bot_stream(self, bot_id: str, query: str, tenant_id: str) -> AsyncGenerator[str, None]:
    bot = self.get_bot(bot_id, tenant_id)
    if not bot:
      raise ValueError(f"Bot {bot_id} not found")

    kb_ids = bot.get("kb_ids")
    if not kb_ids:
      yield "Bot is not configured with any knowledge bases."
      return

    config_model = bot.get("config_model")
    if not config_model:
      # Provide default model and temperature if not configured
      model = "gpt-3.5-turbo"
      temperature = 0.7
    else:
      model = config_model.get("model", "gpt-3.5-turbo")
      temperature = config_model.get("temperature", 0.7)

    results = self.vector_repo.search(
        query=query,
        k=5,
        kb_ids=kb_ids,
        score_threshold=0.1,
    )

    if not results:
      yield "Xin lỗi, tôi không tìm thấy câu trả lời phù hợp."
      return

    context = "\n".join([r["text"] for r in results])

    async for chunk in self._call_llm_stream(
        query=query,
        context=context,
        model=model,
        temperature=temperature
    ):
      yield chunk

  def _call_llm(self, query: str, context: str, model: str, temperature: float):
    prompt = f"""
      Dựa trên thông tin sau, hãy trả lời câu hỏi một cách chính xác và rõ ràng.
      ===
      {context}
      ===
      Câu hỏi: {query}
    """
    # url = Settings.openai_url
    # match provider.lower():
    #   case 'openai':
    #     url = Settings.openai_url
    #   case 'gemini':
    #     url = Settings.gemini_url

    # client = httpx.AsyncClient()
    # headers = {
    #     "Authorization": f"Bearer {API_KEY}",
    #     "Content-Type": "application/json"
    # }

    # 3. Define the Payload (Body)
    # payload = {
    #     "model": "gpt-4o",  # or "gpt-3.5-turbo"
    #     "messages": [
    #         {"role": "system", "content": "You are a helpful coding assistant."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     "temperature": 0.7
    # }

    # 4. Make the Request
    # async with httpx.AsyncClient() as client:
    #     try:
    #         # Set a timeout (OpenAI can sometimes take >5s to reply)
    #         response = await client.post(
    #             url,
    #             headers=headers,
    #             json=payload,
    #             timeout=30.0
    #         )
    #         response.raise_for_status() # Raises error for 4xx/5xx responses

    #         data = response.json()
    #         return data["choices"][0]["message"]["content"]

    #     except httpx.HTTPStatusError as e:
    #         print(f"Error response {e.response.status_code}: {e.response.text}")
    #     except httpx.RequestError as e:
    #         print(f"An error occurred while requesting: {e}")

    result = self.llm_service.chat(
        prompt=prompt,
        model=model,
        temperature=temperature,
        streaming=False
    )

    return result

  async def _call_llm_stream(self, query: str, context: str, model: str, temperature: float) -> AsyncGenerator[
          str, None]:
    prompt = f"""
    Dựa trên thông tin sau, hãy trả lời câu hỏi một cách chính xác và rõ ràng.
    ===
    {context}
    ===
    Câu hỏi: {query}
    """
    async for chunk in self.llm_service.stream_chat(
        prompt=prompt,
        model=model,
        temperature=temperature
    ):
      yield chunk
