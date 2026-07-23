from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

from app.services.intent_router import (
    NONE,
    UNKNOWN,
    QuestionAnalysis,
    analyze_question,
)


@dataclass(frozen=True)
class SearchQueryPlan:
    """사용자 질문을 법률 검색용 문장으로 바꾼 결과."""

    original_question: str
    search_question: str
    route_key: str
    confidence: float
    legacy_intent: str | None
    used_template: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


INTENT_QUERY_TEMPLATES: Final[dict[str, str]] = {
    "replacement_defective_refund": (
        "교환 또는 교체받은 상품에 다시 성능·기능상 하자가 "
        "발생한 경우 소비자가 환불 또는 청약철회를 요구할 수 "
        "있는 기준"
    ),
    "carrier_blame_return_cost": (
        "배송 중 파손된 상품에 대해 판매자가 택배회사 책임을 "
        "이유로 반품 배송비 부담을 거절할 수 있는지에 관한 기준"
    ),
    "wrong_item_return_cost": (
        "주문한 상품과 다른 제품이 배송된 경우 반품에 필요한 "
        "배송비를 누가 부담하는지에 관한 기준"
    ),
    "defective_product_return_cost": (
        "불량 또는 하자가 있는 상품을 반품할 때 반환 배송비를 "
        "누가 부담하는지에 관한 기준"
    ),
    "mismatch_return_deadline": (
        "상품이 표시·광고 또는 계약 내용과 다르게 제공된 경우 "
        "소비자가 청약철회할 수 있는 기간과 기한"
    ),
    "change_of_mind_return": (
        "온라인 구매 상품을 단순 변심으로 반품할 수 있는 기간과 "
        "소비자가 부담해야 하는 반환 비용"
    ),
    "out_of_stock_refund": (
        "판매자가 상품 품절로 공급할 수 없는 경우 소비자에게 "
        "통지하고 결제대금을 환급해야 하는 기한"
    ),
    "return_obstruction": (
        "온라인 쇼핑몰이 소비자의 반품이나 청약철회를 방해하는 "
        "행위와 판매자의 금지행위"
    ),
}


ISSUE_QUERY_PHRASES: Final[dict[str, str]] = {
    "defective_product": "상품의 불량·하자 또는 성능·기능상 문제",
    "wrong_item": "주문한 상품과 다른 상품의 배송",
    "mismatch": "표시·광고 또는 계약 내용과 다른 상품 제공",
    "change_of_mind": "소비자의 단순 변심",
    "out_of_stock": "상품 품절 또는 공급 불가능",
    "return_obstruction": "판매자의 반품 또는 청약철회 방해",
    "seller_information": "온라인 판매자의 신원정보 제공",
    "privacy": "온라인 쇼핑몰의 개인정보 처리",
    "payment": "온라인 쇼핑몰 결제 처리",
}


REQUEST_QUERY_PHRASES: Final[dict[str, str]] = {
    "refund": "환불 또는 대금 환급 가능 여부와 요건",
    "return": "반품 또는 청약철회 가능 여부와 요건",
    "exchange": "교환 또는 교체 가능 여부와 요건",
    "return_cost": "반품 배송비 또는 반환 비용의 부담 주체",
    "deadline": "소비자가 권리를 행사할 수 있는 기간과 기한",
    "seller_information": "소비자에게 제공해야 하는 판매자 정보",
    "privacy": "개인정보 동의·제공·보관·파기 기준",
    "payment": "결제·취소·환급 처리 기준",
}


HISTORY_QUERY_PHRASES: Final[dict[str, str]] = {
    "replacement": "교환 또는 교체받은 상품",
    "repair": "수리받은 상품",
}


DISPUTE_QUERY_PHRASES: Final[dict[str, str]] = {
    "seller_refusal": "판매자가 소비자의 요구를 거절하는 경우",
    "carrier_blame": "판매자가 택배회사 또는 배송업체에 책임을 돌리는 경우",
    "return_obstruction": "판매자가 반품 절차를 방해하는 경우",
}


SYMPTOM_QUERY_PHRASES: Final[dict[str, str]] = {
    "power_failure": "전원이 켜지지 않는 작동 불량",
    "boot_failure": "부팅되지 않는 작동 불량",
    "charging_failure": "충전되지 않는 기능상 하자",
    "operation_failure": "정상적으로 작동하지 않는 기능상 하자",
    "display_failure": "화면이 표시되지 않는 기능상 하자",
    "connection_failure": "연결 또는 인식되지 않는 기능상 하자",
    "physical_damage": "파손 또는 훼손된 상태",
}


def _append_unique(
    parts: list[str],
    value: str | None,
) -> None:
    if value and value not in parts:
        parts.append(value)


def build_fallback_search_question(
    analysis: QuestionAnalysis,
) -> str:
    """
    전용 템플릿이 없는 질문을 구조화 정보로 조합한다.

    질문을 그대로 검색하지 않고 법률 문서에서 사용될 가능성이
    높은 표현으로 바꾼다.
    """
    parts: list[str] = []

    if analysis.history not in {NONE, UNKNOWN}:
        _append_unique(
            parts,
            HISTORY_QUERY_PHRASES.get(analysis.history),
        )

    if analysis.issue != UNKNOWN:
        _append_unique(
            parts,
            ISSUE_QUERY_PHRASES.get(analysis.issue),
        )

    if analysis.symptom not in {NONE, UNKNOWN}:
        _append_unique(
            parts,
            SYMPTOM_QUERY_PHRASES.get(analysis.symptom),
        )

    if analysis.request != UNKNOWN:
        _append_unique(
            parts,
            REQUEST_QUERY_PHRASES.get(analysis.request),
        )

    if analysis.dispute not in {NONE, UNKNOWN}:
        _append_unique(
            parts,
            DISPUTE_QUERY_PHRASES.get(analysis.dispute),
        )

    if not parts:
        return (
            "온라인 쇼핑몰 거래에서 소비자 권리와 판매자 의무에 "
            "관한 전자상거래 소비자보호 기준"
        )

    return " ".join(parts) + " 관련 전자상거래 소비자보호 기준"


def build_search_query(
    question: str,
    analysis: QuestionAnalysis | None = None,
) -> SearchQueryPlan:
    """사용자 질문을 Qdrant 검색용 법률 문장으로 변환한다."""
    cleaned_question = str(question).strip()

    if not cleaned_question:
        raise ValueError("질문을 입력해주세요.")

    resolved_analysis = (
        analysis
        if analysis is not None
        else analyze_question(cleaned_question)
    )

    template = None

    if resolved_analysis.legacy_intent:
        template = INTENT_QUERY_TEMPLATES.get(
            resolved_analysis.legacy_intent
        )

    if template:
        search_question = template
        used_template = True
    else:
        search_question = build_fallback_search_question(
            resolved_analysis
        )
        used_template = False

    return SearchQueryPlan(
        original_question=cleaned_question,
        search_question=search_question,
        route_key=resolved_analysis.route_key,
        confidence=resolved_analysis.confidence,
        legacy_intent=resolved_analysis.legacy_intent,
        used_template=used_template,
    )


def get_search_question(
    question: str,
    analysis: QuestionAnalysis | None = None,
) -> str:
    """검색 문장 문자열만 필요한 곳에서 사용하는 편의 함수."""
    return build_search_query(
        question,
        analysis,
    ).search_question