import os
import os
import openai
import asyncio
import ollama

# Google
from google import genai
from google.genai import types

# Hugging Face
from huggingface_hub import InferenceClient

from app.config.config import settings


class LLMService:
  def chat(
      self,
      prompt: str,
      system_instruction: str = None,
      provider: str = "ollama",
      model: str = "gemma3:4b",
      temperature: float = 0.7,
      api_key: str = None,
      base_url: str = None
  ) -> str:
    print(
      f"Calling LLM with provider: {provider}, model: {model}, temperature: {temperature}")

    provider = provider.lower()
    if provider == "openai":
      return self._openai_chat(prompt, system_instruction, model, temperature, api_key, base_url)
    elif provider == "google":
      # Google genai doesn't easily support base_url yet
      return self._google_chat(prompt, system_instruction, model, temperature, api_key)
    elif provider == "huggingface":
      return self._huggingface_chat(prompt, system_instruction, model, temperature, api_key, base_url)
    elif provider == "ollama":
      return self._ollama_chat(prompt, system_instruction, model, temperature, base_url)
    else:
      return self._ollama_chat(prompt, system_instruction, model, temperature, base_url)

  async def stream_chat(
      self,
      prompt: str,
      system_instruction: str = None,
      provider: str = "ollama",
      model: str = "gemma3:4b",
      temperature: float = 0.7,
      api_key: str = None,
      base_url: str = None
  ):
    provider = provider.lower()
    if provider == "openai":
      async for chunk in self._stream_openai_chat(prompt, system_instruction, model, temperature, api_key, base_url):
        yield chunk
    elif provider == "google":
      async for chunk in self._stream_google_chat(prompt, system_instruction, model, temperature, api_key):
        yield chunk
    elif provider == "huggingface":
      async for chunk in self._stream_huggingface_chat(prompt, system_instruction, model, temperature, api_key, base_url):
        yield chunk
    elif provider == "ollama":
      async for chunk in self._stream_ollama_chat(prompt, system_instruction, model, temperature, base_url):
        yield chunk
    else:
      async for chunk in self._stream_ollama_chat(prompt, system_instruction, model, temperature, base_url):
        yield chunk

  # --------------------
  # OPENAI
  # --------------------
  def _openai_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None,
      base_url: str = None
  ) -> str:
    # If base_url is set (custom endpoint) and no key is provided/globally set,
    # use a dummy key to satisfy the SDK validation.
    final_key = api_key
    if not final_key and base_url:
      final_key = "ollama"

    client = openai.Client(
      api_key=final_key, base_url=base_url)
    messages = []
    if system_instruction:
      messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return content.strip() if content is not None else ""

  async def _stream_openai_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None,
      base_url: str = None
  ):
    # If base_url is set (custom endpoint) and no key is provided/globally set,
    # use a dummy key to satisfy the SDK validation.
    final_key = api_key
    if not final_key and base_url:
      final_key = "ollama"

    client = openai.AsyncClient(
      api_key=final_key, base_url=base_url)
    messages = []
    if system_instruction:
      messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True
    )

    for chunk in stream:
      content = chunk.choices[0].delta.content
      if content:
        yield content
      await asyncio.sleep(0)

  # --------------------
  # GOOGLE (GEMINI)
  # --------------------
  def _google_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None
  ) -> str:
    final_key = api_key
    if not final_key:
      return "Error: Google API Key not configured."

    try:
      client = genai.Client(api_key=final_key)

      generation_config = types.GenerateContentConfig(
          temperature=temperature,
          system_instruction=system_instruction
      )

      # Determine model name
      model_name = model if model.startswith(
          "models/") or model.startswith("gemini-") else f"models/{model}"

      response = client.models.generate_content(
          model=model_name,
          contents=prompt,
          config=generation_config
      )
      return response.text
    except Exception as e:
      print(f"Google GenAI Error: {e}")
      return f"Error calling Google AI: {str(e)}"

  async def _stream_google_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None
  ):
    final_key = api_key
    if not final_key:
      yield "Error: Google API Key not configured."
      return

    try:
      client = genai.Client(api_key=final_key)

      generation_config = types.GenerateContentConfig(
          temperature=temperature,
          system_instruction=system_instruction
      )

      model_name = model if model.startswith(
          "models/") or model.startswith("gemini-") else f"models/{model}"

      response = client.models.generate_content_stream(
          model=model_name,
          contents=prompt,
          config=generation_config
      )

      for chunk in response:
        if chunk.text:
          yield chunk.text
          await asyncio.sleep(0)  # Yield control

    except Exception as e:
      print(f"Google GenAI Stream Error: {e}")
      yield f"Error calling Google AI: {str(e)}"

  # --------------------
  # HUGGING FACE
  # --------------------
  def _huggingface_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None,
      base_url: str = None
  ) -> str:
    final_key = api_key
    # Allow no key if using self-hosted base_url maybe? But usually key is good.
    if not final_key and not base_url:
      return "Error: Hugging Face API Key not configured."

    try:
      # If base_url is provided, use it as the 'model' argument which acts as the endpoint URL
      # Otherwise use the model name to infer the default HF endpoint
      client = InferenceClient(model=base_url or model, token=final_key)

      messages = []
      if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
      messages.append({"role": "user", "content": prompt})

      response = client.chat_completion(
          model=model,
          messages=messages,
          temperature=temperature,
          max_tokens=2048
      )

      return response.choices[0].message.content
    except Exception as e:
      print(f"HuggingFace Error: {e}")
      return f"Error calling Hugging Face: {str(e)}"

  async def _stream_huggingface_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      api_key: str = None,
      base_url: str = None
  ):
    final_key = api_key
    if not final_key and not base_url:
      yield "Error: Hugging Face API Key not configured."
      return

    try:
      client = InferenceClient(model=base_url or model, token=final_key)

      messages = []
      if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
      messages.append({"role": "user", "content": prompt})

      stream = client.chat_completion(
          model=model,
          messages=messages,
          temperature=temperature,
          max_tokens=2048,
          stream=True
      )

      for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
          yield content
        # Yield control to event loop to make it truly async-ish
        await asyncio.sleep(0)

    except Exception as e:
      print(f"HuggingFace Stream Error: {e}")
      yield f"Error calling Hugging Face: {str(e)}"

  # --------------------
  # OLLAMA
  # --------------------
  def _ollama_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      base_url: str = None
  ) -> str:
    print(f"Calling Ollama API with model {model}")
    try:
      client = ollama.Client(host=base_url or settings.OLLAMA_URL)

      messages = []
      if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
      messages.append({"role": "user", "content": prompt})

      response = client.chat(
        model=model,
        messages=messages,
        options={
          "temperature": temperature
        }
      )
      return response['message']['content']
    except Exception as e:
      print(f"Ollama Error: {e}")
      return f"Error calling Ollama: {str(e)}"

  async def _stream_ollama_chat(
      self,
      prompt: str,
      system_instruction: str,
      model: str,
      temperature: float,
      base_url: str = None
  ):
    try:
      client = ollama.AsyncClient(host=base_url or settings.OLLAMA_URL)

      messages = []
      if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
      messages.append({"role": "user", "content": prompt})

      async for part in await client.chat(
        model=model,
        messages=messages,
        options={
          "temperature": temperature
        },
        stream=True
      ):
        content = part['message']['content']
        if content:
          yield content
    except Exception as e:
      print(f"Ollama Stream Error: {e}")
      yield f"Error calling Ollama: {str(e)}"


llm_service = LLMService()
