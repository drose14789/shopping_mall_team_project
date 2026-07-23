from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final

from app.services.intent_router import normalize_text


UNKNOWN_PRODUCT_CATEGORY: Final[str] = "unknown"


PRODUCT_CATEGORY_TERMS: Final[
    dict[str, tuple[str, ...]]
] = {
    "computer_software": (
        "소프트웨어",
        "프로그램",
        "앱",
        "애플리케이션",
        "게임소프트웨어",
        "라이선스",
    ),
    "medicine_chemical": (
        "의약품",
        "약품",
        "약",
        "화학제품",
        "세제",
        "살충제",
    ),
    "industrial_goods": (
        "공산품",
        "전자제품",
        "가전제품",
        "노트북",
        "컴퓨터",
        "모니터",
        "휴대폰",
        "스마트폰",
        "태블릿",
        "이어폰",
        "헤드폰",
        "충전기",
        "카메라",
        "프린터",
        "가구",
    ),
}


DOCUMENT_CATEGORY_MARKERS: Final[
    dict[str, tuple[str, ...]]
] = {
    "computer_software": (
        "컴퓨터소프트웨어",
    ),
    "medicine_chemical": (
        "의약품및화학제품",
    ),
    "industrial_goods": (
        "공산품",
    ),
}


@dataclass(frozen=True)
class DocumentFilterResult:
    kept_documents: list[dict[str, Any]]
    excluded_documents: list[dict[str, Any]]
    product_category: str

    @property
    def product_category_known(self) -> bool:
        return self.product_category != UNKNOWN_PRODUCT_CATEGORY


def detect_product_category(question: str) -> str:
    """질문에 명시된 상품 종류를 제한적으로 판별한다."""
    normalized = normalize_text(question)

    for category, terms in PRODUCT_CATEGORY_TERMS.items():
        if any(
            normalize_text(term) in normalized
            for term in terms
        ):
            return category

    return UNKNOWN_PRODUCT_CATEGORY


def build_document_text(
    document: dict[str, Any],
) -> str:
    """문서 판별에 필요한 제목과 파일명을 하나로 합친다."""
    values = (
        document.get("heading", ""),
        document.get("section", ""),
        document.get("title", ""),
        document.get("source_file", ""),
    )

    return normalize_text(
        " ".join(str(value) for value in values)
    )


def is_item_specific_standard(
    document: dict[str, Any],
) -> bool:
    """
    소비자분쟁해결기준의 특정 품목별 해결기준 표인지 판별한다.

    일반 원칙이나 전자상거래법 문서는 제외 대상이 아니다.
    """
    heading = str(document.get("heading", ""))
    normalized = build_document_text(document)

    has_item_standard_marker = (
        "품목별해결기준" in normalized
        and "별표" in normalized
    )

    has_numbered_category = bool(
        re.search(
            r"(?:^|>)\s*\d+\.\s*[^>]+",
            heading,
        )
    )

    return (
        "소비자분쟁해결기준" in normalized
        and has_item_standard_marker
        and has_numbered_category
    )


def detect_document_category(
    document: dict[str, Any],
) -> str:
    """특정 품목표가 어느 상품군에 해당하는지 판별한다."""
    normalized = build_document_text(document)

    for category, markers in DOCUMENT_CATEGORY_MARKERS.items():
        if any(
            normalize_text(marker) in normalized
            for marker in markers
        ):
            return category

    return UNKNOWN_PRODUCT_CATEGORY


def filter_documents_for_question(
    question: str,
    documents: list[dict[str, Any]],
) -> DocumentFilterResult:
    """
    질문에 제품 종류가 없으면 특정 품목별 해결기준 표를 제외한다.

    제품 종류가 명확한 경우에도 해당 상품군의 표만 남기고,
    전자상거래법·표준약관·일반 해결기준은 항상 유지한다.
    """
    product_category = detect_product_category(question)

    kept_documents: list[dict[str, Any]] = []
    excluded_documents: list[dict[str, Any]] = []

    for document in documents:
        if not is_item_specific_standard(document):
            kept_documents.append(document)
            continue

        if product_category == UNKNOWN_PRODUCT_CATEGORY:
            excluded_documents.append(document)
            continue

        document_category = detect_document_category(document)

        if document_category == product_category:
            kept_documents.append(document)
        else:
            excluded_documents.append(document)

    return DocumentFilterResult(
        kept_documents=kept_documents,
        excluded_documents=excluded_documents,
        product_category=product_category,
    )


def get_filtered_documents(
    question: str,
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """필터링된 문서 목록만 반환하는 편의 함수."""
    return filter_documents_for_question(
        question,
        documents,
    ).kept_documents