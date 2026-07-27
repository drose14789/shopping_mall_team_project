from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Final


UNKNOWN: Final[str] = "unknown"
NONE: Final[str] = "none"


def normalize_text(text: str) -> str:
    """질문 비교를 위해 공백과 문장부호를 제거한다."""
    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        str(text).lower(),
    )


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


@dataclass(frozen=True)
class QuestionAnalysis:
    """사용자 질문을 구조화한 결과."""

    issue: str
    request: str
    history: str
    dispute: str
    symptom: str
    confidence: float
    route_key: str
    legacy_intent: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


ISSUE_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "defective_product": (
        "불량",
        "하자",
        "고장",
        "파손",
        "훼손",
        "깨져",
        "깨진",
        "망가져",
        "망가진",
        "찌그러져",
        "먹통",
        "작동하지않",
        "작동안",
        "켜지지않",
        "전원이안켜",
        "전원이켜지지않",
        "전원이들어오지않",
        "부팅되지않",
        "부팅안",
        "충전되지않",
        "충전안",
        "화면이나오지않",
        "화면안나오",
        "인식되지않",
        "인식안",
        "연결되지않",
        "연결안",
    ),
    "wrong_item": (
        "오배송",
        "잘못배송",
        "잘못배달",
        "주문한상품과다른",
        "주문한제품과다른",
        "주문한것과다른",
        "다른상품이배송",
        "다른제품이배송",
        "다른상품이왔",
        "다른제품이왔",
        "엉뚱한상품",
        "엉뚱한제품",
    ),
    "mismatch": (
        "상품설명과다른",
        "제품설명과다른",
        "광고내용과다른",
        "표시광고와다른",
        "계약내용과다른",
        "사진과다른",
        "설명과실제",
    ),
    "change_of_mind": (
        "단순변심",
        "마음에들지않",
        "마음에안들",
        "생각과달라",
        "필요없어",
        "취향에안맞",
    ),
    "out_of_stock": (
        "품절",
        "품절됐",
        "품절되",
        "재고없",
        "재고가없",
        "재고부족",
        "재고가부족",
        "재고소진",
        "재고가소진",
        "공급할수없",
        "배송할수없",
        "발송할수없",
    ),
    "return_obstruction": (
        "반품방해",
        "반품을방해",
        "반품절차를어렵",
        "반품을못하게",
        "청약철회방해",
        "세일상품반품불가",
        "할인상품반품불가",
        "특가상품반품불가",
        "세일상품은반품안",
        "할인상품은반품안",
        "특가상품은반품안",
        "세일이라며반품",
        "할인이라며반품",
        "특가라며반품",
        "세일상품이라며",
        "할인상품이라며",
        "특가상품이라며",
    ),
    "seller_information": (
        "판매자정보",
        "판매자신원",
        "사업자정보",
        "상호주소전화번호",
        "개인판매자정보",
    ),
    "privacy": (
        "개인정보",
        "개인정보제공",
        "개인정보파기",
        "제3자제공",
        "처리위탁",
        "택배회사에전달",
    ),
    "payment": (
        "카드결제",
        "현금결제",
        "결제취소",
        "결제금액",
        "총결제금액",
        "유료부가",
    ),
}


REQUEST_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "refund": (
        "환불",
        "환급",
        "환불받",
        "환급받",
        "돈을돌려",
        "돈돌려",
        "돌려받",
        "대금반환",
        "결제취소",
        "청약철회",
        "계약취소",
        "계약해제",
    ),
    "return": (
        "반품",
        "반환",
        "돌려보내",
        "청약철회",
    ),
    "exchange": (
        "교환",
        "교체",
        "새제품",
        "새상품",
    ),
    "return_cost": (
        "반품비",
        "반품배송비",
        "반송비",
        "반환비용",
        "택배비",
        "배송비",
    ),
    "deadline": (
        "언제까지",
        "언제환불",
        "언제환급",
        "언제돌려",
        "환불시점",
        "환급시점",
        "기한",
        "기간",
        "며칠",
        "몇일",
        "몇영업일",
        "3개월",
        "30일",
        "7일",
    ),
    "seller_information": (
        "판매자정보",
        "신원정보",
        "제공해야",
        "확인해야",
    ),
    "privacy": (
        "동의",
        "제공해도",
        "파기",
        "보관",
        "처리위탁",
    ),
    "payment": (
        "결제",
        "카드",
        "현금",
        "청구",
        "결제취소",
    ),
}


HISTORY_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "replacement": (
        "교환받은",
        "교환한",
        "교환된",
        "교환품",
        "교체받은",
        "교체한",
        "교체된",
        "교체품",
        "대체상품",
        "대체제품",
        "새상품으로교환",
        "새제품으로교환",
        "새상품으로교체",
        "새제품으로교체",
    ),
    "repair": (
        "수리받은",
        "수리한",
        "수리후",
        "수리했는데",
        "수리이력",
    ),
}


DISPUTE_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "seller_refusal": (
        "거절",
        "거부",
        "안해주",
        "못해주",
        "교환만",
        "수리만",
        "환불안",
        "환불못",
        "반품안",
        "반품못",
        "내지않겠",
        "부담하지않겠",
    ),
    "carrier_blame": (
        "택배회사책임",
        "택배사책임",
        "배송업체책임",
        "운송업체책임",
        "택배회사잘못",
        "택배사잘못",
        "배송업체잘못",
        "택배회사와해결",
        "택배사와해결",
        "배송업체와해결",
    ),
    "return_obstruction": (
        "반품방해",
        "반품을방해",
        "반품절차를어렵",
        "반품을못하게",
        "청약철회방해",
    ),
}


SYMPTOM_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "power_failure": (
        "전원이켜지지않",
        "전원이안켜",
        "전원이들어오지않",
        "전원안들어",
    ),
    "boot_failure": (
        "부팅되지않",
        "부팅안",
    ),
    "charging_failure": (
        "충전되지않",
        "충전안",
    ),
    "operation_failure": (
        "작동하지않",
        "작동안",
        "정상작동하지않",
        "먹통",
        "실행되지않",
        "실행안",
    ),
    "display_failure": (
        "화면이나오지않",
        "화면안나오",
    ),
    "connection_failure": (
        "연결되지않",
        "연결안",
        "인식되지않",
        "인식안",
    ),
    "physical_damage": (
        "파손",
        "깨져",
        "깨진",
        "망가져",
        "찌그러져",
        "훼손",
    ),
}


def find_category(
    normalized: str,
    categories: dict[str, tuple[str, ...]],
    *,
    default: str = UNKNOWN,
) -> str:
    """등록된 표현이 가장 먼저 발견되는 분류를 반환한다."""
    for category, terms in categories.items():
        if contains_any(normalized, terms):
            return category

    return default


def find_request(normalized: str) -> str:
    """
    질문 목적을 우선순위로 판별한다.

    '언제까지 반품'은 반품 자체보다 기한 질문으로 처리한다.
    """
    priority = (
        "return_cost",
        "deadline",
        "refund",
        "return",
        "exchange",
        "seller_information",
        "privacy",
        "payment",
    )

    for request in priority:
        if contains_any(
            normalized,
            REQUEST_TERMS[request],
        ):
            return request

    return UNKNOWN


def build_route_key(
    issue: str,
    request: str,
    history: str,
    dispute: str,
) -> str:
    values = [
        value
        for value in (history, issue, request, dispute)
        if value not in {UNKNOWN, NONE}
    ]

    return ".".join(values) if values else UNKNOWN


def build_legacy_intent(
    *,
    issue: str,
    request: str,
    history: str,
    dispute: str,
) -> str | None:
    """
    현재 rag_service.py의 주요 intent와 연결하기 위한 임시 호환값.

    새 구조가 안정될 때까지 기존 intent를 한 번에 삭제하지 않는다.
    """
    if (
        history == "replacement"
        and issue == "defective_product"
        and request == "refund"
    ):
        return "replacement_defective_refund"

    if (
        issue == "defective_product"
        and request == "return_cost"
        and dispute == "carrier_blame"
    ):
        return "carrier_blame_return_cost"

    if issue == "wrong_item" and request == "return_cost":
        return "wrong_item_return_cost"

    if issue == "defective_product" and request == "return_cost":
        return "defective_product_return_cost"

    if issue == "mismatch" and request == "deadline":
        return "mismatch_return_deadline"

    if issue == "change_of_mind" and request == "return":
        return "change_of_mind_return"

    if (
        issue == "out_of_stock"
        and request in {"refund", "deadline"}
    ):
        return "sold_out_refund"

    if issue == "return_obstruction":
        return "return_obstruction"

    return None


def calculate_confidence(
    *,
    issue: str,
    request: str,
    history: str,
    dispute: str,
    symptom: str,
) -> float:
    """
    분류 결과에 따른 간단한 내부 신뢰도.

    법률 판단의 신뢰도가 아니라 질문 구조 분석의 신뢰도다.
    """
    score = 0.0

    if issue != UNKNOWN:
        score += 0.45

    if request != UNKNOWN:
        score += 0.35

    if history != NONE:
        score += 0.08

    if dispute != NONE:
        score += 0.07

    if symptom != NONE:
        score += 0.05

    return round(min(score, 1.0), 2)


def analyze_question(question: str) -> QuestionAnalysis:
    """사용자 질문을 문제·요구·이력·분쟁·증상으로 분해한다."""
    normalized = normalize_text(question)

    if not normalized:
        raise ValueError("질문을 입력해주세요.")

    issue = find_category(
        normalized,
        ISSUE_TERMS,
    )

    # '반품절차'에는 문자열상 '품절'이 포함된다.
    # 반품 방해 표현이 확인되면 품절보다 우선해 분류한다.
    if contains_any(
        normalized,
        ISSUE_TERMS["return_obstruction"],
    ):
        issue = "return_obstruction"

    sale_terms = (
        "세일",
        "할인",
        "특가",
        "프로모션",
    )

    return_refusal_terms = (
        "반품불가",
        "반품이불가",
        "반품안",
        "반품이안",
        "반품할수없",
        "반품을거절",
        "반품거절",
        "반품을못",
        "무조건반품",
    )

    # 세일·할인·특가 상품이라는 이유와 반품 거절 표현이
    # 함께 나타나면 청약철회 방해 질문으로 우선 처리한다.
    if (
        contains_any(normalized, sale_terms)
        and contains_any(
            normalized,
            return_refusal_terms,
        )
    ):
        issue = "return_obstruction"

    request = find_request(normalized)

    history = find_category(
        normalized,
        HISTORY_TERMS,
        default=NONE,
    )

    dispute = find_category(
        normalized,
        DISPUTE_TERMS,
        default=NONE,
    )

    symptom = find_category(
        normalized,
        SYMPTOM_TERMS,
        default=NONE,
    )

    # 택배회사 책임 전가는 판매자 거절보다 구체적인 분쟁 유형이다.
    if contains_any(
        normalized,
        DISPUTE_TERMS["carrier_blame"],
    ):
        dispute = "carrier_blame"

    route_key = build_route_key(
        issue,
        request,
        history,
        dispute,
    )

    legacy_intent = build_legacy_intent(
        issue=issue,
        request=request,
        history=history,
        dispute=dispute,
    )

    confidence = calculate_confidence(
        issue=issue,
        request=request,
        history=history,
        dispute=dispute,
        symptom=symptom,
    )

    return QuestionAnalysis(
        issue=issue,
        request=request,
        history=history,
        dispute=dispute,
        symptom=symptom,
        confidence=confidence,
        route_key=route_key,
        legacy_intent=legacy_intent,
    )