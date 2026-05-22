"""Runtime configuration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    llm_provider: str = Field(
        default="",
        alias="CONTEXTPACK_LLM_PROVIDER",
        description="azure_foundry | openai (only when using --llm / ask_llm)",
    )
    # Azure AI Foundry / Azure OpenAI (not api.openai.com)
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_embedding_deployment: str | None = Field(
        default=None, alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    azure_openai_api_version: str = Field(
        default="2024-10-21", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_ai_inference_endpoint: str | None = Field(
        default=None,
        alias="AZURE_AI_INFERENCE_ENDPOINT",
        description="Optional Foundry project inference URL (OpenAI-compatible)",
    )
    azure_use_inference_endpoint: bool = Field(
        default=False, alias="AZURE_USE_INFERENCE_ENDPOINT"
    )
    embedding_provider: str = Field(default="hash", alias="CONTEXTPACK_EMBEDDING_PROVIDER")
    vector_store: str = Field(
        default="sqlite",
        alias="CONTEXTPACK_VECTOR_STORE",
        description="sqlite (fast) or chroma (heavy cold start)",
    )
    guidelines_max_chars: int = Field(default=12_000, alias="CONTEXTPACK_GUIDELINES_MAX_CHARS")
    jira_base_url: str | None = Field(default=None, alias="JIRA_BASE_URL")
    jira_email: str | None = Field(default=None, alias="JIRA_EMAIL")
    jira_api_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")
    default_token_budget: int = 8_000
    # Tiered embedding: cap total entities sent to the embedder.
    # Hub nodes (high graph degree) are always included first.
    max_embed_entities: int = Field(default=2000, alias="CONTEXTPACK_MAX_EMBED_ENTITIES")
    embed_hubs_first: bool = Field(default=True, alias="CONTEXTPACK_EMBED_HUBS_FIRST")

    def context_dir(self, repo_path: Path) -> Path:
        return repo_path / ".contextpack"


def get_settings() -> Settings:
    return Settings()
