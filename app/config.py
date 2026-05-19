"""Application configuration loaded from environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """All runtime configuration. Values come from `.env` (see `.env.example`)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "naija-persona-agent"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # --- LLM API keys ---
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    # NVIDIA model for synthetic + rating refinement — override if your account
    # doesn't have access to the default (set NVIDIA_NEMO_MODEL in .env).
    # Run the diagnostic in the Colab notebook to find which models work for you.
    nvidia_nemo_model: str = "meta/llama-3.3-70b-instruct"
    hf_token: str | None = None

    # --- LangSmith / W&B ---
    wandb_api_key: str | None = None
    wandb_project: str = "naija-persona-agent"
    langsmith_api_key: str | None = None
    langsmith_project: str = "naija-persona-agent"
    langchain_tracing_v2: bool = False

    # --- Service endpoints ---
    ollama_url: str = "http://localhost:11434"
    lm_studio_url: str = "http://localhost:1234/v1"
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # --- Model defaults (format: "provider:model-id") ---
    task1_backbone: str = "anthropic:claude-sonnet-4-20250514"
    task1_fallback: str = "anthropic:claude-sonnet-4-20250514"
    task2_reranker: str = "anthropic:claude-sonnet-4-20250514"
    persona_extractor: str = "anthropic:claude-sonnet-4-20250514"
    # Default: local sentence-transformers (384-dim, free, no API key required).
    # Switch to "openai:text-embedding-3-small" (1536-dim) if you want frontier
    # embedding quality — set OPENAI_API_KEY and re-run build_product_index.py
    # to rebuild the Chroma collection with matching dimensionality.
    embedding_model: str = "local:paraphrase-MiniLM-L6-v2"

    # --- Feature flags ---
    enable_business_demo: bool = False
    enable_streaming: bool = True
    enable_reasoning_trace: bool = True

    # --- Paths ---
    sqlite_path: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "personas.db")
    chroma_path: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "chroma_db")
    sample_personas_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "sample" / "personas"
    )
    sample_products_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "sample" / "products"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
