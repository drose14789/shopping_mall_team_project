from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services import rag_service
from app.services.chat_service import answer_chat


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


def _get_controlled_intent_detectors() -> list[Callable[[str], bool]]:
    """
    rag_service.py에 정의된 고정 intent 판별 함수를 자동으로 가져온다.

    함수 이름이 is_로 시작하고 _question으로 끝나는 함수만
    판별기로 사용한다. 이후 rag_service.py에 새로운 intent를
    추가해도 chat.py를 다시 수정할 필요가 없다.
    """
    detectors: list[Callable[[str], bool]] = []

    for name, value in vars(rag_service).items():
        if (
            name.startswith("is_")
            and name.endswith("_question")
            and callable(value)
        ):
            detectors.append(value)

    return detectors


CONTROLLED_INTENT_DETECTORS = _get_controlled_intent_detectors()


def _matches_controlled_rag_intent(question: str) -> bool:
    """
    질문이 rag_service의 고정 intent 중 하나에 해당하는지 확인한다.

    고정 intent 질문은 chat_service에서 질문을 재작성하기 전에
    rag_service.answer_question()으로 직접 전달해야 한다.
    """
    cleaned_question = " ".join(str(question).split())

    if not cleaned_question:
        return False

    for detector in CONTROLLED_INTENT_DETECTORS:
        try:
            if detector(cleaned_question):
                return True
        except (TypeError, ValueError):
            continue

    return False


def _answer_request(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    고정 법률 intent와 일반 대화 처리 경로를 분리한다.

    1. rag_service의 고정 intent 질문
       -> 원문 그대로 rag_service.answer_question() 호출
    2. 인사, 챗봇 소개, 일반 대화, 대화 내역이 필요한 후속 질문
       -> 기존 chat_service.answer_chat() 호출
    """
    question = " ".join(request.question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    if _matches_controlled_rag_intent(question):
        return rag_service.answer_question(question)

    history = [
        message.model_dump()
        for message in request.history
    ]

    return answer_chat(
        question=question,
        history=history,
    )


@router.post(
    "",
    response_model=ChatResponse,
    summary="온라인 쇼핑몰 법률 챗봇 질문",
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    사용자의 질문과 최근 대화 내역을 받아 질문 유형에 따라 처리한다.

    - 고정 법률 intent: rag_service에서 원문 그대로 처리
    - 챗봇 소개 질문: 기존 chat_service에서 처리
    - 인사·간단한 일상 대화: 기존 chat_service에서 처리
    - 일반 쇼핑몰 법률 질문: 기존 Qdrant RAG 처리
    - 후속 질문: 최근 대화 내역과 함께 처리
    """
    try:
        result = _answer_request(request)
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