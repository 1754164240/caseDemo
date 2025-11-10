from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Database (使用 psycopg 驱动)
    DATABASE_URL: str = "postgresql+psycopg://postgres:ccb.life*123@localhost:5432/test_case_db"

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

    # Embedding 模型配置(支持单独的 API)
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_API_KEY: str = ""  # 为空时使用 OPENAI_API_KEY
    EMBEDDING_API_BASE: str = "https://api.siliconflow.cn/v1"  # 为空时使用 OPENAI_API_BASE

    # SiliconFlow Embeddings
    DOCUMENT_CHUNK_SIZE: int = 500
    DOCUMENT_CHUNK_OVERLAP: int = 100
    EMBEDDING_BATCH_SIZE: int = 16

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # CORS (使用逗号分隔的字符串)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()

