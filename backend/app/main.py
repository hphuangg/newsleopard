from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
import logging

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# 新增: 啟動時打印資料庫連線字串
@app.on_event("startup")
async def print_db_url():
    logging.basicConfig(level=logging.INFO)
    logging.info(f"[Startup] Database URL: {settings.database.url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/")
async def root():
    return {"message": "Welcome to Backend API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}