from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat import router as chat_router
from app.routers.score import router as score_router
from app.routers.today import router as today_router


app = FastAPI(
    title="온라인 쇼핑몰 데이터분석 및 법률 RAG API",
    description="상품 데이터분석과 Qdrant·Ollama 기반 법률 챗봇 API",
    version="1.0.0",
)


# React에서 FastAPI를 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 법률 챗봇 API 연결
app.include_router(chat_router)

# 데이터분석 API 연결
app.include_router(score_router)

# 오늘의 추천 API 연결
app.include_router(today_router)


@app.get(
    "/",
    tags=["health"],
    summary="서버 실행 확인",
)
def root() -> dict[str, str]:
    return {
        "message": "쇼핑몰 데이터분석 및 법률 RAG API가 실행 중입니다."
    }


@app.get(
    "/health",
    tags=["health"],
    summary="서버 상태 확인",
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok"
    }