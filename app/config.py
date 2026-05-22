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
        populate_by_name=True,
    )

    # --- App ---
    app_name: str = "naija-persona-agent"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # --- LLM API keys ---
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    # freemodel.dev — OpenAI-compatible gateway providing GPT-5/5.5 and other
    # frontier models at promotional pricing. Lives next to openai_api_key so
    # both can coexist; pick per call via the `freemodel:` provider prefix.
    # Env name: FREE_MODEL_APIKEY (the docs use that exact form).
    freemodel_api_key: str | None = Field(default=None, alias="FREE_MODEL_API_KEY")
    freemodel_base_url: str = "https://api.freemodel.dev/v1"
    # Cohere — used as the Stage-2.5 cross-encoder pre-reranker between
    # Pinecone retrieval and the LLM rerank stage. Cheap + fast (~200ms,
    # multilingual). Narrows top-30 → top-N before the persona-aware LLM call.
    cohere_api_key: str | None = None
    cohere_rerank_model: str = "rerank-v3.5"
    cohere_rerank_top_n: int = 15  # narrow 30 → 15 before LLM rerank
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    # NVIDIA model for synthetic + rating refinement — override if your account
    # doesn't have access to the default (set NVIDIA_NEMO_MODEL in .env).
    # Run the diagnostic in the Colab notebook to find which models work for you.
    nvidia_nemo_model: str = "meta/llama-3.3-70b-instruct"
    hf_token: str | None = None
    # Modal-hosted NaijaReviewer-8B (GGUF on a serverless L4). OpenAI-compatible
    # endpoint, open by default. base_url should end in /v1. Use the `modal:`
    # provider prefix (e.g. TASK1_BACKBONE=modal:naija-reviewer-8b) so it doesn't
    # collide with the real OpenAI base URL.
    modal_base_url: str | None = None
    modal_api_key: str = "x"  # any non-empty string; the endpoint is open

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

    # --- Supabase / Database ---
    supabase_url: str | None = None
    supabase_service_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_KEY")
    supabase_jwt_secret: str | None = Field(default=None, alias="SUPABASE_JWT_SECRET")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    direct_url: str | None = Field(default=None, alias="DIRECT_URL")

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
