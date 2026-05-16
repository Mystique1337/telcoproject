"""LLM client abstraction — single interface over Anthropic, OpenAI, and Ollama."""

from app.llm.client import LLMClient, get_llm_client

__all__ = ["LLMClient", "get_llm_client"]
