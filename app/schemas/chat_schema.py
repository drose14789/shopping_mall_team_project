from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    """이전 대화 한 건의 데이터 형식."""

    role: Literal["user", "assistant"] = Field(
        ...,
        description="메시지를 작성한 주체",
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="이전 질문 또는 답변 내용",
    )


class ChatRequest(BaseModel):
    """사용자가 챗봇에 보내는 요청 형식."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="온라인 쇼핑몰 법률 또는 정책 관련 질문",
        examples=[
            "단순 변심으로도 반품할 수 있나요?"
        ],
    )

    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=10,
        description="현재 질문 이전의 최근 대화 내역",
    )


class SourceDocument(BaseModel):
    """Qdrant에서 검색한 출처 문서 형식."""

    rank: int
    heading: str
    source_file: str
    parent_id: str
    child_content: str
    parent_content: str
    dense_score: float
    rerank_score: float
    rank_group: str
    retrieved_by: list[str]


class ChatResponse(BaseModel):
    """챗봇이 반환하는 최종 응답 형식."""

    question: str
    answer: str
    intent: str | None = None
    sources: list[SourceDocument]