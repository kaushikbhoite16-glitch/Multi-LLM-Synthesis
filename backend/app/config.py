import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    PROJECT_NAME: str = "Multi-LLM Response Evaluation and Adaptive Answer Synthesis"
    API_V1_STR: str = "/api"
    
    # LLM Gateway
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./multi_llm.db")
    
    # Defaults
    DEFAULT_EVALUATOR_MODEL: str = os.getenv("DEFAULT_EVALUATOR_MODEL", "openai/gpt-4o-mini")
    DEFAULT_SYNTHESIS_MODEL: str = os.getenv("DEFAULT_SYNTHESIS_MODEL", "openai/gpt-4o-mini")
    DEFAULT_CANDIDATE_MODELS: List[str] = [
        "google/gemini-2.5-flash",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    
    # Resource Limits
    MAX_COST_PER_QUERY: float = float(os.getenv("MAX_COST_PER_QUERY", "0.50"))
    MAX_TOKENS_PER_QUERY: int = int(os.getenv("MAX_TOKENS_PER_QUERY", "16000"))
    REQUEST_TIMEOUT_SECONDS: float = 60.0
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

settings = Settings()
