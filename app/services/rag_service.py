from __future__ import annotations

import re
from typing import Any

from app.services.answer_builder import build_hybrid_answer
from app.services.document_filter import (
    filter_documents_for_question,
)
from app.services.evidence_selector import (
    select_evidence_documents,
)
from app.services.intent_router import analyze_question
from app.services.legal_rules import get_legal_rule
from app.services.query_builder import build_search_query
from app.services.ollama_service import generate_answer
from app.services.qdrant_service import search_documents


SEARCH_TOP_K = 5
MAX_CONTEXT_DOCUMENTS = 3
MIN_RERANK_SCORE = 0.1
RELATIVE_SCORE_RATIO = 0.25
MAX_DOCUMENT_LENGTH = 4000
STRUCTURED_INTENT_MIN_CONFIDENCE = 0.8
GENERAL_SEARCH_TOP_K = 8


GENERAL_LEGAL_QUERY_TEMPLATES = {
    "replacement_defective_refund": (
        "전자상거래법과 전자상거래 표준약관에서 상품이 "
        "표시·광고 또는 계약 내용과 다르게 제공된 경우의 "
        "청약철회와 환불 가능 기간 및 판매자 의무"
    ),
    "mismatch_return_deadline": (
        "전자상거래법과 전자상거래 표준약관에서 상품이 "
        "표시·광고 또는 계약 내용과 다르게 제공된 경우의 "
        "청약철회 기간과 반품 기한"
    ),
    "wrong_item_return_cost": (
        "전자상거래법과 전자상거래 표준약관에서 주문한 상품과 "
        "다른 상품이 배송된 경우 반환 비용의 부담 주체"
    ),
    "return_cost": (
        "전자상거래법 제18조에 따른 단순 변심 청약철회와 "
        "표시·광고 또는 계약 내용과 다른 상품의 반환 비용 "
        "부담 주체 및 위약금·손해배상 청구 제한"
    ),
    "carrier_blame_return_cost": (
        "전자상거래법과 전자상거래 표준약관에서 계약 내용과 "
        "다른 상품 또는 배송 중 파손 상품의 반환 비용과 "
        "판매자 책임"
    ),
    "defective_product_return_cost": (
        "전자상거래법과 전자상거래 표준약관에서 불량 또는 "
        "계약 내용과 다른 상품을 반환할 때 배송비 부담 기준"
    ),
    "change_of_mind_return": (
        "전자상거래법과 전자상거래 표준약관에서 단순 변심으로 "
        "청약철회할 수 있는 기간과 반환 비용"
    ),
    "sold_out_refund": (
        "전자상거래법과 전자상거래 표준약관에서 상품 품절 또는 "
        "재고 부족으로 공급할 수 없는 경우 소비자에게 지체 없이 "
        "알리고, 선결제 대금을 지급받은 날부터 3영업일 이내에 "
        "환급하거나 환급에 필요한 조치를 해야 하는 기준"
    ),
    "return_obstruction": (
        "전자상거래법상 판매자가 거짓 또는 과장된 사실을 알리거나 "
        "기만적인 방법으로 소비자의 청약철회 또는 계약 해지를 "
        "방해해서는 안 되는 기준과, 세일·특가 상품의 일률적 "
        "반품 제한, 법정 청약철회 기간의 임의 축소, 반환 배송비 "
        "외 인건비·운송비·포장비·보관비·취소수수료·반품위약금 "
        "등 추가 금액 요구 금지 사례"
    ),
}


SYSTEM_PROMPT = """
당신은 온라인 쇼핑몰 법률 및 정책 안내 챗봇입니다.

다음 규칙을 반드시 지키세요.

1. 제공된 검색 문서에 직접 근거하여 답변하세요.
2. 사용자 질문과 관련 없는 문서는 사용하지 마세요.
3. 모든 검색 문서를 반드시 사용할 필요는 없습니다.
4. 질문과 직접 관련된 문서만 선택하여 답변하세요.
5. 문서에 없는 내용을 추측하거나 만들어내지 마세요.
6. 핵심 결론을 먼저 간결하게 설명하세요.
7. 기간, 금액, 조건 등의 수치는 문서 내용 그대로 작성하세요.
8. 답변 본문에는 출처 번호나 문서명을 표시하지 마세요.
9. 근거가 부족하면 확인할 수 없다고 답변하세요.
10. 서로 다른 상품이나 분쟁 유형의 내용을 임의로 결합하지 마세요.
11. 같은 내용을 여러 문장으로 반복하지 마세요.
12. 환급 기한, 반품 가능 기간, 비용 부담 기준을 서로 혼동하지 마세요.
""".strip()


def build_general_legal_search_question(
    original_question: str,
    structured_intent: str | None,
) -> str:
    """
    특정 품목표만 검색된 경우 일반 법률 문서를 찾기 위한
    재검색 문장을 만든다.
    """
    if structured_intent:
        template = GENERAL_LEGAL_QUERY_TEMPLATES.get(
            structured_intent
        )

        if template:
            return template

    return (
        "전자상거래법과 전자상거래 표준약관에 따른 온라인 쇼핑몰 "
        "소비자의 청약철회·반품·환불 권리와 판매자의 일반 의무 "
        f"관련 질문: {original_question}"
    )


def resolve_structured_intent(
    question: str,
) -> str | None:
    """
    intent_router의 구조화 분석 결과를 기존 intent 이름으로 변환한다.

    분석 신뢰도가 낮거나 아직 연결되지 않은 질문은 None을 반환하여
    기존 is_* 판별 함수가 그대로 처리하게 한다.
    """
    try:
        analysis = analyze_question(question)
    except (TypeError, ValueError):
        return None

    if (
        analysis.confidence
        < STRUCTURED_INTENT_MIN_CONFIDENCE
    ):
        return None

    return analysis.legacy_intent


def sanitize_source_documents(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    화면에 표시되는 출처 제목과 파일명의 앞뒤 불필요한
    Markdown 표 기호와 공백을 제거한다.
    """
    sanitized_documents: list[dict[str, Any]] = []

    for document in documents:
        sanitized_document = dict(document)

        for key in (
            "heading",
            "source_file",
        ):
            value = str(
                sanitized_document.get(key, "")
            ).strip()

            value = re.sub(
                r"^[|\s]+|[|\s]+$",
                "",
                value,
            )

            sanitized_document[key] = value

        sanitized_documents.append(
            sanitized_document
        )

    return sanitized_documents


def build_registered_rule_answer(
    intent: str,
) -> str:
    """
    legal_rules.py에 등록된 핵심 결론과 필수 문단으로
    검증 완료 답변을 만든다.

    Ollama 또는 answer_builder에서 오류가 발생했을 때도
    같은 규칙을 사용하므로 답변 기준이 달라지지 않는다.
    """
    rule = get_legal_rule(intent)

    if rule is None:
        raise KeyError(
            f"등록되지 않은 법률 intent입니다: {intent}"
        )

    paragraphs = [
        rule.core_conclusion,
        *rule.mandatory_paragraphs,
    ]

    return "\n\n".join(
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    )


def select_relevant_documents(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """rerank 점수를 기준으로 관련성이 높은 문서만 선택한다."""
    if not documents:
        return []

    sorted_documents = sorted(
        documents,
        key=lambda document: float(
            document.get("rerank_score", 0.0)
        ),
        reverse=True,
    )

    best_score = float(
        sorted_documents[0].get("rerank_score", 0.0)
    )

    if best_score < MIN_RERANK_SCORE:
        return []

    final_threshold = max(
        MIN_RERANK_SCORE,
        best_score * RELATIVE_SCORE_RATIO,
    )

    relevant_documents = [
        document
        for document in sorted_documents
        if float(document.get("rerank_score", 0.0))
        >= final_threshold
    ]

    return relevant_documents[:MAX_CONTEXT_DOCUMENTS]


def build_context(
    documents: list[dict[str, Any]],
) -> str:
    """검색 문서를 Ollama에 전달할 문맥으로 변환한다."""
    context_parts: list[str] = []

    for document in documents:
        heading = str(
            document.get("heading", "")
        ).strip()

        source_file = str(
            document.get("source_file", "")
        ).strip()

        content = str(
            document.get("parent_content", "")
        ).strip()

        if not content:
            continue

        content = content[:MAX_DOCUMENT_LENGTH]

        context_parts.append(
            "\n".join(
                [
                    "--- 근거 문서 시작 ---",
                    f"문서명: {source_file}",
                    f"문서 위치: {heading}",
                    f"문서 내용:\n{content}",
                    "--- 근거 문서 끝 ---",
                ]
            )
        )

    return "\n\n".join(context_parts)


def build_prompt(
    question: str,
    documents: list[dict[str, Any]],
) -> str:
    """일반 질문용 Ollama 프롬프트를 생성한다."""
    context = build_context(documents)

    return f"""
아래 근거 문서를 바탕으로 사용자의 질문에 답변하세요.

[사용자 질문]
{question}

[근거 문서]
{context}

[답변 작성 규칙]
- 질문에 대한 직접적인 결론부터 작성하세요.
- 질문과 무관한 상품이나 사례는 언급하지 마세요.
- 모든 문서를 억지로 사용하지 마세요.
- 답변 본문에 출처 번호나 문서명을 작성하지 마세요.
- 근거 문서에 없는 예외나 조건은 추가하지 마세요.
- 같은 내용을 반복하지 마세요.
- 환급 시기, 반품 기한, 비용 부담 주체를 서로 혼동하지 마세요.
- 답변은 2~3문단 이내로 작성하세요.
""".strip()


def normalize_text(text: str) -> str:
    """공백과 문장부호를 제거해 질문 의도 판별에 사용한다."""
    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        str(text).lower(),
    )


def is_replacement_defective_refund_question(
    question: str,
) -> bool:
    """
    불량으로 교환받은 상품에도 다시 불량이 발생하여
    환불을 요구할 수 있는지 묻는 질문을 판별한다.
    """
    normalized = normalize_text(question)

    replacement_terms = (
        "교환받은상품",
        "교환받은제품",
        "교환받은물건",
        "교환한상품",
        "교환한제품",
        "교환된상품",
        "교환된제품",
        "교환상품",
        "교환제품",
        "교환품",
        "교체받은상품",
        "교체받은제품",
        "교체받은물건",
        "교체한상품",
        "교체한제품",
        "교체된상품",
        "교체된제품",
        "교체상품",
        "교체제품",
        "교체품",
        "대체상품",
        "대체제품",
        "새상품으로교환",
        "새제품으로교환",
        "새상품으로교체",
        "새제품으로교체",
        "교환받았는데",
        "교환했는데",
        "교환후",
        "교체받았는데",
        "교체했는데",
        "교체후",
    )

    repeated_defect_terms = (
        "다시불량",
        "또불량",
        "재불량",
        "여전히불량",
        "계속불량",
        "또하자",
        "다시하자",
        "하자가또",
        "하자가다시",
        "불량이또",
        "불량이다시",
        "다시고장",
        "또고장",
        "재고장",
        "여전히고장",
        "계속고장",
        "고장이다시",
        "고장이또",
        "고장났는데",
        "고장났고",
        "교환품도불량",
        "교환상품도불량",
        "교환제품도불량",
        "교환된상품도불량",
        "교환받은상품도불량",
        "교환받은제품도불량",
        "교환품도고장",
        "교환상품도고장",
        "교환제품도고장",
        "교환된상품도고장",
        "교환받은상품도고장",
        "교환받은제품도고장",
        "교환후에도불량",
        "교환했는데도불량",
        "교환받았는데도불량",
        "교환후에도고장",
        "교환했는데도고장",
        "교환받았는데도고장",
        "같은문제가",
        "동일한문제가",
        "같은하자",
        "동일한하자",
        "같은고장",
        "동일한고장",
        "전원이켜지지않",
        "전원이안켜",
        "전원이들어오지않",
        "전원안들어",
        "전원불량",
        "작동하지않",
        "작동안",
        "작동이안",
        "작동이안되",
        "작동이안돼",
        "작동이되지않",
        "정상작동하지않",
        "정상적으로작동하지않",
        "부팅되지않",
        "부팅안",
        "실행되지않",
        "실행안",
        "켜지지않",
        "화면이나오지않",
        "화면안나오",
        "충전되지않",
        "충전안",
        "연결되지않",
        "연결안",
        "인식되지않",
        "인식안",
        "소리가나지않",
        "소리안나",
        "멈춰버",
        "먹통",
    )

    refund_terms = (
        "환불",
        "환급",
        "청약철회",
        "계약해제",
        "계약취소",
        "구매취소",
        "돈을돌려",
        "대금반환",
    )

    request_terms = (
        "요구할수",
        "요청할수",
        "받을수",
        "가능",
        "되나요",
        "돼나요",
        "해도되",
        "해달라고",
        "해야하",
        "거절할수",
        "거부할수",
    )

    return (
        any(
            term in normalized
            for term in replacement_terms
        )
        and any(
            term in normalized
            for term in repeated_defect_terms
        )
        and any(term in normalized for term in refund_terms)
        and any(term in normalized for term in request_terms)
    )


def build_replacement_defective_refund_answer() -> str:
    """교환·교체 후 재불량 환불 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "replacement_defective_refund"
    )


def is_defective_product_refund_question(
    question: str,
) -> bool:
    """불량 상품에 교환만 허용하고 환불을 거절하는 질문을 판별한다."""
    normalized = normalize_text(question)

    defect_terms = (
        "불량상품",
        "상품불량",
        "제품불량",
        "불량품",
        "하자상품",
        "상품하자",
        "제품하자",
        "하자가있",
        "고장난상품",
        "고장난제품",
        "파손상품",
        "파손된상품",
        "불량인데",
        "불량이",
    )

    exchange_only_terms = (
        "교환만가능",
        "교환만된",
        "교환만해준",
        "교환만",
        "교환밖에",
        "교환으로만",
        "교환만할수",
        "교환처리만",
        "교환해주고",
    )

    refund_refusal_terms = (
        "환불은안",
        "환불안",
        "환불이안",
        "환불불가",
        "환불거절",
        "환불을거절",
        "환불거부",
        "환불을거부",
        "반품은안",
        "반품안",
        "반품불가",
        "청약철회안",
        "청약철회불가",
    )

    legality_terms = (
        "해도되",
        "가능한가",
        "가능하나",
        "괜찮",
        "맞나요",
        "되나요",
        "돼나요",
        "할수있",
        "정당한",
    )

    has_defect = any(
        term in normalized
        for term in defect_terms
    )
    has_exchange_only = any(
        term in normalized
        for term in exchange_only_terms
    )
    has_refund_refusal = any(
        term in normalized
        for term in refund_refusal_terms
    )
    has_legality_context = any(
        term in normalized
        for term in legality_terms
    )

    return (
        has_defect
        and has_exchange_only
        and has_refund_refusal
        and has_legality_context
    )


def build_defective_product_refund_answer() -> str:
    """불량 상품의 청약철회·환불 가능성과 예외를 안내한다."""
    return (
        "아니요. 상품이 불량이거나 표시·광고 또는 계약 내용과 "
        "다르게 제공되었다면 쇼핑몰이 일률적으로 교환만 강제하고 "
        "환불을 거절할 수는 없습니다.\n\n"
        "소비자는 상품을 받은 날부터 3개월 이내이면서, 불량 사실을 "
        "안 날 또는 알 수 있었던 날부터 30일 이내에 청약철회하고 "
        "환불을 요구할 수 있습니다. 이 경우 상품 반환 비용은 "
        "판매자가 부담합니다.\n\n"
        "다만 청약철회 기간이 지났거나 상품 종류와 하자의 정도에 "
        "따라 소비자분쟁해결기준상 수리나 교환 절차가 우선 적용되는 "
        "경우에는 처리 기준이 달라질 수 있습니다."
    )


def is_mismatch_deadline_question(question: str) -> bool:
    """상품 불일치에 따른 반품 가능 여부와 기한 질문을 확인한다."""
    normalized = normalize_text(question)

    mismatch_terms = (
        "상품설명과실제상품이다르",
        "설명과실제가다르",
        "표시광고와다르",
        "광고내용과다르",
        "계약내용과다르게이행",
        "상품사진과다",
        "사진과다",
        "사진이랑다",
        "이미지와다",
        "이미지랑다",
        "상세페이지와다",
        "상세페이지랑다",
        "설명과다",
        "광고와다",
        "받은상품이다",
        "다른상품이왔",
    )

    return_terms = (
        "반품",
        "청약철회",
        "철회",
        "환불",
        "돌려보",
        "돌려주",
    )

    deadline_terms = (
        "언제까지",
        "반품기한",
        "반품기간",
        "청약철회기간",
        "청약철회기한",
        "기한",
        "기간",
        "한달",
        "한달이지나",
        "지나도",
        "지났",
        "며칠",
        "몇일",
        "늦었",
        "아직",
        "가능",
        "할수",
        "되나요",
        "돼나요",
    )

    return (
        any(term in normalized for term in mismatch_terms)
        and any(term in normalized for term in return_terms)
        and any(term in normalized for term in deadline_terms)
    )


def build_mismatch_deadline_answer() -> str:
    """상품 불일치 청약철회 기한 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "mismatch_return_deadline"
    )


def is_minor_purchase_cancellation_question(
    question: str,
) -> bool:
    """미성년자의 법정대리인 동의 없는 구매 취소 질문을 판별한다."""
    normalized = normalize_text(question)

    minor_terms = (
        "미성년자",
        "미성년",
    )

    no_consent_terms = (
        "부모동의없이",
        "부모의동의없이",
        "부모허락없이",
        "부모의허락없이",
        "부모몰래",
        "법정대리인동의없이",
        "법정대리인의동의없이",
        "보호자동의없이",
        "보호자의동의없이",
        "동의를받지않고",
        "동의받지않고",
    )

    purchase_terms = (
        "온라인쇼핑몰",
        "쇼핑몰",
        "온라인구매",
        "인터넷구매",
        "상품을구매",
        "물건을구매",
        "구매했다",
        "구매했",
        "계약",
        "결제",
    )

    cancellation_terms = (
        "계약취소",
        "구매취소",
        "취소할수",
        "취소가능",
        "취소되",
        "취소해도",
        "환불",
        "무효",
        "철회",
        "되나요",
        "돼나요",
        "가능한가",
        "가능하나",
    )

    return (
        any(term in normalized for term in minor_terms)
        and any(term in normalized for term in no_consent_terms)
        and any(term in normalized for term in purchase_terms)
        and any(term in normalized for term in cancellation_terms)
    )


def build_minor_purchase_cancellation_answer() -> str:
    """미성년자의 계약 취소 원칙과 주요 예외를 안내한다."""
    return (
        "네. 미성년자가 법정대리인의 동의 없이 온라인 "
        "쇼핑몰에서 상품을 구매했다면, 원칙적으로 미성년자 "
        "본인이나 법정대리인이 계약을 취소할 수 있습니다.\n\n"
        "쇼핑몰은 미성년자와 계약할 때 법정대리인이 동의하지 "
        "않으면 계약을 취소할 수 있다는 사실을 미성년자에게 "
        "알려야 합니다. 다만 법정대리인이 사용을 허락한 용돈 등 "
        "처분을 허락한 재산의 범위에서 구매한 경우에는 취소가 "
        "제한될 수 있습니다."
    )


def is_preselected_paid_addon_question(
    question: str,
) -> bool:
    """유료 부가상품·서비스의 사전 선택 질문을 판별한다."""
    normalized = normalize_text(question)

    paid_addon_terms = (
        "유료부가상품",
        "유료부가서비스",
        "유료서비스",
        "추가상품",
        "부가상품",
        "부가서비스",
        "추가옵션",
        "유료옵션",
        "선택상품",
        "선택서비스",
    )

    preselection_terms = (
        "미리선택",
        "선택해두",
        "선택되어",
        "체크되어",
        "체크해두",
        "기본선택",
        "자동선택",
        "사전선택",
        "미리체크",
        "기본체크",
    )

    passive_payment_terms = (
        "해제하지않으면",
        "해제안하면",
        "취소하지않으면",
        "취소안하면",
        "선택을풀지않으면",
        "체크를풀지않으면",
        "그대로결제",
        "자동결제",
        "결제되게",
        "결제되도록",
        "결제해도",
        "결제해버",
    )

    legality_terms = (
        "해도되",
        "가능한가",
        "가능하나",
        "괜찮",
        "문제없",
        "불법",
        "금지",
        "되나요",
        "돼나요",
        "할수있",
    )

    return (
        any(term in normalized for term in paid_addon_terms)
        and any(term in normalized for term in preselection_terms)
        and (
            any(
                term in normalized
                for term in passive_payment_terms
            )
            or any(term in normalized for term in legality_terms)
        )
    )


def build_preselected_paid_addon_answer() -> str:
    """유료 선택항목의 사전 선택 금지와 직접 동의를 안내한다."""
    return (
        "안 됩니다. 쇼핑몰은 유료 부가상품이나 서비스가 선택된 "
        "상태로 미리 설정해 두고, 소비자가 이를 해제하지 않았다는 "
        "이유로 결제되게 해서는 안 됩니다.\n\n"
        "유료 항목의 가격과 내용을 명확히 안내한 뒤 소비자가 "
        "직접 선택하거나 동의하도록 해야 합니다."
    )


def is_card_payment_refusal_question(
    question: str,
) -> bool:
    """카드 결제 거부 또는 현금 결제 강요 질문을 판별한다."""
    normalized = normalize_text(question)

    card_terms = (
        "신용카드",
        "카드결제",
        "카드로결제",
        "카드거래",
        "카드를",
        "카드",
    )

    refusal_terms = (
        "카드결제를거부",
        "카드결제거부",
        "카드결제를거절",
        "카드결제거절",
        "카드를거부",
        "카드거부",
        "카드를거절",
        "카드거절",
        "카드를안받",
        "카드안받",
        "카드결제가안되",
        "카드결제안되",
        "카드로는안되",
        "카드로결제못",
        "카드결제를못",
    )

    cash_only_terms = (
        "현금으로만",
        "현금결제만",
        "현금만받",
        "현금만가능",
        "현금결제하라고",
        "현금으로결제하라고",
        "계좌이체만",
        "계좌이체하라고",
        "무통장입금만",
    )

    merchant_terms = (
        "쇼핑몰",
        "판매자",
        "사업자",
        "가맹점",
        "온라인몰",
        "몰에서",
    )

    legality_terms = (
        "해도되",
        "가능한가",
        "가능하나",
        "괜찮",
        "문제없",
        "불법",
        "금지",
        "되나요",
        "돼나요",
        "할수있",
    )

    has_card = any(
        term in normalized
        for term in card_terms
    )
    has_refusal_or_cash_only = (
        any(term in normalized for term in refusal_terms)
        or any(
            term in normalized
            for term in cash_only_terms
        )
    )
    has_merchant_context = any(
        term in normalized
        for term in merchant_terms
    )
    has_legality_context = any(
        term in normalized
        for term in legality_terms
    )

    return (
        has_card
        and has_refusal_or_cash_only
        and has_merchant_context
        and has_legality_context
    )


def build_card_payment_refusal_answer() -> str:
    """신용카드가맹점의 카드 결제 거부 금지를 안내한다."""
    return (
        "신용카드가맹점인 쇼핑몰이라면 카드 결제라는 이유로 "
        "결제를 거절하고 현금으로만 결제하도록 요구해서는 "
        "안 됩니다.\n\n"
        "신용카드가맹점은 카드 거래를 이유로 신용카드 결제를 "
        "거절하거나 카드회원을 불리하게 대우할 수 없습니다. "
        "다만 해당 판매자가 신용카드가맹점이 아닌 경우에는 "
        "카드 결제 수단을 반드시 제공해야 하는지는 별도로 "
        "확인해야 합니다."
    )


def is_card_payment_refund_cancellation_question(
    question: str,
) -> bool:
    """카드 결제 상품 환불 시 결제 취소 요청 질문을 판별한다."""
    normalized = normalize_text(question)

    card_terms = (
        "카드",
        "신용카드",
        "체크카드",
        "카드결제",
        "결제업자",
        "카드사",
    )

    refund_terms = (
        "환불",
        "환급",
        "반품",
        "청약철회",
        "결제취소",
        "대금반환",
    )

    cancellation_terms = (
        "결제취소",
        "승인취소",
        "카드취소",
        "청구정지",
        "대금청구정지",
        "취소요청",
        "요청해야",
        "알려야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    return (
        any(term in normalized for term in card_terms)
        and any(term in normalized for term in refund_terms)
        and any(
            term in normalized
            for term in cancellation_terms
        )
    )


def build_card_payment_refund_cancellation_answer() -> str:
    """카드 환불 시 결제업자에 대한 취소·환급 절차를 안내한다."""
    return (
        "네. 카드로 결제한 상품을 환불하는 경우 쇼핑몰은 "
        "카드사 등 결제업자에게 대금 청구를 정지하거나 결제를 "
        "취소하도록 지체 없이 요청해야 합니다.\n\n"
        "쇼핑몰이 이미 결제업자로부터 상품 대금을 받은 경우에는 "
        "그 대금을 결제업자에게 지체 없이 환급하고, 그 사실을 "
        "소비자에게 알려야 합니다."
    )


def is_refund_delay_compensation_question(
    question: str,
) -> bool:
    """환급 지연에 따른 지연이자·지연배상금 질문을 판별한다."""
    normalized = normalize_text(question)

    refund_terms = (
        "환불",
        "환급",
        "대금반환",
        "결제취소",
        "돈을돌려",
        "돈돌려",
    )

    delay_terms = (
        "환불지연",
        "환급지연",
        "늦게",
        "늦어",
        "지연",
        "미뤄",
        "미루",
        "제때안",
        "기한을넘",
        "3영업일을넘",
        "삼영업일을넘",
    )

    compensation_terms = (
        "지연이자",
        "지연배상금",
        "이자",
        "배상금",
        "받을수",
        "청구할수",
        "지급해야",
        "줘야",
        "보상",
    )

    return (
        any(term in normalized for term in refund_terms)
        and any(term in normalized for term in delay_terms)
        and any(
            term in normalized
            for term in compensation_terms
        )
    )


def build_refund_delay_compensation_answer() -> str:
    """환급기한과 환급 지연에 따른 지연배상금을 안내한다."""
    return (
        "네. 쇼핑몰이 법정 환급기한을 넘겨 환불하면 소비자는 "
        "지연 기간에 대한 지연배상금을 받을 수 있습니다.\n\n"
        "상품을 반품한 경우 쇼핑몰은 상품을 반환받은 날부터 "
        "3영업일 이내에 대금을 환급해야 합니다. 이 기간을 넘긴 "
        "경우에는 시행령에서 정한 이율에 따라 계산한 "
        "지연배상금을 함께 지급해야 합니다."
    )


def is_contract_document_delivery_question(
    question: str,
) -> bool:
    """계약 체결 후 계약내용 서면 교부 질문을 판별한다."""
    normalized = normalize_text(question)

    contract_terms = (
        "계약내용",
        "계약조건",
        "거래조건",
        "계약서",
        "계약이체결",
        "계약체결",
    )

    document_terms = (
        "서면",
        "문서",
        "전자문서",
        "계약서",
        "이메일",
        "메일",
    )

    timing_terms = (
        "주문이완료",
        "주문완료",
        "주문후",
        "구매후",
        "결제후",
        "계약이체결",
        "계약체결후",
        "계약후",
    )

    delivery_terms = (
        "보내줘야",
        "보내주어야",
        "전달해야",
        "교부해야",
        "제공해야",
        "발급해야",
        "받을수",
        "줘야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    return (
        any(term in normalized for term in contract_terms)
        and any(term in normalized for term in document_terms)
        and any(term in normalized for term in timing_terms)
        and any(term in normalized for term in delivery_terms)
    )


def build_contract_document_delivery_answer() -> str:
    """계약내용 서면의 교부 내용·시점·형태를 안내한다."""
    return (
        "네. 쇼핑몰은 계약이 체결되면 상품 정보, 가격과 "
        "결제방법, 배송 및 청약철회 조건 등 계약 내용이 적힌 "
        "서면을 소비자에게 제공해야 합니다.\n\n"
        "계약내용 서면은 상품이 공급될 때까지 제공해야 하며, "
        "소비자가 내용을 확인하고 보관할 수 있는 전자문서 "
        "형태로 제공할 수도 있습니다."
    )


def is_order_receipt_confirmation_question(
    question: str,
) -> bool:
    """온라인 주문 접수 사실과 주문 내용 확인 질문을 판별한다."""
    normalized = normalize_text(question)

    order_terms = (
        "온라인주문",
        "인터넷주문",
        "주문",
        "구매신청",
        "청약",
    )

    receipt_terms = (
        "주문접수",
        "접수됐",
        "접수되었",
        "접수사실",
        "주문완료",
        "주문이들어",
        "정상접수",
        "주문확인",
    )

    notice_terms = (
        "알려줘야",
        "알려주어야",
        "통지해야",
        "확인해줘야",
        "확인시켜",
        "보여줘야",
        "보내줘야",
        "제공해야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    return (
        any(term in normalized for term in order_terms)
        and any(term in normalized for term in receipt_terms)
        and any(term in normalized for term in notice_terms)
    )


def build_order_receipt_confirmation_answer() -> str:
    """온라인 주문 접수 사실과 주문 내용 확인 절차를 안내한다."""
    return (
        "네. 쇼핑몰은 온라인으로 주문을 받은 경우 주문이 "
        "정상적으로 접수되었다는 사실과 주문 내용을 소비자가 "
        "확인할 수 있도록 해야 합니다.\n\n"
        "주문한 상품, 수량, 가격 등에 오류가 있는 경우에는 "
        "소비자가 이를 확인하고 수정하거나 취소할 수 있는 절차도 "
        "제공해야 합니다."
    )


def is_pre_payment_order_review_correction_question(
    question: str,
) -> bool:
    """결제 전 주문 내용 확인·수정 질문을 판별한다."""
    normalized = normalize_text(question)

    order_terms = (
        "주문내용",
        "주문한상품",
        "주문상품",
        "장바구니",
        "구매상품",
        "상품과수량",
        "상품수량",
    )

    detail_terms = (
        "상품",
        "품목",
        "수량",
        "가격",
        "금액",
        "옵션",
        "색상",
        "사이즈",
    )

    pre_payment_terms = (
        "결제하기전",
        "결제전에",
        "결제전",
        "주문완료전",
        "구매확정전",
        "청약전",
    )

    review_terms = (
        "확인",
        "검토",
        "다시볼",
        "보여줘",
        "보여주어",
    )

    correction_terms = (
        "수정",
        "변경",
        "정정",
        "취소",
        "바꿀",
        "고칠",
    )

    duty_terms = (
        "할수있어야",
        "할수있나요",
        "가능해야",
        "가능한가",
        "제공해야",
        "마련해야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    has_order_context = (
        any(term in normalized for term in order_terms)
        or (
            "주문" in normalized
            and any(term in normalized for term in detail_terms)
        )
    )

    return (
        has_order_context
        and any(term in normalized for term in pre_payment_terms)
        and any(term in normalized for term in review_terms)
        and any(term in normalized for term in correction_terms)
        and any(term in normalized for term in duty_terms)
    )


def build_pre_payment_order_review_correction_answer() -> str:
    """결제 전 주문 내용 확인·정정 절차를 안내한다."""
    return (
        "네. 소비자는 결제하기 전에 주문한 상품, 수량, 가격 등 "
        "주문 내용을 확인할 수 있어야 합니다.\n\n"
        "주문 내용이 잘못된 경우에는 결제가 완료되기 전에 "
        "수량이나 상품을 수정하거나 주문을 취소할 수 있는 절차도 "
        "제공되어야 합니다."
    )


def is_pre_purchase_shipping_information_question(
    question: str,
) -> bool:
    """구매 전 배송 방법·비용·기간 안내 질문을 판별한다."""
    normalized = normalize_text(question)

    shipping_terms = (
        "배송",
        "배달",
        "택배",
        "운송",
    )

    method_or_period_terms = (
        "배송방법",
        "배송수단",
        "배송기간",
        "배송일",
        "배송예정일",
        "예상배송기간",
        "도착예정일",
        "언제도착",
        "얼마나걸",
    )

    cost_terms = (
        "배송비",
        "배송료",
        "운송비",
        "택배비",
        "비용부담",
        "부담자",
    )

    pre_purchase_terms = (
        "결제하기전",
        "결제전에",
        "결제전",
        "구매하기전",
        "구매전에",
        "구매전",
        "주문하기전",
        "주문전에",
        "주문전",
    )

    notice_terms = (
        "알려줘야",
        "알려주어야",
        "표시해야",
        "명시해야",
        "고지해야",
        "보여줘야",
        "보여주어야",
        "확인할수",
        "제공해야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    has_method_or_period = any(
        term in normalized for term in method_or_period_terms
    )
    has_cost = any(term in normalized for term in cost_terms)

    return (
        any(term in normalized for term in shipping_terms)
        and (has_method_or_period or has_cost)
        and any(term in normalized for term in pre_purchase_terms)
        and any(term in normalized for term in notice_terms)
    )


def build_pre_purchase_shipping_information_answer() -> str:
    """구매 전 배송정보와 배송 지연 배상 원칙을 안내한다."""
    return (
        "네. 쇼핑몰은 소비자가 구매하기 전에 배송 방법, 배송비 "
        "부담자, 예상 배송기간 등을 확인할 수 있도록 명시해야 "
        "합니다.\n\n"
        "쇼핑몰의 고의나 과실로 약정한 배송기간을 넘겨 소비자에게 "
        "손해가 발생한 경우에는 그 손해를 배상해야 합니다. 다만 "
        "쇼핑몰이 고의·과실이 없었음을 입증한 경우에는 예외가 될 "
        "수 있습니다."
    )


def is_pre_payment_total_amount_question(
    question: str,
) -> bool:
    """결제 전 상품 가격·배송비 포함 총금액 확인 질문을 판별한다."""
    normalized = normalize_text(question)

    price_terms = (
        "상품가격",
        "제품가격",
        "상품금액",
        "판매가격",
        "물건가격",
        "가격",
    )

    shipping_cost_terms = (
        "배송비",
        "배송료",
        "운송비",
        "택배비",
        "추가비용",
    )

    total_amount_terms = (
        "최종결제금액",
        "총결제금액",
        "전체결제금액",
        "총금액",
        "최종금액",
        "실제부담금액",
        "합친금액",
        "포함한금액",
        "합계",
    )

    pre_payment_terms = (
        "결제하기전",
        "결제전에",
        "결제전",
        "주문하기전",
        "주문전에",
        "주문전",
        "구매하기전",
        "구매전에",
        "구매전",
    )

    display_or_confirmation_terms = (
        "보여줘야",
        "보여주어야",
        "표시해야",
        "알려줘야",
        "고지해야",
        "확인할수",
        "확인시켜",
        "제공해야",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
    )

    return (
        any(term in normalized for term in price_terms)
        and any(
            term in normalized
            for term in shipping_cost_terms
        )
        and any(term in normalized for term in total_amount_terms)
        and any(term in normalized for term in pre_payment_terms)
        and any(
            term in normalized
            for term in display_or_confirmation_terms
        )
    )


def build_pre_payment_total_amount_answer() -> str:
    """결제 전 총 결제금액 확인 및 직접 동의 절차를 안내한다."""
    return (
        "네. 쇼핑몰은 소비자가 결제하기 전에 상품 가격과 배송비 등 "
        "추가 비용을 포함하여 실제로 부담할 총 결제금액을 명확하게 "
        "확인할 수 있도록 해야 합니다.\n\n"
        "소비자는 표시된 주문 내용과 결제금액을 확인한 뒤 직접 "
        "동의 여부를 선택할 수 있어야 하며, 쇼핑몰이 결제 동의를 "
        "미리 선택해 두어서는 안 됩니다."
    )


def is_delivery_courier_privacy_outsourcing_question(
    question: str,
) -> bool:
    """배송을 위한 택배회사 개인정보 전달 질문을 확인한다."""
    normalized = normalize_text(question)

    delivery_terms = (
        "배송",
        "상품배송",
        "주문배송",
        "배달",
        "택배",
    )

    courier_terms = (
        "택배회사",
        "택배사",
        "택배업체",
        "배송업체",
        "운송업체",
        "배송회사",
    )

    personal_data_terms = (
        "개인정보",
        "주소",
        "배송지",
        "이름",
        "성명",
        "연락처",
        "전화번호",
    )

    transfer_terms = (
        "전달",
        "제공",
        "넘겨",
        "보내",
        "공유",
        "알려",
    )

    legality_terms = (
        "불법",
        "위법",
        "해도되",
        "되나요",
        "돼나요",
        "가능",
        "괜찮",
        "문제",
    )

    return (
        any(term in normalized for term in delivery_terms)
        and any(term in normalized for term in courier_terms)
        and any(
            term in normalized
            for term in personal_data_terms
        )
        and any(term in normalized for term in transfer_terms)
        and any(term in normalized for term in legality_terms)
    )


def build_delivery_courier_privacy_outsourcing_answer() -> str:
    """배송 목적 개인정보 처리위탁의 원칙을 안내한다."""
    return (
        "무조건 불법은 아닙니다. 쇼핑몰이 주문한 상품을 배송하기 "
        "위해 필요한 이름, 주소, 연락처를 택배회사에 전달하는 것은 "
        "배송 업무를 맡기는 개인정보 처리위탁에 해당할 수 있습니다.\n\n"
        "다만 택배회사는 배송에 필요한 범위에서만 개인정보를 "
        "처리해야 하며, 쇼핑몰은 위탁 목적과 업무 범위를 정하고 "
        "개인정보가 안전하게 처리되는지 관리·감독해야 합니다. "
        "배송 목적과 관계없는 용도로 이용하거나 다른 곳에 "
        "제공해서는 안 됩니다."
    )


def is_account_withdrawal_privacy_destruction_question(
    question: str,
) -> bool:
    """회원 탈퇴 후 개인정보 파기 질문을 확인한다."""
    normalized = normalize_text(question)

    withdrawal_terms = (
        "회원탈퇴",
        "탈퇴",
        "계정삭제",
        "계정탈퇴",
        "회원해지",
        "가입해지",
    )

    privacy_terms = (
        "개인정보",
        "회원정보",
        "가입정보",
        "내정보",
    )

    destruction_terms = (
        "삭제",
        "파기",
        "지워",
        "없애",
        "보관",
        "남겨",
        "남아",
    )

    timing_or_duty_terms = (
        "바로",
        "즉시",
        "지체없이",
        "언제",
        "해야하",
        "해야되",
        "되나요",
        "돼나요",
        "의무",
        "가능",
        "보관해도되",
    )

    return (
        any(term in normalized for term in withdrawal_terms)
        and any(term in normalized for term in privacy_terms)
        and any(term in normalized for term in destruction_terms)
        and any(
            term in normalized
            for term in timing_or_duty_terms
        )
    )


def build_account_withdrawal_privacy_destruction_answer() -> str:
    """회원 탈퇴 후 개인정보 파기 원칙과 보존 예외를 안내한다."""
    return (
        "원칙적으로 회원 탈퇴로 개인정보가 불필요해지면 "
        "쇼핑몰은 해당 개인정보를 지체 없이 파기해야 합니다.\n\n"
        "다만 계약, 결제, 청약철회, 소비자 불만 처리 등 다른 "
        "법령에서 일정 기간 보관하도록 정한 거래기록은 즉시 "
        "삭제하지 않고 별도로 분리하여 보관할 수 있습니다. "
        "보존기간이 끝나면 해당 정보도 파기해야 합니다."
    )


def is_third_party_personal_data_provision_question(
    question: str,
) -> bool:
    """개인정보 제3자 제공과 동의 필요 여부 질문을 확인한다."""
    normalized = normalize_text(question)

    privacy_terms = (
        "개인정보",
        "개인정보제공",
        "정보제공",
        "개인정보를넘기",
        "개인정보를전달",
    )

    third_party_terms = (
        "제3자",
        "다른회사",
        "타회사",
        "외부업체",
        "다른업체",
        "다른사업자",
        "다른기관",
    )

    consent_terms = (
        # 동의 없이 제공하는 경우
        "동의없이",
        "동의받지않",
        "동의안받",
        "허락없이",
        "모르게",

        # 동의를 받아야 하는지 묻는 경우
        "동의를받",
        "동의받아야",
        "동의가필요",
        "동의필요",
        "동의해야",
        "허락받아야",
    )

    direct_permission_terms = (
        "제공해도되",
        "넘겨도되",
        "전달해도되",
        "보내도되",
        "공유해도되",
        "제공할수있",
        "넘길수있",
    )

    question_terms = (
        "되나요",
        "돼나요",
        "해야하나요",
        "해야하나",
        "받아야하나요",
        "받아야하나",
        "필요하나요",
        "필요한가요",
        "가능",
        "괜찮",
        "문제",
        "위법",
        "불법",
    )

    has_privacy = any(
        term in normalized
        for term in privacy_terms
    )
    has_third_party = any(
        term in normalized
        for term in third_party_terms
    )
    has_consent_expression = any(
        term in normalized
        for term in consent_terms
    )
    has_direct_permission_expression = any(
        term in normalized
        for term in direct_permission_terms
    )
    has_question_expression = any(
        term in normalized
        for term in question_terms
    )

    return (
        has_privacy
        and has_third_party
        and (
            has_consent_expression
            or has_direct_permission_expression
        )
        and has_question_expression
    )


def build_third_party_personal_data_provision_answer() -> str:
    """개인정보 제3자 제공의 원칙과 예외를 안내한다."""
    return (
        "원칙적으로 안 됩니다. 쇼핑몰이 개인정보를 다른 회사 등 "
        "제3자에게 제공하려면 정보주체의 동의를 받아야 합니다.\n\n"
        "동의를 받을 때에는 제공받는 자, 제공 목적, 제공 항목, "
        "보유·이용 기간 등을 알려야 합니다. 다만 법률에 특별한 "
        "규정이 있거나 법에서 정한 요건을 충족하는 경우에는 "
        "동의 없이 제공할 수 있는 예외가 있습니다."
    )


def is_optional_privacy_consent_refusal_question(
    question: str,
) -> bool:
    """선택 개인정보 동의 거부에 따른 가입 제한 질문을 확인한다."""
    normalized = normalize_text(question)

    privacy_terms = (
        "개인정보",
        "개인정보수집",
        "개인정보이용",
        "개인정보제공",
        "정보제공동의",
    )

    optional_terms = (
        "필수아닌",
        "필수가아닌",
        "필수항목아닌",
        "필수항목이아닌",
        "선택항목",
        "선택동의",
        "추가정보",
        "추가개인정보",
        "필요이상",
        "최소한외",
        "최소한이외",
        "과도한",
    )

    refusal_terms = (
        "동의하지않",
        "동의안",
        "거부",
        "제공하지않",
        "제공안",
    )

    restriction_terms = (
        "회원가입",
        "가입",
        "서비스제공",
        "서비스이용",
        "이용제한",
        "가입제한",
        "가입거절",
        "막아",
        "거절",
        "제한",
    )

    permission_terms = (
        "해도되",
        "되나요",
        "돼나요",
        "가능",
        "괜찮",
        "문제",
        "위법",
        "불법",
    )

    return (
        any(term in normalized for term in privacy_terms)
        and any(term in normalized for term in optional_terms)
        and any(term in normalized for term in refusal_terms)
        and any(
            term in normalized
            for term in restriction_terms
        )
        and any(term in normalized for term in permission_terms)
    )


def build_optional_privacy_consent_refusal_answer() -> str:
    """선택 개인정보 동의 거부 시 서비스 제한 금지를 안내한다."""
    return (
        "안 됩니다. 쇼핑몰은 서비스 제공에 필요한 최소한의 "
        "개인정보 외에 추가 개인정보 수집·이용 또는 제공에 "
        "동의하지 않았다는 이유로 회원가입이나 서비스 제공을 "
        "제한하거나 거절해서는 안 됩니다.\n\n"
        "다만 회원가입이나 계약 이행에 실제로 필요한 필수정보를 "
        "제공하지 않은 경우에는 해당 서비스 이용이 제한될 수 "
        "있습니다."
    )


def is_false_exaggerated_ad_question(
    question: str,
) -> bool:
    """상품 효과의 거짓·과장 광고 질문을 확인한다."""
    normalized = normalize_text(question)

    advertising_terms = (
        "광고",
        "표시광고",
        "홍보",
        "상품설명",
        "상세페이지",
    )

    exaggeration_terms = (
        "과장",
        "부풀",
        "실제보다좋",
        "실제보다우수",
        "사실과다르",
        "거짓",
        "허위",
        "효과를크게",
        "효능을과장",
        "성능을과장",
        "효과를단정",
        "효능을단정",
    )

    permission_terms = (
        "해도되",
        "되나요",
        "돼나요",
        "가능",
        "괜찮",
        "문제",
        "위법",
        "불법",
        "금지",
    )

    product_effect_terms = (
        "효과",
        "효능",
        "성능",
        "품질",
        "기능",
        "상품",
        "제품",
    )

    return (
        any(term in normalized for term in advertising_terms)
        and any(term in normalized for term in exaggeration_terms)
        and any(
            term in normalized
            for term in product_effect_terms
        )
        and any(term in normalized for term in permission_terms)
    )


def build_false_exaggerated_ad_answer() -> str:
    """거짓·과장 광고 금지 원칙을 검증된 문장으로 안내한다."""
    return (
        "안 됩니다. 상품 효과를 사실과 다르게 표시하거나 "
        "실제보다 지나치게 부풀려 소비자를 속이거나 잘못 알게 "
        "할 우려가 있다면 거짓·과장 광고에 해당할 수 있습니다.\n\n"
        "상품의 효능이나 성능은 확인할 수 있는 사실에 근거해 "
        "광고해야 하며, 객관적인 근거 없이 효과를 확정적으로 "
        "표현하거나 실제보다 우수한 것처럼 광고해서는 안 됩니다."
    )


def is_apparel_product_info_question(
    question: str,
) -> bool:
    """의류 상품의 필수 제공정보 질문을 확인한다."""
    normalized = normalize_text(question)

    apparel_terms = (
        "의류",
        "옷",
        "의복",
        "티셔츠",
        "셔츠",
        "바지",
        "치마",
        "원피스",
        "재킷",
        "자켓",
        "코트",
        "니트",
    )

    product_info_terms = (
        "소재",
        "섬유조성",
        "혼용률",
        "세탁방법",
        "세탁법",
        "취급시주의사항",
        "주의사항",
        "상품정보",
        "제품정보",
        "표시사항",
    )

    action_terms = (
        "표시",
        "제공",
        "고지",
        "알려",
        "써야",
        "적어야",
        "필수",
        "반드시",
        "해야하",
        "해야되",
        "의무",
    )

    return (
        any(term in normalized for term in apparel_terms)
        and any(
            term in normalized
            for term in product_info_terms
        )
        and any(term in normalized for term in action_terms)
    )


def build_apparel_product_info_answer() -> str:
    """의류 상품의 필수 제공정보를 검증된 문장으로 안내한다."""
    return (
        "네. 온라인에서 의류를 판매할 때에는 소비자가 구매하기 "
        "전에 제품 소재와 세탁방법, 취급 시 주의사항 등의 "
        "상품정보를 확인할 수 있도록 제공해야 합니다.\n\n"
        "의류 상품정보에는 제품 소재, 색상, 치수, 제조자, 제조국, "
        "세탁방법과 취급 시 주의사항, 제조연월, 품질보증기준 등이 "
        "포함됩니다."
    )


def is_return_received_refund_question(question: str) -> bool:
    """판매자가 반품 상품을 받은 뒤의 환급 기한 질문을 확인한다."""
    normalized = normalize_text(question)

    return_terms = (
        "반품한상품",
        "반품상품",
        "상품을반품",
        "상품을반환",
        "상품을돌려보",
        "반품을보냈",
        "반품보냈",
        "반품회수",
    )

    received_terms = (
        "판매자가받",
        "판매자에게도착",
        "판매자가돌려받",
        "쇼핑몰이받",
        "반품완료",
        "회수완료",
        "도착했",
        "도착한",
    )

    refund_terms = (
        "환불",
        "환급",
        "결제취소",
        "돈을돌려",
        "돌려받",
    )

    deadline_terms = (
        "언제까지",
        "언제",
        "며칠",
        "몇일",
        "기한",
        "기간",
        "영업일",
        "해야하",
        "해줘야",
    )

    return (
        any(term in normalized for term in return_terms)
        and any(term in normalized for term in received_terms)
        and any(term in normalized for term in refund_terms)
        and any(term in normalized for term in deadline_terms)
    )


def build_return_received_refund_answer() -> str:
    """반품 상품 수령 후 환급 기한을 검증된 문장으로 안내한다."""
    return (
        "판매자는 반품한 상품을 돌려받은 날부터 3영업일 이내에 "
        "이미 지급받은 상품 대금을 환급해야 합니다.\n\n"
        "신용카드 등으로 결제한 경우에는 결제 취소나 대금 청구 "
        "정지에 필요한 조치도 함께 해야 합니다."
    )


def is_out_of_stock_refund_question(question: str) -> bool:
    """품절·재고 부족에 따른 선결제 환급 질문을 확인한다."""
    normalized = normalize_text(question)

    out_of_stock_terms = (
        "품절",
        "재고없",
        "재고가없",
        "재고부족",
        "공급불가",
        "배송불가",
        "발송불가",
        "상품을못보내",
        "상품을보낼수없",
    )

    payment_or_refund_terms = (
        "환불",
        "환급",
        "결제취소",
        "결제한돈",
        "결제금액",
        "대금",
        "돈을돌려",
        "돌려받",
        "언제받",
        "언제환불",
        "언제환급",
    )

    return (
        any(term in normalized for term in out_of_stock_terms)
        and any(
            term in normalized
            for term in payment_or_refund_terms
        )
    )


def build_sold_out_refund_answer() -> str:
    """품절·재고 부족 환급 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "sold_out_refund"
    )


def build_out_of_stock_refund_answer() -> str:
    """
    이전 함수명을 사용하는 코드와의 호환성을 유지한다.
    새 intent 이름은 sold_out_refund이다.
    """
    return build_sold_out_refund_answer()


def is_change_of_mind_return_deadline_expired_question(
    question: str,
) -> bool:
    """7일이 지난 단순 변심 반품 질문을 판별한다."""
    normalized = normalize_text(question)

    change_of_mind_terms = (
        "단순변심",
        "마음이바뀌",
        "마음바뀌",
        "생각이바뀌",
        "구매후회",
        "필요없어",
        "필요없어서",
    )

    return_terms = (
        "반품",
        "청약철회",
        "환불",
        "구매취소",
        "주문취소",
        "돌려보",
        "돌려주",
    )

    expired_period_terms = (
        "7일이지났",
        "7일지났",
        "일주일이지났",
        "일주일지났",
        "일주일을넘",
        "일주일넘",
        "반품기간이지났",
        "반품기간지났",
        "청약철회기간이지났",
        "청약철회기간지났",
        "반품기한이지났",
        "반품기한지났",
        "기한이지났",
        "기한지났",
        "열흘",
        "팔일",
        "구일",
        "십일",
    )

    day_values = [
        int(value)
        for value in re.findall(r"(\d+)일", normalized)
    ]
    has_over_seven_days = any(
        value >= 8
        for value in day_values
    )

    return (
        any(
            term in normalized
            for term in change_of_mind_terms
        )
        and any(term in normalized for term in return_terms)
        and (
            has_over_seven_days
            or any(
                term in normalized
                for term in expired_period_terms
            )
        )
    )


def extract_elapsed_return_days(
    question: str,
) -> int | None:
    """질문에서 상품 수령 후 경과 일수를 추출한다."""
    normalized = normalize_text(question)

    numeric_match = re.search(
        r"(\d+)일",
        normalized,
    )

    if numeric_match:
        return int(numeric_match.group(1))

    korean_day_values = {
        "팔일": 8,
        "구일": 9,
        "열흘": 10,
        "십일": 10,
    }

    for term, value in korean_day_values.items():
        if term in normalized:
            return value

    return None


def build_change_of_mind_return_deadline_expired_answer(
    question: str,
) -> str:
    """단순 변심 반품기간 경과와 예외를 구분해 안내한다."""
    elapsed_days = extract_elapsed_return_days(
        question
    )

    if elapsed_days is None:
        elapsed_text = "7일이 지난 경우에는"
    else:
        elapsed_text = (
            f"{elapsed_days}일이 지났다면"
        )

    return (
        "단순 변심이라면 원칙적으로 상품을 받은 날부터 7일 "
        f"이내에 반품을 요청해야 하므로, {elapsed_text} 법정 "
        "청약철회 기간을 넘겨 반품이 어려울 수 있습니다.\n\n"
        "다만 쇼핑몰이 7일보다 긴 반품 기간을 정한 경우에는 "
        "그 기간을 따릅니다. 또한 상품이 표시·광고 또는 계약 "
        "내용과 다른 경우에는 상품을 받은 날부터 3개월 이내이면서 "
        "그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 "
        "청약철회할 수 있습니다."
    )


def is_discounted_product_return_question(
    question: str,
) -> bool:
    """세일·할인 상품의 단순 변심 반품 질문을 판별한다."""
    normalized = normalize_text(question)

    discount_terms = (
        "세일상품",
        "할인상품",
        "특가상품",
        "할인가상품",
        "행사상품",
        "프로모션상품",
        "쿠폰할인상품",
        "재고정리상품",
        "시즌오프상품",
        "아울렛상품",
        "세일중인상품",
        "할인중인상품",
    )

    return_terms = (
        "반품",
        "청약철회",
        "환불",
        "구매취소",
        "돌려보",
        "돌려주",
    )

    restriction_terms = (
        "단순변심",
        "할인이라는이유",
        "세일이라는이유",
        "특가라는이유",
        "반품불가",
        "환불불가",
        "취소불가",
        "반품할수없",
        "반품이안",
        "거절",
        "거부",
        "제한",
        "가능",
        "되나요",
        "돼나요",
        "해도되",
    )

    return (
        any(term in normalized for term in discount_terms)
        and any(term in normalized for term in return_terms)
        and any(term in normalized for term in restriction_terms)
    )


def build_discounted_product_return_answer() -> str:
    """할인 여부와 법정 청약철회 제한 사유를 구분해 안내한다."""
    return (
        "아니요. 세일이나 할인 상품이라는 이유만으로 쇼핑몰이 "
        "단순 변심 반품을 거절할 수는 없습니다.\n\n"
        "소비자의 책임으로 상품이 훼손되었거나 상품을 사용하여 "
        "가치가 현저히 감소한 경우 등 법에서 정한 제한 사유가 "
        "없다면, 원칙적으로 상품을 받은 날부터 7일 이내에 "
        "반품할 수 있습니다. 단순 변심에 따른 반품 배송비는 "
        "소비자가 부담합니다."
    )


def is_custom_made_return_question(
    question: str,
) -> bool:
    """주문제작 상품의 단순 변심 반품 제한 질문을 판별한다."""
    normalized = normalize_text(question)

    custom_made_terms = (
        "주문제작",
        "맞춤제작",
        "맞춤상품",
        "커스텀상품",
        "커스텀제작",
        "주문생산",
        "개별제작",
        "제작상품",
        "각인상품",
        "이니셜상품",
    )

    return_terms = (
        "반품",
        "청약철회",
        "환불",
        "구매취소",
        "주문취소",
        "돌려보",
        "돌려주",
    )

    restriction_terms = (
        "단순변심",
        "무조건",
        "반품불가",
        "환불불가",
        "취소불가",
        "반품할수없",
        "반품이안",
        "거절",
        "제한",
        "가능",
        "되나요",
        "돼나요",
    )

    return (
        any(term in normalized for term in custom_made_terms)
        and any(term in normalized for term in return_terms)
        and any(term in normalized for term in restriction_terms)
    )


def build_custom_made_return_answer() -> str:
    """주문제작 상품의 청약철회 제한 요건을 안내한다."""
    return (
        "아니요. 주문제작 상품이라는 이유만으로 무조건 반품할 "
        "수 없는 것은 아닙니다.\n\n"
        "단순 변심에 따른 청약철회를 제한하려면 청약철회를 "
        "인정할 경우 판매자에게 회복할 수 없는 중대한 피해가 "
        "예상되어야 합니다. 또한 판매자가 계약 전에 해당 거래에 "
        "대해 반품 제한 사실을 별도로 알린 뒤 소비자의 서면 또는 "
        "전자문서 동의를 받아야 합니다.\n\n"
        "이러한 요건을 갖추지 않았다면 주문제작 상품이라는 "
        "이유만으로 반품을 거절하기는 어렵습니다."
    )


def is_packaging_opening_return_question(
    question: str,
) -> bool:
    """상품 확인 목적의 포장 개봉 후 반품 질문을 판별한다."""
    normalized = normalize_text(question)

    packaging_terms = (
        "포장을뜯",
        "포장뜯",
        "포장을열",
        "포장열",
        "포장개봉",
        "포장훼손",
        "개봉했",
        "개봉한",
        "봉인을뜯",
        "봉인훼손",
        "비닐을뜯",
        "박스를열",
        "박스를뜯",
    )

    confirmation_terms = (
        "상품을확인",
        "내용을확인",
        "상태를확인",
        "제품을확인",
        "확인하려",
        "확인하기위해",
        "보려고",
        "보기위해",
        "꺼내보려고",
        "사이즈확인",
        "색상확인",
    )

    return_terms = (
        "반품",
        "청약철회",
        "환불",
        "구매취소",
        "거절",
        "거부",
        "안된",
        "못하",
        "제한",
        "가능",
        "되나요",
        "돼나요",
    )

    return (
        any(term in normalized for term in packaging_terms)
        and any(
            term in normalized
            for term in confirmation_terms
        )
        and any(term in normalized for term in return_terms)
    )


def build_packaging_opening_return_answer() -> str:
    """확인 목적의 포장 개봉과 상품 가치 감소를 구분해 안내한다."""
    return (
        "아니요. 상품의 내용이나 상태를 확인하기 위해 포장을 "
        "뜯은 것만으로 쇼핑몰이 반품을 거절할 수는 없습니다.\n\n"
        "다만 상품을 실제로 사용하거나 소비자의 책임으로 상품 "
        "자체를 훼손하여 상품 가치가 현저히 감소한 경우에는 "
        "반품이 제한될 수 있습니다."
    )


def is_return_obstruction_question(question: str) -> bool:
    """반품 또는 청약철회 방해의 자연어 변형 질문을 확인한다."""
    normalized = normalize_text(question)

    return_terms = (
        "반품",
        "청약철회",
        "계약해지",
        "구매취소",
        "환불",
        "돌려보",
        "돌려주",
    )

    obstruction_terms = (
        "방해",
        "막",
        "거절",
        "거부",
        "숨기",
        "없애",
        "못하게",
        "안되게",
        "어렵게",
        "신청불가",
        "접수불가",
        "버튼이없",
        "버튼없",
        "버튼을숨",
        "절차를숨",
        "연락이안",
        "응답하지않",
        "처리하지않",
    )

    issue_terms = (
        "문제",
        "괜찮",
        "가능",
        "되나요",
        "돼나요",
        "해도되",
        "위법",
        "불법",
        "어떻게",
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )

    has_obstruction = any(
        term in normalized
        for term in obstruction_terms
    )

    # 문제 여부 표현이 없어도 방해 행위가 명확하면 인식한다.
    return has_return_topic and has_obstruction


def build_return_obstruction_answer() -> str:
    """반품·청약철회 방해 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "return_obstruction"
    )


def is_change_of_mind_return_question(question: str) -> bool:
    """단순 변심 반품 가능 여부와 자연어 변형 질문을 확인한다."""
    normalized = normalize_text(question)

    has_change_of_mind = any(
        term in normalized
        for term in (
            "단순변심",
            "마음이바뀌",
            "마음바뀌",
            "생각이바뀌",
            "구매후회",
            "필요없어",
            "필요없어서",
        )
    )

    has_return_topic = any(
        term in normalized
        for term in (
            "반품",
            "청약철회",
            "구매취소",
            "주문취소",
            "돌려보",
            "돌려줄",
            "돌려줘",
            "되돌려",
            "환불",
        )
    )

    has_cost_topic = any(
        term in normalized
        for term in (
            "반품비",
            "배송비",
            "반환비용",
            "누가부담",
            "비용",
        )
    )

    return (
        has_change_of_mind
        and has_return_topic
        and not has_cost_topic
    )


def build_change_of_mind_return_answer() -> str:
    """단순 변심 반품 질문에 사용할 검증된 답변이다."""
    return (
        "네. 단순 변심의 경우에도 일반적으로 상품을 받은 날부터 "
        "7일 이내에는 청약철회와 반품이 가능합니다.\n\n"
        "다만 소비자의 책임으로 상품이 훼손되었거나, 상품을 "
        "사용·소비하여 가치가 크게 감소한 경우 등에는 반품이 "
        "제한될 수 있습니다. 단순 변심에 따른 상품 반환 비용은 "
        "소비자가 부담합니다."
    )


def is_personal_seller_info_question(question: str) -> bool:
    """개인 판매자의 신원정보 확인·제공 질문을 판별한다."""
    normalized = normalize_text(question)

    personal_terms = (
        "개인판매자",
        "개인이판매",
        "개인간거래",
        "중고거래",
        "중고마켓",
        "개인거래",
        "사업자가아닌개인",
    )

    seller_terms = (
        "판매자",
        "개인판매자",
        "개인이판매",
    )

    info_terms = (
        "정보",
        "신원",
        "이름",
        "성명",
        "연락처",
        "전화번호",
        "주소",
        "거래내역",
    )

    action_terms = (
        "제공",
        "확인",
        "알수",
        "알려",
        "공개",
        "고지",
        "보여",
        "받을수",
        "받을",
        "열람",
        "요청",
    )

    has_personal_scope = any(
        term in normalized
        for term in personal_terms
    )

    has_seller = any(
        term in normalized
        for term in seller_terms
    )

    has_info = any(
        term in normalized
        for term in info_terms
    )

    has_action = any(
        term in normalized
        for term in action_terms
    )

    return (
        has_personal_scope
        and has_seller
        and has_info
        and has_action
    )


def build_personal_seller_info_answer() -> str:
    """개인 판매자 신원정보 규정을 오해 없이 안내한다."""
    return (
        "개인 판매자의 신원정보가 소비자에게 항상 공개되는 것은 "
        "아닙니다.\n\n"
        "통신판매중개업자는 개인 판매자의 전화번호 등 법령에서 "
        "정한 신원정보를 확인해야 합니다. 거래 분쟁이 발생한 "
        "경우에는 소비자피해 분쟁조정기구 또는 법원의 요청에 따라 "
        "개인 판매자의 신원정보와 거래내역을 제공하여 분쟁 해결에 "
        "협조해야 합니다."
    )


def is_business_seller_info_question(question: str) -> bool:
    """사업자 판매자의 신원정보 제공 질문과 자연어 변형을 확인한다."""
    if is_personal_seller_info_question(question):
        return False

    normalized = normalize_text(question)

    seller_terms = (
        "판매자",
        "입점판매자",
        "입점한판매자",
        "입점업체",
        "판매업체",
        "셀러",
        "통신판매중개의뢰자",
    )

    info_terms = (
        "정보",
        "신원",
        "이름",
        "성명",
        "상호",
        "연락처",
        "전화번호",
        "주소",
        "대표자",
    )

    timing_or_action_terms = (
        "제공",
        "확인",
        "알수",
        "알려",
        "공개",
        "고지",
        "보여",
        "구매전",
        "주문전",
        "결제전",
        "청약전",
        "사기전",
    )

    has_seller = any(
        term in normalized
        for term in seller_terms
    )

    has_info = any(
        term in normalized
        for term in info_terms
    )

    has_timing_or_action = any(
        term in normalized
        for term in timing_or_action_terms
    )

    # 플랫폼을 직접 언급하지 않아도 입점 판매자 정보 질문이면 인식한다.
    return has_seller and has_info and has_timing_or_action


def build_business_seller_info_answer() -> str:
    """사업자 판매자의 신원정보 제공 의무를 간결하게 안내한다."""
    return (
        "네. 통신판매중개업자는 판매자가 사업자인 경우 판매자의 "
        "성명, 주소, 전화번호 등 신원정보를 확인하여 소비자의 "
        "청약이 이루어지기 전까지 제공해야 합니다.\n\n"
        "판매자가 법인이라면 법인의 명칭과 대표자의 성명이 "
        "포함됩니다."
    )


def is_wrong_item_return_cost_question(
    question: str,
) -> bool:
    """주문한 것과 다른 상품이 배송된 경우의 반품비 질문을 판별한다."""
    normalized = normalize_text(question)

    wrong_item_terms = (
        "오배송",
        "잘못배송",
        "잘못배달",
        "주문한상품과다른",
        "주문한제품과다른",
        "주문한것과다른",
        "주문한물건과다른",
        "주문상품과다른",
        "주문제품과다른",
        "주문과다른상품",
        "주문과다른제품",
        "다른상품이배송",
        "다른제품이배송",
        "다른물건이배송",
        "다른상품이도착",
        "다른제품이도착",
        "다른물건이도착",
        "다른상품이왔",
        "다른제품이왔",
        "다른물건이왔",
        "엉뚱한상품",
        "엉뚱한제품",
        "엉뚱한물건",
        "상품이바뀌어",
        "제품이바뀌어",
    )

    return_terms = (
        "반품",
        "청약철회",
        "환불",
        "돌려보",
        "돌려주",
        "반송",
    )

    cost_terms = (
        "반품비",
        "반품배송비",
        "배송비",
        "택배비",
        "반환비용",
        "반송비",
        "비용",
        "누가부담",
        "누가내",
        "누가내야",
    )

    return (
        any(term in normalized for term in wrong_item_terms)
        and any(term in normalized for term in return_terms)
        and any(term in normalized for term in cost_terms)
    )


def build_wrong_item_return_cost_answer() -> str:
    """오배송 반품비 부담 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "wrong_item_return_cost"
    )


def is_carrier_blame_return_cost_question(
    question: str,
) -> bool:
    """
    배송 중 파손 상품에 대해 판매자가 택배회사 책임을 이유로
    반품비 부담을 거절하는 질문을 판별한다.
    """
    normalized = normalize_text(question)

    damage_terms = (
        "배송중파손",
        "배송도중파손",
        "운송중파손",
        "택배중파손",
        "파손돼왔",
        "파손되어왔",
        "파손돼서왔",
        "파손되어서왔",
        "파손된채로왔",
        "파손상품",
        "파손된상품",
        "상품파손",
        "제품파손",
        "물건파손",
        "깨져왔",
        "깨져서왔",
        "깨진채로왔",
        "망가져왔",
        "망가져서왔",
        "찌그러져왔",
        "찌그러져서왔",
        "훼손돼왔",
        "훼손되어왔",
        "훼손돼서왔",
        "훼손되어서왔",
        "파손",
    )

    carrier_blame_terms = (
        "택배회사책임",
        "택배사책임",
        "배송업체책임",
        "운송업체책임",
        "택배기사책임",
        "택배회사잘못",
        "택배사잘못",
        "배송업체잘못",
        "운송업체잘못",
        "택배기사잘못",
        "택배회사에문의",
        "택배사에문의",
        "배송업체에문의",
        "택배회사와해결",
        "택배사와해결",
        "배송업체와해결",
        "판매자책임아니",
        "판매자잘못아니",
        "판매자는책임없",
        "자기책임아니",
        "우리책임아니",
    )

    return_cost_terms = (
        "반품비",
        "반품배송비",
        "반송비",
        "반환비용",
        "택배비",
        "배송비",
        "반품비용",
    )

    refusal_terms = (
        "내지않겠",
        "안내겠",
        "못내겠",
        "부담하지않겠",
        "부담안하겠",
        "부담못하겠",
        "부담하지않",
        "부담안",
        "부담못",
        "지급하지않",
        "지급안",
        "지급못",
        "거절",
        "거부",
        "소비자가내",
        "구매자가내",
        "고객이내",
        "소비자부담",
        "구매자부담",
        "고객부담",
        "내라고",
        "청구",
        "요구",
    )

    legality_terms = (
        "해도되",
        "되나요",
        "돼나요",
        "가능한가",
        "가능하나",
        "괜찮",
        "맞나요",
        "정당한",
        "문제없",
    )

    return (
        any(term in normalized for term in damage_terms)
        and any(
            term in normalized
            for term in carrier_blame_terms
        )
        and any(
            term in normalized
            for term in return_cost_terms
        )
        and any(term in normalized for term in refusal_terms)
        and any(term in normalized for term in legality_terms)
    )


def build_carrier_blame_return_cost_answer() -> str:
    """배송 중 파손 책임 전가 규칙 답변을 반환한다."""
    return build_registered_rule_answer(
        "carrier_blame_return_cost"
    )


def is_defective_product_return_cost_question(
    question: str,
) -> bool:
    """불량·하자 상품의 반품 배송비 부담 질문을 판별한다."""
    normalized = normalize_text(question)

    defect_terms = (
        "불량상품",
        "상품불량",
        "제품불량",
        "불량품",
        "불량",
        "하자상품",
        "상품하자",
        "제품하자",
        "하자가있",
        "하자있는",
        "하자",
        "고장난상품",
        "고장난제품",
        "고장",
        "파손상품",
        "파손된상품",
        "파손",
        "오배송",
        "주문과다른상품",
        "다른상품이왔",
        "표시광고와다르",
        "계약내용과다르",
    )

    return_terms = (
        "반품",
        "청약철회",
        "돌려보",
        "돌려주",
        "반송",
        "환불",
    )

    cost_terms = (
        "반품비",
        "반품배송비",
        "배송비",
        "택배비",
        "반환비용",
        "반송비",
        "비용",
    )

    consumer_burden_terms = (
        "소비자에게내",
        "소비자가내",
        "소비자부담",
        "구매자에게내",
        "구매자가내",
        "구매자부담",
        "고객에게내",
        "고객이내",
        "고객부담",
        "내라고",
        "내야",
        "부담하라고",
        "부담해야",
        "누가부담",
        "누가내",
        "누가내야",
        "누구부담",
        "누구가부담",
        "판매자부담",
        "판매자가부담",
        "요구",
        "청구",
    )

    return (
        any(term in normalized for term in defect_terms)
        and any(term in normalized for term in return_terms)
        and any(term in normalized for term in cost_terms)
        and any(
            term in normalized
            for term in consumer_burden_terms
        )
    )


def build_defective_product_return_cost_answer() -> str:
    """불량·하자 상품의 반품 배송비 부담 주체를 안내한다."""
    return (
        "아니요. 불량 상품이거나 상품이 표시·광고 또는 계약 "
        "내용과 다르게 제공된 경우에는 반품에 필요한 배송비를 "
        "판매자가 부담해야 합니다.\n\n"
        "따라서 판매자가 해당 반품 택배비를 소비자에게 부담하도록 "
        "요구해서는 안 됩니다. 다만 상품에 문제가 없는 단순 "
        "변심 반품이라면 반환 비용은 소비자가 부담합니다."
    )


def is_return_cost_question(question: str) -> bool:
    """반품 배송비 부담 주체를 묻는 자연어 질문을 확인한다."""
    normalized = normalize_text(question)

    return_terms = (
        "반품",
        "반송",
        "청약철회",
        "돌려보",
        "돌려주",
        "환불",
    )

    cost_terms = (
        "반품비",
        "반품비용",
        "반품배송비",
        "배송비",
        "택배비",
        "반환비용",
        "반송비",
        "반송비용",
        "돌려보내는비용",
        "반환하는비용",
        "누가부담",
        "누가내",
        "누가내야",
        "비용부담",
    )

    return (
        any(term in normalized for term in return_terms)
        and any(term in normalized for term in cost_terms)
    )


def build_return_cost_answer(
    documents: list[dict[str, Any]] | None = None,
) -> str:
    """일반 반품비 부담 규칙 답변을 반환한다."""
    del documents

    return build_registered_rule_answer(
        "return_cost"
    )


def clean_answer(answer: str) -> str:
    """답변에 남아 있는 출처 표시와 불필요한 공백을 제거한다."""
    answer = answer.strip()

    answer = re.sub(
        r"\s*[\[\(]?\s*출처\s*\d+\s*[\]\)]?",
        "",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"\(\s*\)|\[\s*\]",
        "",
        answer,
    )

    answer = re.sub(
        r"[ \t]+\n",
        "\n",
        answer,
    )

    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer,
    )

    return answer.strip()


def answer_question(
    question: str,
) -> dict[str, Any]:
    """Qdrant 검색부터 답변 반환까지 전체 RAG 과정을 실행한다."""
    question = " ".join(question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    structured_query_plan = None

    try:
        candidate_query_plan = build_search_query(question)
    except (TypeError, ValueError):
        candidate_query_plan = None

    if (
        candidate_query_plan is not None
        and candidate_query_plan.confidence
        >= STRUCTURED_INTENT_MIN_CONFIDENCE
    ):
        structured_query_plan = candidate_query_plan

    structured_intent = (
        structured_query_plan.legacy_intent
        if structured_query_plan is not None
        else resolve_structured_intent(question)
    )

    # 새 구조가 분류한 intent를 우선 사용한다.
    # 아직 분류되지 않은 질문은 기존 판별 함수로 처리한다.
    matches_replacement_defective_refund = (
        structured_intent == "replacement_defective_refund"
        or is_replacement_defective_refund_question(question)
    )
    matches_mismatch_deadline = (
        structured_intent == "mismatch_return_deadline"
        or is_mismatch_deadline_question(question)
    )
    matches_sold_out_refund = (
        structured_intent == "sold_out_refund"
        or is_out_of_stock_refund_question(question)
    )
    matches_return_obstruction = (
        structured_intent == "return_obstruction"
        or is_return_obstruction_question(question)
    )
    matches_wrong_item_return_cost = (
        structured_intent == "wrong_item_return_cost"
        or is_wrong_item_return_cost_question(question)
    )
    matches_carrier_blame_return_cost = (
        structured_intent == "carrier_blame_return_cost"
        or is_carrier_blame_return_cost_question(question)
    )
    matches_defective_product_return_cost = (
        structured_intent == "defective_product_return_cost"
        or is_defective_product_return_cost_question(question)
    )
    matches_change_of_mind_return = (
        structured_intent == "change_of_mind_return"
        or is_change_of_mind_return_question(question)
    )
    matches_return_cost = (
        structured_intent == "return_cost"
        or is_return_cost_question(question)
    )

    # query_builder가 전용 템플릿을 제공한 intent는 구조화된
    # 법률 검색 문장을 사용한다.
    #
    # 아직 query_builder에 연결되지 않은 질문은 기존의 상세한
    # 검색 문장 변환 체인을 그대로 사용하여 기존 기능을 보존한다.
    if (
        structured_query_plan is not None
        and structured_query_plan.legacy_intent is not None
        and structured_query_plan.used_template
    ):
        search_question = (
            structured_query_plan.search_question
        )
    else:
        search_question = question

        if matches_replacement_defective_refund:
            search_question = (
                "불량으로 교환받은 상품에도 다시 불량이 있다면 "
                "소비자가 환불을 요구할 수 있나요?"
            )
        elif is_defective_product_refund_question(question):
            search_question = (
                "불량 상품에 대해 쇼핑몰이 교환만 가능하다고 하며 "
                "환불을 거절할 수 있나요?"
            )
        elif matches_mismatch_deadline:
            search_question = (
                "상품 설명과 실제 상품이 다르면 "
                "언제까지 반품할 수 있나요?"
            )
        elif is_minor_purchase_cancellation_question(question):
            search_question = (
                "미성년자가 법정대리인의 동의 없이 온라인 쇼핑몰에서 "
                "상품을 구매하면 본인이나 법정대리인이 계약을 "
                "취소할 수 있나요?"
            )
        elif is_preselected_paid_addon_question(question):
            search_question = (
                "쇼핑몰이 유료 부가상품이나 서비스를 미리 선택해 두고 "
                "소비자가 해제하지 않으면 결제되게 해도 되나요?"
            )
        elif is_card_payment_refusal_question(question):
            search_question = (
                "신용카드가맹점인 쇼핑몰이 카드 결제를 거부하고 "
                "현금으로만 결제하도록 요구해도 되나요?"
            )
        elif is_card_payment_refund_cancellation_question(question):
            search_question = (
                "카드로 결제한 상품을 환불하면 쇼핑몰은 "
                "결제업자에게 대금 청구 정지나 결제 취소를 "
                "요청해야 하나요?"
            )
        elif is_refund_delay_compensation_question(question):
            search_question = (
                "쇼핑몰이 상품 반환 후 3영업일의 환급기한을 넘기면 "
                "소비자에게 지연배상금을 지급해야 하나요?"
            )
        elif is_contract_document_delivery_question(question):
            search_question = (
                "계약이 체결되면 쇼핑몰은 계약 내용이 적힌 서면을 "
                "상품이 공급될 때까지 소비자에게 제공해야 하나요?"
            )
        elif is_order_receipt_confirmation_question(question):
            search_question = (
                "온라인 주문을 받으면 쇼핑몰은 주문 접수 사실과 "
                "주문 내용을 소비자에게 확인해줘야 하나요?"
            )
        elif is_pre_payment_order_review_correction_question(question):
            search_question = (
                "결제하기 전에 주문한 상품, 수량, 가격을 확인하고 "
                "수정하거나 주문을 취소할 수 있어야 하나요?"
            )
        elif is_pre_payment_total_amount_question(question):
            search_question = (
                "결제하기 전에 상품 가격과 배송비를 포함한 "
                "총 결제금액을 표시해야 하나요?"
            )
        elif is_pre_purchase_shipping_information_question(question):
            search_question = (
                "쇼핑몰은 결제 전에 배송 방법, 배송비 부담자, "
                "예상 배송기간을 알려야 하나요?"
            )
        elif is_delivery_courier_privacy_outsourcing_question(question):
            search_question = (
                "상품 배송을 위해 택배회사에 이름, 주소, 연락처를 "
                "전달하는 것은 개인정보 처리위탁인가요?"
            )
        elif is_account_withdrawal_privacy_destruction_question(question):
            search_question = (
                "회원 탈퇴 후 쇼핑몰은 개인정보를 "
                "언제 파기해야 하나요?"
            )
        elif is_third_party_personal_data_provision_question(question):
            search_question = (
                "쇼핑몰이 동의 없이 개인정보를 다른 회사에 "
                "제공해도 되나요?"
            )
        elif is_optional_privacy_consent_refusal_question(question):
            search_question = (
                "필수항목이 아닌 개인정보 제공에 동의하지 않았다는 "
                "이유로 회원가입을 거절할 수 있나요?"
            )
        elif is_false_exaggerated_ad_question(question):
            search_question = (
                "상품 효과를 실제보다 좋다고 과장해서 "
                "광고해도 되나요?"
            )
        elif is_apparel_product_info_question(question):
            search_question = (
                "온라인에서 의류를 판매할 때 제품 소재와 세탁방법, "
                "취급 시 주의사항을 제공해야 하나요?"
            )
        elif is_return_received_refund_question(question):
            search_question = (
                "반품 상품을 판매자가 돌려받은 경우 "
                "언제까지 환급해야 하나요?"
            )
        elif matches_sold_out_refund:
            search_question = "품절이면 판매자는 언제 환불해야 하나요?"
        elif is_change_of_mind_return_deadline_expired_question(
            question
        ):
            elapsed_days = (
                extract_elapsed_return_days(question)
            )

            if elapsed_days is None:
                search_question = (
                    "상품을 받은 지 7일이 지난 뒤 단순 변심으로 "
                    "반품할 수 있나요?"
                )
            else:
                search_question = (
                    f"상품을 받은 지 {elapsed_days}일이 지난 뒤 "
                    "단순 변심으로 반품할 수 있나요?"
                )
        elif (
            is_discounted_product_return_question(question)
            and not matches_return_obstruction
        ):
            search_question = (
                "세일이나 할인 상품이라는 이유만으로 쇼핑몰이 "
                "단순 변심 반품을 거절할 수 있나요?"
            )
        elif is_custom_made_return_question(question):
            search_question = (
                "주문제작 상품의 단순 변심 반품을 제한하려면 "
                "판매자가 별도로 고지하고 소비자의 서면 또는 "
                "전자문서 동의를 받아야 하나요?"
            )
        elif is_packaging_opening_return_question(question):
            search_question = (
                "상품의 내용이나 상태를 확인하기 위해 포장을 뜯은 "
                "경우에도 쇼핑몰이 반품을 거절할 수 있나요?"
            )
        elif matches_return_obstruction:
            search_question = "쇼핑몰이 반품을 방해하면 어떻게 되나요?"
        elif is_personal_seller_info_question(question):
            search_question = (
                "중고거래 플랫폼은 개인 판매자의 신원정보를 확인하고 "
                "분쟁 발생 시 제공해야 하나요?"
            )
        elif is_business_seller_info_question(question):
            search_question = (
                "플랫폼은 판매자 정보를 소비자에게 "
                "제공해야 하나요?"
            )
        elif matches_wrong_item_return_cost:
            search_question = (
                "주문한 상품과 다른 상품이 배송된 경우 반품 배송비는 "
                "판매자가 부담하나요?"
            )
        elif matches_carrier_blame_return_cost:
            search_question = (
                "배송 중 파손된 상품에 대해 판매자가 택배회사 "
                "책임을 이유로 반품 배송비 부담을 거절할 수 있나요?"
            )
        elif matches_defective_product_return_cost:
            search_question = (
                "불량 상품이나 계약 내용과 다른 상품을 반품할 때 "
                "반환 배송비는 판매자가 부담하나요?"
            )
        elif matches_return_cost:
            search_question = "반품 배송비는 누가 부담하나요?"
        elif matches_change_of_mind_return:
            search_question = "단순 변심으로도 반품할 수 있나요?"


    search_result = search_documents(
        question=search_question,
        top_k=SEARCH_TOP_K,
    )

    intent = search_result.get("intent")

    initial_documents = search_result["documents"]

    filter_result = filter_documents_for_question(
        question,
        initial_documents,
    )

    searched_documents = sanitize_source_documents(
        filter_result.kept_documents
    )

    # 제품 종류가 없는 질문에서 검색 결과가 특정 품목별 표로만
    # 구성된 경우, 전자상거래법·표준약관 중심으로 한 번 재검색한다.
    if (
        not searched_documents
        and filter_result.excluded_documents
    ):
        general_search_question = (
            build_general_legal_search_question(
                original_question=question,
                structured_intent=structured_intent,
            )
        )

        general_search_result = search_documents(
            question=general_search_question,
            top_k=GENERAL_SEARCH_TOP_K,
        )

        general_filter_result = (
            filter_documents_for_question(
                question,
                general_search_result["documents"],
            )
        )

        searched_documents = sanitize_source_documents(
            general_filter_result.kept_documents
        )

        if intent is None:
            intent = general_search_result.get("intent")

    relevant_documents = select_relevant_documents(
        searched_documents
    )

    # 불량으로 교환받은 상품까지 다시 불량인 경우에는
    # 검색 문서 안에서 질문과 직접 관련된 근거 문장만 선별한 뒤
    # 검증된 핵심 결론과 결합한다.
    if matches_replacement_defective_refund:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="replacement_defective_refund",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="replacement_defective_refund",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            # Ollama 호출이나 답변 생성에 문제가 생겨도
            # 기존 검증 답변으로 안전하게 복구한다.
            hybrid_answer = (
                build_replacement_defective_refund_answer()
            )

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "replacement_defective_refund",
            # 화면에는 원래 검색 문서의 제목과 파일명을 표시한다.
            "sources": source_documents,
        }

    # 불량 상품에 교환만 강제하는 질문은 기한 질문보다 먼저
    # 처리하여 환불 거절 가능 여부에 직접 답변한다.
    if is_defective_product_refund_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_defective_product_refund_answer(),
            "intent": "defective_product_refund",
            "sources": source_documents,
        }

    # 상품 설명·광고 또는 계약 내용과 실제 상품이 다른 경우에는
    # 관련 기한 문장만 선별하고 3개월·30일 조건을 필수 검증한다.
    if matches_mismatch_deadline:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="mismatch_return_deadline",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="mismatch_return_deadline",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = build_mismatch_deadline_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "mismatch_return_deadline",
            "sources": source_documents,
        }

    # 미성년자 계약 취소 질문은 검색 결과가 없더라도
    # 취소 원칙과 주요 예외만 분리하여 안내한다.
    if is_minor_purchase_cancellation_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_minor_purchase_cancellation_answer(),
            "intent": "minor_purchase_cancellation",
            "sources": source_documents,
        }

    # 유료 부가상품 사전 선택 질문은 검색 결과가 없더라도
    # 소비자의 직접 선택·동의 원칙을 안내한다.
    if is_preselected_paid_addon_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_preselected_paid_addon_answer(),
            "intent": "preselected_paid_addon",
            "sources": source_documents,
        }

    # 카드 결제 거부·현금 결제 강요 질문은 검색 결과가 없어도
    # 신용카드가맹점에 적용되는 금지 원칙을 안내한다.
    if is_card_payment_refusal_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_card_payment_refusal_answer(),
            "intent": "card_payment_refusal",
            "sources": source_documents,
        }

    # 카드 결제 환불 질문은 검색 결과가 없더라도 결제업자에 대한
    # 청구 정지·취소 요청과 이미 받은 대금의 환급 절차를 안내한다.
    if is_card_payment_refund_cancellation_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_card_payment_refund_cancellation_answer(),
            "intent": "card_payment_refund_cancellation",
            "sources": source_documents,
        }

    # 환불 지연 질문은 잘못된 조문 번호나 배송 지연 내용이
    # 섞이지 않도록 검증된 답변을 반환한다.
    if is_refund_delay_compensation_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_refund_delay_compensation_answer(),
            "intent": "refund_delay_compensation",
            "sources": source_documents,
        }

    # 계약내용 서면 교부 질문은 검색 결과가 없더라도
    # 제공 시점과 전자문서 가능 여부가 포함된 답변을 반환한다.
    if is_contract_document_delivery_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_contract_document_delivery_answer(),
            "intent": "contract_document_delivery",
            "sources": source_documents,
        }

    # 온라인 주문 접수 확인 질문은 검색 결과가 없더라도
    # 검증된 답변을 반환한다.
    if is_order_receipt_confirmation_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_order_receipt_confirmation_answer(),
            "intent": "order_receipt_confirmation",
            "sources": source_documents,
        }

    # 결제 전 주문 내용 확인·수정 질문은 검색 결과가 없더라도
    # 검증된 답변을 반환한다.
    if is_pre_payment_order_review_correction_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_pre_payment_order_review_correction_answer(),
            "intent": "pre_payment_order_review_correction",
            "sources": source_documents,
        }

    # 결제 전 총 결제금액 질문은 배송비라는 단어가 포함되어도
    # 구매 전 배송정보 질문보다 우선 처리한다.
    if is_pre_payment_total_amount_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_pre_payment_total_amount_answer(),
            "intent": "pre_payment_total_amount",
            "sources": source_documents,
        }

    # 구매 전 배송정보 질문은 배송 지연 시 배상 예외가 빠지지
    # 않도록 검증된 답변을 반환한다.
    if is_pre_purchase_shipping_information_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_pre_purchase_shipping_information_answer(),
            "intent": "pre_purchase_shipping_information",
            "sources": source_documents,
        }

    # 배송 목적의 택배회사 개인정보 전달 질문은 제3자 제공과
    # 처리위탁을 혼동하지 않도록 검증된 답변을 반환한다.
    if is_delivery_courier_privacy_outsourcing_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_delivery_courier_privacy_outsourcing_answer(),
            "intent": "delivery_courier_privacy_outsourcing",
            "sources": source_documents,
        }

    # 회원 탈퇴 후 개인정보 파기 질문은 회원자격 상실 절차와
    # 혼동하지 않도록 검증된 답변을 반환한다.
    if is_account_withdrawal_privacy_destruction_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_account_withdrawal_privacy_destruction_answer(),
            "intent": "account_withdrawal_privacy_destruction",
            "sources": source_documents,
        }

    # 개인정보 제3자 제공 질문은 동의 원칙과 법률상 예외가
    # 반대로 설명되지 않도록 검증된 답변을 반환한다.
    if is_third_party_personal_data_provision_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_third_party_personal_data_provision_answer(),
            "intent": "third_party_personal_data_provision",
            "sources": source_documents,
        }

    # 선택 개인정보 동의 거부 질문은 결론이 반대로 생성되지
    # 않도록 검증된 답변을 반환한다.
    if is_optional_privacy_consent_refusal_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_optional_privacy_consent_refusal_answer(),
            "intent": "optional_privacy_consent_refusal",
            "sources": source_documents,
        }

    # 거짓·과장 광고 질문은 법률 개정번호나 고의 요건을
    # 잘못 덧붙이지 않도록 검증된 답변을 반환한다.
    if is_false_exaggerated_ad_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_false_exaggerated_ad_answer(),
            "intent": "false_exaggerated_advertising",
            "sources": source_documents,
        }

    # 의류 상품정보 질문은 근거 없는 성적서·허가서 등의 내용을
    # 추가하지 않도록 검증된 답변을 반환한다.
    if is_apparel_product_info_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_apparel_product_info_answer(),
            "intent": "apparel_product_info",
            "sources": source_documents,
        }

    # 반품 상품 수령 후 환급 질문은 품절 환급 기준과 혼동하지
    # 않도록 검증된 답변을 반환한다.
    if is_return_received_refund_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_return_received_refund_answer(),
            "intent": "return_received_refund",
            "sources": source_documents,
        }

    # 품절·재고 부족 환급 질문은 관련 근거 문장만 선별하고,
    # 지체 없는 통지와 선결제 대금 3영업일 환급을 필수 검증한다.
    if matches_sold_out_refund:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="sold_out_refund",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="sold_out_refund",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = build_sold_out_refund_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "sold_out_refund",
            "sources": source_documents,
        }

    # 7일이 지난 단순 변심 질문은 일반 단순 변심 질문보다
    # 먼저 처리하여 기간 경과에 직접 답변한다.
    if is_change_of_mind_return_deadline_expired_question(
        question
    ):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": (
                build_change_of_mind_return_deadline_expired_answer(
                    question
                )
            ),
            "intent": "change_of_mind_return_deadline_expired",
            "sources": source_documents,
        }

    # 일반적인 세일·할인 상품 질문은 전용 답변으로 처리한다.
    # 단, 판매자의 일률적 반품 거절로 분류된 질문은
    # return_obstruction 흐름이 우선한다.
    if (
        is_discounted_product_return_question(question)
        and not matches_return_obstruction
    ):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_discounted_product_return_answer(),
            "intent": "discounted_product_return",
            "sources": source_documents,
        }

    # 주문제작 상품 질문은 일반적인 단순 변심 반품 질문보다
    # 먼저 처리하여 별도 고지·동의 요건을 정확히 안내한다.
    if is_custom_made_return_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_custom_made_return_answer(),
            "intent": "custom_made_return",
            "sources": source_documents,
        }

    # 상품 확인 목적의 포장 개봉 질문은 일반적인 반품 방해
    # 질문으로 분류하지 않고 검증된 답변을 반환한다.
    if is_packaging_opening_return_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_packaging_opening_return_answer(),
            "intent": "packaging_opening_return",
            "sources": source_documents,
        }

    # 반품·청약철회 방해 질문은 관련 금지행위 문장만 선별하고,
    # 일률적 반품 제한과 추가 비용 요구 금지를 필수 검증한다.
    if matches_return_obstruction:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="return_obstruction",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="return_obstruction",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = build_return_obstruction_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "return_obstruction",
            "sources": source_documents,
        }

    # 개인 판매자 신원정보 질문은 소비자가 정보를 항상 열람할 수
    # 있다고 오해하지 않도록 검증된 답변을 반환한다.
    if is_personal_seller_info_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_personal_seller_info_answer(),
            "intent": "personal_seller_info",
            "sources": source_documents,
        }

    # 사업자 판매자 신원정보 변형 질문은 점수 필터 결과가 비어 있어도
    # 이미 검증된 답변을 반환한다.
    if is_business_seller_info_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_business_seller_info_answer(),
            "intent": "business_seller_info",
            "sources": source_documents,
        }

    # 주문한 것과 다른 상품이 배송된 경우에는 관련 비용 문장만
    # 선별하고 판매자 부담이라는 핵심 사실을 필수 검증한다.
    if matches_wrong_item_return_cost:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="wrong_item_return_cost",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="wrong_item_return_cost",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = build_wrong_item_return_cost_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "wrong_item_return_cost",
            "sources": source_documents,
        }

    # 배송 중 파손을 택배회사 책임으로 돌리는 질문은 관련
    # 비용 부담 문장만 선별하고 판매자의 처리 의무를 검증한다.
    if matches_carrier_blame_return_cost:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="carrier_blame_return_cost",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="carrier_blame_return_cost",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = (
                build_carrier_blame_return_cost_answer()
            )

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "carrier_blame_return_cost",
            "sources": source_documents,
        }

    # 불량·하자 상품의 반품 배송비 질문은 일반 반품비 질문보다
    # 먼저 처리하여 판매자 부담이라는 결론부터 안내한다.
    if matches_defective_product_return_cost:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_defective_product_return_cost_answer(),
            "intent": "defective_product_return_cost",
            "sources": source_documents,
        }

    # 일반적인 반품비 질문은 단순 변심과 판매자 책임 사유를
    # 구분하는 문장만 선별하고 두 비용 부담 원칙을 필수 검증한다.
    if matches_return_cost:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        evidence_result = select_evidence_documents(
            question=question,
            intent="return_cost",
            documents=source_documents,
        )

        evidence_documents = (
            evidence_result.selected_documents
        )

        try:
            hybrid_answer = build_hybrid_answer(
                question=question,
                intent="return_cost",
                documents=evidence_documents,
                validation_documents=source_documents,
            )
        except Exception:
            hybrid_answer = build_return_cost_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "return_cost",
            "sources": source_documents,
        }

    # 단순 변심 변형 질문은 점수 필터 결과가 비어 있어도
    # 이미 검증된 답변을 반환한다.
    if matches_change_of_mind_return:
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_change_of_mind_return_answer(),
            "intent": "change_of_mind_return",
            "sources": source_documents,
        }

    if not relevant_documents:
        return {
            "question": question,
            "answer": (
                "질문에 직접 답변할 수 있는 근거 문서를 "
                "찾지 못했습니다. 질문을 조금 더 구체적으로 "
                "입력해주세요."
            ),
            "intent": intent,
            "sources": [],
        }

    if intent == "return_cost":
        return {
            "question": question,
            "answer": build_return_cost_answer(),
            "intent": intent,
            "sources": relevant_documents,
        }

    prompt = build_prompt(
        question=question,
        documents=relevant_documents,
    )

    answer = generate_answer(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
    )

    answer = clean_answer(answer)

    return {
        "question": question,
        "answer": answer,
        "intent": intent,
        "sources": relevant_documents,
    }