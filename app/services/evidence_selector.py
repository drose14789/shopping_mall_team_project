from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final

from app.services.legal_rules import (
    get_legal_rule,
)


MAX_EVIDENCE_SENTENCES: Final[int] = 6
MAX_EVIDENCE_LENGTH: Final[int] = 2400
MIN_EVIDENCE_SCORE: Final[int] = 3


@dataclass(frozen=True)
class EvidenceSelectionResult:
    selected_documents: list[dict[str, Any]]
    excluded_document_count: int
    selected_sentence_count: int
    intent: str


def normalize_space(text: str) -> str:
    """연속 공백을 하나로 정리한다."""
    return re.sub(
        r"\s+",
        " ",
        str(text),
    ).strip()


def get_document_content(
    document: dict[str, Any],
) -> str:
    """Qdrant 결과에서 사용할 본문을 안전하게 가져온다."""
    for key in (
        "parent_content",
        "child_content",
        "content",
        "text",
        "excerpt",
        "snippet",
    ):
        value = str(document.get(key, "")).strip()

        if value:
            return value

    return ""


def split_evidence_units(text: str) -> list[str]:
    """
    문서 본문을 문장 또는 Markdown 표의 행 단위로 나눈다.
    """
    cleaned = str(text).replace(
        "\r\n",
        "\n",
    )

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
    """legal_rules.py에 등록된 제외 표현인지 확인한다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return False

    return any(
        term in sentence
        for term in rule.excluded_evidence_terms
    )


def score_sentence(
    sentence: str,
    intent: str,
) -> int:
    """intent 규칙의 가중치로 근거 문장을 채점한다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return 0

    if contains_excluded_term(
        sentence,
        intent,
    ):
        return -100

    score = 0

    for term, weight in rule.positive_evidence_terms:
        if term in sentence:
            score += weight

    # return_cost는 청약철회와 비용 부담의 관계 자체가 핵심이다.
    # 다른 intent에서는 구체 조건 없이 '청약철회'만 있는 문장이
    # 높은 점수를 받지 않도록 제한한다.
    if (
        intent != "return_cost"
        and "청약철회" in sentence
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
    """질문 intent와 직접 관련된 문장만 점수순으로 선택한다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return split_evidence_units(content)

    scored_units: list[tuple[int, int, str]] = []

    for index, sentence in enumerate(
        split_evidence_units(content)
    ):
        score = score_sentence(
            sentence,
            intent,
        )

        if score >= MIN_EVIDENCE_SCORE:
            scored_units.append(
                (
                    score,
                    index,
                    sentence,
                )
            )

    # 점수가 높은 문장을 고른 뒤 원래 문서 순서로 복원한다.
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
    선별된 문장만 parent_content에 저장한다.
    """
    del question

    rule = get_legal_rule(intent)

    if rule is None:
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
        selected_document["selected_evidence"] = (
            selected_sentences
        )
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