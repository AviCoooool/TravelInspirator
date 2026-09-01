from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    provider: str = "gemini"
    llm_fallback_enabled: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    max_tokens: int = 4000
    query_timeout: int = 300
    dev_bearer_token: str = "dev-token-123"


settings = Settings()
