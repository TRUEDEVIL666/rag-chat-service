import os
import requests
import openai
import asyncio

from app.config.config import settings


class LLMService:
	def chat(self, prompt: str, model: str = "gpt-oss:20b", temperature: float = 0.7, streaming: bool = False) -> str:
		# TODO: Double check this file
		print(f"Bot nèeeeeeeeeeeeeeeeeee ku")
		if streaming:
			raise RuntimeError("Call stream_chat() for streaming response")
		print(f"Calling LLM with model: {model}, temperature: {temperature}")
		# if model.startswith("gpt"):
		#     return self._openai_chat(prompt, model, temperature)
		# else:

		return self._ollama_chat(prompt, model, temperature)

	async def stream_chat(self, prompt: str, model: str = "gpt-4", temperature: float = 0.7):
		if model.startswith("gpt"):
			async for chunk in self._stream_openai_chat(prompt, model, temperature):
				yield chunk
		else:
			async for chunk in self._stream_ollama_chat(prompt, model, temperature):
				yield chunk

	def _openai_chat(self, prompt: str, model: str, temperature: float) -> str:
		openai.api_key = os.getenv("OPENAI_API_KEY")
		response = openai.chat.completions.create(
			model=model,
			messages=[{"role": "system", "content": prompt}],
			temperature=temperature,
		)
		content = response.choices[0].message.content
		return content.strip() if content is not None else ""

	def _ollama_chat(self, prompt: str, model: str, temperature: float) -> str:
		# TODO: Make sure to update the correct url
		url_ollama = settings.ollama_url
		payload = {
			"model": model,
			"prompt": prompt,
			"temperature": temperature,
			"stream": False
		}
		print(f"Calling Ollama API at {url_ollama} with model {model}")
		response = requests.post(f"{url_ollama}/api/generate", json=payload)
		response.raise_for_status()
		return response.json()["response"].strip()

	async def _stream_ollama_chat(self, prompt: str, model: str, temperature: float):
		import aiohttp

		url_ollama = os.getenv("OLLAMA_URL")
		payload = {
			"model": model,
			"prompt": prompt,
			"temperature": temperature,
			"stream": True
		}

		async with aiohttp.ClientSession() as session:
			async with session.post(f"{url_ollama}/api/generate", json=payload) as resp:
				async for line in resp.content:
					if not line:
						continue
					try:
						data = line.decode("utf-8").strip()
						if not data:
							continue
						import json
						parsed = json.loads(data)
						yield parsed.get("response", "")
					except Exception:
						continue

	async def _stream_openai_chat(self, prompt: str, model: str, temperature: float):
		openai.api_key = os.getenv("OPENAI_API_KEY")
		stream = openai.chat.completions.create(
			model=model,
			messages=[{"role": "system", "content": prompt}],
			temperature=temperature,
			stream=True
		)

		for chunk in stream:
			content = chunk.choices[0].delta.content
			if content:
				yield content
			await asyncio.sleep(0)


llm_service = LLMService()
