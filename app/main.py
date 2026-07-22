from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat import router as chat_router


app = FastAPI(
    title="온라인 쇼핑몰 법률 RAG 챗봇",
    description="Qdrant 검색과 Ollama를 이용한 법률·정책 안내 API",
    version="1.0.0",
)


# 나중에 React에서 FastAPI를 호출할 수 있도록 허용
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


# chat.py에 만든 /chat API 연결
app.include_router(chat_router)


@app.get(
    "/",
    tags=["health"],
    summary="서버 실행 확인",
)
def root() -> dict[str, str]:
    return {
        "message": "쇼핑몰 법률 RAG 챗봇 API가 실행 중입니다."
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