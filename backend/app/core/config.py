from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:175416@localhost:5432/test_case_db"

    # Milvus
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_TOKEN: str = ""
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION_NAME: str = "test_cases"

    # OpenAI/LLM
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-4"

    # Embedding provider
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_API_KEY: str = "sk-tqtmkwhiyecjwvsfhtjsotsblspvfkwbsmjzmkqmyupbgsfv"
    EMBEDDING_API_BASE: str = "https://api.siliconflow.cn/v1"

    # SiliconFlow Embeddings
    DOCUMENT_CHUNK_SIZE: int = 500
    DOCUMENT_CHUNK_OVERLAP: int = 100
    EMBEDDING_BATCH_SIZE: int = 16

    # Requirement processing
    TEST_POINT_MAX_INPUT_CHARS: int = 120000  # ≈120KB
    TEST_POINT_CONTEXT_CHUNKS: int = 24
    MIN_REQUIREMENT_CHARACTERS: int = 200
    MIN_NON_EMPTY_LINE_RATIO: float = 0.05

    # LLM retry
    AI_MAX_RETRIES: int = 3
    AI_RETRY_INTERVAL: float = 2.0

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52_428_800  # 50MB

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
