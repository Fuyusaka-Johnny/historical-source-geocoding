import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_timeout: float
    chunk_chars: int
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            os.getenv("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1"),
            os.getenv("LLM_MODEL", "MiniMax/MiniMax-M2.5"),
            os.getenv("LLM_API_KEY", ""),
            float(os.getenv("LLM_TIMEOUT", "120")),
            max(100, min(5000, int(os.getenv("CHUNK_CHARS", "1500")))),
            os.getenv("MYSQL_HOST", "127.0.0.1"),
            int(os.getenv("MYSQL_PORT", "3307")),
            os.getenv("MYSQL_DATABASE", "historical_sources"),
            os.getenv("MYSQL_USER", "historian"),
            os.getenv("MYSQL_PASSWORD", ""),
        )
