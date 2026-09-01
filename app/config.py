from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # gemini | self-hosted | mock
    provider: str = "self-hosted"
    llm_fallback_enabled: bool = True

    # Google AI Studio (direct) — optional
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Coforge Quasar / OpenAI-compatible router
    llm_api_key: str = ""
    llm_api_url: str = "https://quasarmarket.coforge.com/qag/llmrouter-api/v2/chat/completions"
    model: str = "gpt-5.2"

    max_tokens: int = 4000
    query_timeout: int = 300
    dev_bearer_token: str = "dev-token-123"


settings = Settings()
