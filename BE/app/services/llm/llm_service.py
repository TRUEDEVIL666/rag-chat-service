import os
import requests
import openai
import asyncio
import aiohttp
import json

from app.config.config import settings


class LLMService:
  def chat(self, prompt: str, provider: str = "ollama", model: str = "gemma3:4b", temperature: float = 0.7) -> str:
    print(
      f"Calling LLM with provider: {provider}, model: {model}, temperature: {temperature}")

    if provider.lower() == "openai":
      return self._openai_chat(prompt, model, temperature)
    else:
      return self._ollama_chat(prompt, model, temperature)

  async def stream_chat(self, prompt: str, provider: str = "ollama", model: str = "gemma3:4b", temperature: float = 0.7):
    if provider.lower() == "openai":
      async for chunk in self._stream_openai_chat(prompt, model, temperature):
        yield chunk
    else:
      async for chunk in self._stream_ollama_chat(prompt, model, temperature):
        yield chunk

  # --------------------
  # OPENAI
  # --------------------

  def _openai_chat(self, prompt: str, model: str, temperature: float) -> str:
    openai.api_key = settings.OPENAI_API_KEY
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return content.strip() if content is not None else ""

  async def _stream_openai_chat(self, prompt: str, model: str, temperature: float):
    openai.api_key = settings.OPENAI_API_KEY
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

  # --------------------
  # OLLAMA
  # --------------------

  def _ollama_chat(self, prompt: str, model: str, temperature: float) -> str:
    url_ollama = settings.OLLAMA_URL
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
    url_ollama = settings.OLLAMA_URL
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
            parsed = json.loads(data)
            yield parsed.get("response", "")
          except Exception as e:
            print(f"Error parsing Ollama stream: {e}. Data: '{data}'")
            raise ValueError("Error parsing message")


llm_service = LLMService()
