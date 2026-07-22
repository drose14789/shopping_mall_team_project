from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import answer_chat


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    summary="온라인 쇼핑몰 법률 챗봇 질문",
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    사용자의 질문과 최근 대화 내역을 받아 질문 유형에 따라 처리합니다.

    - 챗봇 소개 질문: 고정 답변
    - 인사·간단한 일상 대화: 일반 대화 처리
    - 쇼핑몰 법률 질문: 기존 Qdrant RAG
    - 후속 질문: 최근 대화 내역과 함께 처리
    """
    try:
        history = [
            message.model_dump()
            for message in request.history
        ]

        result = answer_chat(
            question=request.question,
            history=history,
        )

        return ChatResponse(**result)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="챗봇 답변 생성 중 오류가 발생했습니다.",
        ) from error