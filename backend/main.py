from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import engine
from app.db.base import Base, import_models
from app.utils.file_paths import get_upload_dir_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(get_upload_dir_path(), exist_ok=True)
    # Import all models to register them with SQLAlchemy
    import_models()
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


app = FastAPI(
    title="智能测试用例平台",
    description="保险行业智能测试用例生成平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
upload_dir = get_upload_dir_path()
if upload_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "智能测试用例平台 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
