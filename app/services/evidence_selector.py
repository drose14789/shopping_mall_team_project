from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final


MAX_EVIDENCE_SENTENCES: Final[int] = 6
MAX_EVIDENCE_LENGTH: Final[int] = 2400


SUPPORTED_INTENTS: Final[set[str]] = {
    "replacement_defective_refund",
}


REPLACEMENT_REFUND_POSITIVE_TERMS: Final[
    tuple[tuple[str, int], ...]
] = (
    ("교환", 3),
    ("교체", 3),
    ("다시", 2),
    ("하자", 4),
    ("불량", 4),
    ("고장", 4),
    ("작동", 3),
    ("성능", 3),
    ("기능", 3),
    ("표시·광고", 4),
    ("표시광고", 4),
    ("계약 내용과 다르게", 5),
    ("계약내용과 다르게", 5),
    ("청약철회", 3),
    ("환불", 4),
    ("환급", 4),
    ("3개월", 5),
    ("30일", 5),
    ("3영업일", 5),
    ("반환받은", 3),
    ("대금을 환급", 4),
)


REPLACEMENT_REFUND_EXCLUDED_TERMS: Final[
    tuple[str, ...]
] = (
    "단순 변심",
    "단순변심",
    "7일 이내",
    "7일이내",
    "포장을 훼손",
    "포장 훼손",
    "포장훼손",
    "원본인 재화",
    "가치가 현저히 감소",
    "멸실 또는 훼손",
    "구매 시의 배송비",
    "구매시의 배송비",
    "소비자가 부담",
    "이용자가 부담",
    "반환 비용을 부담",
    "반환비용을 부담",
)


@dataclass(frozen=True)
class EvidenceSelectionResult:
    selected_documents: list[dict[str, Any]]
    excluded_document_count: int
    selected_sentence_count: int
    intent: str


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def get_document_content(
    document: dict[str, Any],
) -> str:
    for key in (
        "parent_content",
        "content",
        "text",
    ):
        value = str(document.get(key, "")).strip()

        if value:
            return value

    return ""


def split_evidence_units(text: str) -> list[str]:
    """
    문서 본문을 문장 또는 표의 행 단위로 나눈다.

    마침표뿐 아니라 줄바꿈, Markdown 표 구분도 함께 처리한다.
    """
    cleaned = str(text).replace("\r\n", "\n")

    raw_units = re.split(
        r"(?<=[.!?。])\s+|\n+",
        cleaned,
    )

    units: list[str] = []

    for raw_unit in raw_units:
        unit = normalize_space(raw_unit)

        if not unit:
            continue

        # Markdown 표 구분선은 근거 문장으로 사용하지 않는다.
        if re.fullmatch(
            r"[\|\-:\s]+",
            unit,
        ):
            continue

        units.append(unit)

    return units


def contains_excluded_term(
    sentence: str,
    intent: str,
) -> bool:
    if intent != "replacement_defective_refund":
        return False

    return any(
        term in sentence
        for term in REPLACEMENT_REFUND_EXCLUDED_TERMS
    )


def score_sentence(
    sentence: str,
    intent: str,
) -> int:
    if intent != "replacement_defective_refund":
        return 0

    if contains_excluded_term(
        sentence,
        intent,
    ):
        return -100

    score = 0

    for term, weight in REPLACEMENT_REFUND_POSITIVE_TERMS:
        if term in sentence:
            score += weight

    # 청약철회라는 단어만 있고 구체 조건이 없으면 낮은 점수만 준다.
    if (
        "청약철회" in sentence
        and not any(
            marker in sentence
            for marker in (
                "3개월",
                "30일",
                "계약 내용과 다르게",
                "계약내용과 다르게",
                "표시·광고",
                "표시광고",
                "환급",
                "반환받은",
            )
        )
    ):
        score = min(score, 2)

    return score


def select_relevant_sentences(
    content: str,
    intent: str,
    *,
    max_sentences: int = MAX_EVIDENCE_SENTENCES,
) -> list[str]:
    """
    질문 intent와 직접 관련된 문장만 점수순으로 선택한다.
    """
    if intent not in SUPPORTED_INTENTS:
        return split_evidence_units(content)

    scored_units: list[tuple[int, int, str]] = []

    for index, sentence in enumerate(
        split_evidence_units(content)
    ):
        score = score_sentence(
            sentence,
            intent,
        )

        if score >= 3:
            scored_units.append(
                (
                    score,
                    index,
                    sentence,
                )
            )

    # 점수가 높은 문장을 우선 고른 뒤 원래 문서 순서로 복원한다.
    top_units = sorted(
        scored_units,
        key=lambda item: (
            -item[0],
            item[1],
        ),
    )[:max_sentences]

    selected_in_original_order = sorted(
        top_units,
        key=lambda item: item[1],
    )

    return [
        sentence
        for _, _, sentence in selected_in_original_order
    ]


def select_evidence_documents(
    question: str,
    intent: str,
    documents: list[dict[str, Any]],
) -> EvidenceSelectionResult:
    """
    검색 문서별로 관련 문장만 남긴 복사본을 반환한다.

    answer_builder가 parent_content를 우선 읽으므로,
    선택된 문장만 parent_content에 넣는다.
    """
    del question  # 현재 버전은 intent 기준으로 선별한다.

    if intent not in SUPPORTED_INTENTS:
        return EvidenceSelectionResult(
            selected_documents=[
                dict(document)
                for document in documents
            ],
            excluded_document_count=0,
            selected_sentence_count=0,
            intent=intent,
        )

    selected_documents: list[dict[str, Any]] = []
    excluded_document_count = 0
    selected_sentence_count = 0

    for document in documents:
        content = get_document_content(document)

        if not content:
            excluded_document_count += 1
            continue

        selected_sentences = select_relevant_sentences(
            content,
            intent,
        )

        if not selected_sentences:
            excluded_document_count += 1
            continue

        selected_content = "\n".join(
            selected_sentences
        )[:MAX_EVIDENCE_LENGTH]

        selected_document = dict(document)
        selected_document["parent_content"] = selected_content
        selected_document["selected_evidence"] = selected_sentences
        selected_document["evidence_sentence_count"] = len(
            selected_sentences
        )

        selected_documents.append(
            selected_document
        )
        selected_sentence_count += len(
            selected_sentences
        )

    return EvidenceSelectionResult(
        selected_documents=selected_documents,
        excluded_document_count=excluded_document_count,
        selected_sentence_count=selected_sentence_count,
        intent=intent,
    )


def get_selected_evidence_documents(
    question: str,
    intent: str,
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """선별된 문서 목록만 반환하는 편의 함수."""
    return select_evidence_documents(
        question=question,
        intent=intent,
        documents=documents,
    ).selected_documents