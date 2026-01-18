"""Application configuration with environment variable support."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database (defaults to SQLite for easy local development)
    database_url: str = "sqlite:///./agent_chat.db"

    # Anthropic
    anthropic_api_key: str = "mock"  # Default to mock for local development
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    use_mock_model: bool = False  # Set to True to use mock model instead of real API

    # Agent settings
    max_agent_iterations: int = 10
    tool_timeout_seconds: int = 30

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000


# Global settings instance
settings = Settings()
