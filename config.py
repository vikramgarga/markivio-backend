from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    anthropic_api_key: str
    openai_api_key: str
    langsmith_api_key: str
    langsmith_project: str = "Markivio phase 1"
    cors_origins: str = "http://localhost:3000"
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    model_config = {"env_file": ".env", "case_sensitive": False}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()

# Wire LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
