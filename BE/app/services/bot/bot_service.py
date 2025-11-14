# app/services/bot/bot_service.py
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator
from app.services.llm.llm_service import LLMService
from app.services.supabase.supabase_client import supabase
from app.services.indexer.vector_store import VectorRepository
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest


class BotService:
	def __init__(self, vector_repo: VectorRepository, llm_service: LLMService):
		self.vector_repo = vector_repo
		self.llm_service = llm_service

	@staticmethod
	def create_bot(data: BotCreateRequest, tenant_id: str, user_id: str):
		bot_id = str(uuid4())
		now = datetime.utcnow().isoformat()

		insert_data = {
			"id": bot_id,
			"tenant_id": tenant_id,
			"name": data.name,
			"description": data.description,
			"config_prompt": None,
			"config_model": None,
			"kb_ids": None,
			"created_at": now,
		}

		result = supabase.table("bots").insert(insert_data).execute()
		if result.data:
			return result.data[0]
		else:
			raise Exception("Failed to insert bot")

	@staticmethod
	def update_config(bot_id: str, tenant_id: str, request: BotUpdateConfigRequest):
		existing = (
			supabase.table("bots")
			.select("*")
			.eq("id", bot_id)
			.eq("tenant_id", tenant_id)
			.single()
			.execute()
		)
		if not existing.data:
			raise ValueError("Bot not found or not owned by tenant")

		update_data = {}
		if request.config_prompt is not None:
			update_data["config_prompt"] = request.config_prompt
		if request.config_model is not None:
			update_data["config_model"] = request.config_model.dict()
		if request.kb_ids is not None:
			update_data["kb_ids"] = request.kb_ids

		updated = (
			supabase.table("bots")
			.update(update_data)
			.eq("id", bot_id)
			.execute()
		)
		if updated.data:
			return updated.data[0]
		else:
			raise ValueError("Failed to update bot")

	@staticmethod
	def list_bots(tenant_id: str):
		result = (
			supabase.table("bots")
			.select("*")
			.eq("tenant_id", tenant_id)
			.order("created_at", desc=True)
			.execute()
		)
		return result.data or []

	@staticmethod
	def get_bot(bot_id: str, tenant_id: str):
		print(f"Fetching bot {bot_id} for tenant {tenant_id}")
		result = (
			supabase.table("bots")
			.select("*")
			.eq("id", bot_id)
			.eq("tenant_id", tenant_id)
			.single()
			.execute()
		)
		print(f"Bot fetch result: {result.data}")
		return result.data

	@staticmethod
	def delete_bot(bot_id: str, tenant_id: str):
		result = (
			supabase.table("bots")
			.delete()
			.eq("id", bot_id)
			.eq("tenant_id", tenant_id)
			.execute()
		)
		return result.data

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
