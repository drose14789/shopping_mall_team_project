from __future__ import annotations

import re
from typing import Any

from app.services.ollama_service import generate_general_answer
from app.services.rag_service import answer_question


FIXED_GENERAL_RESPONSES = {
    # 인사
    "안녕": "안녕하세요! 온라인 쇼핑 관련해서 궁금한 점을 말씀해주세요.",
    "안녕하세요": "안녕하세요! 온라인 쇼핑 관련해서 궁금한 점을 말씀해주세요.",
    "안녕하십니까": "안녕하세요! 무엇을 도와드릴까요?",
    "반가워": "반가워요! 온라인 쇼핑 관련 질문이 있으면 말씀해주세요.",
    "반가워요": "반가워요! 온라인 쇼핑 관련 질문이 있으면 말씀해주세요.",
    "반갑습니다": "반갑습니다! 무엇을 도와드릴까요?",
    "좋은 아침": "좋은 아침이에요! 오늘도 궁금한 점이 있으면 말씀해주세요.",
    "좋은 아침이에요": "좋은 아침이에요! 무엇을 도와드릴까요?",
    "좋은 저녁": "좋은 저녁이에요! 온라인 쇼핑 관련 질문이 있으면 말씀해주세요.",
    "좋은 저녁이에요": "좋은 저녁이에요! 무엇을 도와드릴까요?",

    # 감사와 마무리
    "고마워": "도움이 되었다니 다행이에요.",
    "고마워요": "도움이 되었다니 다행이에요.",
    "고맙습니다": "도움이 되었다니 다행입니다.",
    "감사해": "도움이 되었다니 다행이에요.",
    "감사해요": "도움이 되었다니 다행이에요.",
    "감사합니다": "도움이 되었다니 다행입니다.",
    "수고했어": "감사해요. 더 궁금한 점이 있으면 말씀해주세요.",
    "수고했어요": "감사해요. 더 궁금한 점이 있으면 말씀해주세요.",
    "수고하셨습니다": "감사합니다. 더 궁금한 점이 있으면 말씀해주세요.",
    "잘 부탁해": "네, 정확하고 이해하기 쉽게 안내해드릴게요.",
    "잘 부탁해요": "네, 정확하고 이해하기 쉽게 안내해드릴게요.",
    "잘 부탁드립니다": "네, 정확하고 이해하기 쉽게 안내해드리겠습니다.",
    "좋은 하루 보내": "감사해요. 좋은 하루 보내세요!",
    "좋은 하루 보내세요": "감사합니다. 좋은 하루 보내세요!",

    # 짧은 일상 대화
    "잘 지내": "네, 잘 지내고 있어요. 무엇을 도와드릴까요?",
    "잘 지내요": "네, 잘 지내고 있어요. 무엇을 도와드릴까요?",
    "잘 지냈어": "네, 잘 지냈어요. 궁금한 점을 말씀해주세요.",
    "잘 지냈어요": "네, 잘 지냈어요. 궁금한 점을 말씀해주세요.",
    "오늘 어때": "저는 기분을 느끼지는 않지만, 도와드릴 준비가 되어 있어요.",
    "오늘 기분 어때": "저는 기분을 느끼지는 않지만, 즐겁게 도와드릴 준비가 되어 있어요.",
    "기분 어때": "저는 기분을 느끼지는 않지만, 도와드릴 준비가 되어 있어요.",
    "뭐해": "온라인 쇼핑 관련 질문을 도와드리기 위해 기다리고 있어요.",
    "뭐 하고 있어": "온라인 쇼핑 관련 질문을 도와드리기 위해 기다리고 있어요.",
    "뭐하고 있어": "온라인 쇼핑 관련 질문을 도와드리기 위해 기다리고 있어요.",
    "심심해": "온라인 쇼핑과 관련해 궁금했던 내용을 질문해보세요.",
}


OLLAMA_GENERAL_CHAT_PHRASES = {
    "재미있는 이야기 해줘",
    "재밌는 이야기 해줘",
}


BOT_INFO_QUESTIONS = {
    "너는 누구야",
    "넌 누구야",
    "누구세요",
    "무슨 일을 해",
    "무슨 일을 하나요",
    "어떤 일을 해",
    "어떤 질문을 할 수 있어",
    "어떤 질문을 할 수 있나요",
    "무엇을 물어볼 수 있어",
    "뭘 물어볼 수 있어",
    "도와줄 수 있는 게 뭐야",
    "무엇을 도와줄 수 있어",
    "뭘 도와줄 수 있어",
    "사용 방법을 알려줘",
}


BOT_INFO_ANSWER = (
    "저는 온라인 쇼핑몰 법률·정책 안내 챗봇입니다. "
    "반품, 환불, 품절, 판매자 정보, 반품 비용과 같은 "
    "온라인 쇼핑 관련 질문에 근거 문서를 바탕으로 답변합니다.\n\n"
    "간단한 인사나 일상 대화에도 답할 수 있지만, "
    "법률과 무관한 전문 지식이나 최신 정보는 정확하게 안내하기 어려울 수 있습니다."
)


def normalize_question(question: str) -> str:
    """
    문장을 비교하기 위해 공백과 문장부호를 제거합니다.
    """
    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        question.lower(),
    )


def build_normalized_phrase_map(
    responses: dict[str, str],
) -> dict[str, str]:
    """
    고정 응답 사전을 비교하기 쉬운 형태로 변환합니다.
    """
    return {
        normalize_question(question): answer
        for question, answer in responses.items()
    }


def matches_registered_phrase(
    question: str,
    phrases: set[str],
) -> bool:
    """
    질문이 등록된 표현 중 하나와 정확히 일치하는지 확인합니다.
    """
    normalized = normalize_question(question)

    return normalized in {
        normalize_question(phrase)
        for phrase in phrases
    }


def get_fixed_general_answer(
    question: str,
) -> str | None:
    """
    등록된 짧은 일반 대화에 대한 고정 답변을 반환합니다.
    """
    normalized_responses = build_normalized_phrase_map(
        FIXED_GENERAL_RESPONSES
    )

    return normalized_responses.get(
        normalize_question(question)
    )


def is_ollama_general_chat(question: str) -> bool:
    """
    자유로운 생성이 필요한 일부 일반 대화만 Ollama로 보냅니다.
    """
    return matches_registered_phrase(
        question=question,
        phrases=OLLAMA_GENERAL_CHAT_PHRASES,
    )


def is_bot_info_question(question: str) -> bool:
    """
    챗봇의 역할이나 사용 방법을 묻는 질문인지 확인합니다.
    """
    return matches_registered_phrase(
        question=question,
        phrases=BOT_INFO_QUESTIONS,
    )


def get_recent_user_messages(
    history: list[dict[str, str]],
    limit: int = 3,
) -> list[str]:
    """
    최근 사용자 질문만 추출합니다.
    """
    user_messages = [
        str(message.get("content", "")).strip()
        for message in history
        if message.get("role") == "user"
        and str(message.get("content", "")).strip()
    ]

    return user_messages[-limit:]


def is_shipping_cost_followup(question: str) -> bool:
    """
    현재 질문이 배송비 또는 반품비를 묻는 짧은 후속 질문인지 확인합니다.
    """
    normalized = normalize_question(question)

    cost_terms = (
        "배송비",
        "택배비",
        "반품비",
        "반송비",
        "비용",
    )

    question_terms = (
        "누가",
        "부담",
        "내야",
        "내나요",
        "내는",
        "얼마",
        "어떻게",
    )

    has_cost_term = any(
        term in normalized
        for term in cost_terms
    )

    has_question_term = any(
        term in normalized
        for term in question_terms
    )

    return has_cost_term and has_question_term


def resolve_followup_question(
    question: str,
    history: list[dict[str, str]],
) -> str:
    """
    최근 사용자 질문을 참고해 짧은 후속 질문을 독립적인 질문으로 바꿉니다.

    현재 단계에서는 반품 배송비 후속 질문만 처리합니다.
    """
    if not history or not is_shipping_cost_followup(question):
        return question

    recent_user_messages = get_recent_user_messages(
        history=history,
        limit=3,
    )

    if not recent_user_messages:
        return question

    previous_context = normalize_question(
        " ".join(recent_user_messages)
    )

    change_of_mind_terms = (
        "단순변심",
        "마음이바뀌",
        "마음에들지않",
        "구매후회",
        "필요없",
    )

    mismatch_terms = (
        "상품설명과다르",
        "사진과다르",
        "광고와다르",
        "실제상품이다르",
        "불량",
        "하자",
        "오배송",
    )

    return_terms = (
        "반품",
        "청약철회",
        "돌려보",
        "환불",
    )

    if any(
        term in previous_context
        for term in change_of_mind_terms
    ):
        return "단순 변심 반품 배송비는 누가 부담하나요?"

    if any(
        term in previous_context
        for term in mismatch_terms
    ):
        return (
            "상품 설명과 실제 상품이 다르거나 하자가 있는 경우 "
            "반품 배송비는 누가 부담하나요?"
        )

    if any(
        term in previous_context
        for term in return_terms
    ):
        return "반품 배송비는 누가 부담하나요?"

    return question


def answer_chat(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    질문 유형에 따라 답변 경로를 선택합니다.

    - 챗봇 소개 질문: 고정 답변
    - 짧은 인사·감사·일상 대화: 고정 답변
    - 자유로운 일부 일반 대화: 빠른 1B 모델
    - 반품 배송비 후속 질문: 이전 질문을 반영해 보완
    - 나머지 질문: 기존 법률 RAG
    """
    cleaned_question = " ".join(question.split())

    if not cleaned_question:
        raise ValueError("질문을 입력해주세요.")

    history = history or []

    if is_bot_info_question(cleaned_question):
        return {
            "question": cleaned_question,
            "answer": BOT_INFO_ANSWER,
            "intent": "bot_info",
            "sources": [],
        }

    fixed_answer = get_fixed_general_answer(
        cleaned_question
    )

    if fixed_answer is not None:
        return {
            "question": cleaned_question,
            "answer": fixed_answer,
            "intent": "general_chat",
            "sources": [],
        }

    if is_ollama_general_chat(cleaned_question):
        return {
            "question": cleaned_question,
            "answer": generate_general_answer(
                cleaned_question
            ),
            "intent": "general_chat",
            "sources": [],
        }

    resolved_question = resolve_followup_question(
        question=cleaned_question,
        history=history,
    )

    result = answer_question(resolved_question)

    # 화면에는 사용자가 실제로 입력한 질문을 유지합니다.
    result["question"] = cleaned_question

    return result