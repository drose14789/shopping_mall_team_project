from __future__ import annotations

import re
import time
from functools import wraps
from typing import Any, Callable

from app.services.answer_builder import build_hybrid_answer as _build_hybrid_answer
from app.services.document_filter import (
    filter_documents_for_question as _filter_documents_for_question,
)
from app.services.evidence_selector import (
    select_evidence_documents as _select_evidence_documents,
)
from app.services.intent_router import analyze_question
from app.services.legal_rules import get_legal_rule
from app.services.query_builder import build_search_query as _build_search_query
from app.services.ollama_service import generate_answer as _generate_answer
from app.services.qdrant_service import search_documents as _search_documents


SEARCH_TOP_K = 5
MAX_CONTEXT_DOCUMENTS = 3
MIN_RERANK_SCORE = 0.1
RELATIVE_SCORE_RATIO = 0.25

# 단순 질문은 작은 문맥을 사용하고, 조건·예외·필수 항목을
# 묻는 질문은 충분한 문맥을 사용합니다.
FAST_CONTEXT_DOCUMENTS = 2
FAST_DOCUMENT_LENGTH = 1600
FAST_TOTAL_CONTEXT_LENGTH = 3000
FAST_NUM_PREDICT = 220

DETAIL_CONTEXT_DOCUMENTS = 3
DETAIL_DOCUMENT_LENGTH = 2400
DETAIL_TOTAL_CONTEXT_LENGTH = 6000
DETAIL_NUM_PREDICT = 320

MAX_DOCUMENT_LENGTH = DETAIL_DOCUMENT_LENGTH
MAX_TOTAL_CONTEXT_LENGTH = DETAIL_TOTAL_CONTEXT_LENGTH
MAX_SOURCE_CHILD_LENGTH = 800
MAX_SOURCE_PARENT_LENGTH = 1400
STRUCTURED_INTENT_MIN_CONFIDENCE = 0.8
GENERAL_SEARCH_TOP_K = 8
REVIEW_PRIVACY_SEARCH_TOP_K = 10
REVIEW_PRIVACY_ARTICLE_2_TOP_K = 5
REVIEW_PRIVACY_SOURCE_LIMIT = 4
PLATFORM_EXPRESSION_SEARCH_TOP_K = 8
PLATFORM_EXPRESSION_SOURCE_LIMIT = 3

RAG_SERVICE_BUILD = "2026-08-05-coupon-discount-return-v53"

TokenCallback = Callable[[str], None]


def _timed_call(
    label: str,
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    started_at = time.perf_counter()
    print(f"[RAG Timing] {label} 시작", flush=True)

    try:
        return function(*args, **kwargs)
    finally:
        elapsed = time.perf_counter() - started_at
        print(
            f"[RAG Timing] {label}: {elapsed:.2f}초",
            flush=True,
        )


def build_search_query(*args: Any, **kwargs: Any) -> Any:
    return _timed_call(
        "질문 분석",
        _build_search_query,
        *args,
        **kwargs,
    )


def search_documents(*args: Any, **kwargs: Any) -> Any:
    return _timed_call(
        "Qdrant 검색 + 임베딩 + reranker",
        _search_documents,
        *args,
        **kwargs,
    )


def filter_documents_for_question(
    *args: Any,
    **kwargs: Any,
) -> Any:
    return _timed_call(
        "문서 필터",
        _filter_documents_for_question,
        *args,
        **kwargs,
    )


def select_evidence_documents(
    *args: Any,
    **kwargs: Any,
) -> Any:
    return _timed_call(
        "근거 문장 선별",
        _select_evidence_documents,
        *args,
        **kwargs,
    )


def generate_answer(*args: Any, **kwargs: Any) -> str:
    return _timed_call(
        "Ollama 답변 생성",
        _generate_answer,
        *args,
        **kwargs,
    )


def build_hybrid_answer(
    *args: Any,
    **kwargs: Any,
) -> str:
    return _timed_call(
        "하이브리드 답변 구성",
        _build_hybrid_answer,
        *args,
        **kwargs,
    )


def _measure_total(
    function: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, Any]]:
    @wraps(function)
    def wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        question = ""

        if args:
            question = str(args[0])
        elif "question" in kwargs:
            question = str(kwargs["question"])

        started_at = time.perf_counter()

        print(
            f"[RAG Timing] 전체 시작: {question[:80]}",
            flush=True,
        )

        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started_at
            print(
                f"[RAG Timing] 전체 처리: {elapsed:.2f}초",
                flush=True,
            )

    return wrapper


def _build_streaming_generator(
    on_token: TokenCallback | None,
) -> Callable[..., str] | None:
    """
    answer_builder가 사용하는 generate_answer 호출에
    Ollama 스트리밍 콜백을 연결한다.
    """
    if on_token is None:
        return None

    def streaming_generator(**kwargs: Any) -> str:
        return generate_answer(
            **kwargs,
            on_token=on_token,
        )

    return streaming_generator


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

        child_content = str(
            sanitized_document.get("child_content", "")
        ).strip()
        parent_content = str(
            sanitized_document.get("parent_content", "")
        ).strip()

        sanitized_document["child_content"] = (
            child_content[:MAX_SOURCE_CHILD_LENGTH]
        )
        sanitized_document["parent_content"] = (
            parent_content[:MAX_SOURCE_PARENT_LENGTH]
        )

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


def _requires_detailed_context(
    question: str,
) -> bool:
    """
    조건, 예외, 필수 항목처럼 여러 근거를 함께 확인해야 하는
    질문인지 판단합니다.
    """
    normalized_question = " ".join(question.split())

    detail_terms = (
        "조건",
        "예외",
        "필수",
        "항목",
        "정보",
        "기준",
        "주의",
        "제한",
        "문제",
        "의무",
        "동의",
        "개인정보",
        "광고",
        "상세페이지",
        "플랫폼",
        "활용",
        "어떻게",
        "무엇",
        "뭐",
        "알려",
        "설명",
    )

    multi_part_terms = (
        "그리고",
        "또는",
        "및",
        "동시에",
        "각각",
        "차이",
        "구분",
    )

    return (
        len(normalized_question) >= 45
        or any(
            term in normalized_question
            for term in detail_terms
        )
        or any(
            term in normalized_question
            for term in multi_part_terms
        )
    )


def _resolve_context_limits(
    question: str,
) -> tuple[int, int, int, int]:
    """
    문서 수, 문서별 최대 길이, 전체 문맥 길이,
    답변 생성 토큰 수를 반환합니다.
    """
    if _requires_detailed_context(question):
        return (
            DETAIL_CONTEXT_DOCUMENTS,
            DETAIL_DOCUMENT_LENGTH,
            DETAIL_TOTAL_CONTEXT_LENGTH,
            DETAIL_NUM_PREDICT,
        )

    return (
        FAST_CONTEXT_DOCUMENTS,
        FAST_DOCUMENT_LENGTH,
        FAST_TOTAL_CONTEXT_LENGTH,
        FAST_NUM_PREDICT,
    )


def build_context(
    question: str,
    documents: list[dict[str, Any]],
) -> str:
    """질문 난이도에 맞춰 검색 문서를 Ollama 문맥으로 변환한다."""
    (
        max_documents,
        max_document_length,
        max_total_context_length,
        _,
    ) = _resolve_context_limits(question)

    context_parts: list[str] = []
    used_length = 0

    for document in documents[:max_documents]:
        heading = str(
            document.get("heading", "")
        ).strip()

        source_file = str(
            document.get("source_file", "")
        ).strip()

        # 답변에 필요한 조건과 예외가 보존된 부모 청크를 우선 사용한다.
        # 부모 청크가 없을 때만 검색된 자식 청크를 사용한다.
        content = str(
            document.get("parent_content", "")
        ).strip()

        if not content:
            content = str(
                document.get("child_content", "")
            ).strip()

        if not content:
            continue

        remaining_length = (
            max_total_context_length - used_length
        )

        if remaining_length <= 0:
            break

        content = content[:min(
            max_document_length,
            remaining_length,
        )]

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

        used_length += len(content)

    return "\n\n".join(context_parts)


def build_prompt(
    question: str,
    documents: list[dict[str, Any]],
) -> str:
    """일반 질문용 Ollama 프롬프트를 생성한다."""
    context = build_context(
        question=question,
        documents=documents,
    )

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


def is_review_data_privacy_analysis_question(
    question: str,
) -> bool:
    """
    리뷰·상품평 데이터를 분석할 때 개인정보 문제가 있는지
    묻는 질문을 판별합니다.
    """
    normalized = normalize_text(question)

    review_terms = (
        "리뷰",
        "고객리뷰",
        "상품리뷰",
        "구매리뷰",
        "후기",
        "고객후기",
        "구매후기",
        "상품후기",
        "상품평",
        "평가글",
    )

    analysis_terms = (
        "분석",
        "데이터분석",
        "통계",
        "집계",
        "분류",
        "가공",
        "활용",
        "감성분석",
        "텍스트마이닝",
        "인공지능학습",
        "ai학습",
        "모델학습",
    )

    privacy_terms = (
        "개인정보",
        "개인정보문제",
        "프라이버시",
        "정보보호",
        "동의",
        "불법",
        "위법",
        "문제없",
        "문제될",
        "괜찮",
        "해도되",
        "가능",
    )

    return (
        any(term in normalized for term in review_terms)
        and any(term in normalized for term in analysis_terms)
        and any(term in normalized for term in privacy_terms)
    )


def build_review_data_privacy_analysis_answer() -> str:
    """리뷰 데이터 분석 시 개인정보 처리 원칙을 안내합니다."""
    return (
        "무조건 문제없다고 볼 수는 없습니다. 리뷰에 작성자 "
        "닉네임, 사진, 주문정보나 다른 정보와 결합하여 개인을 "
        "알아볼 수 있는 내용이 포함되어 있다면 개인정보에 "
        "해당할 수 있고, 이를 분류·가공·통계 분석하는 행위도 "
        "개인정보 처리에 포함됩니다.\n\n"
        "쇼핑몰이 자체 리뷰를 서비스 개선이나 상품 품질 분석에 "
        "이용하려면 적법한 이용 근거가 있는지, 당초 수집 목적과 "
        "합리적으로 관련된 범위인지 확인해야 합니다. 분석에 "
        "필요하지 않은 회원 ID, 이름, 연락처, 사진 등은 제거하고, "
        "목적을 달성할 수 있다면 개인을 더 이상 알아볼 수 없도록 "
        "익명 처리하는 것이 안전합니다.\n\n"
        "가명 처리한 정보는 여전히 개인정보이므로 안전조치와 "
        "이용 목적 제한을 지켜야 합니다. 개인을 식별할 수 없는 "
        "집계·통계 형태로 분석하면 개인정보 위험을 줄일 수 있지만, "
        "개인별 성향 분석이나 맞춤 광고처럼 당초 목적과 다른 "
        "용도로 활용하려면 별도의 법적 근거나 동의가 필요한지 "
        "추가로 검토해야 합니다."
    )


def _review_privacy_document_text(
    document: dict[str, Any],
) -> str:
    return normalize_text(
        " ".join(
            str(document.get(key, "") or "")
            for key in (
                "heading",
                "source_file",
                "child_content",
                "parent_content",
            )
        )
    )


def _extract_review_privacy_article_number(
    document: dict[str, Any],
) -> tuple[int, int | None] | None:
    """
    근거 카드의 heading에 표시된 조문 번호만 판별합니다.

    본문에서 다른 조문을 인용한 경우에는 해당 인용 조문으로
    잘못 분류하지 않습니다.
    """
    heading = str(
        document.get("heading", "")
        or ""
    ).strip()

    article_matches = re.findall(
        r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?",
        heading,
    )

    if not article_matches:
        # heading이 비어 있는 예외적인 문서만 자식 청크의
        # 앞부분에서 조문 제목을 확인합니다.
        child_prefix = str(
            document.get("child_content", "")
            or ""
        )[:250]

        article_matches = re.findall(
            r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?",
            child_prefix,
        )

    if not article_matches:
        return None

    article_text, sub_article_text = article_matches[-1]

    return (
        int(article_text),
        (
            int(sub_article_text)
            if sub_article_text
            else None
        ),
    )


def _review_privacy_article_group(
    document: dict[str, Any],
) -> str | None:
    """
    리뷰 분석 답변에 직접 필요한 개인정보 보호법 조항만
    heading의 정확한 조문 번호를 기준으로 분류합니다.
    """
    text_key = _review_privacy_document_text(document)

    if "개인정보보호법" not in text_key:
        return None

    article_number = _extract_review_privacy_article_number(
        document
    )

    if article_number is None:
        return None

    article, sub_article = article_number

    if article == 2 and sub_article is None:
        return "article_2"

    if article == 15 and sub_article is None:
        return "article_15"

    if article == 16 and sub_article is None:
        return "article_16"

    if article == 18 and sub_article is None:
        return "article_18"

    if article == 3 and sub_article is None:
        return "article_3"

    if article == 28 and sub_article == 2:
        return "article_28_2"

    return None

def _has_review_privacy_article(
    documents: list[dict[str, Any]],
    article_group: str,
) -> bool:
    return any(
        _review_privacy_article_group(document)
        == article_group
        for document in documents
    )


def _select_exact_review_privacy_article(
    documents: list[dict[str, Any]],
    article_group: str,
) -> dict[str, Any] | None:
    """heading의 정확한 조문 번호가 일치하는 문서만 선택합니다."""
    matches = [
        document
        for document in documents
        if _review_privacy_article_group(document)
        == article_group
    ]

    if not matches:
        return None

    matches.sort(
        key=lambda document: float(
            document.get("rerank_score", 0.0)
        ),
        reverse=True,
    )

    return matches[0]


def _same_source_document(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    """두 근거 카드가 같은 부모 청크인지 확인합니다."""
    first_key = str(
        first.get("parent_id")
        or first.get("child_id")
        or (
            f"{first.get('source_file', '')}:"
            f"{first.get('heading', '')}"
        )
    )

    second_key = str(
        second.get("parent_id")
        or second.get("child_id")
        or (
            f"{second.get('source_file', '')}:"
            f"{second.get('heading', '')}"
        )
    )

    return first_key == second_key


def _prepend_review_privacy_article_2(
    documents: list[dict[str, Any]],
    article_2_document: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """제2조 근거를 첫 번째 카드로 고정합니다."""
    if article_2_document is None:
        return documents[:REVIEW_PRIVACY_SOURCE_LIMIT]

    remaining = [
        document
        for document in documents
        if not _same_source_document(
            document,
            article_2_document,
        )
    ]

    return [
        article_2_document,
        *remaining,
    ][:REVIEW_PRIVACY_SOURCE_LIMIT]


def merge_review_privacy_documents(
    *document_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """여러 검색 결과를 부모 청크 기준으로 중복 제거합니다."""
    merged: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for documents in document_groups:
        for document in documents:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            merged.append(document)

    return merged


def select_review_data_privacy_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    리뷰 데이터 분석 답변의 직접 근거만 선택합니다.

    우선순위:
    제2조 → 제15조 → 제16조 → 제18조
    보조:
    제3조 → 제28조의2
    """
    if not documents:
        return []

    priority_groups = (
        "article_2",
        "article_15",
        "article_16",
        "article_18",
        "article_3",
        "article_28_2",
    )

    grouped: dict[str, list[dict[str, Any]]] = {
        group: []
        for group in priority_groups
    }

    for document in documents:
        group = _review_privacy_article_group(document)

        if group is None:
            continue

        grouped[group].append(document)

    for group_documents in grouped.values():
        group_documents.sort(
            key=lambda document: float(
                document.get("rerank_score", 0.0)
            ),
            reverse=True,
        )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for group in priority_groups:
        if not grouped[group]:
            continue

        document = grouped[group][0]

        unique_key = str(
            document.get("parent_id")
            or document.get("child_id")
            or (
                f"{document.get('source_file', '')}:"
                f"{document.get('heading', '')}"
            )
        )

        if unique_key in used_keys:
            continue

        used_keys.add(unique_key)
        selected.append(document)

        if len(selected) >= REVIEW_PRIVACY_SOURCE_LIMIT:
            break

    return selected

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


def is_platform_restricted_expression_question(
    question: str,
) -> bool:
    """
    특정 쇼핑 플랫폼에서 제한되거나 사용할 수 없는 표현을
    묻는 질문을 판별합니다.
    """
    normalized = normalize_text(question)

    platform_terms = (
        "지그재그",
        "무신사",
        "에이블리",
        "브랜디",
        "쿠팡",
        "스마트스토어",
        "네이버쇼핑",
        "오픈마켓",
        "쇼핑플랫폼",
        "플랫폼",
    )

    expression_terms = (
        "표현",
        "문구",
        "광고문구",
        "상세페이지문구",
        "상품명",
        "홍보문구",
        "단어",
    )

    restriction_terms = (
        "제한",
        "금지",
        "쓰면안",
        "사용하면안",
        "사용불가",
        "못쓰",
        "피해야",
        "문제될",
        "허용되지않",
        "어떤표현",
        "제한되는",
    )

    return (
        any(term in normalized for term in platform_terms)
        and any(term in normalized for term in expression_terms)
        and any(term in normalized for term in restriction_terms)
    )


def extract_platform_name(question: str) -> str:
    """질문에 포함된 대표 플랫폼 이름을 반환합니다."""
    normalized = normalize_text(question)

    platform_names = (
        "지그재그",
        "무신사",
        "에이블리",
        "브랜디",
        "쿠팡",
        "스마트스토어",
        "네이버쇼핑",
    )

    for platform_name in platform_names:
        if normalize_text(platform_name) in normalized:
            return platform_name

    return "해당 플랫폼"


def build_platform_restricted_expression_answer(
    platform_name: str,
) -> str:
    """
    플랫폼 자체 정책과 법률상 제한 표현을 구분하여 안내합니다.
    """
    return (
        f"{platform_name} 자체 입점·광고 운영정책에서 제한하는 "
        "모든 표현은 현재 보유한 법률 문서만으로 단정할 수 "
        "없습니다. 플랫폼별 내부 기준은 해당 판매자센터의 최신 "
        "상품등록·광고 운영정책을 별도로 확인해야 합니다.\n\n"
        "다만 법률상 온라인 상품명, 광고와 상세페이지에서는 "
        "다음과 같은 표현이 문제될 수 있습니다.\n\n"
        "• 사실과 다르거나 실제보다 부풀린 거짓·과장 표현\n"
        "• 중요한 조건이나 제한을 숨겨 소비자를 오인시키는 "
        "기만 표현\n"
        "• 객관적인 근거 없이 다른 상품보다 우수하다고 하는 "
        "부당 비교 표현\n"
        "• 근거 없이 다른 사업자나 상품을 깎아내리는 비방 표현\n"
        "• ‘무조건 반품·환불 불가’처럼 소비자의 법정 권리를 "
        "일률적으로 제한하는 표현\n\n"
        "따라서 구체적인 문구가 있다면 그 문구가 사실에 근거하는지, "
        "중요 조건을 빠뜨리지 않았는지, 소비자를 오인시킬 가능성이 "
        "있는지를 확인해야 합니다."
    )


def _platform_expression_document_text(
    document: dict[str, Any],
) -> str:
    return normalize_text(
        " ".join(
            str(document.get(key, "") or "")
            for key in (
                "heading",
                "source_file",
                "child_content",
                "parent_content",
            )
        )
    )


def _platform_expression_source_priority(
    document: dict[str, Any],
) -> int:
    """
    플랫폼 제한 표현 질문에 직접 관련된 법률 문서만 점수화합니다.
    """
    heading = str(
        document.get("heading", "")
        or ""
    )
    source_file = str(
        document.get("source_file", "")
        or ""
    )
    text_key = _platform_expression_document_text(document)

    heading_key = normalize_text(heading)
    source_key = normalize_text(source_file)

    if (
        "표시광고" in source_key
        and "시행령" not in source_key
        and "제3조" in heading_key
        and (
            "부당한표시광고행위의금지" in heading_key
            or "부당한표시광고" in text_key
        )
    ):
        return 100

    if (
        "전자상거래" in source_key
        and "제21조" in heading_key
        and "금지행위" in heading_key
    ):
        return 90

    if (
        "전자상거래" in source_key
        and "제35조" in heading_key
        and "소비자에게불리한계약" in heading_key
    ):
        return 75

    if (
        "상품정보제공고시" in source_key
        or "상품정보제공고시" in text_key
    ):
        return 60

    return 0


def select_platform_expression_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """법률상 제한 표현의 직접 근거만 우선순위대로 선택합니다."""
    ranked: list[
        tuple[int, float, dict[str, Any]]
    ] = []

    for document in documents:
        priority = _platform_expression_source_priority(
            document
        )

        if priority <= 0:
            continue

        ranked.append(
            (
                priority,
                float(document.get("rerank_score", 0.0)),
                document,
            )
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for _, _, document in ranked:
        unique_key = str(
            document.get("parent_id")
            or document.get("child_id")
            or (
                f"{document.get('source_file', '')}:"
                f"{document.get('heading', '')}"
            )
        )

        if unique_key in used_keys:
            continue

        used_keys.add(unique_key)
        selected.append(document)

        if len(selected) >= PLATFORM_EXPRESSION_SOURCE_LIMIT:
            break

    return selected


def _natural_material_source_type(
    document: dict[str, Any],
) -> str | None:
    """
    소재·함량 사실 표시의 근거를 판별합니다.

    - prohibition: 표시광고법 제3조
    - substantiation: 표시광고법 제5조
    """
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    source_key = normalize_text(source_file)
    structured_key = normalize_text(structured_text)

    if "표시광고" not in source_key:
        return None

    if "시행령" in source_key or "시행령" in structured_key:
        return None

    if (
        "제3조" in structured_key
        and (
            "부당한표시광고행위의금지" in structured_key
            or "부당한표시광고" in structured_key
        )
    ):
        return "prohibition"

    if (
        "제5조" in structured_key
        and (
            "표시광고내용의실증" in structured_key
            or "실증" in structured_key
        )
    ):
        return "substantiation"

    return None


def _natural_material_source_score(
    document: dict[str, Any],
) -> float:
    for key in (
        "rerank_score",
        "score",
        "similarity_score",
        "dense_score",
    ):
        value = document.get(key)

        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue

    return 0.0


def select_natural_material_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    소재·함량 표시 근거를 다음 순서로 고정합니다.

    1. 표시광고법 제3조
    2. 표시광고법 제5조
    """
    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = {
        "prohibition": [],
        "substantiation": [],
    }

    for document in documents:
        source_type = _natural_material_source_type(
            document
        )

        if source_type in grouped:
            grouped[source_type].append(document)

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for source_type in (
        "prohibition",
        "substantiation",
    ):
        candidates = grouped[source_type]
        candidates.sort(
            key=_natural_material_source_score,
            reverse=True,
        )

        for document in candidates:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def has_natural_material_source_type(
    documents: list[dict[str, Any]],
    source_type: str,
) -> bool:
    return any(
        _natural_material_source_type(document)
        == source_type
        for document in documents
    )


def ensure_natural_material_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    표시광고법 제3조와 제5조를 각각 확인하고,
    누락된 조문만 별도로 검색합니다.
    """
    merged_documents = list(documents)

    selected = select_natural_material_sources(
        merged_documents
    )

    if not has_natural_material_source_type(
        selected,
        "prohibition",
    ):
        prohibition_result = search_documents(
            question=(
                "표시 광고의 공정화에 관한 법률 제3조 "
                "부당한 표시 광고 행위의 금지 소비자를 속이거나 "
                "잘못 알게 할 우려가 있는 거짓 과장 표시 광고와 "
                "기만적인 표시 광고"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                prohibition_result.get("documents", [])
            )
        )

    selected = select_natural_material_sources(
        merged_documents
    )

    if not has_natural_material_source_type(
        selected,
        "substantiation",
    ):
        substantiation_result = search_documents(
            question=(
                "표시 광고의 공정화에 관한 법률 제5조 "
                "표시 광고 내용의 실증 사업자는 자기가 한 "
                "표시 광고 중 사실과 관련한 사항을 실증할 수 "
                "있어야 한다"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                substantiation_result.get("documents", [])
            )
        )

    return select_natural_material_sources(
        merged_documents
    )


def select_product_performance_claim_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    상품 성능·품질에 관한 사실 표시의 근거를
    표시광고법 제3조, 제5조 순서로 선택합니다.
    """
    return select_natural_material_sources(documents)


def ensure_product_performance_claim_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    상품 성능 주장에 필요한 표시광고법 제3조와 제5조를
    각각 확인하고 누락된 조문만 검색합니다.
    """
    return ensure_natural_material_sources(documents)


def _free_shipping_source_type(
    document: dict[str, Any],
) -> str | None:
    """
    무료배송 조건·예외 누락의 직접 근거인
    표시광고법 제3조만 판별합니다.
    """
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    source_key = normalize_text(source_file)
    structured_key = normalize_text(structured_text)

    if "표시광고" not in source_key:
        return None

    # 표시광고법 시행령은 사용하지 않습니다.
    if "시행령" in source_key or "시행령" in structured_key:
        return None

    if "제3조" not in structured_key:
        return None

    if (
        "부당한표시광고행위의금지" in structured_key
        or "부당한표시광고" in structured_key
    ):
        return "law"

    return None


def _free_shipping_source_score(
    document: dict[str, Any],
) -> float:
    """동일 조문 후보 중 검색 관련도가 높은 문서를 선택합니다."""
    for key in (
        "rerank_score",
        "score",
        "similarity_score",
        "dense_score",
    ):
        value = document.get(key)

        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue

    return 0.0


def select_free_shipping_ad_copy_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    무료배송 문구의 근거로 표시광고법 제3조 하나만 선택합니다.
    """
    candidates = [
        document
        for document in documents
        if _free_shipping_source_type(document) == "law"
    ]

    candidates.sort(
        key=_free_shipping_source_score,
        reverse=True,
    )

    if not candidates:
        return []

    return [candidates[0]]


def ensure_free_shipping_ad_copy_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    표시광고법 제3조가 없을 때에만 본법 제3조를 별도로 검색합니다.
    표시광고법 시행령은 검색하거나 출처로 사용하지 않습니다.
    """
    merged_documents = list(documents)

    selected = select_free_shipping_ad_copy_sources(
        merged_documents
    )

    if selected:
        return selected

    law_result = search_documents(
        question=(
            "표시 광고의 공정화에 관한 법률 제3조 "
            "부당한 표시 광고 행위의 금지 소비자를 속이거나 "
            "소비자로 하여금 잘못 알게 할 우려가 있는 "
            "거짓 과장 표시 광고와 기만적인 표시 광고"
        ),
        top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
    )

    merged_documents.extend(
        sanitize_source_documents(
            law_result.get("documents", [])
        )
    )

    return select_free_shipping_ad_copy_sources(
        merged_documents
    )


def _blanket_return_source_priority(
    document: dict[str, Any],
) -> int:
    """
    일률적인 반품·환불 불가 문구의 직접 근거를 점수화합니다.

    우선순위:
    전자상거래법 제17조 → 제35조 → 제18조
    """
    heading = str(document.get("heading", "") or "")
    source_file = str(document.get("source_file", "") or "")

    heading_key = normalize_text(heading)
    source_key = normalize_text(source_file)

    document_text = normalize_text(
        " ".join(
            str(document.get(key, "") or "")
            for key in (
                "heading",
                "source_file",
                "child_content",
                "parent_content",
            )
        )
    )

    if (
        "전자상거래" not in source_key
        and "전자상거래법" not in document_text
    ):
        return 0

    if (
        "제17조" in heading_key
        and "청약철회" in heading_key
    ):
        return 100

    if (
        "제35조" in heading_key
        and "소비자에게불리한계약" in heading_key
    ):
        return 95

    if (
        "제18조" in heading_key
        and "청약철회등의효과" in heading_key
    ):
        return 85

    return 0


def select_blanket_return_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """반품·환불 불가 문구의 직접 근거를 최대 2개 선택합니다."""
    ranked: list[
        tuple[int, float, dict[str, Any]]
    ] = []

    for document in documents:
        priority = _blanket_return_source_priority(document)

        if priority <= 0:
            continue

        ranked.append(
            (
                priority,
                float(document.get("rerank_score", 0.0)),
                document,
            )
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for _, _, document in ranked:
        unique_key = str(
            document.get("parent_id")
            or document.get("child_id")
            or (
                f"{document.get('source_file', '')}:"
                f"{document.get('heading', '')}"
            )
        )

        if unique_key in used_keys:
            continue

        used_keys.add(unique_key)
        selected.append(document)

        if len(selected) >= 2:
            break

    return selected


def is_stockout_refund_source(
    document: dict[str, Any],
) -> bool:
    """출처가 전자상거래법 제15조(재화등의 공급 등)인지 확인합니다."""
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    source_key = normalize_text(source_file)
    structured_key = normalize_text(structured_text)

    if (
        "전자상거래" not in source_key
        and "전자상거래" not in structured_key
    ):
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        if "전자상거래" not in body_key:
            return False

    if (
        "제15조" in structured_key
        and "재화등의공급" in structured_key
    ):
        return True

    if not structured_key:
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")[:700]
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        return (
            "제15조" in body_key
            and "재화등의공급" in body_key
        )

    return False


def select_stockout_refund_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    품절·공급 곤란 환급 문구의 직접 근거인
    전자상거래법 제15조 하나만 선택합니다.
    """
    candidates = [
        document
        for document in documents
        if is_stockout_refund_source(document)
    ]

    def source_score(
        document: dict[str, Any],
    ) -> float:
        for key in (
            "rerank_score",
            "score",
            "similarity_score",
            "dense_score",
        ):
            value = document.get(key)

            try:
                if value is not None:
                    return float(value)
            except (TypeError, ValueError):
                continue

        return 0.0

    candidates.sort(
        key=source_score,
        reverse=True,
    )

    return candidates[:1]


def ensure_stockout_refund_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    제15조가 검색 후보에 없으면 조문명과 핵심 문언으로
    별도 검색한 뒤 다시 선택합니다.
    """
    merged_documents = list(documents)

    selected = select_stockout_refund_sources(
        merged_documents
    )

    if selected:
        return selected

    article_15_result = search_documents(
        question=(
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제15조 재화등의 공급 등 통신판매업자는 청약을 받은 "
            "재화등을 공급하기 곤란하다는 것을 알았을 때 그 사유를 "
            "소비자에게 지체 없이 알리고, 선지급식 통신판매의 경우 "
            "대금을 지급한 날부터 3영업일 이내에 환급하거나 "
            "환급에 필요한 조치를 하여야 한다"
        ),
        top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
    )

    merged_documents.extend(
        sanitize_source_documents(
            article_15_result.get("documents", [])
        )
    )

    return select_stockout_refund_sources(
        merged_documents
    )


def _refund_delay_notice_source_article(
    document: dict[str, Any],
) -> int | None:
    """
    환급 기한을 법정 기준보다 늦게 정한 문구의 근거 조문을
    판별합니다.

    우선순위:
    전자상거래법 제18조 → 제35조
    """
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    source_key = normalize_text(source_file)
    structured_key = normalize_text(structured_text)

    if (
        "전자상거래" not in source_key
        and "전자상거래" not in structured_key
    ):
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        if "전자상거래" not in body_key:
            return None

    if (
        "제18조" in structured_key
        and "청약철회" in structured_key
    ):
        return 18

    if (
        "제35조" in structured_key
        and "소비자에게불리한계약" in structured_key
    ):
        return 35

    if not structured_key:
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")[:500]
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        if "제18조" in body_key and "청약철회" in body_key:
            return 18

        if (
            "제35조" in body_key
            and "소비자에게불리한계약" in body_key
        ):
            return 35

    return None


def select_refund_delay_notice_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    환급 지연 문구의 근거를 제18조 → 제35조 순서로
    최대 2개 선택합니다.
    """
    article_candidates: dict[
        int,
        list[dict[str, Any]],
    ] = {
        18: [],
        35: [],
    }

    for document in documents:
        article_number = _refund_delay_notice_source_article(
            document
        )

        if article_number in article_candidates:
            article_candidates[article_number].append(
                document
            )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for article_number in (18, 35):
        candidates = article_candidates[article_number]

        candidates.sort(
            key=lambda document: float(
                document.get(
                    "rerank_score",
                    document.get("score", 0.0),
                )
                or 0.0
            ),
            reverse=True,
        )

        for document in candidates:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def has_refund_delay_notice_source_article(
    documents: list[dict[str, Any]],
    article_number: int,
) -> bool:
    """선택된 출처에 제18조 또는 제35조가 있는지 확인합니다."""
    return any(
        _refund_delay_notice_source_article(document)
        == article_number
        for document in documents
    )


def ensure_refund_delay_notice_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    환급 지연 문구의 직접 근거인 제18조와 제35조를 각각
    확인하고, 누락된 조문만 별도로 검색합니다.
    """
    merged_documents = list(documents)

    selected = select_refund_delay_notice_sources(
        merged_documents
    )

    if not has_refund_delay_notice_source_article(
        selected,
        18,
    ):
        article_18_result = search_documents(
            question=(
                "전자상거래 등에서의 소비자보호에 관한 법률 "
                "제18조 청약철회등의 효과 통신판매업자는 "
                "재화를 반환받은 날부터 3영업일 이내에 "
                "이미 지급받은 재화등의 대금을 환급하여야 하고 "
                "환급 지연 시 지연배상금을 지급"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                article_18_result.get("documents", [])
            )
        )

    selected = select_refund_delay_notice_sources(
        merged_documents
    )

    if not has_refund_delay_notice_source_article(
        selected,
        35,
    ):
        article_35_result = search_documents(
            question=(
                "전자상거래 등에서의 소비자보호에 관한 법률 "
                "제35조 소비자에게 불리한 계약의 금지 "
                "제17조부터 제19조까지를 위반한 약정으로서 "
                "소비자에게 불리한 것은 효력이 없음"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                article_35_result.get("documents", [])
            )
        )

    return select_refund_delay_notice_sources(
        merged_documents
    )


def _return_penalty_source_body(
    document: dict[str, Any],
) -> str:
    """위약금 출처의 검색 자식·부모 청크를 하나의 문자열로 합칩니다."""
    return "\n\n".join(
        content
        for content in (
            str(document.get("child_content", "") or "").strip(),
            str(document.get("parent_content", "") or "").strip(),
        )
        if content
    )


def _return_penalty_article_18_rank(
    document: dict[str, Any],
) -> float:
    """
    제18조 후보 중 제8항~제10항의 핵심 문구가 포함된
    청크를 최우선으로 선택합니다.
    """
    body_key = normalize_text(
        _return_penalty_source_body(document)
    )

    relevance_bonus = 0.0

    if "위약금이나손해배상" in body_key:
        relevance_bonus += 1000.0

    if (
        "청약철회등을이유로" in body_key
        and "청구할수없" in body_key
    ):
        relevance_bonus += 800.0

    if (
        "반환에필요한비용" in body_key
        and "소비자가부담" in body_key
    ):
        relevance_bonus += 500.0

    if (
        "반환에필요한비용" in body_key
        and "통신판매업자가부담" in body_key
    ):
        relevance_bonus += 500.0

    if (
        "일부사용하거나일부소비" in body_key
        or "사용또는일부소비" in body_key
    ):
        relevance_bonus += 300.0

    try:
        base_score = float(
            document.get(
                "rerank_score",
                document.get("score", 0.0),
            )
            or 0.0
        )
    except (TypeError, ValueError):
        base_score = 0.0

    return relevance_bonus + base_score


def _return_penalty_excerpt_order(
    content: str,
) -> int:
    """제18조제8항 → 제9항 → 제10항 순서로 출처 조각을 배치합니다."""
    normalized = normalize_text(content)

    if (
        "⑧" in content
        or "일부사용하거나일부소비" in normalized
        or "사용또는일부소비" in normalized
    ):
        return 8

    if (
        "⑨" in content
        or "위약금이나손해배상" in normalized
        or "청약철회등을이유로" in normalized
    ):
        return 9

    if (
        "⑩" in content
        or (
            "반환에필요한비용" in normalized
            and "통신판매업자가부담" in normalized
        )
    ):
        return 10

    return 99


def _focus_return_penalty_article_18_source(
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    제18조 후보의 관련 자식 청크를 합쳐 제8항~제10항이
    출처 카드 처음부터 표시되도록 만듭니다.
    """
    if not candidates:
        return None

    ranked_candidates = sorted(
        candidates,
        key=_return_penalty_article_18_rank,
        reverse=True,
    )

    best_document = dict(ranked_candidates[0])

    evidence_terms = (
        "일부사용하거나일부소비",
        "사용또는일부소비",
        "위약금이나손해배상",
        "청약철회등을이유로",
        "반환에필요한비용은소비자가부담",
        "반환에필요한비용은통신판매업자가부담",
    )

    excerpt_candidates: list[tuple[int, str]] = []
    used_excerpt_keys: set[str] = set()

    for document in ranked_candidates:
        # 검색된 자식 청크를 먼저 사용합니다. 부모 청크는
        # 제18조 앞부분만 담긴 경우가 많으므로 보조로만 봅니다.
        for content in (
            str(document.get("child_content", "") or "").strip(),
            str(document.get("parent_content", "") or "").strip(),
        ):
            if not content:
                continue

            normalized = normalize_text(content)

            if not any(
                term in normalized
                for term in evidence_terms
            ):
                continue

            # 부모 청크 안에 제8항 이후가 함께 있다면 앞부분을
            # 제거하여 핵심 조항부터 화면에 표시합니다.
            start_positions = [
                position
                for position in (
                    content.find("⑧"),
                    content.find("⑨"),
                    content.find("⑩"),
                )
                if position >= 0
            ]

            if start_positions:
                content = content[min(start_positions):].strip()

            excerpt_key = normalize_text(content)

            if not excerpt_key or excerpt_key in used_excerpt_keys:
                continue

            used_excerpt_keys.add(excerpt_key)
            excerpt_candidates.append(
                (
                    _return_penalty_excerpt_order(content),
                    content,
                )
            )

    excerpt_candidates.sort(
        key=lambda item: item[0]
    )

    focused_parts: list[str] = []
    focused_length = 0
    max_focused_length = 2600

    for _, content in excerpt_candidates:
        remaining = max_focused_length - focused_length

        if remaining <= 0:
            break

        focused_content = content[:remaining].strip()

        if not focused_content:
            continue

        focused_parts.append(focused_content)
        focused_length += len(focused_content) + 2

    focused_excerpt = "\n\n".join(focused_parts).strip()

    if not focused_excerpt:
        focused_excerpt = str(
            best_document.get("child_content", "")
            or best_document.get("parent_content", "")
            or ""
        ).strip()

    # 프런트엔드가 parent_content를 우선 표시하므로 두 필드 모두
    # 핵심 조항 발췌문으로 맞춥니다.
    best_document["parent_content"] = focused_excerpt
    best_document["child_content"] = focused_excerpt[
        :MAX_SOURCE_CHILD_LENGTH
    ]

    return best_document


def select_return_penalty_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    반품 정률 위약금 문구의 근거를 제18조 → 제35조 순서로
    선택합니다. 제18조는 제8항~제10항 관련 청크를 우선합니다.
    """
    article_18_candidates: list[dict[str, Any]] = []
    article_35_candidates: list[dict[str, Any]] = []

    for document in documents:
        article_number = _refund_delay_notice_source_article(
            document
        )

        if article_number == 18:
            article_18_candidates.append(document)
        elif article_number == 35:
            article_35_candidates.append(document)

    selected: list[dict[str, Any]] = []

    focused_article_18 = (
        _focus_return_penalty_article_18_source(
            article_18_candidates
        )
    )

    if focused_article_18 is not None:
        selected.append(focused_article_18)

    if article_35_candidates:
        article_35_candidates.sort(
            key=lambda document: float(
                document.get(
                    "rerank_score",
                    document.get("score", 0.0),
                )
                or 0.0
            ),
            reverse=True,
        )

        selected.append(
            dict(article_35_candidates[0])
        )

    return selected


def ensure_return_penalty_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    위약금 유형에서는 기존 제18조 앞부분 청크가 있더라도
    제8항~제10항을 직접 검색하여 출처 카드에 표시합니다.
    """
    merged_documents = list(documents)

    article_18_result = search_documents(
        question=(
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제18조 제8항 일부 사용 또는 일부 소비로 얻은 이익 "
            "제9항 반환에 필요한 비용은 소비자가 부담하며 "
            "통신판매업자는 청약철회등을 이유로 위약금이나 "
            "손해배상을 청구할 수 없음 제10항 표시광고 또는 "
            "계약 내용과 다르게 이행된 경우 반환 비용은 "
            "통신판매업자가 부담"
        ),
        top_k=max(
            PLATFORM_EXPRESSION_SEARCH_TOP_K,
            8,
        ),
    )

    merged_documents.extend(
        sanitize_source_documents(
            article_18_result.get("documents", [])
        )
    )

    selected = select_return_penalty_sources(
        merged_documents
    )

    if not any(
        _refund_delay_notice_source_article(document) == 35
        for document in selected
    ):
        article_35_result = search_documents(
            question=(
                "전자상거래 등에서의 소비자보호에 관한 법률 "
                "제35조 소비자에게 불리한 계약의 금지 "
                "제17조부터 제19조까지를 위반한 약정으로서 "
                "소비자에게 불리한 것은 효력이 없음"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                article_35_result.get("documents", [])
            )
        )

    return select_return_penalty_sources(
        merged_documents
    )


def _extract_return_cost_article_18_excerpt(
    content: str,
) -> str:
    """
    제18조 전체 원문에서 반품 비용의 직접 근거인
    제9항과 제10항만 추출합니다.

    검색 결과를 화면 길이로 자르기 전에 실행해야 하므로
    원본 parent_content를 그대로 전달받습니다.
    """
    content = str(content or "").strip()

    if not content:
        return ""

    start_position = content.find("⑨")

    if start_position < 0:
        normalized = normalize_text(content)

        fallback_terms = (
            "제17조제1항에따른청약철회등의경우",
            "반환에필요한비용은소비자가부담",
            "위약금이나손해배상을청구할수없",
        )

        if not any(
            term in normalized
            for term in fallback_terms
        ):
            return ""

        start_candidates = [
            position
            for term in (
                "제17조제1항",
                "공급받은 재화등의 반환에 필요한 비용",
            )
            for position in (content.find(term),)
            if position >= 0
        ]

        if not start_candidates:
            return ""

        start_position = min(start_candidates)

    end_candidates = [
        position
        for marker in (
            "⑪",
            "[전문개정",
            "\n제19조",
            "\n## 제19조",
        )
        for position in (
            content.find(marker, start_position + 1),
        )
        if position >= 0
    ]

    end_position = (
        min(end_candidates)
        if end_candidates
        else len(content)
    )

    excerpt = content[
        start_position:end_position
    ].strip()

    normalized_excerpt = normalize_text(excerpt)

    has_consumer_cost_rule = (
        "반환에필요한비용" in normalized_excerpt
        and "소비자가부담" in normalized_excerpt
    )

    has_seller_cost_rule = (
        "반환에필요한비용" in normalized_excerpt
        and "통신판매업자가부담" in normalized_excerpt
    )

    if not (
        has_consumer_cost_rule
        and has_seller_cost_rule
    ):
        return ""

    return excerpt


def _set_source_display_excerpt(
    document: dict[str, Any],
    excerpt: str,
) -> dict[str, Any]:
    """
    프런트엔드와 응답 스키마에서 사용할 가능성이 있는
    모든 본문 필드를 같은 발췌문으로 맞춥니다.
    """
    focused_document = dict(document)
    clean_excerpt = str(excerpt or "").strip()

    if not clean_excerpt:
        return focused_document

    focused_document["parent_content"] = clean_excerpt
    focused_document["child_content"] = clean_excerpt[
        :MAX_SOURCE_CHILD_LENGTH
    ]

    # 프런트엔드는 parent_content를 우선하지만,
    # 응답 스키마나 향후 UI가 다른 필드를 사용할 경우에도
    # 동일한 직접 근거가 표시되도록 함께 설정합니다.
    for key in (
        "content",
        "text",
        "excerpt",
        "page_content",
        "document_content",
        "snippet",
        "passage",
    ):
        focused_document[key] = clean_excerpt

    metadata = focused_document.get("metadata")

    if isinstance(metadata, dict):
        focused_metadata = dict(metadata)

        for key in (
            "parent_content",
            "child_content",
            "content",
            "text",
            "excerpt",
            "snippet",
        ):
            focused_metadata[key] = clean_excerpt

        focused_document["metadata"] = focused_metadata

    return focused_document


def _return_cost_article_18_rank(
    document: dict[str, Any],
) -> float:
    """
    반품 배송비 질문의 제18조 후보 중 제9항·제10항을
    직접 포함한 청크를 최우선으로 선택합니다.
    """
    body_key = normalize_text(
        _return_penalty_source_body(document)
    )

    relevance_bonus = 0.0

    if (
        "반환에필요한비용은소비자가부담" in body_key
        or (
            "반환에필요한비용" in body_key
            and "소비자가부담" in body_key
        )
    ):
        relevance_bonus += 900.0

    if (
        "반환에필요한비용은통신판매업자가부담" in body_key
        or (
            "반환에필요한비용" in body_key
            and "통신판매업자가부담" in body_key
        )
    ):
        relevance_bonus += 1200.0

    if "위약금이나손해배상" in body_key:
        relevance_bonus += 300.0

    try:
        base_score = float(
            document.get(
                "rerank_score",
                document.get("score", 0.0),
            )
            or 0.0
        )
    except (TypeError, ValueError):
        base_score = 0.0

    return relevance_bonus + base_score


def _return_cost_excerpt_order(
    content: str,
) -> int:
    """제18조제9항 → 제10항 순서로 출처 조각을 배치합니다."""
    normalized = normalize_text(content)

    if (
        "⑨" in content
        or (
            "반환에필요한비용" in normalized
            and "소비자가부담" in normalized
        )
        or "위약금이나손해배상" in normalized
    ):
        return 9

    if (
        "⑩" in content
        or (
            "반환에필요한비용" in normalized
            and "통신판매업자가부담" in normalized
        )
    ):
        return 10

    return 99


def _focus_return_cost_article_18_source(
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    제18조 후보의 잘리지 않은 원문에서 제9항·제10항을 먼저
    추출한 후 화면용 출처를 구성합니다.
    """
    if not candidates:
        return None

    ranked_candidates = sorted(
        candidates,
        key=_return_cost_article_18_rank,
        reverse=True,
    )

    # parent_content 전체에 제9항·제10항이 함께 있는 후보를
    # 가장 먼저 사용합니다.
    for document in ranked_candidates:
        for content in (
            str(document.get("parent_content", "") or ""),
            str(document.get("child_content", "") or ""),
            str(document.get("content", "") or ""),
            str(document.get("text", "") or ""),
            str(document.get("excerpt", "") or ""),
        ):
            focused_excerpt = (
                _extract_return_cost_article_18_excerpt(
                    content
                )
            )

            if focused_excerpt:
                return _set_source_display_excerpt(
                    document=document,
                    excerpt=focused_excerpt,
                )

    # 검색 결과가 제9항과 제10항을 서로 다른 자식 청크로
    # 반환한 경우 두 조각을 조문 순서대로 결합합니다.
    paragraph_9 = ""
    paragraph_10 = ""
    best_document = dict(ranked_candidates[0])

    for document in ranked_candidates:
        for content in (
            str(document.get("child_content", "") or "").strip(),
            str(document.get("parent_content", "") or "").strip(),
        ):
            if not content:
                continue

            normalized = normalize_text(content)

            if (
                not paragraph_9
                and (
                    "⑨" in content
                    or (
                        "반환에필요한비용" in normalized
                        and "소비자가부담" in normalized
                    )
                    or "위약금이나손해배상" in normalized
                )
            ):
                start_position = content.find("⑨")

                if start_position >= 0:
                    content_9 = content[start_position:]
                else:
                    content_9 = content

                end_position = content_9.find("⑩")

                if end_position >= 0:
                    content_9 = content_9[:end_position]

                paragraph_9 = content_9.strip()

            if (
                not paragraph_10
                and (
                    "⑩" in content
                    or (
                        "반환에필요한비용" in normalized
                        and "통신판매업자가부담" in normalized
                    )
                )
            ):
                start_position = content.find("⑩")

                if start_position >= 0:
                    content_10 = content[start_position:]
                else:
                    content_10 = content

                end_candidates = [
                    position
                    for marker in (
                        "⑪",
                        "[전문개정",
                    )
                    for position in (
                        content_10.find(marker),
                    )
                    if position >= 0
                ]

                if end_candidates:
                    content_10 = content_10[
                        :min(end_candidates)
                    ]

                paragraph_10 = content_10.strip()

    combined_excerpt = "\n\n".join(
        part
        for part in (
            paragraph_9,
            paragraph_10,
        )
        if part
    ).strip()

    combined_key = normalize_text(combined_excerpt)

    if (
        "소비자가부담" in combined_key
        and "통신판매업자가부담" in combined_key
    ):
        return _set_source_display_excerpt(
            document=best_document,
            excerpt=combined_excerpt,
        )

    return None

def select_return_cost_excerpt_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    반품 배송비 질문에서는 제18조제9항·제10항이 포함된
    출처 하나만 선택합니다.
    """
    article_18_candidates = [
        document
        for document in documents
        if _refund_delay_notice_source_article(document) == 18
    ]

    focused_source = _focus_return_cost_article_18_source(
        article_18_candidates
    )

    if focused_source is None:
        return []

    return [focused_source]


def ensure_return_cost_excerpt_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    불량·오배송·계약 불일치 및 일반 반품 배송비 질문에서
    제18조제9항·제10항을 직접 검색해 출처로 반환합니다.
    """
    merged_documents = list(documents)

    article_18_result = search_documents(
        question=(
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제18조 제9항 단순 변심 청약철회 재화 반환에 "
            "필요한 비용은 소비자가 부담하고 통신판매업자는 "
            "청약철회를 이유로 위약금이나 손해배상을 청구할 수 "
            "없음 제10항 상품이 표시광고 또는 계약 내용과 "
            "다르게 이행된 경우 반환에 필요한 비용은 "
            "통신판매업자가 부담"
        ),
        top_k=max(
            PLATFORM_EXPRESSION_SEARCH_TOP_K,
            8,
        ),
    )

    raw_article_18_documents = (
        article_18_result.get("documents", [])
    )

    # 중요: sanitize_source_documents는 parent_content를
    # MAX_SOURCE_PARENT_LENGTH로 자릅니다. 제9항·제10항은
    # 제18조 뒤쪽에 있으므로 발췌하기 전에는 자르지 않습니다.
    merged_documents.extend(
        dict(document)
        for document in raw_article_18_documents
        if isinstance(document, dict)
    )

    return select_return_cost_excerpt_sources(
        merged_documents
    )


def _customer_service_obstruction_source_article(
    document: dict[str, Any],
) -> int | None:
    """고객센터 승인형 반품 방해 문구의 근거 조문을 판별합니다."""
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    source_key = normalize_text(source_file)
    structured_key = normalize_text(structured_text)

    if (
        "전자상거래" not in source_key
        and "전자상거래" not in structured_key
    ):
        return None

    if "제17조" in structured_key and "청약철회" in structured_key:
        return 17

    if "제21조" in structured_key and "금지행위" in structured_key:
        return 21

    if (
        "제35조" in structured_key
        and "소비자에게불리한계약" in structured_key
    ):
        return 35

    if not structured_key:
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")[:1800]
                for key in (
                    "child_content",
                    "parent_content",
                    "content",
                    "text",
                )
            )
        )

        if "제17조" in body_key and "청약철회" in body_key:
            return 17
        if "제21조" in body_key and "금지행위" in body_key:
            return 21
        if (
            "제35조" in body_key
            and "소비자에게불리한계약" in body_key
        ):
            return 35

    return None


def _customer_service_obstruction_source_score(
    document: dict[str, Any],
) -> float:
    """같은 조문 후보 중 질문과 직접 관련된 청크를 우선합니다."""
    body_key = normalize_text(
        " ".join(
            str(document.get(key, "") or "")
            for key in (
                "child_content",
                "parent_content",
                "content",
                "text",
            )
        )
    )

    article_number = _customer_service_obstruction_source_article(document)
    relevance_bonus = 0.0

    if article_number == 17:
        if (
            "방해행위가종료한날부터7일" in body_key
            or (
                "방해행위" in body_key
                and "종료한날부터7일" in body_key
            )
        ):
            relevance_bonus += 600.0
        if "청약철회등을할수있" in body_key:
            relevance_bonus += 200.0

    if article_number == 21:
        if (
            "청약철회등을방해" in body_key
            or ("청약철회" in body_key and "방해" in body_key)
        ):
            relevance_bonus += 800.0
        if (
            "거짓또는과장된사실" in body_key
            or "기만적인방법" in body_key
        ):
            relevance_bonus += 300.0

    if article_number == 35:
        if "소비자에게불리한것은효력이없" in body_key:
            relevance_bonus += 600.0

    try:
        base_score = float(
            document.get(
                "rerank_score",
                document.get("score", 0.0),
            )
            or 0.0
        )
    except (TypeError, ValueError):
        base_score = 0.0

    return relevance_bonus + base_score


def select_customer_service_obstruction_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    전화 접수·판매자 승인형 반품 방해 문구의 근거를
    제17조 → 제21조 → 제35조 순서로 선택합니다.
    """
    candidates: dict[int, list[dict[str, Any]]] = {
        17: [],
        21: [],
        35: [],
    }

    for document in documents:
        article_number = _customer_service_obstruction_source_article(
            document
        )
        if article_number in candidates:
            candidates[article_number].append(document)

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for article_number in (17, 21, 35):
        article_documents = candidates[article_number]
        article_documents.sort(
            key=_customer_service_obstruction_source_score,
            reverse=True,
        )

        for document in article_documents:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}:"
                    f"{article_number}"
                )
            )
            if unique_key in used_keys:
                continue
            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def ensure_customer_service_obstruction_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """제17조·제21조·제35조가 모두 반환되도록 보완합니다."""
    merged_documents = list(documents)

    article_queries = {
        17: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제17조 청약철회등 소비자는 법정 기간 안에 "
            "청약철회할 수 있고 제21조의 청약철회 방해 행위가 "
            "있는 경우 방해 행위가 종료한 날부터 7일"
        ),
        21: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제21조 금지행위 거짓 또는 과장된 사실이나 기만적인 "
            "방법을 사용하여 소비자의 청약철회등을 방해하는 행위 금지"
        ),
        35: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제35조 소비자에게 불리한 계약의 금지 제17조부터 "
            "제19조까지의 규정을 위반한 약정으로서 소비자에게 "
            "불리한 것은 효력이 없음"
        ),
    }

    for article_number in (17, 21, 35):
        selected = select_customer_service_obstruction_sources(
            merged_documents
        )

        if any(
            _customer_service_obstruction_source_article(document)
            == article_number
            for document in selected
        ):
            continue

        search_result = search_documents(
            question=article_queries[article_number],
            top_k=max(PLATFORM_EXPRESSION_SEARCH_TOP_K, 8),
        )

        merged_documents.extend(
            sanitize_source_documents(
                search_result.get("documents", [])
            )
        )

    return select_customer_service_obstruction_sources(
        merged_documents
    )


def _mismatch_refund_source_article(
    document: dict[str, Any],
) -> int | None:
    """
    출처가 전자상거래법 제17조·제18조·제35조 중
    어느 조문인지 판별합니다.

    heading뿐 아니라 heading_path, title 등 화면 표시용
    메타데이터도 함께 확인해 검색 결과 형식 차이를 흡수합니다.
    """
    source_file = str(
        document.get("source_file", "")
        or document.get("file_name", "")
        or ""
    )

    source_key = normalize_text(source_file)

    structured_text = " ".join(
        str(document.get(key, "") or "")
        for key in (
            "heading",
            "heading_path",
            "title",
            "section",
            "section_title",
            "article_title",
        )
    )

    structured_key = normalize_text(structured_text)

    if (
        "전자상거래" not in source_key
        and "전자상거래" not in structured_key
    ):
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        if "전자상거래" not in body_key:
            return None

    if (
        "제17조" in structured_key
        and "청약철회" in structured_key
    ):
        return 17

    if (
        "제18조" in structured_key
        and "청약철회" in structured_key
    ):
        return 18

    if (
        "제35조" in structured_key
        and "소비자에게불리한계약" in structured_key
    ):
        return 35

    # heading 계열이 비어 있는 검색 결과에 한해서만
    # 본문 첫 부분을 보조적으로 사용합니다.
    if not structured_key:
        body_key = normalize_text(
            " ".join(
                str(document.get(key, "") or "")[:500]
                for key in (
                    "child_content",
                    "parent_content",
                )
            )
        )

        if "제17조" in body_key and "청약철회" in body_key:
            return 17

        if "제18조" in body_key and "청약철회" in body_key:
            return 18

        if (
            "제35조" in body_key
            and "소비자에게불리한계약" in body_key
        ):
            return 35

    return None


def _mismatch_refund_source_score(
    document: dict[str, Any],
) -> float:
    """같은 조문 후보 중 가장 직접적인 검색 결과를 고릅니다."""
    for key in (
        "rerank_score",
        "score",
        "similarity_score",
        "dense_score",
    ):
        value = document.get(key)

        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue

    return 0.0


def has_mismatch_refund_source_article(
    documents: list[dict[str, Any]],
    article_number: int,
) -> bool:
    """선택된 출처에 특정 조문이 포함됐는지 확인합니다."""
    return any(
        _mismatch_refund_source_article(document)
        == article_number
        for document in documents
    )


def select_mismatch_refund_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    상품 설명 불일치 환불 제한 문구의 근거를
    제17조 → 제18조 순서로 고정합니다.

    제35조는 제17조 또는 제18조가 없을 때만 보조 근거로
    사용할 수 있지만, 제18조보다 앞에 표시하지 않습니다.
    """
    article_candidates: dict[
        int,
        list[dict[str, Any]],
    ] = {
        17: [],
        18: [],
        35: [],
    }

    for document in documents:
        article_number = _mismatch_refund_source_article(
            document
        )

        if article_number in article_candidates:
            article_candidates[article_number].append(
                document
            )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    # 조문 순서는 검색 점수와 관계없이 고정합니다.
    for article_number in (17, 18, 35):
        candidates = article_candidates[article_number]

        candidates.sort(
            key=_mismatch_refund_source_score,
            reverse=True,
        )

        for document in candidates:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

        if len(selected) >= 2:
            break

    return selected


def ensure_mismatch_refund_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    상품 설명 불일치 답변의 직접 근거인 제17조와 제18조를
    각각 확인하고, 누락된 조문만 정확한 조문명으로 별도
    검색합니다.

    최종 반환 순서는 항상 제17조 → 제18조입니다.
    """
    merged_documents = list(documents)

    selected_documents = select_mismatch_refund_sources(
        merged_documents
    )

    if not has_mismatch_refund_source_article(
        selected_documents,
        17,
    ):
        article_17_result = search_documents(
            question=(
                "전자상거래 등에서의 소비자보호에 관한 법률 "
                "제17조 청약철회등 제3항 재화등의 내용이 "
                "표시 광고의 내용과 다르거나 계약내용과 다르게 "
                "이행된 경우 공급받은 날부터 3개월 이내, "
                "그 사실을 안 날 또는 알 수 있었던 날부터 "
                "30일 이내 청약철회"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        article_17_documents = sanitize_source_documents(
            article_17_result.get("documents", [])
        )

        merged_documents.extend(article_17_documents)

    selected_documents = select_mismatch_refund_sources(
        merged_documents
    )

    if not has_mismatch_refund_source_article(
        selected_documents,
        18,
    ):
        article_18_result = search_documents(
            question=(
                "전자상거래 등에서의 소비자보호에 관한 법률 "
                "제18조 청약철회등의 효과 재화 반환, "
                "반환받은 날부터 3영업일 이내 대금 환급, "
                "표시 광고 또는 계약 내용과 다른 경우 "
                "반환 비용 통신판매업자 부담"
            ),
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        article_18_documents = sanitize_source_documents(
            article_18_result.get("documents", [])
        )

        merged_documents.extend(article_18_documents)

    return select_mismatch_refund_sources(
        merged_documents
    )


def select_discounted_return_prohibition_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    세일·할인 상품 반품·환불 전면 제한 문구의 직접 근거를
    제17조 → 제18조 → 제35조 순서로 하나씩 선택합니다.
    """
    article_candidates: dict[
        int,
        list[dict[str, Any]],
    ] = {
        17: [],
        18: [],
        35: [],
    }

    for document in documents:
        article_number = _mismatch_refund_source_article(
            document
        )

        if article_number in article_candidates:
            article_candidates[article_number].append(
                document
            )

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for article_number in (17, 18, 35):
        candidates = article_candidates[article_number]

        candidates.sort(
            key=lambda document: float(
                document.get(
                    "rerank_score",
                    document.get("score", 0.0),
                )
                or 0.0
            ),
            reverse=True,
        )

        for document in candidates:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def has_discounted_return_source_article(
    documents: list[dict[str, Any]],
    article_number: int,
) -> bool:
    """선택된 출처에 요청한 전자상거래법 조문이 있는지 확인합니다."""
    return any(
        _mismatch_refund_source_article(document)
        == article_number
        for document in documents
    )


def ensure_discounted_return_prohibition_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    제17조·제18조·제35조를 확보하고,
    제18조는 반품 비용의 직접 근거인 제9항·제10항만
    화면에 표시되도록 발췌합니다.
    """
    merged_documents = list(documents)

    article_queries = {
        17: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제17조 청약철회등 소비자가 계약내용 서면을 받은 "
            "날부터 7일 이내에 청약철회할 수 있는 원칙, "
            "소비자 책임의 훼손과 사용으로 가치가 현저히 감소한 "
            "경우의 제한, 표시 광고 또는 계약 내용과 다른 경우 "
            "3개월 이내 및 안 날부터 30일 이내 청약철회"
        ),
        35: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제35조 소비자에게 불리한 계약의 금지 제17조부터 "
            "제19조까지의 규정을 위반한 약정으로서 소비자에게 "
            "불리한 것은 효력이 없음"
        ),
    }

    for article_number in (17, 35):
        selected = select_discounted_return_prohibition_sources(
            merged_documents
        )

        if has_discounted_return_source_article(
            selected,
            article_number,
        ):
            continue

        search_result = search_documents(
            question=article_queries[article_number],
            top_k=max(
                PLATFORM_EXPRESSION_SEARCH_TOP_K,
                8,
            ),
        )

        merged_documents.extend(
            sanitize_source_documents(
                search_result.get("documents", [])
            )
        )

    # 제18조 뒤쪽의 제9항·제10항이 잘리지 않도록
    # 원문 검색 결과를 sanitize 전에 그대로 병합합니다.
    article_18_result = search_documents(
        question=(
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제18조 제9항 단순 변심 청약철회의 반환 비용은 "
            "소비자가 부담하고 청약철회를 이유로 위약금이나 "
            "손해배상을 청구할 수 없음, 제10항 표시 광고 또는 "
            "계약 내용과 다른 경우 반환 비용은 통신판매업자가 부담"
        ),
        top_k=max(
            PLATFORM_EXPRESSION_SEARCH_TOP_K,
            8,
        ),
    )

    raw_article_18_documents = (
        article_18_result.get("documents", [])
    )

    merged_documents.extend(
        dict(document)
        for document in raw_article_18_documents
        if isinstance(document, dict)
    )

    selected_documents = (
        select_discounted_return_prohibition_sources(
            merged_documents
        )
    )

    article_18_candidates = [
        document
        for document in merged_documents
        if _mismatch_refund_source_article(document) == 18
    ]

    focused_article_18 = _focus_return_cost_article_18_source(
        article_18_candidates
    )

    final_documents: list[dict[str, Any]] = []

    for article_number in (17, 18, 35):
        if (
            article_number == 18
            and focused_article_18 is not None
        ):
            final_documents.append(focused_article_18)
            continue

        matching_document = next(
            (
                document
                for document in selected_documents
                if _mismatch_refund_source_article(document)
                == article_number
            ),
            None,
        )

        if matching_document is not None:
            final_documents.append(matching_document)

    return final_documents


def select_custom_made_return_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    주문제작 반품 질문의 근거를
    전자상거래법 제17조 → 제35조 순서로 선택합니다.

    현재 데이터 정책상 시행령은 사용하지 않습니다.
    """
    candidates: dict[int, list[dict[str, Any]]] = {
        17: [],
        35: [],
    }

    for document in documents:
        article_number = _mismatch_refund_source_article(
            document
        )

        if article_number in candidates:
            candidates[article_number].append(document)

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for article_number in (17, 35):
        article_documents = candidates[article_number]
        article_documents.sort(
            key=_mismatch_refund_source_score,
            reverse=True,
        )

        for document in article_documents:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}:"
                    f"{article_number}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def ensure_custom_made_return_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    주문제작 질문에서 제18조가 잘못 노출되지 않도록
    제17조와 제35조를 별도 검색하여 출처를 고정합니다.
    """
    merged_documents = list(documents)

    article_queries = {
        17: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제17조 청약철회등 계약내용에 관한 서면을 받은 "
            "날부터 7일 이내 청약철회, 소비자 책임의 훼손과 "
            "사용으로 가치가 현저히 감소한 경우의 제한, "
            "표시 광고 또는 계약 내용과 다른 경우 공급일부터 "
            "3개월 이내 및 안 날부터 30일 이내 청약철회"
        ),
        35: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제35조 소비자에게 불리한 계약의 금지 "
            "제17조부터 제19조까지의 규정을 위반한 약정으로서 "
            "소비자에게 불리한 것은 효력이 없음"
        ),
    }

    for article_number in (17, 35):
        selected = select_custom_made_return_sources(
            merged_documents
        )

        if any(
            _mismatch_refund_source_article(document)
            == article_number
            for document in selected
        ):
            continue

        search_result = search_documents(
            question=article_queries[article_number],
            top_k=max(
                PLATFORM_EXPRESSION_SEARCH_TOP_K,
                8,
            ),
        )

        merged_documents.extend(
            sanitize_source_documents(
                search_result.get("documents", [])
            )
        )

    return select_custom_made_return_sources(
        merged_documents
    )


def select_short_return_period_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """짧은 반품 기간의 근거를 제17조 → 제35조 순서로 선택합니다."""
    candidates: dict[int, list[dict[str, Any]]] = {
        17: [],
        35: [],
    }

    for document in documents:
        article_number = _mismatch_refund_source_article(document)

        if article_number in candidates:
            candidates[article_number].append(document)

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for article_number in (17, 35):
        article_documents = candidates[article_number]
        article_documents.sort(
            key=_mismatch_refund_source_score,
            reverse=True,
        )

        for document in article_documents:
            unique_key = str(
                document.get("parent_id")
                or document.get("child_id")
                or document.get("id")
                or (
                    f"{document.get('source_file', '')}:"
                    f"{document.get('heading', '')}"
                )
            )

            if unique_key in used_keys:
                continue

            used_keys.add(unique_key)
            selected.append(document)
            break

    return selected


def ensure_short_return_period_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """누락된 제17조·제35조를 검색하고 출처 순서를 고정합니다."""
    merged_documents = list(documents)

    article_queries = {
        17: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제17조 청약철회등 계약내용에 관한 서면을 받은 날부터 "
            "7일 이내 청약철회, 상품 공급이 늦은 경우 공급받은 "
            "날부터 7일, 표시 광고 또는 계약 내용과 다른 경우 "
            "공급일부터 3개월 이내 및 안 날부터 30일 이내 청약철회"
        ),
        35: (
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제35조 소비자에게 불리한 계약의 금지 제17조부터 "
            "제19조까지의 규정을 위반한 약정으로서 소비자에게 "
            "불리한 것은 효력이 없음"
        ),
    }

    for article_number in (17, 35):
        selected = select_short_return_period_sources(
            merged_documents
        )

        if any(
            _mismatch_refund_source_article(document)
            == article_number
            for document in selected
        ):
            continue

        search_result = search_documents(
            question=article_queries[article_number],
            top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
        )

        merged_documents.extend(
            sanitize_source_documents(
                search_result.get("documents", [])
            )
        )

    return select_short_return_period_sources(
        merged_documents
    )


def detect_explicit_copy_label(
    question: str,
) -> str:
    """
    사용자가 입력한 문구 유형을 답변에 그대로 반영합니다.

    예:
    - 상세페이지 문구: ... -> 상세페이지 문구
    - 반품·환불 문구: ...  -> 반품·환불 문구
    - 광고 문구: ...       -> 광고 문구
    - 홍보 문구: ...       -> 홍보 문구
    - 카피: ...            -> 광고 카피
    """
    if re.search(
        r"상세\s*페이지\s*문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "상세페이지 문구"

    if re.search(
        r"상품\s*상세\s*(?:페이지\s*)?문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "상세페이지 문구"

    if re.search(
        r"반품\s*(?:[·ㆍ/]|및|과|와)?\s*환불\s*문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "반품·환불 문구"

    if re.search(
        r"환불\s*(?:[·ㆍ/]|및|과|와)?\s*반품\s*문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "반품·환불 문구"

    if re.search(
        r"홍보\s*문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "홍보 문구"

    if re.search(
        r"광고\s*문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "광고 문구"

    if re.search(
        r"카피\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "광고 카피"

    if re.search(
        r"문구\s*[:：]",
        question,
        flags=re.IGNORECASE,
    ):
        return "검토 문구"

    return "광고 문구"


def extract_explicit_ad_copy(
    question: str,
) -> str | None:
    """
    질문에 포함된 실제 광고 문구를 추출합니다.

    지원 형태:
    - "광고 문구"
    - '광고 문구'
    - “광고 문구”
    - 광고 문구: 내용
    """
    colon_match = re.search(
        r"(?:"
        r"상세\s*페이지\s*문구|"
        r"상품\s*상세\s*(?:페이지\s*)?문구|"
        r"반품\s*(?:[·ㆍ/]|및|과|와)?\s*환불\s*문구|"
        r"환불\s*(?:[·ㆍ/]|및|과|와)?\s*반품\s*문구|"
        r"광고\s*문구|"
        r"홍보\s*문구|"
        r"문구|"
        r"카피"
        r")\s*[:：]\s*(.+)",
        question,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if colon_match:
        candidate = colon_match.group(1).strip()
        candidate = candidate.strip(" \"'“”‘’")

        if len(candidate) >= 2:
            return candidate

    quoted_patterns = (
        r'"([^"\n]{2,})"',
        r"'([^'\n]{2,})'",
        r"“([^”\n]{2,})”",
        r"‘([^’\n]{2,})’",
    )

    for pattern in quoted_patterns:
        match = re.search(pattern, question)

        if match:
            candidate = match.group(1).strip()

            if len(candidate) >= 2:
                return candidate

    return None


def has_explicit_ad_copy(question: str) -> bool:
    """질문에 실제 검토할 광고 문구가 있는지 확인합니다."""
    return extract_explicit_ad_copy(question) is not None


def is_explicit_ad_copy_assessment_question(
    question: str,
) -> bool:
    """
    실제 광고 문구를 추출할 수 있으면 광고 문구 검토 질문으로
    처리합니다.

    `광고 문구:`, `홍보 문구:`, `문구:`, `카피:` 형식과
    따옴표로 입력된 문구를 지원합니다.
    """
    return extract_explicit_ad_copy(question) is not None

def get_korean_topic_particle(value: str) -> str:
    """
    문자열 마지막 한글 음절의 받침 여부에 따라
    주제 조사 '은/는'을 반환합니다.
    """
    for character in reversed(value.strip()):
        if "가" <= character <= "힣":
            has_final_consonant = (
                (ord(character) - ord("가")) % 28
                != 0
            )
            return "은" if has_final_consonant else "는"

        if character.isdigit():
            # 숫자의 한국어 독음을 기준으로 받침 여부를 처리합니다.
            return (
                "은"
                if character in {"0", "1", "3", "6", "7", "8"}
                else "는"
            )

        if character.isalpha():
            # 외국어 문구는 안전한 기본값을 사용합니다.
            return "은"

    return "은"


def is_domestic_sales_rank_ad_copy(
    ad_copy: str,
) -> bool:
    """
    '국내 판매 1위'처럼 특정 시장에서의 판매순위를
    사실로 주장하는 문구를 판별합니다.
    """
    normalized_ad_copy = normalize_text(ad_copy)

    rank_match = re.search(
        r"(\d+)\s*위",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_sales_metric = any(
        term in normalized_ad_copy
        for term in (
            "판매",
            "판매량",
            "판매수량",
            "매출",
            "매출액",
            "구매",
            "주문",
            "베스트셀러",
        )
    )

    has_market_scope = any(
        term in normalized_ad_copy
        for term in (
            "국내",
            "전국",
            "대한민국",
            "한국",
            "온라인",
            "오프라인",
            "자사몰",
            "쇼핑몰",
            "플랫폼",
            "카테고리",
            "부문",
        )
    )

    return (
        rank_match is not None
        and has_sales_metric
        and has_market_scope
    )


def is_domestic_sales_rank_ad_copy_question(
    question: str,
) -> bool:
    """질문에서 판매순위 사실 주장 문구를 판별합니다."""
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_domestic_sales_rank_ad_copy(ad_copy)
    )


def is_comparative_multiplier_ad_copy(
    ad_copy: str,
) -> bool:
    """
    '타사 제품보다 보정 효과가 2배 뛰어나다'처럼
    비교 대상과 배수 수치가 포함된 성능 주장을 판별합니다.
    """
    normalized_ad_copy = normalize_text(ad_copy)

    multiplier_match = re.search(
        r"(\d+(?:\.\d+)?)\s*배",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_comparison_target = any(
        term in normalized_ad_copy
        for term in (
            "타사제품보다",
            "타사보다",
            "다른제품보다",
            "일반제품보다",
            "기존제품보다",
            "자사기존제품보다",
            "경쟁제품보다",
            "비교제품보다",
        )
    )

    has_performance_claim = any(
        term in normalized_ad_copy
        for term in (
            "효과",
            "성능",
            "보정",
            "압박",
            "지지력",
            "신축성",
            "흡수력",
            "보온",
            "통기",
            "지속력",
            "뛰어",
            "우수",
            "강하",
            "높",
        )
    )

    return (
        multiplier_match is not None
        and has_comparison_target
        and has_performance_claim
    )


def is_comparative_multiplier_ad_copy_question(
    question: str,
) -> bool:
    """질문에서 타사 대비 배수 효과 문구가 추출되는지 확인합니다."""
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_comparative_multiplier_ad_copy(ad_copy)
    )


def is_universal_numeric_waist_appearance_ad_copy(
    ad_copy: str,
) -> bool:
    """
    '누구나 허리가 5cm 가늘어 보인다'처럼 모든 착용자에게
    동일한 정량적 시각 효과가 나타난다고 주장하는 문구를
    판별합니다.
    """
    normalized_ad_copy = normalize_text(ad_copy)

    measurement_match = re.search(
        r"(\d+(?:\.\d+)?)\s*"
        r"(cm|센티미터|mm|밀리미터|인치|inch|in)",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_universal_scope = any(
        term in normalized_ad_copy
        for term in (
            "누구나",
            "누가입어도",
            "모든사람",
            "모든착용자",
            "어떤체형도",
            "어떤체형이든",
            "체형에관계없이",
        )
    )

    has_waist_subject = any(
        term in normalized_ad_copy
        for term in (
            "허리",
            "허리라인",
            "웨이스트",
        )
    )

    has_visual_appearance_claim = any(
        term in normalized_ad_copy
        for term in (
            "가늘어보",
            "얇아보",
            "슬림해보",
            "잘록해보",
            "작아보",
            "줄어보",
        )
    )

    return (
        measurement_match is not None
        and has_universal_scope
        and has_waist_subject
        and has_visual_appearance_claim
    )


def is_universal_numeric_waist_appearance_ad_copy_question(
    question: str,
) -> bool:
    """질문에서 보편적·정량적 허리 시각 효과 문구를 판별합니다."""
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_universal_numeric_waist_appearance_ad_copy(
            ad_copy
        )
    )


def is_laundry_shrinkage_ad_copy(
    ad_copy: str,
) -> bool:
    """
    세탁 후 수축이 전혀 없다고 단정하는 성능 문구를 판별합니다.
    """
    normalized_ad_copy = normalize_text(ad_copy)

    has_laundry_context = any(
        term in normalized_ad_copy
        for term in (
            "세탁",
            "물세탁",
            "손세탁",
            "기계세탁",
            "빨래",
            "세탁기",
            "건조기",
        )
    )

    has_shrinkage_subject = any(
        term in normalized_ad_copy
        for term in (
            "줄어들",
            "줄지않",
            "수축",
            "축소",
            "사이즈변화",
            "크기변화",
            "형태변화",
        )
    )

    has_no_shrinkage_claim = any(
        term in normalized_ad_copy
        for term in (
            "절대줄어들지않",
            "전혀줄어들지않",
            "줄어들지않",
            "줄지않",
            "수축하지않",
            "수축되지않",
            "수축없",
            "수축이없",
            "수축률0",
            "변형되지않",
            "형태변화없",
            "형태변화가없",
        )
    )

    return (
        has_laundry_context
        and has_shrinkage_subject
        and has_no_shrinkage_claim
    )


def is_laundry_shrinkage_ad_copy_question(
    question: str,
) -> bool:
    """질문에서 세탁 수축 관련 문구가 추출되는지 확인합니다."""
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_laundry_shrinkage_ad_copy(ad_copy)
    )


def is_full_natural_material_ad_copy(
    ad_copy: str,
) -> bool:
    """
    천연가죽 100%, 면 100%, 울 100%처럼 소재와 함량을
    사실로 표시하는 문구를 판별합니다.
    """
    normalized_ad_copy = normalize_text(ad_copy)

    percentage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        ad_copy,
        flags=re.IGNORECASE,
    )

    if (
        percentage_match is None
        or percentage_match.group(1) != "100"
    ):
        return False

    material_terms = (
        "천연소재",
        "천연섬유",
        "자연소재",
        "천연원료",
        "순수천연",
        "내추럴소재",
        "천연가죽",
        "천연피혁",
        "리얼레더",
        "소가죽",
        "양가죽",
        "염소가죽",
        "돈피",
        "면100",
        "울100",
        "모100",
        "실크100",
        "린넨100",
    )

    return any(
        term in normalized_ad_copy
        for term in material_terms
    )


def is_full_natural_material_ad_copy_question(
    question: str,
) -> bool:
    """질문에서 100% 천연 소재 문구가 추출되는지 확인합니다."""
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_full_natural_material_ad_copy(ad_copy)
    )


def is_unconditional_free_shipping_ad_copy(
    ad_copy: str,
) -> bool:
    """'전 상품 무료배송'과 같은 전면 무료배송 문구를 판별합니다."""
    normalized_ad_copy = normalize_text(ad_copy)

    has_free_shipping_claim = any(
        term in normalized_ad_copy
        for term in (
            "무료배송",
            "배송비무료",
            "배송비0원",
            "배송비제로",
            "배송료무료",
        )
    )

    has_all_products_scope = any(
        term in normalized_ad_copy
        for term in (
            "전상품",
            "모든상품",
            "전체상품",
            "전제품",
            "모든제품",
            "전체제품",
        )
    )

    return (
        has_free_shipping_claim
        and has_all_products_scope
    )


def _contains_any_ad_copy_term(
    ad_copy: str,
    terms: tuple[str, ...],
) -> bool:
    normalized = normalize_text(ad_copy)

    return any(
        normalize_text(term) in normalized
        for term in terms
    )


def build_explicit_ad_copy_assessment_answer(
    ad_copy: str,
    copy_label: str = "광고 문구",
) -> str:
    """
    실제 광고 문구에 포함된 위험 표현을 기준으로
    검토 결과와 수정 예시를 반환합니다.
    """
    absolute_terms = (
        "무조건",
        "반드시",
        "누구나",
        "항상",
        "절대",
        "100%",
        "완벽",
        "확실히",
        "즉시",
        "단번에",
    )

    appearance_terms = (
        "날씬",
        "슬림",
        "키가커보",
        "다리가길어보",
        "얼굴이작아보",
        "체형보정",
        "군살",
        "사이즈작아보",
        "한사이즈작아보",
        "두사이즈작아보",
        "작아보",
        "체형이작아보",
    )

    effect_terms = (
        "효과",
        "효능",
        "개선",
        "치료",
        "완치",
        "감량",
        "살이빠",
        "지방제거",
        "통증완화",
    )

    superiority_terms = (
        "최고",
        "최상",
        "최초",
        "유일",
        "1위",
        "가장",
        "압도적",
        "완벽한",
    )

    has_absolute = _contains_any_ad_copy_term(
        ad_copy,
        absolute_terms,
    )
    has_appearance = _contains_any_ad_copy_term(
        ad_copy,
        appearance_terms,
    )
    has_effect = _contains_any_ad_copy_term(
        ad_copy,
        effect_terms,
    )
    has_superiority = _contains_any_ad_copy_term(
        ad_copy,
        superiority_terms,
    )

    normalized_ad_copy = normalize_text(ad_copy)

    has_numeric_appearance_effect = (
        re.search(
            r"\d+(?:\.\d+)?\s*(?:kg|킬로그램)",
            ad_copy,
            flags=re.IGNORECASE,
        )
        is not None
        and any(
            term in normalized_ad_copy
            for term in (
                "빠져보",
                "날씬해보",
                "슬림해보",
                "작아보",
                "감량해보",
            )
        )
    )

    has_immediate_effect = any(
        term in normalized_ad_copy
        for term in (
            "입는순간",
            "착용즉시",
            "즉시",
            "바로",
            "단번에",
        )
    )

    has_complete_disappearance_claim = (
        any(
            body_term in normalized_ad_copy
            for body_term in (
                "군살",
                "뱃살",
                "옆구리살",
                "팔뚝살",
                "허벅지살",
            )
        )
        and any(
            disappearance_term in normalized_ad_copy
            for disappearance_term in (
                "완전히사라져",
                "완전히사라진",
                "전부사라져",
                "모두사라져",
                "싹사라져",
                "완전히없어져",
                "완전히제거",
            )
        )
    )

    comparative_multiplier_match = re.search(
        r"(\d+(?:\.\d+)?)\s*배",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_comparison_target = any(
        comparison_term in normalized_ad_copy
        for comparison_term in (
            "타사제품보다",
            "타사보다",
            "다른제품보다",
            "일반제품보다",
            "기존제품보다",
            "자사기존제품보다",
            "경쟁제품보다",
            "비교제품보다",
        )
    )

    has_domestic_sales_rank_claim = (
        is_domestic_sales_rank_ad_copy(ad_copy)
    )

    has_comparative_multiplier_claim = (
        is_comparative_multiplier_ad_copy(ad_copy)
    )

    has_universal_numeric_waist_appearance_claim = (
        is_universal_numeric_waist_appearance_ad_copy(
            ad_copy
        )
    )

    has_laundry_shrinkage_claim = (
        is_laundry_shrinkage_ad_copy(ad_copy)
    )

    has_full_natural_material_claim = (
        is_full_natural_material_ad_copy(ad_copy)
    )

    has_leather_material_expression = any(
        leather_term in normalized_ad_copy
        for leather_term in (
            "천연가죽",
            "천연피혁",
            "리얼레더",
            "소가죽",
            "양가죽",
            "염소가죽",
            "돈피",
        )
    )

    discount_rate_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_discount_expression = any(
        discount_term in normalized_ad_copy
        for discount_term in (
            "할인",
            "세일",
            "가격인하",
            "특가",
        )
    )

    has_today_only_expression = any(
        limited_time_term in normalized_ad_copy
        for limited_time_term in (
            "오늘만",
            "오늘하루",
            "단하루",
            "하루만",
            "금일한정",
            "오늘한정",
            "당일한정",
        )
    )

    has_limited_discount_claim = (
        discount_rate_match is not None
        and has_discount_expression
        and has_today_only_expression
    )

    has_free_shipping_claim = any(
        free_shipping_term in normalized_ad_copy
        for free_shipping_term in (
            "무료배송",
            "배송비무료",
            "배송비0원",
            "배송비제로",
            "배송료무료",
        )
    )

    has_all_products_scope = any(
        all_scope_term in normalized_ad_copy
        for all_scope_term in (
            "전상품",
            "모든상품",
            "전체상품",
            "전제품",
            "모든제품",
            "전체제품",
        )
    )

    has_unconditional_free_shipping_claim = (
        is_unconditional_free_shipping_ad_copy(
            ad_copy
        )
    )

    has_disparagement_target = any(
        target_term in normalized_ad_copy
        for target_term in (
            "다른쇼핑몰제품",
            "타쇼핑몰제품",
            "타사제품",
            "경쟁사제품",
            "경쟁업체제품",
            "다른브랜드제품",
            "다른업체제품",
            "경쟁제품",
            "타사상품",
            "다른쇼핑몰",
            "경쟁사",
        )
    )

    has_disparaging_expression = any(
        disparaging_term in normalized_ad_copy
        for disparaging_term in (
            "형편없",
            "최악",
            "저질",
            "쓰레기",
            "엉망",
            "볼품없",
            "품질이나쁘",
            "품질이낮",
            "품질이떨어",
            "핏이나쁘",
            "못입",
            "촌스럽",
            "후지",
        )
    )

    has_disparagement_claim = (
        has_disparagement_target
        and has_disparaging_expression
    )

    has_quality_disparagement_subject = any(
        quality_term in normalized_ad_copy
        for quality_term in (
            "품질",
            "원단",
            "소재",
            "봉제",
            "내구성",
            "마감",
            "불량",
            "수축",
            "변색",
        )
    )

    has_fit_disparagement_subject = any(
        fit_term in normalized_ad_copy
        for fit_term in (
            "핏",
            "실루엣",
            "착용감",
            "사이즈",
            "라인",
        )
    )

    has_discoloration_claim = (
        any(
            discoloration_term in normalized_ad_copy
            for discoloration_term in (
                "변색",
                "색이변",
                "색변화",
                "색빠짐",
                "색이바래",
            )
        )
        and any(
            no_discoloration_term in normalized_ad_copy
            for no_discoloration_term in (
                "되지않",
                "안되",
                "없",
                "발생하지않",
                "변하지않",
                "바래지않",
            )
        )
    )

    has_lifetime_or_permanent_claim = any(
        lifetime_term in normalized_ad_copy
        for lifetime_term in (
            "평생",
            "영구",
            "영원히",
            "반영구",
            "절대",
            "100",
        )
    )

    has_lifetime_discoloration_claim = (
        has_discoloration_claim
        and has_lifetime_or_permanent_claim
    )

    has_pilling_claim = (
        any(
            pilling_term in normalized_ad_copy
            for pilling_term in (
                "보풀",
                "필링",
            )
        )
        and any(
            no_pilling_term in normalized_ad_copy
            for no_pilling_term in (
                "생기지않",
                "안생",
                "발생하지않",
                "보풀없",
                "필링없",
                "보풀제로",
            )
        )
    )

    numeric_length_match = re.search(
        r"(\d+(?:\.\d+)?)\s*"
        r"(cm|센티미터|mm|밀리미터|인치|inch|in)",
        ad_copy,
        flags=re.IGNORECASE,
    )

    has_numeric_length_effect = (
        numeric_length_match is not None
        and any(
            length_term in normalized_ad_copy
            for length_term in (
                "다리가길어보",
                "다리길어보",
                "키가커보",
                "키커보",
                "길어보",
            )
        )
    )

    if has_universal_numeric_waist_appearance_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        measurement_match = re.search(
            r"(\d+(?:\.\d+)?)\s*"
            r"(cm|센티미터|mm|밀리미터|인치|inch|in)",
            ad_copy,
            flags=re.IGNORECASE,
        )

        measurement = (
            f"{measurement_match.group(1)}"
            f"{measurement_match.group(2)}"
            if measurement_match is not None
            else "표시된 수치"
        )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 모든 착용자에게 "
            "동일한 시각적 효과가 나타나고, 그 효과가 "
            f"{measurement}에 해당한다는 의미로 받아들여질 수 "
            "있어 수정하는 것이 안전합니다.\n\n"
            "‘가늘어 보인다’는 실제 허리둘레가 감소한다는 뜻과는 "
            "다르지만, 구체적인 길이 수치를 함께 표시하면 "
            "객관적으로 측정된 효과처럼 받아들여질 수 있습니다. "
            "허리가 가늘어 보이는 정도는 착용자의 체형, 선택한 "
            "사이즈, 착용 방법, 자세, 촬영 거리와 각도, 조명 및 "
            "비교 방법에 따라 달라질 수 있습니다. 따라서 일부 "
            "착용 사례만으로 ‘누구나’라고 표시하거나 객관적인 "
            f"평가 기준 없이 ‘{measurement}’라는 수치를 사용해서는 "
            "안 됩니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 착용 평가에 참여한 인원과 체형 범위\n"
            "• 평가에 사용한 제품 사이즈와 착용 방법\n"
            "• 착용 전후의 자세, 촬영 거리·각도와 조명 조건\n"
            f"• {measurement} 효과를 판단한 측정 또는 평가 기준\n"
            "• 평균 결과인지 모든 참여자에게 나타난 결과인지\n"
            "• 실제 허리둘레 감소가 아닌 시각적 연출 효과라는 점\n\n"
            "객관적인 수치 근거가 없다면 다음처럼 실제 디자인 "
            "특징을 설명하는 방식으로 바꾸는 것이 안전합니다.\n"
            "• 허리 라인을 슬림하게 연출하는 디자인\n"
            "• 허리 절개선으로 시각적인 슬림 효과 연출\n"
            "• 착용 시 허리선을 강조하는 실루엣\n\n"
            "착용 평가 결과를 사용하려면 실제 조사 대상과 방법, "
            "참여 인원, 응답 인원 및 개인차를 함께 표시해야 "
            "합니다. 예를 들면 ‘자사 착용 평가 참여자 ○명 중 "
            "○명이 허리 라인이 더 슬림해 보인다고 응답 "
            "(개인에 따라 차이가 있을 수 있음)’처럼 실제 조사 "
            "결과를 정확하게 입력해야 합니다. 임의의 조사 인원이나 "
            "응답 수를 만들어 표시해서는 안 됩니다.\n\n"
            "실제 허리둘레가 감소한 것과 시각적인 연출 효과를 "
            "혼동하게 해서는 안 되며, 확인된 조사나 시험 범위를 "
            "넘어서 모든 착용자에게 같은 결과가 나타난다고 "
            "보장해서는 안 됩니다."
        )

    if has_laundry_shrinkage_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 세탁 방법이나 "
            "건조 조건과 관계없이 제품에 수축이 전혀 발생하지 "
            "않는다는 의미로 받아들여질 수 있어 수정하는 것이 "
            "안전합니다.\n\n"
            "세탁 후 수축 여부는 물의 온도, 세탁 방식, 세제, "
            "탈수 강도, 건조기 사용 여부, 건조 온도와 세탁 횟수 "
            "등에 따라 달라질 수 있습니다. 따라서 확인하지 않은 "
            "조건까지 포함해 수축이 전혀 없다고 단정해서는 안 "
            "됩니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 시험에 사용한 세탁 방법과 물의 온도\n"
            "• 세제 종류, 세탁 시간과 탈수 조건\n"
            "• 자연 건조 또는 건조기 사용 여부와 건조 온도\n"
            "• 시험한 세탁 횟수\n"
            "• 세탁 전후 길이·폭과 수축률 측정 결과\n"
            "• 시험 대상 제품과 실제 판매 제품의 소재·제조 조건 일치 여부\n\n"
            "객관적인 시험 결과가 있다면 확인된 조건과 수치를 "
            "함께 표시하는 방식으로 바꿀 수 있습니다.\n"
            "• 표시된 세탁 방법 준수 시 수축률 3% 이하\n"
            "• 30℃ 중성세제 세탁 시험 결과, 1회 세탁 후 "
            "길이 방향 수축률 1.5%\n"
            "• 자연 건조 기준 형태 변화 최소화\n"
            "• 건조기 사용 시 수축이 발생할 수 있음\n\n"
            "시험하지 않은 모든 세탁 환경에서 수축이 전혀 없다고 "
            "보장해서는 안 됩니다. 실제 시험으로 확인한 세탁 조건, "
            "세탁 횟수와 수축률 범위에 한해서만 구체적으로 "
            "표시해야 합니다."
        )

    if has_full_natural_material_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        if has_leather_material_expression:
            material_name = "천연가죽"
            scope_examples = (
                "• 겉감: 천연가죽 100%\n"
                "• 외피: 소가죽 100% / 안감: 폴리에스터 100%\n"
                "• 본체: 천연가죽 / 안감·밑창·장식: 별도 소재\n"
                "• 천연가죽 사용 (부자재 제외)"
            )
            component_examples = (
                "안감, 밑창, 코팅, 접착층, 장식과 부자재"
            )
        else:
            material_name = "표시한 천연 소재"
            scope_examples = (
                "• 겉감: 면 100%\n"
                "• 본체: 울 100% (안감·장식 제외)\n"
                "• 면 60%, 폴리에스터 40% 혼방\n"
                "• 천연 소재 사용 (부자재 제외)"
            )
            component_examples = (
                "안감, 충전재, 코팅, 장식과 부자재"
            )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 소재와 함량에 "
            "관한 사실 표현입니다. ‘100%’라는 이유만으로 반드시 "
            "수정해야 하는 것은 아니지만, 표시한 범위가 실제로 "
            f"{material_name} 100%인지 객관적인 자료로 확인할 수 "
            "있어야 합니다.\n\n"
            "제품 전체를 대상으로 한 문구처럼 표시하면 소비자는 "
            "제품의 주요 구성 전체가 해당 소재로 이루어졌다고 "
            "받아들일 수 있습니다. 실제로는 겉감이나 외피만 "
            f"해당하고 {component_examples}에 다른 소재가 사용됐다면 "
            "100%가 적용되는 부분을 구체적으로 밝혀야 합니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 정확한 소재 명칭과 함량\n"
            "• 100%가 적용되는 범위가 제품 전체인지 겉감·외피인지\n"
            f"• {component_examples}의 별도 소재\n"
            "• 제조사 소재 명세서, 거래명세서, 시험성적서 등 확인 자료\n"
            "• 상품정보에 표시한 소재 구성과 광고 문구의 일치 여부\n\n"
            "표시 범위에 맞게 다음처럼 작성할 수 있습니다.\n"
            f"{scope_examples}\n\n"
            f"실제로 표시한 범위가 {material_name} 100%이고 이를 "
            "입증할 수 있다면 100% 표현을 사용할 수 있습니다. "
            "일부 구성에만 해당한다면 제품 전체가 같은 소재인 "
            "것처럼 표시하지 말고 적용 부위와 제외 범위를 함께 "
            "밝혀야 합니다."
        )

    if has_limited_discount_claim:
        discount_rate = f"{discount_rate_match.group(1)}%"
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        if has_all_products_scope:
            concluding_scope = "전 상품이"
            concluding_claim = (
                f"오늘만 전 상품 {discount_rate} 할인"
            )
        else:
            concluding_scope = "광고 대상 상품이"
            concluding_claim = (
                f"오늘만 {discount_rate} 할인"
            )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 실제 할인 기간, "
            "할인율의 기준과 적용 조건이 사실과 일치하는 경우에만 "
            "사용하는 것이 안전합니다.\n\n"
            "‘오늘만’은 해당 할인이 그날 종료되고 이후에는 같은 "
            "조건으로 계속 제공되지 않는다는 의미로 받아들여질 "
            f"수 있습니다. 또한 ‘{discount_rate} 할인’은 정당한 "
            "비교가격을 기준으로 계산한 실제 할인율이어야 합니다. "
            "행사를 다음 날에도 반복하거나 종료 시각 이후까지 "
            "연장하면서 계속 ‘오늘만’이라고 표시하면 소비자에게 "
            "구매를 서두르게 하는 잘못된 긴급성으로 받아들여질 "
            "수 있습니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 행사의 정확한 시작일과 종료일·종료 시각\n"
            "• 할인 대상 상품과 제외 상품의 범위\n"
            "• 할인율을 계산한 기준가격과 실제 판매가격\n"
            "• 쿠폰, 회원 등급, 결제수단 등 추가 적용 조건\n"
            f"• 일부 상품만 {discount_rate}이고 나머지는 할인율이 "
            "다른지 여부\n"
            "• 같은 내용의 ‘오늘만’ 행사를 반복하거나 연장하는지 여부\n\n"
            "조건이 있다면 광고 문구 가까이에 명확하게 표시해야 "
            "합니다. 예를 들면 다음처럼 바꿀 수 있습니다.\n"
            f"• ○월 ○일 23:59까지 행사 대상 상품 {discount_rate} 할인\n"
            f"• 회원 쿠폰 적용 시 대상 상품 {discount_rate} 할인 "
            "(일부 상품 제외)\n"
            f"• 행사 대상 상품 최대 {discount_rate} 할인 "
            "(상품별 할인율 상이)\n\n"
            f"실제로 {concluding_scope} {discount_rate} 할인되고 "
            "행사가 그날 종료된다면 "
            f"‘{concluding_claim}’이라고 표현할 수 있지만, "
            "기준가격이나 기간·대상·적용 조건을 소비자가 오인하지 "
            "않도록 함께 표시해야 합니다."
        )

    if has_unconditional_free_shipping_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 예외조건 없이 "
            "단독으로 사용하려면 실제로 모든 상품에 무료배송이 "
            "적용되어야 합니다. 지역·구매금액·회원 여부 등에 "
            "예외가 있다면 문구 가까이에 그 조건을 명확하게 "
            "표시해야 합니다.\n\n"
            "‘전 상품’은 일부 상품도 제외되지 않는다는 의미로, "
            "‘무료배송’은 소비자가 일반적인 배송비를 부담하지 "
            "않는다는 의미로 받아들여질 수 있습니다. 따라서 "
            "최소 구매금액, 회원 전용 혜택, 특정 상품 제외, "
            "제주·도서산간 추가배송비와 같은 조건이나 예외가 "
            "있는데도 이를 눈에 띄게 알리지 않으면 소비자가 "
            "모든 주문에 배송비가 전혀 없는 것으로 잘못 알 수 "
            "있습니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 무료배송 대상 상품의 범위\n"
            "• 최소 구매금액이나 회원 등 적용 조건\n"
            "• 제주·도서산간 등 지역별 추가배송비\n"
            "• 묶음배송, 설치배송, 예약상품 등 별도 배송 조건\n"
            "• 반품·교환 배송비는 무료배송 혜택과 별개라는 점\n\n"
            "조건이나 예외가 있다면 광고 문구 가까이에 명확하게 "
            "표시하는 것이 안전합니다. 예를 들면 다음과 같이 "
            "바꿀 수 있습니다.\n"
            "• 3만원 이상 구매 시 무료배송\n"
            "• 회원 대상 전 상품 무료배송 "
            "(제주·도서산간 추가비용 별도)\n"
            "• 일부 설치배송 상품을 제외한 전 상품 무료배송\n\n"
            "실제로 모든 상품과 모든 지역에 조건 없이 배송비가 "
            "부과되지 않는 경우에는 ‘전 상품 무료배송’이라고 "
            "표현할 수 있지만, 소비자의 구매 결정에 영향을 줄 "
            "수 있는 예외는 작게 숨기지 말고 함께 표시해야 합니다."
        )

    if has_disparagement_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        if has_quality_disparagement_subject:
            comparison_subject = "품질"
            evaluation_explanation = (
                "‘품질이 형편없습니다’는 어떤 품질 항목을 어떤 "
                "기준으로 평가했는지 밝히지 않은 채 경쟁 상품 "
                "전체가 열등한 것으로 단정하는 표현입니다."
            )
            verification_items = (
                "• 비교 대상 상품의 정확한 명칭, 모델과 규격\n"
                "• 소재 구성, 원단 두께와 혼용률\n"
                "• 봉제 상태, 마감 품질과 내구성 평가 항목\n"
                "• 세탁 후 수축률, 변색·이염 등 시험 결과\n"
                "• 시험 방법, 시험기관, 표본 수와 전체 결과\n"
                "• 불량률이나 품질검사 결과의 산정 기간\n"
                "• 자사에 유리한 결과뿐 아니라 중요한 제한과 예외"
            )
            safer_examples = (
                "• 봉제 마감 상태를 확인할 수 있는 상세 이미지를 "
                "제공합니다.\n"
                "• 원단의 정확한 혼용률과 두께를 표시합니다.\n"
                "• 세탁 시험으로 확인된 수축률을 표시합니다.\n"
                "• 공인시험기관의 시험 결과가 있다면 시험 조건과 "
                "수치를 함께 표시합니다."
            )
        elif has_fit_disparagement_subject:
            comparison_subject = "핏"
            evaluation_explanation = (
                "‘핏이 형편없습니다’는 구체적인 치수나 평가 "
                "기준을 밝히지 않은 채 경쟁 상품의 착용 결과를 "
                "부정적으로 단정하는 표현입니다."
            )
            verification_items = (
                "• 비교 대상 상품의 정확한 명칭, 모델과 규격\n"
                "• 핏을 평가한 구체적인 항목과 측정 기준\n"
                "• 동일한 사이즈와 착용 조건에서 진행한 비교 방법\n"
                "• 시험·조사 주체, 표본 수와 전체 결과\n"
                "• 자사에 유리한 결과뿐 아니라 중요한 제한과 예외"
            )
            safer_examples = (
                "• 상품의 실제 치수와 사이즈별 착용 정보를 "
                "제공합니다.\n"
                "• 여러 체형의 착용 이미지를 함께 제공합니다.\n"
                "• 허리와 힙 라인을 고려한 입체 패턴을 적용했습니다.\n"
                "• 세로 절개선으로 실루엣을 정돈한 디자인입니다."
            )
        else:
            comparison_subject = "상품 특성"
            evaluation_explanation = (
                "‘형편없습니다’와 같은 표현은 구체적인 평가 항목과 "
                "기준을 밝히지 않은 채 경쟁 상품 전체를 부정적으로 "
                "단정하는 표현입니다."
            )
            verification_items = (
                "• 비교 대상 상품의 정확한 명칭, 모델과 규격\n"
                "• 비교한 구체적인 상품 특성과 측정 기준\n"
                "• 동일한 조건에서 진행한 비교 방법\n"
                "• 시험·조사 주체, 표본 수와 전체 결과\n"
                "• 중요한 제한사항과 예외"
            )
            safer_examples = (
                "• 자사 상품의 소재, 구조와 기능을 구체적으로 "
                "설명합니다.\n"
                "• 확인 가능한 시험 결과만 조건과 수치로 "
                "표시합니다.\n"
                "• 경쟁 상품을 낮추기보다 자사 상품의 특징을 "
                "직접 안내합니다."
            )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 다른 사업자의 "
            "상품을 객관적인 근거 없이 낮춰 평가하는 표현으로 "
            "받아들여질 수 있어 수정하는 것이 안전합니다.\n\n"
            "‘다른 쇼핑몰 상품’은 비교 대상의 범위가 지나치게 "
            "넓고 불분명합니다. "
            f"{evaluation_explanation} 객관적인 근거가 없거나 비교 "
            "결과 중 불리한 부분만 강조한다면 소비자가 다른 "
            "사업자의 상품 전체가 열등한 것으로 오인할 수 "
            "있습니다.\n\n"
            f"{comparison_subject}을 비교해 광고하려면 다음 사항을 "
            "명확하게 확인할 수 있어야 합니다.\n"
            f"{verification_items}\n\n"
            "객관적인 비교자료가 있더라도 ‘형편없다’처럼 감정적이고 "
            "모욕적으로 들릴 수 있는 표현보다는 확인된 결과를 "
            "중립적으로 표시하고, 자사 상품의 확인 가능한 특징을 "
            "직접 설명하는 것이 안전합니다.\n"
            f"{safer_examples}\n\n"
            "다른 사업자의 상품을 포괄적으로 낮춰 말하지 말고, "
            "비교가 필요하다면 특정 상품과 객관적인 기준을 "
            "명확히 밝히면서 확인된 사실의 범위 안에서 "
            "표현해야 합니다."
        )

    if has_domestic_sales_rank_claim:
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        rank_match = re.search(
            r"(\d+)\s*위",
            ad_copy,
            flags=re.IGNORECASE,
        )

        rank_label = (
            f"{rank_match.group(1)}위"
            if rank_match is not None
            else "표시된 순위"
        )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 국내 시장에서 "
            f"해당 상품이 판매순위 {rank_label}라는 구체적인 사실 "
            "주장입니다. 따라서 조사 범위, 집계 기간, 판매 채널과 "
            "순위 산정 기준을 객관적인 자료로 확인할 수 있어야 "
            "합니다.\n\n"
            "‘국내 판매 1위’만 표시하면 소비자는 국내 전체 "
            "온·오프라인 시장의 해당 상품군을 대상으로 판매수량 "
            "또는 매출액이 가장 높은 상품이라고 받아들일 수 "
            "있습니다. 실제 근거가 자사몰, 특정 쇼핑몰, 일부 "
            "판매채널이나 짧은 기간의 실적에 한정된다면 그 범위를 "
            "국내 전체 시장의 순위처럼 확대해서 표시해서는 안 "
            "됩니다.\n\n"
            "광고하기 전에 다음 사항을 확인해야 합니다.\n"
            "• 순위를 집계한 시작일과 종료일\n"
            "• 국내 전체 시장인지 특정 온라인·오프라인 채널인지\n"
            "• 비교한 상품 카테고리, 성별, 품목과 가격대의 범위\n"
            "• 판매수량, 주문건수 또는 매출액 중 어떤 지표인지\n"
            "• 비교 대상 브랜드와 상품을 포함한 모집단의 범위\n"
            "• 조사기관, 플랫폼 또는 판매 데이터의 정확한 출처\n"
            "• 순위가 확인된 시점과 해당 자료의 유효기간\n\n"
            "근거 범위에 맞게 다음처럼 구체적으로 표시할 수 "
            "있습니다.\n"
            "• ○년 ○월 자사몰 여성 슬랙스 판매수량 1위 "
            "(자사 판매 데이터 기준)\n"
            "• ○○조사기관 조사 결과, 국내 온라인 여성 슬랙스 "
            "부문 판매수량 1위 "
            "(조사기간·조사대상·산정기준 함께 표시)\n"
            "• 자사 슬랙스 제품 중 ○년 상반기 판매수량 1위\n\n"
            "실제 자료가 특정 기간이나 판매채널에 한정돼 있다면 "
            "그 제한을 문구 가까이에 함께 표시해야 합니다. "
            "객관적인 자료로 국내 전체 시장의 순위를 확인할 수 "
            "없다면 ‘국내 판매 1위’ 대신 제품의 소재, 핏, 누적 "
            "판매수량처럼 확인 가능한 특징을 정확한 범위 안에서 "
            "표시하는 것이 안전합니다."
        )

    if has_comparative_multiplier_claim:
        multiplier = f"{comparative_multiplier_match.group(1)}배"
        topic_particle = get_korean_topic_particle(
            ad_copy
        )

        return (
            f"{copy_label} “{ad_copy}”{topic_particle} 비교 대상과 "
            "객관적인 근거가 명확하지 않다면 수정하는 것이 "
            "안전합니다.\n\n"
            "‘타사 제품보다’라는 표현은 어느 회사의 어떤 제품과 "
            "비교했는지가 명확해야 합니다. 또한 ‘체형 보정 효과가 "
            f"{multiplier}’라는 표현은 무엇을 어떤 방법과 단위로 "
            "측정했을 때 그 차이가 나타났는지 확인할 수 있어야 "
            "합니다. 비교 대상, 평가 항목과 산출 기준이 불분명하면 "
            "모든 타사 제품보다 보정 성능이 우수하고 그 효과가 "
            f"정확히 {multiplier}인 것처럼 소비자가 오인할 수 "
            "있습니다.\n\n"
            "이 표현을 사용하려면 다음 사항을 객관적인 자료로 "
            "확인할 수 있어야 합니다.\n"
            "• 비교한 타사 제품의 정확한 명칭, 모델과 규격\n"
            "• 체형 보정 효과의 구체적인 평가 항목과 측정 단위\n"
            "• 동일한 사이즈·착용자·측정 환경에서 진행한 시험 방법\n"
            "• 시험·조사 주체, 표본 수, 시험 기간과 전체 결과\n"
            f"• ‘{multiplier}’가 계산된 기준값, 비교값과 산출 방식\n"
            "• 일부 시험 결과인지 전체 제품·착용자에 적용되는지 여부\n\n"
            "객관적인 비교 근거가 없다면 다음처럼 실제 디자인 "
            "특징을 설명하는 방식으로 바꾸는 것이 안전합니다.\n"
            "• 신축성 있는 원단과 절개선을 적용한 보정 핏\n"
            "• 허리와 복부 라인을 정돈해 보이도록 설계한 디자인\n"
            "• 착용 시 허리선을 강조하는 입체 패턴 적용\n\n"
            "비교 시험 결과를 광고에 사용할 때에는 실제 값을 "
            "입력해 비교 범위를 명확히 표시해야 합니다.\n"
            f"• 자사 시험 결과, A사 ○○제품 대비 ○○ 평가값이 "
            f"{multiplier}로 측정됨\n"
            "  (시험기관, 시험일, 제품 규격, 시험 방법과 산출 "
            "기준을 함께 표시)\n\n"
            "특정 시험 결과를 전체 타사 제품이나 모든 착용자에게 "
            "일반화해서는 안 됩니다. 확인된 비교 제품, 시험 조건과 "
            "결과 범위 안에서만 표현해야 합니다."
        )

    if has_lifetime_discoloration_claim:
        lifetime_phrase = "사용 기간에 제한이 없는 영구적인 보장"

        if "평생" in normalized_ad_copy:
            lifetime_phrase = (
                "‘평생’이라는 표현은 사용 기간에 제한이 없는 "
                "영구적인 보장"
            )
        elif "영구" in normalized_ad_copy:
            lifetime_phrase = (
                "‘영구’라는 표현은 사용 기간과 환경에 관계없이 "
                "상태가 유지된다는 보장"
            )
        elif "절대" in normalized_ad_copy:
            lifetime_phrase = (
                "‘절대’라는 표현은 어떤 사용 환경에서도 변색이 "
                "발생하지 않는다는 보장"
            )

        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            f"{lifetime_phrase}으로 받아들여질 수 있고, "
            "‘변색되지 않는다’는 표현은 정상적인 착용과 보관 "
            "환경에서도 색상 변화가 전혀 발생하지 않는 품질이 "
            "보장되는 것으로 오인될 수 있습니다. 그러나 "
            "액세서리의 변색 여부와 속도는 금속과 도금 소재, "
            "코팅 방식, 도금 두께, 땀과 물, 향수·화장품, 마찰, "
            "보관 환경과 사용 기간에 따라 달라질 수 있습니다.\n\n"
            "변색 방지 성능을 강조하려면 소재와 표면 처리 방식, "
            "시험 기관, 시험 방법, 시험 조건과 결과를 확인할 수 "
            "있는 객관적인 자료가 필요합니다. 근거를 제시하기 "
            "어렵다면 다음처럼 실제로 확인된 소재나 관리 조건을 "
            "설명하는 방식으로 바꾸는 것이 안전합니다.\n"
            "• 변색을 줄이도록 표면 코팅을 적용한 액세서리\n"
            "• 제품에 사용된 금속과 도금 소재를 구체적으로 표시\n"
            "• 물·땀·향수와의 접촉을 줄이는 관리 방법을 함께 안내\n"
            "• 시험 자료가 있는 경우 시험 조건과 결과를 함께 표시\n\n"
            "수정한 표현도 실제 소재 구성, 도금과 코팅 방식, "
            "시험 결과로 확인할 수 있어야 하며, 모든 사용 "
            "환경에서 평생 변색이 발생하지 않는다고 단정해서는 "
            "안 됩니다."
        )

    if has_pilling_claim:
        absolute_phrase = (
            "‘절대’라는 표현과 "
            if "절대" in normalized_ad_copy
            else ""
        )

        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            f"{absolute_phrase}"
            "‘보풀이 생기지 않는다’는 표현은 정상적인 착용, "
            "마찰과 세탁 조건에서도 보풀이 전혀 발생하지 않는 "
            "품질이 보장되는 것처럼 받아들여질 수 있습니다. "
            "그러나 니트의 보풀 발생 정도는 섬유의 혼용률과 "
            "조직, 착용 중 마찰, 세탁 방법, 건조 방식과 사용 "
            "기간에 따라 달라질 수 있으므로 객관적인 근거 없이 "
            "발생 가능성을 완전히 배제해서는 안 됩니다.\n\n"
            "보풀 방지 성능을 강조하려면 시험 기관, 시험 방법, "
            "시험 조건과 결과를 확인할 수 있는 객관적인 자료가 "
            "필요합니다. 근거를 제시하기 어렵다면 다음처럼 실제로 "
            "확인된 소재나 가공 특성을 설명하는 방식으로 바꾸는 "
            "것이 안전합니다.\n"
            "• 촘촘한 조직으로 제작한 니트 소재\n"
            "• 보풀 발생을 줄이도록 가공한 원단 사용\n"
            "• 시험 자료가 있는 경우 시험 조건과 보풀 등급을 "
            "함께 표시\n\n"
            "수정한 표현도 실제 소재 구성, 가공 방식과 시험 "
            "결과로 확인할 수 있어야 하며, 모든 사용 환경에서 "
            "보풀이 전혀 생기지 않는다고 단정해서는 안 됩니다."
        )

    if has_numeric_length_effect:
        measurement = (
            f"{numeric_length_match.group(1)}"
            f"{numeric_length_match.group(2)}"
        )

        absolute_explanation = ""
        if "무조건" in normalized_ad_copy:
            absolute_explanation = (
                "‘무조건’은 모든 착용자에게 동일한 결과가 "
                "보장되는 것처럼 받아들여질 수 있습니다. "
            )
        elif has_absolute:
            absolute_explanation = (
                "결과를 단정하는 절대 표현은 모든 착용자에게 "
                "동일한 효과가 보장되는 것처럼 받아들여질 수 "
                "있습니다. "
            )

        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            f"{absolute_explanation}"
            f"특히 ‘{measurement} 길어 보인다’처럼 구체적인 "
            "길이 수치를 제시하면 실제 다리 길이가 늘어나거나 "
            "모든 착용자에게 동일한 시각적 효과가 나타나는 것으로 "
            "오인될 수 있습니다. 의류는 신체 비율을 시각적으로 "
            "보완할 수는 있지만 실제 다리 길이를 변화시키지는 "
            "않으며, 보이는 정도도 착용자의 체형, 선택한 사이즈, "
            "상품의 기장과 핏, 신발과 촬영 조건에 따라 달라질 수 "
            "있습니다.\n\n"
            "해당 수치를 사용하려면 측정 대상, 비교 기준, 시험 "
            "방법, 착용 조건과 결과를 뒷받침하는 객관적인 자료가 "
            "필요합니다. 근거를 제시하기 어렵다면 다음처럼 실제 "
            "디자인 특징을 설명하는 방식으로 바꾸는 것이 "
            "안전합니다.\n"
            "• 하이웨이스트 디자인으로 다리가 길어 보이는 "
            "실루엣\n"
            "• 세로 절개선을 적용해 길고 정돈된 느낌을 주는 핏\n"
            "• 발목까지 자연스럽게 이어지는 스트레이트 실루엣\n\n"
            "수정한 표현도 실제 상품의 기장, 재단, 패턴과 착용 "
            "이미지로 확인할 수 있어야 하며, 모든 착용자에게 "
            "동일한 길이 효과가 나타난다고 단정해서는 안 됩니다."
        )

    if has_complete_disappearance_claim:
        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            "‘이 원피스 하나면’이라는 표현은 해당 상품만 "
            "착용하면 결과가 나타나는 것처럼 받아들여질 수 있고, "
            "‘군살이 완전히 사라져’는 모든 착용자에게 군살이 "
            "없어진 것과 같은 완전한 효과가 보장되는 것으로 "
            "오인될 수 있습니다. 의류는 실루엣을 시각적으로 "
            "보완할 수는 있지만 실제 군살을 없애는 것은 아니며, "
            "보이는 정도도 체형, 선택한 사이즈, 상품의 재단과 "
            "착용 방법에 따라 달라질 수 있습니다.\n\n"
            "다음처럼 실제 디자인 특징과 보이는 느낌을 설명하는 "
            "방식으로 바꾸는 것이 안전합니다.\n"
            "• 복부 라인을 자연스럽게 커버하는 디자인\n"
            "• 허리선을 강조해 실루엣을 정돈해 보이게 하는 핏\n"
            "• 드레이핑과 절개선으로 체형을 보완하는 디자인\n\n"
            "수정한 표현도 실제 재단, 소재, 패턴과 착용 이미지로 "
            "확인할 수 있어야 하며, 모든 착용자에게 동일한 효과가 "
            "나타난다고 단정해서는 안 됩니다."
        )

    if (
        has_absolute
        and has_numeric_appearance_effect
    ):
        immediate_explanation = (
            "‘입는 순간’은 착용 즉시 효과가 나타나는 것처럼 "
            "받아들여질 수 있고, "
            if has_immediate_effect
            else ""
        )

        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            f"{immediate_explanation}"
            "‘무조건’은 모든 소비자에게 동일한 결과가 보장되는 "
            "것처럼 받아들여질 수 있습니다. 특히 ‘5kg 빠져 "
            "보인다’처럼 구체적인 수치를 사용하면 실제 체중이 "
            "감소하거나 모든 착용자에게 같은 시각적 효과가 "
            "나타나는 것으로 오인될 수 있습니다.\n\n"
            "이러한 수치 표현을 사용하려면 측정 대상, 시험 방법, "
            "착용 조건과 결과를 뒷받침하는 객관적인 자료가 "
            "필요합니다. 근거를 제시하기 어렵다면 다음처럼 상품의 "
            "디자인 특징을 설명하는 방식으로 바꾸는 것이 "
            "안전합니다.\n"
            "• 슬림한 실루엣을 연출하는 핏\n"
            "• 허리선을 강조한 디자인\n"
            "• 세로 절개선으로 길고 정돈된 느낌을 주는 디자인\n\n"
            "수정한 문구도 실제 상품의 재단, 패턴과 착용 이미지로 "
            "확인할 수 있어야 하며, 모든 사람에게 동일한 결과를 "
            "보장해서는 안 됩니다."
        )

    if has_absolute and has_appearance:
        detected_claims: list[str] = []

        if re.search(
            r"100\s*%",
            ad_copy,
            flags=re.IGNORECASE,
        ):
            detected_claims.append("‘100%’")

        if "완벽" in normalized_ad_copy:
            detected_claims.append("‘완벽한’")

        if "누구나" in normalized_ad_copy:
            detected_claims.append("‘누구나’")

        if "무조건" in normalized_ad_copy:
            detected_claims.append("‘무조건’")

        if "항상" in normalized_ad_copy:
            detected_claims.append("‘항상’")

        if "절대" in normalized_ad_copy:
            detected_claims.append("‘절대’")

        claim_text = (
            "와 ".join(detected_claims)
            if detected_claims
            else "결과를 단정하는 표현"
        )

        if (
            "체형보정" in normalized_ad_copy
            and (
                "100" in normalized_ad_copy
                or "완벽" in normalized_ad_copy
            )
        ):
            return (
                f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
                "안전합니다.\n\n"
                f"{claim_text}이라는 표현은 체형 보정 효과가 "
                "예외 없이 완전하게 나타나는 것처럼 받아들여질 "
                "수 있습니다. 그러나 체형 보정의 정도는 착용자의 "
                "체형, 선택한 사이즈, 상품의 재단과 핏에 따라 "
                "달라질 수 있으므로 객관적인 근거 없이 100% 또는 "
                "완벽한 효과를 보장해서는 안 됩니다.\n\n"
                "다음처럼 실제 상품의 디자인 특징을 설명하는 "
                "방식으로 바꾸는 것이 안전합니다.\n"
                "• 체형을 정돈해 보이도록 설계한 핏\n"
                "• 허리선을 강조한 디자인\n"
                "• 신축성 있는 소재와 절개선을 적용한 보정 핏\n\n"
                "수정한 표현도 실제 재단, 소재, 패턴과 착용 "
                "이미지로 확인할 수 있어야 하며, 모든 착용자에게 "
                "동일한 보정 효과가 나타난다고 단정해서는 안 됩니다."
            )

        return (
            f"{copy_label} “{ad_copy}”는 수정해서 사용하는 것이 "
            "안전합니다.\n\n"
            f"{claim_text}은 모든 소비자에게 동일한 착용 효과가 "
            "보장되는 것처럼 받아들여질 수 있습니다. 착용 결과는 "
            "체형, 선택한 사이즈, 상품의 핏과 착용 방법에 따라 "
            "달라질 수 있으므로 객관적인 근거 없이 결과를 "
            "단정해서는 안 됩니다.\n\n"
            "다음처럼 상품의 객관적인 디자인 특징을 설명하는 "
            "방식으로 바꾸는 것이 좋습니다.\n"
            "• 슬림한 실루엣을 연출하는 핏\n"
            "• 허리선을 강조한 디자인\n"
            "• 세로 절개선으로 길고 정돈된 느낌을 주는 디자인\n\n"
            "수정한 표현도 실제 재단, 패턴과 착용 이미지로 "
            "확인할 수 있어야 하며, 모든 착용자에게 같은 결과가 "
            "나타난다고 보장해서는 안 됩니다."
        )

    if has_absolute and has_effect:
        return (
            f"{copy_label} “{ad_copy}”는 과장광고로 문제될 가능성이 "
            "있어 수정이 필요합니다.\n\n"
            "‘무조건’, ‘누구나’, ‘100%’, ‘즉시’처럼 결과를 "
            "보장하는 표현은 실제 효과가 사람이나 사용 조건에 "
            "따라 달라질 수 있는데도 동일한 결과가 확실한 것처럼 "
            "소비자를 오인시킬 수 있습니다. 객관적으로 확인된 "
            "범위와 적용 조건만 구체적으로 표시해야 합니다."
        )

    if has_superiority:
        return (
            f"{copy_label} “{ad_copy}”는 객관적인 비교 근거가 없다면 "
            "문제될 수 있습니다.\n\n"
            "‘최고’, ‘1위’, ‘유일’, ‘가장’과 같은 최상급·비교 "
            "표현은 비교 대상, 조사 시점, 평가 기준과 객관적인 "
            "자료가 확인되어야 합니다. 근거를 표시할 수 없다면 "
            "상품의 구체적인 특징을 설명하는 표현으로 바꾸는 것이 "
            "안전합니다."
        )

    if has_absolute:
        return (
            f"{copy_label} “{ad_copy}”에는 결과를 단정하는 절대 "
            "표현이 포함되어 있어 수정하는 것이 안전합니다.\n\n"
            "‘무조건’, ‘항상’, ‘절대’, ‘100%’ 같은 표현은 예외가 "
            "없는 사실처럼 받아들여질 수 있으므로, 객관적으로 "
            "입증할 수 없는 경우 거짓·과장 광고로 판단될 위험이 "
            "있습니다. 적용 조건과 확인된 범위를 구체적으로 "
            "표시하세요."
        )

    return (
        f"{copy_label} “{ad_copy}”만으로 곧바로 과장광고라고 "
        "단정하기는 어렵습니다.\n\n"
        "실제 상품의 성능·재질·착용 결과와 문구가 일치하는지, "
        "객관적인 자료로 확인할 수 있는지, 중요한 조건이나 예외를 "
        "빠뜨리지 않았는지, 광고 전체의 인상이 소비자를 잘못 "
        "알게 할 우려가 있는지를 함께 확인해야 합니다. 사실로 "
        "확인할 수 없는 효과나 결과는 단정적으로 표현하지 않는 "
        "것이 안전합니다."
    )


def is_missing_ad_copy_assessment_question(
    question: str,
) -> bool:
    """
    과장광고 여부를 묻지만 실제 검토할 문구가 없는 질문을
    판별합니다.
    """
    normalized = normalize_text(question)

    ad_copy_terms = (
        "광고문구",
        "이광고",
        "이문구",
        "해당광고",
        "광고카피",
        "홍보문구",
        "상세페이지문구",
    )

    assessment_terms = (
        "과장광고",
        "허위광고",
        "거짓광고",
        "문제될",
        "문제가될",
        "위법",
        "불법",
        "괜찮",
        "사용해도",
        "써도",
        "판단",
    )

    return (
        any(term in normalized for term in ad_copy_terms)
        and any(term in normalized for term in assessment_terms)
        and not has_explicit_ad_copy(question)
    )


def build_missing_ad_copy_assessment_answer() -> str:
    """실제 광고 문구가 없는 경우 정확한 입력을 요청합니다."""
    return (
        "판단할 광고 문구가 질문에 포함되어 있지 않아 지금은 "
        "과장광고 여부를 판단하기 어렵습니다. 검토할 문구를 "
        "따옴표로 묶거나 `광고 문구:` 뒤에 그대로 입력해 주세요.\n\n"
        "예: 광고 문구: “이 제품을 사용하면 누구나 즉시 효과를 "
        "볼 수 있습니다.”\n\n"
        "문구를 확인할 때에는 사실과 다른 내용인지, 실제보다 "
        "지나치게 부풀렸는지, 중요한 조건을 숨기거나 축소했는지, "
        "객관적인 근거 없이 효과나 우수성을 단정했는지, 광고의 "
        "전체적인 인상이 소비자를 잘못 알게 할 우려가 있는지를 "
        "기준으로 살펴봐야 합니다."
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
        "이벤트상품",
        "프로모션상품",
        "쿠폰할인상품",
        "쿠폰적용상품",
        "쿠폰사용상품",
        "할인혜택적용상품",
        "할인혜택을적용한상품",
        "할인혜택받은상품",
        "할인혜택을받은상품",
        "쿠폰이나할인혜택",
        "쿠폰또는할인혜택",
        "쿠폰및할인혜택",
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


def is_discounted_product_return_prohibition_ad_copy(
    ad_copy: str,
) -> bool:
    """
    세일·할인 상품뿐 아니라 다음과 같이 할인 표현과 상품 표현이
    떨어져 있는 문구도 판별합니다.

    예:
    - 쿠폰이나 할인 혜택을 적용한 상품은 반품 불가
    - 쿠폰을 사용해 구매한 상품은 환불 불가
    - 할인 혜택을 받은 제품은 교환·환불 불가
    """
    normalized_ad_copy = normalize_text(ad_copy)

    direct_discount_product_terms = (
        "세일상품",
        "할인상품",
        "특가상품",
        "행사상품",
        "이벤트상품",
        "프로모션상품",
        "쿠폰할인상품",
        "쿠폰적용상품",
        "쿠폰사용상품",
        "할인혜택적용상품",
        "할인혜택을적용한상품",
        "할인혜택받은상품",
        "할인혜택을받은상품",
        "재고정리상품",
        "시즌오프상품",
        "아울렛상품",
        "할인가상품",
        "세일제품",
        "할인제품",
    )

    discount_or_benefit_terms = (
        "쿠폰",
        "할인",
        "할인혜택",
        "혜택",
        "세일",
        "특가",
        "프로모션",
        "이벤트",
        "행사",
    )

    application_terms = (
        "적용",
        "적용한",
        "사용",
        "사용한",
        "받은",
        "혜택받",
        "구매",
        "구매한",
        "결제",
        "결제한",
    )

    product_terms = (
        "상품",
        "제품",
        "물품",
        "주문",
        "구매상품",
        "구매제품",
    )

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "구매취소",
        "교환",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "거절",
        "거부",
        "불허",
        "인정하지않",
    )

    has_direct_discount_product = any(
        term in normalized_ad_copy
        for term in direct_discount_product_terms
    )

    has_separated_discount_expression = (
        any(
            term in normalized_ad_copy
            for term in discount_or_benefit_terms
        )
        and any(
            term in normalized_ad_copy
            for term in application_terms
        )
        and any(
            term in normalized_ad_copy
            for term in product_terms
        )
    )

    return (
        (
            has_direct_discount_product
            or has_separated_discount_expression
        )
        and any(
            term in normalized_ad_copy
            for term in return_terms
        )
        and any(
            term in normalized_ad_copy
            for term in prohibition_terms
        )
    )

def is_discounted_product_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    질문에서 실제 반품·환불 문구를 추출한 뒤
    세일·할인 상품의 전면 제한 문구인지 확인합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)

    return (
        ad_copy is not None
        and is_discounted_product_return_prohibition_ad_copy(
            ad_copy
        )
    )


def get_promotional_product_label(
    ad_copy: str,
) -> str:
    """실제 입력에 포함된 할인·판매 유형을 답변에 반영합니다."""
    normalized_ad_copy = normalize_text(ad_copy)

    has_coupon = "쿠폰" in normalized_ad_copy
    has_discount_benefit = (
        "할인혜택" in normalized_ad_copy
        or (
            "할인" in normalized_ad_copy
            and "혜택" in normalized_ad_copy
        )
    )
    has_application = any(
        term in normalized_ad_copy
        for term in (
            "적용",
            "사용",
            "받은",
            "구매",
            "결제",
        )
    )

    if has_coupon and has_discount_benefit:
        return "쿠폰·할인 혜택 적용 상품"

    if has_coupon and has_application:
        return "쿠폰 적용 상품"

    if has_discount_benefit and has_application:
        return "할인 혜택 적용 상품"

    product_type_labels = (
        ("이벤트상품", "이벤트 상품"),
        ("행사상품", "행사 상품"),
        ("프로모션상품", "프로모션 상품"),
        ("쿠폰할인상품", "쿠폰 할인 상품"),
        ("쿠폰적용상품", "쿠폰 적용 상품"),
        ("쿠폰사용상품", "쿠폰 적용 상품"),
        ("할인혜택적용상품", "할인 혜택 적용 상품"),
        ("할인혜택을적용한상품", "할인 혜택 적용 상품"),
        ("할인혜택받은상품", "할인 혜택 적용 상품"),
        ("할인혜택을받은상품", "할인 혜택 적용 상품"),
        ("재고정리상품", "재고 정리 상품"),
        ("시즌오프상품", "시즌오프 상품"),
        ("아울렛상품", "아울렛 상품"),
        ("특가상품", "특가 상품"),
        ("할인가상품", "할인 상품"),
        ("할인상품", "할인 상품"),
        ("세일상품", "세일 상품"),
        ("할인제품", "할인 제품"),
        ("세일제품", "세일 제품"),
    )

    for term, label in product_type_labels:
        if term in normalized_ad_copy:
            return label

    return "할인 혜택 적용 상품"


def build_discounted_product_return_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    쿠폰·할인 혜택 적용 사실만을 이유로 반품·환불을
    전면 제한하는 문구를 직접 검토합니다.
    """
    product_label = get_promotional_product_label(
        ad_copy
    )

    return (
        f"{copy_label} “{ad_copy}”는 {product_label}이라는 이유만으로 "
        "소비자의 청약철회와 환급 권리를 일률적으로 배제하는 "
        "의미이므로 수정해야 합니다.\n\n"
        "쿠폰 사용이나 할인 혜택 적용 사실 자체는 전자상거래법 "
        "제17조에 열거된 독립적인 청약철회 제한 사유가 아닙니다. "
        "법에서 정한 제한 사유가 없다면 할인 적용 여부와 관계없이 "
        "소비자는 원칙적으로 계약내용에 관한 서면을 받은 날부터 "
        "7일 이내에 청약철회할 수 있습니다. 상품 공급이 더 늦은 "
        "경우에는 상품을 공급받거나 공급이 시작된 날부터 7일을 "
        "기준으로 합니다.\n\n"
        "다만 소비자 책임으로 상품이 멸실·훼손됐거나, 사용 또는 "
        "일부 소비로 상품 가치가 현저히 감소한 경우 등 법정 제한 "
        "사유가 실제로 있는지는 별도로 판단해야 합니다. 할인이나 "
        "쿠폰 적용 사실만으로 이러한 제한 사유가 발생하는 것은 "
        "아닙니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "공급된 경우에는 쿠폰이나 할인 혜택을 적용했더라도 상품을 "
        "공급받은 날부터 3개월 이내이면서 그 사실을 안 날 또는 "
        "알 수 있었던 날부터 30일 이내에 청약철회할 수 있습니다. "
        "이 경우 반환 비용은 판매자가 부담합니다.\n\n"
        "단순 변심에 따른 적법한 청약철회의 반환 비용은 소비자가 "
        "부담할 수 있지만, 판매자는 청약철회를 이유로 위약금이나 "
        "손해배상을 별도로 청구할 수 없습니다. 상품이 표시·광고 "
        "또는 계약 내용과 다른 경우의 반환 비용은 판매자가 "
        "부담합니다.\n\n"
        "다음처럼 할인 여부와 실제 반품 사유를 구분해 안내하는 "
        "것이 적절합니다.\n"
        "• 쿠폰 또는 할인 혜택을 적용한 상품도 법정 제한 사유가 "
        "없다면 원칙적인 청약철회 기간이 적용됩니다.\n"
        "• 소비자의 사용·훼손으로 상품 가치가 현저히 감소한 경우 "
        "등 법정 제한 사유가 있으면 단순 변심 반품이 제한될 수 "
        "있습니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "할인 적용 여부와 관계없이 법정 기간 안에 반품할 수 있고 "
        "반환 비용은 판매자가 부담합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 쿠폰이나 할인 혜택 적용만을 이유로 "
        "반품·환불을 전면 금지하는 문구는 사용하지 않는 것이 "
        "안전합니다."
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
    """
    주문제작이라는 명칭만으로 반품 가능 여부를 단정하지 않고,
    현재 검색 근거인 전자상거래법 제17조와 제35조의 범위에서
    안내합니다.
    """
    return (
        "주문제작 상품의 반품 가능 여부는 '주문제작'이라는 "
        "명칭만으로 일률적으로 판단할 수 없습니다.\n\n"
        "전자상거래법 제17조는 소비자가 원칙적으로 계약내용에 "
        "관한 서면을 받은 날부터 7일 이내에 청약철회할 수 "
        "있도록 정하고 있습니다. 상품 공급이 더 늦은 경우에는 "
        "상품을 공급받거나 공급이 시작된 날부터 7일을 "
        "기준으로 합니다.\n\n"
        "다만 소비자 책임으로 상품이 멸실·훼손되었거나, "
        "사용 또는 일부 소비로 상품 가치가 현저히 감소한 경우 "
        "등 법에서 정한 사유가 있으면 청약철회가 제한될 수 "
        "있습니다. 제17조는 그 밖에 대통령령으로 정하는 경우도 "
        "제한 사유로 두고 있으므로, 개별 주문제작 상품의 단순 "
        "변심 반품 가능 여부는 구체적인 제작 방식과 법령상 "
        "제한 요건을 추가로 확인해야 합니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "제작·공급된 경우에는 주문제작 상품이라도 공급받은 "
        "날부터 3개월 이내이면서 그 사실을 안 날 또는 알 수 "
        "있었던 날부터 30일 이내에 청약철회할 수 있습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없습니다. "
        "따라서 상품의 제작 방식과 반품 사유를 구분하지 않고 "
        "'주문제작 상품은 어떤 경우에도 반품·환불 불가'라고 "
        "일률적으로 안내하는 문구는 수정하는 것이 적절합니다."
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
    """확인 목적의 포장 개봉과 법정 제한 사유를 구분해 안내한다."""
    return (
        "상품의 내용이나 상태를 확인하기 위해 포장을 뜯은 "
        "것만으로 쇼핑몰이 반품을 거절할 수는 없습니다. "
        "전자상거래법은 상품 내용을 확인하기 위한 포장 훼손을 "
        "소비자 책임에 따른 훼손의 예외로 두고 있습니다.\n\n"
        "다만 상품을 실제로 사용하거나 일부 소비하여 가치가 "
        "현저히 감소한 경우, 복제가 가능한 상품의 포장을 훼손한 "
        "경우 등 법에서 정한 제한 사유가 실제로 존재하면 "
        "반품이 제한될 수 있습니다."
    )


def extract_return_penalty_percentage(
    question: str,
) -> int | None:
    """
    반품·청약철회를 이유로 상품 가격이나 결제 금액의
    일정 비율을 위약금·수수료로 공제하는 문구에서
    비율을 추출합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "구매취소",
        "계약취소",
        "계약해제",
    )

    penalty_terms = (
        "위약금",
        "손해배상",
        "페널티",
        "패널티",
        "반품수수료",
        "환불수수료",
        "취소수수료",
        "공제",
        "차감",
        "제외",
        "떼고",
        "제하고",
    )

    price_basis_terms = (
        "상품가격",
        "상품금액",
        "상품대금",
        "구매가격",
        "구매금액",
        "결제금액",
        "결제대금",
        "판매가격",
        "판매금액",
        "환불금",
        "환급금",
        "대금",
        "금액",
    )

    if not any(
        term in normalized
        for term in return_terms
    ):
        return None

    if not any(
        term in normalized
        for term in penalty_terms
    ):
        return None

    if not any(
        term in normalized
        for term in price_basis_terms
    ):
        return None

    percentage_match = re.search(
        r"(\d{1,3}(?:\.\d+)?)\s*(?:%|％|퍼센트)",
        target_text,
        flags=re.IGNORECASE,
    )

    if percentage_match is None:
        return None

    percentage_value = float(
        percentage_match.group(1)
    )

    if percentage_value <= 0 or percentage_value > 100:
        return None

    return int(percentage_value)


def is_return_penalty_deduction_notice_question(
    question: str,
) -> bool:
    """
    반품·청약철회 시 상품 가격의 일정 비율을
    위약금·수수료로 일률 공제하는 문구인지 확인합니다.
    """
    return extract_return_penalty_percentage(
        question
    ) is not None


def is_forced_store_credit_refund_notice_question(
    question: str,
) -> bool:
    """
    적법한 환불금을 원래 결제수단 취소나 금전 환급 대신
    쇼핑몰 적립금·포인트 등으로 강제 지급하는 문구를
    판별합니다.

    소비자가 적립금을 자유롭게 선택할 수 있다고 명확히
    안내한 문구와 품절 전용 문구는 이 유형에서 제외합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)

    refund_terms = (
        "환불금",
        "환급금",
        "환불금액",
        "환급액",
        "반품대금",
        "반품금액",
        "환불",
        "환급",
        "대금환급",
        "결제취소",
        "결제대금",
    )

    store_credit_terms = (
        "쇼핑몰적립금",
        "자사적립금",
        "사이트적립금",
        "적립금",
        "쇼핑몰포인트",
        "자사포인트",
        "포인트",
        "마일리지",
        "예치금",
        "쿠폰",
    )

    replacement_terms = (
        "결제취소대신",
        "카드취소대신",
        "원래결제수단대신",
        "기존결제수단대신",
        "현금환급대신",
        "금전환급대신",
        "계좌환급대신",
        "대금환급대신",
        "취소대신",
        "환급대신",
        "현금이아닌",
        "금전이아닌",
        "결제취소없이",
        "카드취소없이",
        "현금환급없이",
        "금전환급없이",
        "취소하지않",
        "취소는하지않",
        "으로만지급",
        "으로만처리",
        "로만지급",
        "로만처리",
        "적립금으로전환",
        "포인트로전환",
        "마일리지로전환",
        "예치금으로전환",
        "적립금으로지급됩니다",
        "포인트로지급됩니다",
        "마일리지로지급됩니다",
        "예치금으로지급됩니다",
    )

    voluntary_choice_terms = (
        "소비자가원하는경우",
        "고객이원하는경우",
        "소비자가선택한경우",
        "고객이선택한경우",
        "소비자선택시",
        "고객선택시",
        "선택할수있",
        "선택가능",
        "선택사항",
        "희망하는경우",
        "요청하는경우",
        "동의한경우",
        "적립금또는결제취소",
        "결제취소또는적립금",
        "적립금또는환불",
        "환불또는적립금",
        "원래결제수단으로환불",
        "원결제수단으로환불",
    )

    stockout_terms = (
        "품절",
        "재고없",
        "재고가없",
        "재고부족",
        "재고소진",
        "공급불가",
        "공급곤란",
        "배송불가",
        "판매종료",
    )

    has_refund = any(
        term in normalized
        for term in refund_terms
    )
    has_store_credit = any(
        term in normalized
        for term in store_credit_terms
    )
    has_forced_replacement = any(
        term in normalized
        for term in replacement_terms
    )
    has_voluntary_choice = any(
        term in normalized
        for term in voluntary_choice_terms
    )
    has_stockout_context = any(
        term in normalized
        for term in stockout_terms
    )

    if has_voluntary_choice:
        return False

    # 품절로 공급하지 못한 상품의 적립금 환불 문구는
    # 기존 stockout_store_credit_only_notice가 처리합니다.
    if has_stockout_context:
        return False

    return (
        has_refund
        and has_store_credit
        and has_forced_replacement
    )


def is_stockout_store_credit_only_notice_question(
    question: str,
) -> bool:
    """
    '품절된 상품은 적립금으로만 환불'처럼 공급하지 못한
    상품의 결제대금을 적립금·포인트로만 처리하는 문구를
    판별합니다.
    """
    normalized = normalize_text(question)

    stockout_terms = (
        "품절",
        "재고없",
        "재고가없",
        "재고부족",
        "재고소진",
        "공급불가",
        "공급곤란",
        "배송불가",
        "판매종료",
    )

    store_credit_only_terms = (
        "적립금으로만",
        "포인트로만",
        "마일리지로만",
        "예치금으로만",
        "적립금만",
        "포인트만",
        "마일리지만",
        "예치금만",
    )

    refund_context_terms = (
        "환불",
        "환급",
        "돌려",
        "지급",
        "보상",
        "처리",
        "전환",
    )

    return (
        any(
            term in normalized
            for term in stockout_terms
        )
        and any(
            term in normalized
            for term in store_credit_only_terms
        )
        and any(
            term in normalized
            for term in refund_context_terms
        )
    )


def extract_excessive_refund_delay_days(
    question: str,
) -> int | None:
    """
    '반품 상품 확인 후 30일 이내 환불'처럼 재화 반환 후
    법정 3영업일보다 긴 환급 기한을 추출합니다.
    """
    normalized = normalize_text(question)

    refund_terms = (
        "환불",
        "환급",
        "대금반환",
        "결제취소",
        "돈을돌려",
    )

    returned_goods_terms = (
        "반품상품",
        "반환상품",
        "상품반품",
        "상품반환",
        "반품한상품",
        "반품물품",
        "반품확인",
        "반품검수",
        "상품확인후",
        "검수후",
        "확인후",
        "반품도착",
        "반품수령",
        "반환받",
        "돌려받",
    )

    deadline_terms = (
        "이내",
        "안에",
        "내에",
        "까지",
        "기간",
        "기한",
        "후",
    )

    if not any(
        term in normalized
        for term in refund_terms
    ):
        return None

    if not any(
        term in normalized
        for term in returned_goods_terms
    ):
        return None

    if not any(
        term in normalized
        for term in deadline_terms
    ):
        return None

    day_match = re.search(
        r"(\d{1,3})\s*(영업일|일)",
        question,
        flags=re.IGNORECASE,
    )

    if day_match is None:
        return None

    days = int(day_match.group(1))
    unit = day_match.group(2)

    # 3영업일을 초과하는 기한은 직접 위반 소지가 있습니다.
    if unit == "영업일" and days > 3:
        return days

    # 일반 일수 4일 이상도 최대 3영업일보다 긴 기한으로
    # 안내될 수 있으므로 전용 검토 대상으로 처리합니다.
    if unit == "일" and days >= 4:
        return days

    return None


def is_excessive_refund_delay_notice_question(
    question: str,
) -> bool:
    """반품 후 환급 기한을 법정 기준보다 늦게 정했는지 확인합니다."""
    return extract_excessive_refund_delay_days(question) is not None


def is_actual_measurement_mismatch_exchange_only_notice_question(
    question: str,
) -> bool:
    """
    실제 상품의 치수와 상세페이지·사이즈표의 치수가 다른
    경우에도 교환만 허용하거나 환불을 금지하는 문구를
    판별합니다.

    지원 예:
    - 실제 치수가 상세페이지와 달라도 교환만 가능
    - 실측 사이즈가 사이즈표와 달라도 환불 불가
    - 배송 상품 치수가 안내 치수와 다르면 동일 상품 교환만 가능
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    actual_measurement_terms = (
        "실제치수",
        "실측치수",
        "실측사이즈",
        "실제사이즈",
        "실물치수",
        "상품치수",
        "제품치수",
        "배송상품치수",
        "받은상품치수",
        "수령상품치수",
        "실측",
    )

    page_measurement_terms = (
        "상세페이지",
        "상품페이지",
        "제품페이지",
        "사이즈표",
        "치수표",
        "표기치수",
        "기재치수",
        "안내치수",
        "표시치수",
        "상세치수",
        "상품정보",
        "제품정보",
    )

    dimension_terms = (
        "치수",
        "사이즈",
        "실측",
        "길이",
        "총장",
        "가슴단면",
        "허리단면",
        "허리둘레",
        "엉덩이둘레",
        "힙둘레",
        "어깨너비",
        "소매길이",
        "밑위",
        "밑단",
        "너비",
        "폭",
    )

    difference_terms = (
        "다른경우",
        "다르더라도",
        "달라도",
        "다르면",
        "차이가있는",
        "차이가나",
        "차이는",
        "오차가있는",
        "오차가나",
        "상이한",
        "일치하지않",
        "불일치",
    )

    exchange_only_terms = (
        "교환만가능",
        "교환만할수",
        "교환만됩니다",
        "교환으로만처리",
        "교환처리만",
        "동일상품으로만교환",
        "동일제품으로만교환",
        "동일모델로만교환",
        "같은상품으로만교환",
        "같은제품으로만교환",
    )

    refund_terms = (
        "환불",
        "환급",
        "반품",
        "청약철회",
        "계약해제",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    allowed_remedy_terms = (
        "교환또는환불",
        "반품또는환불",
        "교환이나환불",
        "반품이나환불",
        "교환만이아니라환불도",
        "환불도가능",
        "반품도가능",
        "교환과환불이가능",
    )

    display_terms = (
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    has_actual_measurement = any(
        term in normalized
        for term in actual_measurement_terms
    )

    has_page_measurement = any(
        term in normalized
        for term in page_measurement_terms
    )

    has_dimension = any(
        term in normalized
        for term in dimension_terms
    )

    has_difference = any(
        term in normalized
        for term in difference_terms
    )

    has_exchange_only = any(
        term in normalized
        for term in exchange_only_terms
    )

    has_refund_prohibition = (
        any(
            term in normalized
            for term in refund_terms
        )
        and any(
            term in normalized
            for term in prohibition_terms
        )
    )

    explicitly_allows_refund = any(
        term in normalized
        for term in allowed_remedy_terms
    )

    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    if explicitly_allows_refund:
        return False

    return (
        has_actual_measurement
        and has_page_measurement
        and has_dimension
        and has_difference
        and (
            has_exchange_only
            or has_refund_prohibition
        )
        and has_notice_context
    )


def is_screen_actual_color_mismatch_refund_prohibition_notice_question(
    question: str,
) -> bool:
    """
    화면·상세페이지에 표시된 색상과 실제 상품 색상이 다른
    경우에도 환불을 금지하는 문구를 판별합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    screen_terms = (
        "화면",
        "화면상",
        "모니터",
        "디스플레이",
        "상세페이지",
        "상품페이지",
        "상품사진",
        "제품사진",
        "사진",
        "이미지",
        "온라인화면",
        "쇼핑몰화면",
    )

    actual_product_terms = (
        "실제상품",
        "실제제품",
        "실물상품",
        "실물제품",
        "실물",
        "배송된상품",
        "배송된제품",
        "받아본상품",
        "받은상품",
        "수령한상품",
    )

    color_terms = (
        "색상",
        "색감",
        "컬러",
        "색깔",
        "색",
    )

    difference_terms = (
        "다른경우",
        "다르더라도",
        "달라도",
        "다르면",
        "차이가있는",
        "차이가나",
        "차이는",
        "색상차이",
        "색감차이",
        "컬러차이",
        "상이한",
        "일치하지않",
        "불일치",
    )

    refund_terms = (
        "환불",
        "환급",
        "반품",
        "청약철회",
        "계약해제",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    display_terms = (
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    has_screen_reference = any(
        term in normalized
        for term in screen_terms
    )
    has_actual_product_reference = any(
        term in normalized
        for term in actual_product_terms
    )
    has_color = any(
        term in normalized
        for term in color_terms
    )
    has_difference = any(
        term in normalized
        for term in difference_terms
    )
    has_refund_topic = any(
        term in normalized
        for term in refund_terms
    )
    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )
    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_screen_reference
        and has_actual_product_reference
        and has_color
        and has_difference
        and has_refund_topic
        and has_prohibition
        and has_notice_context
    )


def is_mismatch_refund_prohibition_notice_question(
    question: str,
) -> bool:
    """
    '상품 설명과 실제 상품이 달라도 환불 불가'처럼
    표시·광고 또는 계약 내용 불일치 시 청약철회·환급을
    배제하는 문구를 판별합니다.
    """
    normalized = normalize_text(question)

    mismatch_terms = (
        "상품설명과실제상품이다르",
        "상품설명과실제상품이달라",
        "상품설명과실물이다르",
        "설명과실제상품이다르",
        "설명과실물이다르",
        "상세페이지와실제상품이다르",
        "상품정보와실제상품이다르",
        "표시광고내용과다르",
        "표시광고와다르",
        "광고내용과다르",
        "계약내용과다르",
        "주문내용과다르",
        "설명과다르",
        "실제상품이다르",
        "실물이다르",
        "다르게배송",
        "다른상품이배송",
    )

    refund_prohibition_terms = (
        "환불불가",
        "환불은불가능",
        "환불이불가능",
        "환불할수없",
        "반품불가",
        "반품은불가능",
        "반품할수없",
        "청약철회불가",
        "교환불가",
        "환불안됨",
        "반품안됨",
        "환불하지않",
        "반품받지않",
    )

    return (
        any(
            term in normalized
            for term in mismatch_terms
        )
        and any(
            term in normalized
            for term in refund_prohibition_terms
        )
    )


def is_defective_exchange_only_refund_prohibition_notice_question(
    question: str,
) -> bool:
    """
    불량·하자 상품을 동일 상품으로만 교환할 수 있게 하고
    환불을 일률적으로 금지하는 문구를 판별합니다.

    지원 예:
    - 불량 상품은 동일 상품으로만 교환할 수 있으며 환불 불가
    - 하자 상품은 같은 제품 교환만 가능하고 반품 불가
    - 불량품은 동일 모델로만 교환되며 환급은 불가능
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    defect_terms = (
        "불량상품",
        "상품불량",
        "제품불량",
        "불량제품",
        "불량품",
        "하자상품",
        "상품하자",
        "제품하자",
        "하자제품",
        "하자가있는",
        "불량이있는",
        "고장난상품",
        "고장난제품",
        "파손상품",
        "파손제품",
        "초기불량",
    )

    exchange_only_terms = (
        "동일상품으로만교환",
        "동일한상품으로만교환",
        "같은상품으로만교환",
        "동일제품으로만교환",
        "동일한제품으로만교환",
        "같은제품으로만교환",
        "동일모델로만교환",
        "같은모델로만교환",
        "동일상품교환만",
        "동일제품교환만",
        "동일모델교환만",
        "교환만가능",
        "교환만할수",
        "교환으로만처리",
        "교환처리만",
        "교환만",
    )

    refund_terms = (
        "환불",
        "환급",
        "반품",
        "청약철회",
        "계약해제",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    display_terms = (
        "상세페이지",
        "상품상세",
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    has_defect = any(
        term in normalized
        for term in defect_terms
    )

    has_exchange_only = any(
        term in normalized
        for term in exchange_only_terms
    )

    has_refund_topic = any(
        term in normalized
        for term in refund_terms
    )

    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )

    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_defect
        and has_exchange_only
        and has_refund_topic
        and has_prohibition
        and has_notice_context
    )


def is_light_color_product_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    흰색·아이보리 등 밝은 색상만을 이유로 반품을
    일률적으로 제한하는 문구를 판별합니다.

    지원 예:
    - 흰색과 아이보리 상품은 오염 여부와 관계없이 반품 불가
    - 화이트 상품은 교환 및 환불이 불가능
    - 밝은 색상 상품은 반품을 받지 않음

    실제 소비자 책임의 오염·훼손이 발생한 경우만을 구체적으로
    제한하는 문구는 이 전용 유형으로 분류하지 않습니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    light_color_terms = (
        "흰색",
        "화이트",
        "아이보리",
        "오프화이트",
        "오프화이트",
        "크림색",
        "크림컬러",
        "밝은색",
        "밝은색상",
        "연한색",
        "연한색상",
        "라이트컬러",
    )

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "교환",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    unconditional_terms = (
        "오염여부와관계없이",
        "오염과관계없이",
        "오염이없어도",
        "오염되지않아도",
        "사용여부와관계없이",
        "상태와관계없이",
        "불량여부와관계없이",
        "하자여부와관계없이",
        "어떠한경우에도",
        "어떤경우에도",
        "무조건",
        "일절",
    )

    actual_damage_condition_terms = (
        "오염된경우",
        "오염이있는경우",
        "오염되면",
        "화장품자국이있는경우",
        "사용흔적이있는경우",
        "세탁한경우",
        "세탁흔적이있는경우",
        "냄새가나는경우",
        "변색된경우",
        "훼손된경우",
    )

    display_terms = (
        "상세페이지",
        "상품상세",
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    has_light_color = any(
        term in normalized
        for term in light_color_terms
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )

    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )

    has_unconditional_scope = any(
        term in normalized
        for term in unconditional_terms
    )

    has_actual_damage_condition = any(
        term in normalized
        for term in actual_damage_condition_terms
    )

    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    # 실제 오염·훼손이 있는 경우만 제한하는 문구는
    # 색상 자체를 이유로 한 일률적 금지로 보지 않습니다.
    if (
        has_actual_damage_condition
        and not has_unconditional_scope
    ):
        return False

    return (
        has_light_color
        and has_return_topic
        and has_prohibition
        and has_notice_context
    )


def is_worn_product_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    착용·시착 사실만을 이유로 반품을 일률적으로 제한하는
    문구를 판별합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    wearing_terms = (
        "한번이라도착용",
        "한번착용",
        "1회라도착용",
        "한차례라도착용",
        "잠깐이라도착용",
        "조금이라도착용",
        "착용한상품",
        "착용한경우",
        "착용후",
        "착용하면",
        "착용시",
        "시착한상품",
        "시착한경우",
        "시착후",
        "시착하면",
        "시착시",
        "입어본상품",
        "입어본경우",
        "입어보면",
        "입어본후",
        "입은상품",
        "입은경우",
        "신어본상품",
        "신어본경우",
        "신어본후",
    )

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "교환",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    display_terms = (
        "상세페이지",
        "상품상세",
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    negated_wearing_terms = (
        "착용하지않",
        "시착하지않",
        "입어보지않",
        "입지않",
        "신어보지않",
    )

    if any(
        term in normalized
        for term in negated_wearing_terms
    ):
        return False

    has_wearing = any(
        term in normalized
        for term in wearing_terms
    )
    has_return_topic = any(
        term in normalized
        for term in return_terms
    )
    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )
    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_wearing
        and has_return_topic
        and has_prohibition
        and has_notice_context
    )


def is_tag_removed_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    택·태그·라벨 제거만을 이유로 반품을 일률적으로
    제한하는 문구를 판별합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    tag_terms = (
        "상품택을제거",
        "상품택제거",
        "택을제거",
        "택제거",
        "택을떼",
        "택떼",
        "태그를제거",
        "태그제거",
        "태그를떼",
        "태그떼",
        "라벨을제거",
        "라벨제거",
        "라벨을떼",
        "라벨떼",
        "가격표를제거",
        "가격표제거",
        "행택을제거",
        "행택제거",
        "종이택을제거",
        "종이택제거",
    )

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "교환",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    display_terms = (
        "상세페이지",
        "상품상세",
        "반품환불문구",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    negated_tag_removal_terms = (
        "택을제거하지않",
        "택제거하지않",
        "태그를제거하지않",
        "태그제거하지않",
        "라벨을제거하지않",
        "라벨제거하지않",
    )

    if any(
        term in normalized
        for term in negated_tag_removal_terms
    ):
        return False

    has_tag_removal = any(
        term in normalized
        for term in tag_terms
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )

    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )

    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_tag_removal
        and has_return_topic
        and has_prohibition
        and has_notice_context
    )


def is_opened_package_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    포장 개봉 사실만을 이유로 반품·환불을 일률적으로
    제한하는 문구를 판별합니다.

    지원 예:
    - 상품 포장을 개봉한 경우 반품 및 환불이 불가능합니다
    - 개봉 후에는 반품할 수 없습니다
    - 봉인을 뜯으면 환불 불가입니다
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    packaging_terms = (
        "상품포장을개봉",
        "포장을개봉",
        "포장개봉",
        "포장을뜯",
        "포장뜯",
        "포장을열",
        "포장열",
        "개봉후",
        "개봉하면",
        "개봉한경우",
        "개봉시",
        "봉인을뜯",
        "봉인훼손",
        "비닐을뜯",
        "박스를열",
        "박스를뜯",
    )

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "교환",
        "구매취소",
    )

    prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    display_terms = (
        "상세페이지",
        "상품상세",
        "문구",
        "약관",
        "공지",
        "안내",
        "기재",
        "표시",
        "적어",
        "써도",
    )

    has_packaging = any(
        term in normalized
        for term in packaging_terms
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )

    has_prohibition = any(
        term in normalized
        for term in prohibition_terms
    )

    has_notice_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_packaging
        and has_return_topic
        and has_prohibition
        and has_notice_context
    )
def extract_short_return_period_details(
    question: str,
) -> tuple[int, str] | None:
    """
    법정 7일보다 짧은 반품·청약철회 기간을 추출합니다.

    반환값:
    - 첫 번째 값: 기간을 시간으로 환산한 값
    - 두 번째 값: 답변에 사용할 실제 입력 단위 표시

    판별 원칙:
    - '반품·환불 문구:' 형식은 '단순 변심'이 없어도 판별
    - 일반 자연어 질문은 기존 단순 변심 문맥이 있어야 판별
    - 1~6일 또는 1~167시간만 짧은 기간으로 판별
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)

    has_return_refund_copy_label = (
        re.search(
            r"(?:"
            r"반품\s*(?:[·ㆍ/]|및|과|와)?\s*환불\s*문구|"
            r"환불\s*(?:[·ㆍ/]|및|과|와)?\s*반품\s*문구"
            r")\s*[:：]",
            question,
            flags=re.IGNORECASE,
        )
        is not None
    )

    has_return_context = any(
        term in normalized
        for term in (
            "반품",
            "청약철회",
            "환불",
            "구매취소",
        )
    )

    has_change_of_mind_context = any(
        term in normalized
        for term in (
            "단순변심",
            "변심",
            "마음이바뀐",
            "사이즈변경",
            "색상변경",
        )
    )

    has_limit_expression = any(
        term in normalized
        for term in (
            "이내에만",
            "이내만",
            "내에만",
            "까지만",
            "기간은",
            "기한은",
            "만가능",
            "가능합니다",
            "가능",
            "제한",
            "지나면",
            "지난후",
            "이후에는",
            "이후반품",
            "초과하면",
            "넘으면",
            "부터불가",
            "반품할수없",
            "환불할수없",
        )
    )

    if not (
        has_return_context
        and has_limit_expression
        and (
            has_return_refund_copy_label
            or has_change_of_mind_context
        )
    ):
        return None

    hour_match = re.search(
        r"(\d{1,3})\s*시간",
        target_text,
        flags=re.IGNORECASE,
    )

    if hour_match is not None:
        hours = int(hour_match.group(1))

        if 1 <= hours < 168:
            return hours, f"{hours}시간"

        return None

    day_match = re.search(
        r"(\d{1,2})\s*일",
        target_text,
        flags=re.IGNORECASE,
    )

    if day_match is None:
        return None

    days = int(day_match.group(1))

    if 1 <= days < 7:
        return days * 24, f"{days}일"

    return None


def extract_short_return_period_days(
    question: str,
) -> int | None:
    """
    기존 호출 호환용 함수입니다.
    시간 단위 기간은 24시간 단위로 올림한 일수로 반환합니다.
    """
    details = extract_short_return_period_details(
        question
    )

    if details is None:
        return None

    hours, _ = details
    return (hours + 23) // 24
def is_short_return_period_notice_question(
    question: str,
) -> bool:
    """반품·청약철회 기간을 7일보다 짧게 제한하는지 확인합니다."""
    return (
        extract_short_return_period_details(question)
        is not None
    )


def is_blanket_return_prohibition_notice_question(
    question: str,
) -> bool:
    """
    상세페이지·약관·반품환불 문구에서 소비자의 반품·환불
    권리를 일률적으로 배제하는 표현을 판별합니다.

    다음과 같은 형태를 모두 지원합니다.
    - 반품 불가
    - 반품 및 환불이 불가능합니다
    - 모든 상품은 구매 후 반품할 수 없습니다
    - 어떠한 경우에도 환불하지 않습니다
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)
    normalized_question = normalize_text(question)

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "교환",
        "구매취소",
        "결제취소",
    )

    direct_prohibition_terms = (
        "반품불가",
        "환불불가",
        "청약철회불가",
        "교환불가",
        "취소불가",
        "반품안됨",
        "환불안됨",
        "반품할수없",
        "환불할수없",
        "교환할수없",
        "청약철회할수없",
        "반품받지않",
        "환불하지않",
        "교환하지않",
    )

    general_prohibition_terms = (
        "불가",
        "불가능",
        "안됩니다",
        "안됨",
        "할수없",
        "받지않",
        "처리하지않",
        "거절",
        "거부",
        "불허",
    )

    blanket_scope_terms = (
        "모든상품",
        "전상품",
        "전체상품",
        "어떠한경우에도",
        "어떤경우에도",
        "사유와관계없이",
        "이유와관계없이",
        "무조건",
        "예외없이",
        "일절",
        "일체",
        "구매후",
    )

    display_terms = (
        "적어",
        "써도",
        "표시",
        "기재",
        "안내",
        "공지",
        "상세페이지",
        "약관",
        "문구",
        "붙여",
        "해도돼",
        "해도되",
        "가능",
        "괜찮",
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )

    has_prohibition = (
        any(
            term in normalized
            for term in direct_prohibition_terms
        )
        or any(
            term in normalized
            for term in general_prohibition_terms
        )
    )

    has_blanket_scope = any(
        term in normalized
        for term in blanket_scope_terms
    )

    has_display_context = (
        ad_copy is not None
        or any(
            term in normalized_question
            for term in display_terms
        )
    )

    return (
        has_return_topic
        and has_prohibition
        and (
            has_blanket_scope
            or has_display_context
        )
    )


def build_return_penalty_deduction_notice_answer(
    ad_copy: str,
    percentage: int,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    적법한 청약철회를 이유로 상품 가격의 일정 비율을
    위약금으로 공제하는 문구를 전자상거래법
    제18조·제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 적법한 청약철회를 이유로 "
        f"상품 가격의 {percentage}%를 일률적인 위약금으로 "
        "공제하는 의미이므로 수정해야 합니다.\n\n"
        "단순 변심에 따른 청약철회의 경우 소비자에게 상품 반환에 "
        "필요한 비용을 부담시킬 수 있습니다. 그러나 판매자는 "
        "소비자의 청약철회를 이유로 위약금이나 손해배상을 "
        "청구할 수 없습니다. 따라서 실제 반품 배송비와 별도로 "
        "상품 가격이나 결제 금액의 일정 비율을 자동 공제해서는 "
        "안 됩니다.\n\n"
        "소비자가 상품을 일부 사용하거나 일부 소비하여 이익을 "
        "얻은 경우에는 법령에서 정한 범위 안에서 그 이익 또는 "
        "공급에 든 비용에 상당하는 금액을 청구할 수 있습니다. "
        "다만 이는 실제 사용·소비 상태와 허용 범위를 확인해 "
        "산정해야 하며, 모든 반품에 동일하게 적용하는 정률 "
        "위약금과는 구분됩니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "공급되어 반품하는 경우에는 반환에 필요한 비용도 "
        "판매자가 부담합니다. 이러한 경우까지 상품 가격의 "
        f"{percentage}%를 위약금으로 공제해서는 안 됩니다.\n\n"
        "다음처럼 반환 비용과 위약금을 구분해 안내하는 것이 "
        "적절합니다.\n"
        "• 단순 변심 반품의 반환 배송비는 소비자가 부담할 수 "
        "있습니다.\n"
        "• 청약철회를 이유로 상품 가격의 일정 비율을 위약금이나 "
        "손해배상 명목으로 공제하지 않습니다.\n"
        "• 일부 사용·소비가 있는 경우에는 실제 상품 상태와 "
        "법령상 허용되는 범위를 확인해 처리합니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우의 "
        "반환 비용은 판매자가 부담합니다.\n"
        "• 공제할 수 있는 비용이 있는 경우 그 사유와 실제 금액을 "
        "소비자에게 구체적으로 안내합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 모든 반품에 상품 가격의 "
        f"{percentage}%를 위약금으로 공제하는 문구는 사용하지 "
        "않는 것이 안전합니다."
    )


def build_forced_store_credit_refund_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    환불금을 결제 취소나 금전 환급 대신 적립금으로
    강제 지급하는 문구를 전자상거래법 제18조·제35조
    기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 소비자의 선택 없이 법정 "
        "환급 방식을 쇼핑몰에서만 사용할 수 있는 적립금으로 "
        "제한하는 의미이므로 수정해야 합니다.\n\n"
        "적법한 청약철회가 이루어져 상품이 반환되면 판매자는 "
        "원칙적으로 상품을 반환받은 날부터 3영업일 이내에 이미 "
        "지급받은 대금을 환급해야 합니다. 신용카드나 그 밖의 "
        "결제수단으로 결제한 경우에는 결제업자에게 대금 청구 "
        "정지나 결제 취소를 지체 없이 요청해야 합니다.\n\n"
        "따라서 판매자가 원래 결제수단의 취소나 금전 환급 절차를 "
        "진행하지 않고 환불금을 자사 쇼핑몰에서만 사용할 수 있는 "
        "적립금·포인트·마일리지·예치금으로 일방적으로 전환해서는 "
        "안 됩니다. 프로모션으로 제공되는 구매 적립금과 이미 "
        "지급한 상품 대금의 환급은 서로 구분해야 합니다.\n\n"
        "소비자가 원래 결제수단 취소 또는 금전 환급 대신 "
        "적립금 지급을 자유롭게 선택하고, 사용처·사용기한 등 "
        "중요 조건을 확인한 경우에는 적립금을 선택 가능한 대체 "
        "수단으로 안내할 수 있습니다. 다만 적립금을 유일한 환급 "
        "방식으로 강제하거나 적립금 선택을 이유로 환급액과 법정 "
        "권리를 불리하게 줄여서는 안 됩니다.\n\n"
        "다음처럼 원래 결제수단 환급과 소비자의 선택사항을 "
        "구분해 안내하는 것이 적절합니다.\n"
        "• 적법한 반품의 환불금은 원래 결제수단 취소 또는 금전 "
        "환급 방식으로 처리합니다.\n"
        "• 카드 결제는 결제업자에게 청구 정지나 결제 취소를 "
        "지체 없이 요청합니다.\n"
        "• 쇼핑몰 적립금은 소비자가 명확하게 선택한 경우에만 "
        "대체 환급 수단으로 제공합니다.\n"
        "• 적립금의 사용처·사용기한 등 중요한 조건을 선택 전에 "
        "명확하게 안내합니다.\n"
        "• 적립금 선택 여부에 따라 환불 금액이나 소비자의 법정 "
        "권리를 불리하게 제한하지 않습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 결제 취소나 금전 환급을 배제하고 "
        "적립금 지급만을 강제하는 문구는 사용하지 않는 것이 "
        "안전합니다."
    )


def build_stockout_store_credit_only_notice_answer(
    ad_copy: str,
    copy_label: str = "상세페이지 문구",
) -> str:
    """품절 상품의 결제대금을 적립금으로만 처리하는 문구를 검토합니다."""
    return (
        f"{copy_label} “{ad_copy}”는 품절로 공급하지 못한 상품의 "
        "결제대금을 적립금으로만 돌려주도록 정하고 있어 "
        "수정해야 합니다.\n\n"
        "통신판매업자는 주문받은 상품을 공급하기 곤란하다는 "
        "사실을 알게 되면 그 사유를 소비자에게 지체 없이 "
        "알려야 합니다. 소비자가 상품을 받기 전에 대금을 미리 "
        "결제한 선지급식 통신판매라면, 대금을 지급한 날부터 "
        "3영업일 이내에 환급하거나 환급에 필요한 조치를 해야 "
        "합니다.\n\n"
        "법에서 요구하는 대금 환급 또는 환급에 필요한 조치를 "
        "적립금이나 포인트 지급만으로 갈음해서는 안 됩니다. "
        "따라서 적립금 지급만을 유일한 처리 방식으로 정하지 말고, "
        "대금 환급이나 결제 취소 등 법정 환급 절차를 진행해야 "
        "합니다.\n\n"
        "다음처럼 수정하는 것이 안전합니다.\n"
        "• 품절 등으로 상품을 공급하기 어려운 경우 그 사유를 "
        "소비자에게 지체 없이 안내합니다.\n"
        "• 선결제된 대금은 결제일부터 3영업일 이내에 환급하거나 "
        "결제 취소 등 환급에 필요한 조치를 합니다.\n"
        "• 적립금이나 포인트 지급만을 유일한 환급 방식으로 "
        "정하지 않습니다.\n"
        "• 적립금 등을 안내하더라도 법정 대금 환급 또는 결제 "
        "취소 절차를 대체하지 않습니다.\n\n"
        "따라서 ‘품절된 상품은 적립금으로만 환불됩니다’라는 "
        "문구 대신, 품절 사실의 즉시 안내와 법정 환급 기한 및 "
        "환급 방법을 구체적으로 표시해야 합니다."
    )


def build_excessive_refund_delay_notice_answer(
    ad_copy: str,
    days: int,
    copy_label: str = "상세페이지 문구",
) -> str:
    """법정 환급 기한보다 긴 상세페이지 문구를 검토합니다."""
    return (
        f"{copy_label} “{ad_copy}”는 반품 상품의 환급 기한을 "
        f"{days}일로 정하고 있어 수정해야 합니다.\n\n"
        "재화를 반품한 경우 통신판매업자는 반품 상품을 "
        "반환받은 날부터 3영업일 이내에 이미 지급받은 대금을 "
        "환급해야 합니다. 환급 기산점은 판매자의 내부 검수나 "
        "확인이 끝난 날이 아니라, 반품 상품을 실제로 반환받은 "
        "날입니다. 따라서 ‘확인 후 30일 이내’처럼 내부 확인 "
        "시점부터 장기간을 새로 계산하는 문구는 법정 환급 기한보다 "
        "소비자에게 불리합니다.\n\n"
        "상품 훼손이나 사용 여부를 확인할 필요가 있더라도 판매자는 "
        "법정 기간 안에서 필요한 확인과 환급 절차를 진행해야 "
        "합니다. 정당한 사유 없이 환급을 늦추면 지연 기간에 대한 "
        "지연배상금도 지급해야 할 수 있습니다.\n\n"
        "다음처럼 수정하는 것이 안전합니다.\n"
        "• 반품 상품을 반환받은 날부터 3영업일 이내에 대금을 "
        "환급합니다.\n"
        "• 신용카드 등으로 결제한 경우에는 결제업자에게 청구 정지 "
        "또는 결제 취소를 지체 없이 요청합니다.\n"
        "• 상품 상태 확인이 필요한 경우에도 법정 환급 기한 안에서 "
        "확인과 환급 절차를 진행합니다.\n"
        "• 환급이 지연되는 경우에는 관계 법령에 따른 "
        "지연배상금이 발생할 수 있습니다.\n\n"
        "전자상거래법 제18조의 환급 기한을 소비자에게 불리하게 "
        "늘린 약정은 효력이 인정되기 어려우므로, ‘반품 상품 확인 "
        "후 30일 이내 환불’이라는 문구를 사용해서는 안 됩니다."
    )


def build_actual_measurement_mismatch_exchange_only_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    실제 치수와 상세페이지 치수가 다른 경우에도 교환만
    허용하거나 환불을 금지하는 문구를 전자상거래법
    제17조·제18조·제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 실제 상품과 상세페이지의 "
        "치수 차이 정도, 측정 기준 및 표시·광고 또는 계약 "
        "내용과 다른 공급인지 여부를 확인하지 않고 교환만을 "
        "허용하면서 환불을 배제하므로 수정해야 합니다.\n\n"
        "실제 상품의 치수가 상세페이지나 사이즈표에 안내된 "
        "치수와 명확히 다르고, 그 차이가 상품 선택이나 착용에 "
        "영향을 줄 정도라면 표시·광고 또는 계약 내용과 다르게 "
        "공급된 경우에 해당할 수 있습니다. 이 경우 소비자는 "
        "상품을 공급받은 날부터 3개월 이내이면서, 그 사실을 안 "
        "날 또는 알 수 있었던 날부터 30일 이내에 청약철회할 수 "
        "있습니다. 판매자가 교환만을 유일한 처리 방법으로 "
        "강제하면서 환불을 전면 배제할 수는 없습니다.\n\n"
        "다만 상세페이지 수치와 조금 다르다는 이유만으로 언제나 "
        "계약 내용과 다른 공급이라고 단정할 수는 없습니다. "
        "측정 위치와 방법, 측정 도구, 소재의 신축성, 측정 당시 "
        "상품 상태 및 생산 과정에서 발생할 수 있는 합리적인 "
        "오차인지, 상품 선택에 영향을 줄 정도로 명확한 차이인지 "
        "상세페이지의 측정 기준과 실제 상품을 비교해 구체적으로 "
        "판단해야 합니다.\n\n"
        "적법한 청약철회가 이루어지면 판매자는 원칙적으로 반환된 "
        "상품을 받은 날부터 3영업일 이내에 대금을 환급해야 "
        "합니다. 실제 치수가 표시·광고 또는 계약 내용과 다른 "
        "경우에는 반품에 필요한 비용도 판매자가 부담합니다.\n\n"
        "다음처럼 경미한 측정 오차와 계약 내용과 다른 명확한 "
        "치수 차이를 구분해 안내하는 것이 적절합니다.\n"
        "• 실제 치수 차이는 상세페이지에 고지한 측정 위치와 "
        "방법을 기준으로 확인합니다.\n"
        "• 상품 선택이나 착용에 영향을 줄 정도로 치수가 명확히 "
        "다른 경우에는 법정 기준에 따라 반품·환불합니다.\n"
        "• 소재의 신축성, 측정 방법과 생산 과정에 따른 경미한 "
        "오차는 차이의 정도를 구체적으로 확인해 판단합니다.\n"
        "• 표시·광고 또는 계약 내용과 다른 상품의 반환 비용은 "
        "판매자가 부담합니다.\n"
        "• 교환만을 유일한 처리 방법으로 강제하지 않고 법정 "
        "청약철회 요건을 충족하면 환불 절차를 안내합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 치수 차이의 정도와 계약 불일치 "
        "여부를 확인하지 않고 교환만 허용하며 환불을 배제하는 "
        "문구는 사용하지 않는 것이 안전합니다."
    )


def build_screen_actual_color_mismatch_refund_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    화면에 표시된 색상과 실제 상품 색상이 다른 경우에도
    환불을 금지하는 문구를 전자상거래법
    제17조·제18조·제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 화면에 표시된 색상과 실제 "
        "배송된 상품 색상의 차이 정도 및 표시·광고 또는 계약 "
        "내용과 다른 공급인지 여부를 확인하지 않고 환불을 "
        "일률적으로 배제하므로 수정해야 합니다.\n\n"
        "실제 상품의 색상이 상세페이지에 표시된 색상이나 "
        "소비자가 주문한 색상과 명확히 다르다면, 표시·광고 또는 "
        "계약 내용과 다르게 공급된 경우에 해당할 수 있습니다. "
        "이 경우 소비자는 상품을 공급받은 날부터 3개월 "
        "이내이면서, 그 사실을 안 날 또는 알 수 있었던 날부터 "
        "30일 이내에 청약철회할 수 있습니다.\n\n"
        "다만 화면과 실제 상품의 색상이 조금 다르게 보인다는 "
        "사실만으로 언제나 계약 내용과 다른 공급이라고 단정할 "
        "수는 없습니다. 촬영 당시 조명과 카메라 설정, 사용자의 "
        "모니터·휴대전화 화면 설정, 상품 생산 과정에서 발생할 "
        "수 있는 경미한 색상 차이인지, 상품 선택에 영향을 줄 "
        "정도로 명확한 차이인지를 상세페이지, 주문 정보와 실제 "
        "상품을 비교해 구체적으로 판단해야 합니다.\n\n"
        "적법한 청약철회가 이루어지면 판매자는 원칙적으로 반환된 "
        "상품을 받은 날부터 3영업일 이내에 대금을 환급해야 "
        "합니다. 실제 상품이 표시·광고 또는 계약 내용과 다른 "
        "경우에는 반품에 필요한 비용도 판매자가 부담합니다.\n\n"
        "다음처럼 화면 환경에 따른 경미한 차이와 계약 내용과 "
        "다른 명확한 색상 차이를 구분해 안내하는 것이 "
        "적절합니다.\n"
        "• 화면과 실제 상품의 색상 차이는 상세페이지, 주문 정보와 "
        "실제 상품을 비교해 구체적으로 확인합니다.\n"
        "• 표시된 색상이나 주문한 색상과 명확히 다른 상품이 "
        "배송된 경우에는 법정 기준에 따라 반품·환불합니다.\n"
        "• 촬영 조명이나 화면 설정에 따른 경미한 차이는 색상 "
        "차이의 정도와 상품 정보에 미친 영향을 확인해 판단합니다.\n"
        "• 표시·광고 또는 계약 내용과 다른 상품의 반환 비용은 "
        "판매자가 부담합니다.\n"
        "• 색상 차이 여부에 다툼이 있는 경우 상품 사진, "
        "상세페이지와 주문 내역 등 확인 자료를 기준으로 "
        "판단합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 색상 차이의 정도와 계약 불일치 "
        "여부를 확인하지 않고 환불을 전면 금지하는 문구는 "
        "사용하지 않는 것이 안전합니다."
    )


def build_mismatch_refund_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "상세페이지 문구",
) -> str:
    """
    상품 설명과 실제 상품이 다른 경우의 반품·환불 권리를
    배제하는 문구를 구체적으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 표시·광고 또는 계약 내용과 "
        "다른 상품이 제공된 경우의 법정 청약철회·환급 권리를 "
        "배제하고 있어 수정해야 합니다.\n\n"
        "상품의 내용이 상세페이지의 설명·광고와 다르거나 "
        "계약 내용과 다르게 이행된 경우에는 단순 변심과 구분되는 "
        "법정 청약철회 사유에 해당합니다. 소비자는 상품을 "
        "공급받은 날부터 3개월 이내이면서, 그 사실을 안 날 또는 "
        "알 수 있었던 날부터 30일 이내에 청약철회할 수 있습니다. "
        "판매자가 상세페이지에 ‘환불 불가’라고 적었다는 이유만으로 "
        "이 권리를 없앨 수는 없습니다.\n\n"
        "적법한 청약철회가 이루어지면 소비자는 상품을 반환할 수 "
        "있고, 판매자는 반환된 상품을 받은 날부터 3영업일 이내에 "
        "이미 지급받은 대금을 환급해야 합니다. 상품이 표시·광고 "
        "또는 계약 내용과 달라 청약철회하는 경우에는 반환에 필요한 "
        "비용도 판매자가 부담해야 합니다.\n\n"
        "상품 상태나 오배송 여부에 다툼이 있다면 실제 상품, "
        "상세페이지의 표시 내용, 주문 내역과 배송 당시 상태를 "
        "확인해 판단해야 합니다. 소비자의 책임으로 상품이 별도로 "
        "훼손된 사정이 있더라도, 설명과 다른 상품에 관한 법정 "
        "권리를 ‘어떤 경우에도 환불 불가’라고 일률적으로 "
        "배제해서는 안 됩니다.\n\n"
        "다음처럼 수정하는 것이 안전합니다.\n"
        "• 상품이 표시·광고 또는 계약 내용과 다른 경우에는 "
        "전자상거래법에 따라 반품·환불이 가능합니다.\n"
        "• 해당 사실을 확인할 수 있는 상품 사진과 주문 정보를 "
        "고객센터에 제출해 주세요.\n"
        "• 반품 가능 기간과 환급 절차는 전자상거래법상 기준에 "
        "따라 안내합니다.\n"
        "• 설명과 다른 상품의 반품에 필요한 비용은 판매자가 "
        "부담합니다.\n\n"
        "상품 설명과 실제 상품이 다른 경우까지 환불을 전면 "
        "배제하는 문구는 사용하지 말고, 법정 청약철회 기간과 "
        "환급 절차를 구체적으로 안내해야 합니다."
    )


def build_defective_exchange_only_refund_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    불량 상품을 동일 상품으로만 교환하도록 제한하고 환불을
    금지하는 문구를 전자상거래법 제17조·제18조·제35조
    기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 하자의 종류와 정도, "
        "수리·교환 가능 여부 및 전자상거래법상 청약철회 요건을 "
        "구분하지 않고 동일 상품 교환만을 강제하면서 환불을 "
        "일률적으로 배제하므로 수정해야 합니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "공급된 경우에는 상품을 공급받은 날부터 3개월 이내이면서, "
        "그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 "
        "청약철회할 수 있습니다. 이 요건을 충족하는 경우 판매자가 "
        "동일 상품 교환만을 유일한 처리 방법으로 정하고 환불을 "
        "전면적으로 거절할 수는 없습니다.\n\n"
        "적법한 청약철회로 상품이 반환되면 판매자는 원칙적으로 "
        "상품을 반환받은 날부터 3영업일 이내에 대금을 환급해야 "
        "합니다. 상품이 표시·광고 또는 계약 내용과 다르게 공급된 "
        "경우의 반환 비용도 판매자가 부담합니다.\n\n"
        "다만 모든 불량 상품에 소비자가 언제나 즉시 환불만을 "
        "선택할 수 있다고 단정해서도 안 됩니다. 상품의 종류, "
        "하자의 내용과 정도, 수리 가능 여부 및 별도로 적용되는 "
        "분쟁해결기준에 따라 수리나 교환 절차가 우선 적용될 수 "
        "있습니다. 따라서 구체적인 처리 방법은 해당 상품과 하자 "
        "상태를 확인해 판단해야 합니다.\n\n"
        "특히 수리나 정상 상품으로의 교환이 불가능하거나, "
        "교환받은 상품에도 하자가 다시 발생하거나, 전자상거래법상 "
        "청약철회 요건을 충족하는 경우까지 환불을 일률적으로 "
        "배제해서는 안 됩니다.\n\n"
        "다음처럼 하자 상태와 적용 기준을 구분해 안내하는 것이 "
        "적절합니다.\n"
        "• 불량 상품은 하자의 종류와 정도를 확인해 수리·교환·환급 "
        "기준에 따라 처리합니다.\n"
        "• 동일 상품 교환만을 모든 불량 상품의 유일한 처리 "
        "방법으로 강제하지 않습니다.\n"
        "• 전자상거래법상 청약철회 요건을 충족하는 경우에는 "
        "환불을 일률적으로 제한하지 않습니다.\n"
        "• 수리·교환이 불가능하거나 교환 상품에도 하자가 있는 "
        "경우에는 적용 가능한 환급 기준을 안내합니다.\n"
        "• 상품 불량이나 계약 내용과 다른 공급에 따른 반환 비용은 "
        "판매자가 부담합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 불량 상품의 동일 상품 교환만을 "
        "강제하고 환불을 전면적으로 금지하는 문구는 사용하지 않는 "
        "것이 안전합니다."
    )


def build_light_color_product_return_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    흰색·아이보리 등 밝은 색상을 이유로 반품을 제한하는
    문구를 전자상거래법 제17조와 제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 상품의 색상만을 기준으로 "
        "실제 오염·훼손 및 가치 감소 여부를 확인하지 않고 "
        "반품을 일률적으로 제한하는 의미이므로 수정해야 합니다.\n\n"
        "흰색이나 아이보리 상품이라는 사실 자체는 법정 "
        "청약철회 제한 사유가 아닙니다. 따라서 오염이나 사용 "
        "흔적이 없고 상품 가치도 현저히 감소하지 않았다면, "
        "밝은 색상이라는 이유만으로 단순 변심 반품을 자동으로 "
        "거절해서는 안 됩니다.\n\n"
        "다만 소비자의 착용·사용으로 오염, 화장품 자국, 냄새, "
        "세탁 흔적, 변색 또는 훼손 등이 발생하여 재판매가 "
        "곤란할 정도로 상품 가치가 현저히 감소한 경우에는 "
        "소비자 책임에 따른 훼손 또는 사용으로 인한 가치 감소에 "
        "해당하여 단순 변심 청약철회가 제한될 수 있습니다. "
        "반품 가능 여부는 색상이 아니라 실제 상품 상태와 가치 "
        "감소 정도를 기준으로 판단해야 합니다.\n\n"
        "특히 상품이 불량이거나 주문한 색상과 다르게 배송됐거나, "
        "표시·광고 또는 계약 내용과 다르게 공급된 경우에는 "
        "상품을 공급받은 날부터 3개월 이내이면서 그 사실을 안 "
        "날 또는 알 수 있었던 날부터 30일 이내에 청약철회할 수 "
        "있습니다. ‘오염 여부와 관계없이’처럼 색상만으로 이러한 "
        "법정 권리까지 배제할 수는 없습니다.\n\n"
        "다음처럼 색상과 실제 상품 상태를 구분해 안내하는 것이 "
        "적절합니다.\n"
        "• 흰색·아이보리 상품도 법정 청약철회 기준에 따라 "
        "처리합니다.\n"
        "• 소비자 책임의 오염·훼손으로 상품 가치가 현저히 "
        "감소한 경우에는 단순 변심 반품이 제한될 수 있습니다.\n"
        "• 색상만으로 반품을 자동 제한하지 않고 오염, 사용 흔적, "
        "훼손 및 가치 감소 여부를 확인합니다.\n"
        "• 상품 불량, 색상 오배송 또는 표시·광고나 계약 내용과 "
        "다른 경우에는 색상만을 이유로 법정 청약철회권을 "
        "배제하지 않습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 밝은 색상이라는 이유만으로 모든 "
        "반품을 일률적으로 배제하는 문구는 사용하지 않는 것이 "
        "안전합니다."
    )


def build_worn_product_return_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    착용·시착을 이유로 반품을 제한하는 문구를
    전자상거래법 제17조와 제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 착용 목적과 정도, "
        "착용으로 인한 상품 상태 및 가치 감소 여부를 구분하지 "
        "않고 반품을 일률적으로 제한하는 의미이므로 수정해야 "
        "합니다.\n\n"
        "사이즈, 핏 또는 착용감을 확인하기 위해 짧게 시착했다는 "
        "사실만으로 언제나 상품 가치가 현저히 감소했다고 단정할 "
        "수는 없습니다. 따라서 ‘한 번이라도’처럼 착용 횟수만을 "
        "기준으로 단순 변심 반품을 자동으로 거절해서는 안 됩니다.\n\n"
        "다만 외출이나 장시간 착용으로 오염, 냄새, 화장품 자국, "
        "주름, 늘어남 또는 형태 변형 등이 발생하여 재판매가 "
        "곤란할 정도로 상품 가치가 현저히 감소한 경우에는 "
        "소비자의 사용으로 인한 가치 감소에 해당하여 단순 변심 "
        "청약철회가 제한될 수 있습니다. 반품 가능 여부는 착용 "
        "횟수보다 실제 사용 정도와 상품 상태를 기준으로 판단해야 "
        "합니다.\n\n"
        "특히 상품이 불량이거나 표시·광고 또는 계약 내용과 "
        "다르게 공급된 경우에는 상품을 공급받은 날부터 3개월 "
        "이내이면서, 그 사실을 안 날 또는 알 수 있었던 날부터 "
        "30일 이내에 청약철회할 수 있습니다. 착용 사실만으로 "
        "이러한 법정 권리까지 일률적으로 배제할 수는 없습니다.\n\n"
        "다음처럼 시착과 실제 사용을 구분해 안내하는 것이 "
        "적절합니다.\n"
        "• 사이즈와 착용감 확인을 위한 짧은 시착만으로 반품을 "
        "자동 제한하지 않습니다.\n"
        "• 외출·장시간 착용으로 오염, 냄새, 주름, 늘어남 또는 "
        "변형 등이 발생하여 상품 가치가 현저히 감소한 경우에는 "
        "단순 변심 반품이 제한될 수 있습니다.\n"
        "• 반품 가능 여부는 착용 횟수만이 아니라 실제 사용 정도와 "
        "상품 상태 및 가치 감소 여부를 확인해 판단합니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "착용 사실만을 이유로 법정 청약철회권을 배제하지 않습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 한 번의 착용만으로 모든 반품을 "
        "일률적으로 배제하는 문구는 사용하지 않는 것이 안전합니다."
    )


def build_tag_removed_return_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    택·태그·라벨 제거를 이유로 반품을 제한하는 문구를
    전자상거래법 제17조와 제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 택 제거가 상품 상태와 "
        "재판매 가치에 실제로 미친 영향 및 반품 사유를 구분하지 "
        "않고 반품을 일률적으로 제한하는 의미이므로 수정해야 "
        "합니다.\n\n"
        "택을 제거했다는 사실만으로 언제나 상품이 훼손됐거나 "
        "가치가 현저히 감소했다고 단정할 수는 없습니다. 단순 "
        "변심 반품의 경우에도 상품 종류, 택의 기능과 부착 상태, "
        "제거 과정에서 발생한 훼손, 실제 사용 여부 및 재판매 "
        "가치 감소 정도를 구체적으로 확인해야 합니다.\n\n"
        "다만 택 제거로 상품이 훼손됐거나 재판매가 곤란할 "
        "정도로 가치가 현저히 감소한 경우에는 소비자 책임에 "
        "따른 훼손 또는 가치 감소로 보아 단순 변심 청약철회가 "
        "제한될 수 있습니다. 따라서 택 제거가 반품 가능 여부에 "
        "아무런 영향이 없다고 일률적으로 안내하는 것도 적절하지 "
        "않습니다.\n\n"
        "특히 상품이 불량이거나 표시·광고 또는 계약 내용과 "
        "다르게 공급된 경우에는 상품을 공급받은 날부터 3개월 "
        "이내이면서, 그 사실을 안 날 또는 알 수 있었던 날부터 "
        "30일 이내에 청약철회할 수 있습니다. ‘불량 여부와 "
        "관계없이’처럼 택 제거만으로 이러한 법정 권리까지 "
        "배제하는 문구는 사용할 수 없습니다.\n\n"
        "따라서 택 제거 여부만으로 반품을 자동 거절하지 말고, "
        "다음처럼 반품 사유와 실제 상품 상태를 구분해 안내하는 "
        "것이 적절합니다.\n"
        "• 택 제거로 상품이 훼손되거나 재판매가 곤란할 정도로 "
        "가치가 현저히 감소한 경우에는 단순 변심 반품이 제한될 "
        "수 있습니다.\n"
        "• 택 제거 여부만으로 반품을 자동 제한하지 않고 상품의 "
        "종류, 사용 여부, 훼손 및 가치 감소 정도를 확인합니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "택 제거만을 이유로 법정 청약철회권을 배제하지 않습니다.\n"
        "• 제한 사유와 적용 기준을 소비자가 쉽게 알 수 있도록 "
        "상품별로 구체적으로 안내합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 택 제거만으로 불량·계약 불일치까지 "
        "포함한 모든 반품을 일률적으로 배제하는 문구는 사용하지 "
        "않는 것이 안전합니다."
    )


def build_opened_package_return_prohibition_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    포장 개봉만을 이유로 반품·환불을 제한하는 문구를
    전자상거래법 제17조와 제35조 기준으로 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 포장을 개봉한 목적과 "
        "상품 상태를 구분하지 않고 반품과 환불을 일률적으로 "
        "제한하는 의미이므로 수정해야 합니다.\n\n"
        "전자상거래법상 소비자의 책임으로 상품이 멸실되거나 "
        "훼손된 경우에는 청약철회가 제한될 수 있습니다. 그러나 "
        "상품의 내용이나 상태를 확인하기 위해 포장 등을 훼손한 "
        "경우는 그 제한 사유에서 제외됩니다. 따라서 상품 확인을 "
        "위한 단순한 포장 개봉만으로 반품과 환불을 거절할 수는 "
        "없습니다.\n\n"
        "다만 포장을 연 뒤 상품을 실제로 사용하거나 일부 "
        "소비하여 상품 가치가 현저히 감소한 경우에는 청약철회가 "
        "제한될 수 있습니다. 복제가 가능한 상품의 포장을 훼손한 "
        "경우 등 법에서 정한 다른 제한 사유가 실제로 존재하는 "
        "경우에도 제한될 수 있습니다.\n\n"
        "따라서 반품 가능 여부는 단순히 포장을 열었는지만으로 "
        "판단하지 말고, 상품의 종류, 개봉 목적, 실제 사용·소비 "
        "여부와 가치 감소 정도를 기준으로 구체적으로 판단해야 "
        "합니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "공급된 경우에는 상품을 공급받은 날부터 3개월 이내이면서, "
        "그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 "
        "청약철회할 수 있습니다. 포장 개봉 사실만으로 이러한 "
        "법정 권리까지 배제할 수는 없습니다.\n\n"
        "다음처럼 법정 제한 사유와 상품 상태를 구분해 안내하는 "
        "것이 적절합니다.\n"
        "• 상품의 내용이나 상태를 확인하기 위한 단순 포장 "
        "개봉만으로는 반품이 제한되지 않습니다.\n"
        "• 개봉 후 실제 사용·소비로 상품 가치가 현저히 감소한 "
        "경우에는 반품이 제한될 수 있습니다.\n"
        "• 복제가 가능한 상품의 포장을 훼손한 경우 등 법정 "
        "제한 사유는 상품별로 구체적으로 안내합니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "법정 기간에 따라 반품·환불합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 포장 개봉 사실만으로 법정 "
        "청약철회권을 일률적으로 배제하는 문구는 사용하지 않는 "
        "것이 안전합니다."
    )
def build_short_return_period_notice_answer(
    ad_copy: str,
    period_label: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """법정 기간보다 짧은 반품·청약철회 기간 문구를 검토합니다."""
    return (
        f"{copy_label} “{ad_copy}”는 법정 청약철회 기간을 "
        f"{period_label}으로 단축하는 의미이므로 수정해야 합니다.\n\n"
        "통신판매에서 소비자는 원칙적으로 계약내용에 관한 "
        "서면을 받은 날부터 7일 이내에 청약철회할 수 있습니다. "
        "상품 공급이 서면 수령보다 늦게 이루어진 경우에는 "
        "상품을 공급받거나 공급이 시작된 날부터 7일을 "
        "기준으로 합니다. 따라서 반품 신청 기간을 배송 완료나 "
        f"상품 수령 후 {period_label}으로만 제한하면 법정 "
        "기간보다 소비자에게 불리한 약정이 될 수 있습니다.\n\n"
        "다만 소비자의 책임으로 상품이 훼손됐거나, 사용 또는 "
        "일부 소비로 상품 가치가 현저히 감소한 경우 등 법에서 "
        "정한 청약철회 제한 사유가 실제로 존재하면 반품이 "
        "제한될 수 있습니다. 이러한 제한은 법정 사유와 실제 "
        "상품 상태를 기준으로 판단해야 하며, 판매자가 청약철회 "
        f"기간을 일률적인 {period_label} 기한으로 대신할 수는 "
        "없습니다.\n\n"
        "상품이 불량이거나 표시·광고 또는 계약 내용과 다르게 "
        "공급된 경우에는 상품을 공급받은 날부터 3개월 이내이면서, "
        "그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 "
        "청약철회할 수 있습니다. 이 기간도 "
        f"‘{period_label}이 지나면 반품 불가’라는 문구로 줄일 "
        "수 없습니다.\n\n"
        "다음처럼 수정하는 것이 적절합니다.\n"
        "• 단순 변심에 따른 청약철회는 상품 수령 후 7일 이내에 "
        "신청할 수 있습니다.\n"
        "• 소비자의 사용·훼손으로 상품 가치가 현저히 감소한 "
        "경우 등 법정 제한 사유가 있으면 반품이 제한될 수 "
        "있습니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "별도의 법정 청약철회 기간이 적용됩니다.\n"
        "• 배송 완료나 상품 수령 시점을 기준으로 법정 기간보다 "
        "짧은 신청 기한을 일률적으로 정하지 않습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 반품 기한을 {period_label}으로 "
        "단축하는 문구는 사용하지 않는 것이 안전합니다."
    )
def build_blanket_return_prohibition_ad_copy_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """일률적인 반품·환불 불가 문구를 전자상거래법 기준으로 검토합니다."""
    return (
        f"{copy_label} “{ad_copy}”는 상품의 종류나 반품 사유를 "
        "구분하지 않고 소비자의 청약철회와 환급 권리를 "
        "일률적으로 배제하는 의미이므로 수정해야 합니다.\n\n"
        "쇼핑몰이 상세페이지, 약관 또는 반품 안내에 ‘구매 후 "
        "반품·환불 불가’라고 적었다는 사실만으로 소비자의 법정 "
        "권리를 없앨 수는 없습니다. 법에서 정한 제한 사유가 "
        "없다면 소비자는 원칙적으로 계약내용에 관한 서면을 받은 "
        "날부터 7일 이내에 청약철회할 수 있습니다. 상품 공급이 "
        "더 늦은 경우에는 상품을 공급받거나 공급이 시작된 날부터 "
        "7일을 기준으로 합니다.\n\n"
        "다만 소비자의 책임으로 상품이 멸실·훼손됐거나, 사용 또는 "
        "일부 소비로 상품 가치가 현저히 감소한 경우 등 법에서 "
        "정한 사유가 실제로 존재하면 청약철회가 제한될 수 "
        "있습니다. 상품 내용을 확인하기 위한 포장 훼손은 그 "
        "자체만으로 소비자 책임의 훼손에 해당한다고 볼 수 없으므로, "
        "구매 또는 포장 개봉 사실만으로 모든 상품의 반품을 "
        "금지해서는 안 됩니다.\n\n"
        "상품이 불량이거나 상세페이지의 표시·광고 또는 계약 "
        "내용과 다르게 공급된 경우에는 상품을 공급받은 날부터 "
        "3개월 이내이면서, 그 사실을 안 날 또는 알 수 있었던 "
        "날부터 30일 이내에 청약철회할 수 있습니다. 이러한 "
        "법정 권리까지 ‘모든 상품 환불 불가’라는 문구로 배제할 "
        "수는 없습니다.\n\n"
        "적법한 청약철회로 상품이 반환되면 판매자는 원칙적으로 "
        "상품을 반환받은 날부터 3영업일 이내에 대금을 환급해야 "
        "합니다. 단순 변심에 따른 반환 비용은 소비자가 부담할 "
        "수 있지만, 상품이 표시·광고 또는 계약 내용과 다른 경우의 "
        "반환 비용은 판매자가 부담합니다.\n\n"
        "교환 제공 여부와 방식은 판매정책에 따라 달라질 수 있지만, "
        "‘교환 불가’라는 표현을 법정 반품·환불까지 모두 금지하는 "
        "의미로 사용해서는 안 됩니다. 다음처럼 사유와 기준을 "
        "구분해 안내하는 것이 적절합니다.\n"
        "• 단순 변심에 따른 청약철회는 상품 수령 후 7일 이내에 "
        "신청할 수 있으며 반환 비용은 소비자가 부담합니다.\n"
        "• 소비자의 사용·훼손으로 상품 가치가 현저히 감소한 "
        "경우 등 법정 제한 사유가 있으면 반품이 제한될 수 "
        "있습니다.\n"
        "• 상품 불량 또는 표시·광고나 계약 내용과 다른 경우에는 "
        "법정 기간 안에 반품·환불하며 반환 비용은 판매자가 "
        "부담합니다.\n"
        "• 적법한 반품으로 상품을 반환받은 경우에는 원칙적으로 "
        "3영업일 이내에 대금을 환급합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같은 일률적인 문구는 사용하지 않는 것이 "
        "안전합니다."
    )


def build_blanket_return_prohibition_notice_answer() -> str:
    """일률적인 반품 불가 표시 질문에 사용할 검증된 답변입니다."""
    return (
        "원칙적으로 안 됩니다. 상품 상세페이지나 약관에 "
        "‘반품 불가’라고 적었다는 사실만으로 소비자의 법정 "
        "청약철회권을 없앨 수는 없습니다.\n\n"
        "소비자의 책임으로 상품이 훼손되었거나, 사용·소비로 "
        "상품 가치가 현저히 감소한 경우처럼 전자상거래법에서 "
        "정한 청약철회 제한 사유가 실제로 있는 경우에는 "
        "반품이 제한될 수 있습니다. 제한 대상 상품이라면 "
        "소비자가 쉽게 알 수 있는 곳에 그 사실을 명확하게 "
        "알려야 합니다.\n\n"
        "따라서 모든 상품에 대해 일률적으로 ‘반품 불가’라고 "
        "표시하거나 법정 청약철회 기간을 임의로 줄이는 문구는 "
        "효력이 없거나 청약철회 방해로 문제될 수 있습니다."
    )


def is_seller_contact_required_return_obstruction_notice_question(
    question: str,
) -> bool:
    """
    판매자와 미리 통화·연락하지 않고 반송했다는 이유만으로
    반품·환불을 일률적으로 거절하는 문구를 판별합니다.

    단순한 사전 연락 권고나 반송 주소·분실 책임 확인 안내는
    이 유형에서 제외합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)

    return_terms = (
        "반품",
        "환불",
        "청약철회",
        "반송",
        "반환",
        "구매취소",
        "계약해제",
    )

    seller_terms = (
        "판매자",
        "판매처",
        "쇼핑몰",
        "업체",
        "사업자",
        "통신판매업자",
        "고객센터",
        "상담센터",
    )

    contact_terms = (
        "통화",
        "전화",
        "연락",
        "문의",
        "상담",
        "접수",
        "사전통화",
        "사전연락",
        "미리통화",
        "미리연락",
    )

    no_contact_terms = (
        "통화하지않고",
        "전화하지않고",
        "연락하지않고",
        "문의하지않고",
        "상담하지않고",
        "접수하지않고",
        "사전통화없이",
        "사전연락없이",
        "연락없이",
        "통화없이",
        "전화없이",
        "미연락",
        "연락하지않은",
        "통화하지않은",
        "접수하지않은",
        "연락전",
        "통화전",
    )

    shipment_terms = (
        "반송",
        "반환",
        "발송",
        "보낸",
        "보내",
        "택배",
        "상품",
        "물품",
    )

    strict_condition_terms = (
        "통화한경우에만",
        "연락한경우에만",
        "전화한경우에만",
        "접수한경우에만",
        "사전통화후에만",
        "사전연락후에만",
        "통화해야만",
        "연락해야만",
        "전화해야만",
        "접수해야만",
    )

    denial_terms = (
        "환불하지않",
        "반품을인정하지않",
        "반품인정하지않",
        "반품불인정",
        "환불불가",
        "반품불가",
        "청약철회불가",
        "환급하지않",
        "처리하지않",
        "처리불가",
        "받지않",
        "거절",
        "거부",
        "인정하지않",
        "할수없",
    )

    permitted_terms = (
        "통화하지않아도",
        "전화하지않아도",
        "연락하지않아도",
        "사전통화없이도",
        "사전연락없이도",
        "연락여부와관계없이",
        "통화여부와관계없이",
        "반품가능",
        "환불가능",
        "청약철회가능",
        "법정권리를제한하지않",
        "일률적으로거절하지않",
    )

    recommendation_only_terms = (
        "권장",
        "권고",
        "원활한처리를위해",
        "정확한반송주소확인을위해",
        "반송주소를확인",
        "분실책임을확인",
        "책임관계를확인",
    )

    has_return_topic = any(
        term in normalized
        for term in return_terms
    )
    has_seller = any(
        term in normalized
        for term in seller_terms
    )
    has_contact = any(
        term in normalized
        for term in contact_terms
    )
    has_no_contact = any(
        term in normalized
        for term in no_contact_terms
    )
    has_shipment = any(
        term in normalized
        for term in shipment_terms
    )
    has_strict_condition = any(
        term in normalized
        for term in strict_condition_terms
    )
    has_denial = any(
        term in normalized
        for term in denial_terms
    )
    has_permission = any(
        term in normalized
        for term in permitted_terms
    )
    recommendation_only = (
        any(
            term in normalized
            for term in recommendation_only_terms
        )
        and not has_denial
        and not has_strict_condition
    )

    if has_permission or recommendation_only:
        return False

    no_contact_refund_denial = (
        has_seller
        and has_contact
        and has_no_contact
        and has_shipment
        and has_denial
    )

    contact_as_mandatory_condition = (
        has_seller
        and has_contact
        and has_strict_condition
        and (
            has_denial
            or has_return_topic
        )
    )

    return (
        has_return_topic
        and (
            no_contact_refund_denial
            or contact_as_mandatory_condition
        )
    )


def is_customer_service_approval_return_obstruction_notice_question(
    question: str,
) -> bool:
    """
    고객센터 전화 접수만을 유일한 반품 방법으로 정하거나,
    판매자의 내부 검토·승인 전까지 반품을 인정하지 않는
    문구를 판별합니다.
    """
    ad_copy = extract_explicit_ad_copy(question)
    target_text = ad_copy or question
    normalized = normalize_text(target_text)

    return_terms = (
        "반품", "환불", "청약철회", "구매취소", "계약해제", "반환",
    )

    customer_service_terms = (
        "고객센터", "상담센터", "콜센터", "상담원",
        "전화", "전화접수", "유선", "유선접수", "상담접수",
    )

    exclusive_terms = (
        "경우에만", "한경우에만", "접수한경우에만",
        "전화로만", "전화접수만", "유선으로만", "유선접수만",
        "고객센터를통해서만", "고객센터접수만", "상담원접수만",
        "접수해야만", "연락해야만", "전화해야만",
        "전화하지않으면", "연락하지않으면",
        "접수하지않으면", "접수없이는",
    )

    approval_terms = (
        "검토", "검수", "확인", "승인", "허가", "심사", "판정",
    )

    dependency_terms = (
        "완료후", "끝난후", "마친후", "승인후", "허가후",
        "검토후", "검수후", "확인후",
        "승인받아야", "승인을받아야", "승인을받아야만",
        "허가받아야", "허가를받아야", "허가를받아야만",
        "받아야만", "검토될때까지", "검수가끝날때까지",
        "확인될때까지", "승인될때까지",
        "승인전에는", "검토전에는",
    )

    denial_terms = (
        "인정하지않", "반품을인정하지않", "반품불인정",
        "반품불가", "환불불가", "접수불가", "처리하지않",
        "처리불가", "받지않", "거절", "거부",
        "가능하지않", "할수없", "불가능",
    )

    recognition_terms = (
        "인정", "가능", "접수", "처리", "승인", "허용", "받아",
    )

    allowed_alternative_terms = (
        "전화또는온라인", "온라인또는전화", "고객센터또는온라인",
        "온라인접수도가능", "이메일접수도가능",
        "문의게시판접수도가능", "여러방법으로접수",
        "선택할수있", "선택가능", "선택사항", "필수아님",
        "전화접수가필수는아니", "법정청약철회를제한하지않",
    )

    has_return_topic = any(term in normalized for term in return_terms)
    has_customer_service = any(term in normalized for term in customer_service_terms)
    has_exclusive_condition = any(term in normalized for term in exclusive_terms)
    has_approval_process = any(term in normalized for term in approval_terms)
    has_dependency = any(term in normalized for term in dependency_terms)
    has_denial = any(term in normalized for term in denial_terms)
    has_recognition = any(term in normalized for term in recognition_terms)
    has_allowed_alternative = any(
        term in normalized for term in allowed_alternative_terms
    )

    if has_allowed_alternative:
        return False

    exclusive_contact_condition = (
        has_customer_service
        and has_exclusive_condition
        and has_recognition
    )

    approval_dependency_condition = (
        has_approval_process
        and has_dependency
        and (has_denial or has_recognition)
    )

    explicit_denial_until_review = (
        has_customer_service
        and has_approval_process
        and has_denial
    )

    return (
        has_return_topic
        and (
            exclusive_contact_condition
            or approval_dependency_condition
            or explicit_denial_until_review
        )
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


def build_seller_contact_required_return_obstruction_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    판매자와 사전 통화·연락하지 않았다는 이유만으로
    반품·환불을 거절하는 문구를 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 소비자의 법정 청약철회와 "
        "환급 권리를 판매자와의 사전 통화·연락 여부에 "
        "종속시키는 의미이므로 수정해야 합니다.\n\n"
        "판매자와의 사전 연락은 정확한 반품 주소, 수거 방법, "
        "배송 추적 및 환급 절차를 안내하기 위한 운영 절차로 "
        "둘 수 있습니다. 그러나 소비자가 법정 기간 안에 "
        "청약철회 의사를 명확하게 표시했다면 판매자와 미리 "
        "통화하지 않았다는 이유만으로 청약철회를 부인하거나 "
        "환불을 일률적으로 거절해서는 안 됩니다.\n\n"
        "연락 없이 잘못된 주소나 지정되지 않은 장소로 상품을 "
        "보내 판매자가 실제로 반환받지 못했거나, 배송 과정에서 "
        "상품이 분실된 경우에는 반환 사실, 도착 여부와 책임 "
        "관계를 확인할 수 있습니다. 다만 판매자가 정상적으로 "
        "상품을 반환받았는데도 사전 통화가 없었다는 이유만으로 "
        "법정 반품·환불 권리를 배제해서는 안 됩니다.\n\n"
        "반환된 상품에 소비자 책임의 훼손이나 사용으로 인한 "
        "현저한 가치 감소 등 법정 청약철회 제한 사유가 있는지는 "
        "사전 통화 여부와 별도로 실제 상품 상태를 기준으로 "
        "판단해야 합니다.\n\n"
        "전자상거래법은 거짓·과장된 사실이나 기만적인 방법으로 "
        "소비자의 청약철회 또는 계약 해지를 방해하는 행위를 "
        "금지합니다. 청약철회 방해 행위가 있었다면 그 방해 "
        "행위가 종료된 날부터 다시 7일의 청약철회 기간이 "
        "적용될 수 있습니다.\n\n"
        "다음처럼 사전 연락 절차와 법정 권리를 구분해 안내하는 "
        "것이 적절합니다.\n"
        "• 원활한 반품을 위해 판매자에게 연락하여 반품 주소와 "
        "수거 방법을 확인해 주세요.\n"
        "• 사전 연락은 반품 절차를 안내하기 위한 것이며 법정 "
        "청약철회 권리를 제한하지 않습니다.\n"
        "• 연락 없이 반송한 경우에는 상품의 실제 도착 여부와 "
        "반환 주소를 확인할 수 있습니다.\n"
        "• 판매자가 상품을 정상적으로 반환받은 경우 사전 통화가 "
        "없었다는 이유만으로 환불을 거절하지 않습니다.\n"
        "• 법정 청약철회 제한 여부는 실제 상품 상태와 반품 "
        "사유를 기준으로 판단합니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 판매자와의 사전 통화를 반품·환불의 "
        "필수 조건으로 정하는 문구는 사용하지 않는 것이 "
        "안전합니다."
    )


def build_customer_service_approval_return_obstruction_notice_answer(
    ad_copy: str,
    copy_label: str = "반품·환불 문구",
) -> str:
    """
    전화 접수만 인정하거나 판매자의 내부 승인 전까지
    반품을 인정하지 않는 문구를 검토합니다.
    """
    return (
        f"{copy_label} “{ad_copy}”는 소비자의 법정 청약철회 "
        "의사표시 방법을 고객센터 전화 접수로만 제한하거나, "
        "판매자의 내부 검토·승인이 끝나야 반품이 인정되는 "
        "것처럼 정하고 있어 수정해야 합니다.\n\n"
        "고객센터 접수는 반품 주소, 수거 방법, 상품 반환과 "
        "환급 절차를 안내하기 위한 운영 절차로 둘 수 있습니다. "
        "그러나 소비자가 법정 기간 안에 청약철회 의사를 "
        "명확하게 표시했다면 전화 접수를 하지 않았다는 이유만으로 "
        "청약철회를 일률적으로 부인해서는 안 됩니다.\n\n"
        "판매자는 반환된 상품을 확인해 소비자 책임의 훼손, "
        "사용으로 인한 현저한 가치 감소 등 법정 청약철회 제한 "
        "사유가 실제로 있는지 판단할 수 있습니다. 다만 내부 "
        "검토나 승인이 끝날 때까지 모든 반품 접수와 청약철회의 "
        "효력 자체를 인정하지 않는 방식으로 운영해서는 안 됩니다.\n\n"
        "전자상거래법은 거짓·과장된 사실이나 기만적인 방법을 "
        "사용해 소비자의 청약철회를 방해하는 행위를 금지합니다. "
        "청약철회 방해 행위가 있었다면 그 방해 행위가 종료된 "
        "날부터 다시 7일의 청약철회 기간이 적용될 수 있습니다.\n\n"
        "다음처럼 고객센터 안내 절차와 법정 청약철회 권리를 "
        "구분해 표시하는 것이 적절합니다.\n"
        "• 반품을 원하는 경우 고객센터, 온라인 접수 등 제공된 "
        "방법으로 청약철회 의사를 표시할 수 있습니다.\n"
        "• 고객센터 접수는 수거와 환급 절차를 안내하기 위한 "
        "절차이며 법정 청약철회 권리를 제한하지 않습니다.\n"
        "• 반환 상품의 상태를 확인한 결과 법정 제한 사유가 있는 "
        "경우 그 사유와 근거를 구체적으로 안내합니다.\n"
        "• 판매자의 내부 검토나 승인 완료를 청약철회의 성립 "
        "조건으로 정하지 않습니다.\n"
        "• 전화 접수를 하지 않았다는 이유만으로 법정 기간 안의 "
        "청약철회를 일률적으로 거절하지 않습니다.\n\n"
        "전자상거래법 제17조부터 제19조까지의 규정을 위반한 "
        "약정으로서 소비자에게 불리한 것은 효력이 없으므로, "
        f"“{ad_copy}”와 같이 전화 접수나 판매자의 승인을 "
        "반품 인정의 필수 조건으로 정하는 문구는 사용하지 않는 "
        "것이 안전합니다."
    )


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


@_measure_total
def answer_question(
    question: str,
    on_token: TokenCallback | None = None,
) -> dict[str, Any]:
    """Qdrant 검색부터 답변 반환까지 전체 RAG 과정을 실행한다."""
    question = " ".join(question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    streaming_generator = _build_streaming_generator(
        on_token
    )

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
    matches_return_penalty_deduction = (
        is_return_penalty_deduction_notice_question(
            question
        )
    )
    matches_forced_store_credit_refund = (
        is_forced_store_credit_refund_notice_question(
            question
        )
    )
    matches_stockout_store_credit_only = (
        is_stockout_store_credit_only_notice_question(
            question
        )
    )
    matches_excessive_refund_delay_notice = (
        is_excessive_refund_delay_notice_question(
            question
        )
    )
    matches_actual_measurement_mismatch_exchange_only = (
        is_actual_measurement_mismatch_exchange_only_notice_question(
            question
        )
    )
    matches_screen_color_mismatch_prohibition = (
        is_screen_actual_color_mismatch_refund_prohibition_notice_question(
            question
        )
    )
    matches_mismatch_refund_prohibition = (
        is_mismatch_refund_prohibition_notice_question(
            question
        )
    )
    matches_defective_exchange_only_prohibition = (
        is_defective_exchange_only_refund_prohibition_notice_question(
            question
        )
    )
    matches_light_color_return_prohibition = (
        is_light_color_product_return_prohibition_notice_question(
            question
        )
    )
    matches_worn_product_return_prohibition = (
        is_worn_product_return_prohibition_notice_question(
            question
        )
    )
    matches_tag_removed_return_prohibition = (
        is_tag_removed_return_prohibition_notice_question(
            question
        )
    )
    matches_opened_package_prohibition = (
        is_opened_package_return_prohibition_notice_question(
            question
        )
    )
    matches_short_return_period = (
        is_short_return_period_notice_question(
            question
        )
    )
    matches_discounted_return_prohibition_notice = (
        is_discounted_product_return_prohibition_notice_question(
            question
        )
    )
    matches_blanket_return_prohibition = (
        is_blanket_return_prohibition_notice_question(
            question
        )
    )
    matches_review_data_privacy = (
        is_review_data_privacy_analysis_question(
            question
        )
    )
    matches_platform_restricted_expression = (
        is_platform_restricted_expression_question(
            question
        )
    )
    matches_explicit_ad_copy_assessment = (
        is_explicit_ad_copy_assessment_question(
            question
        )
    )
    matches_missing_ad_copy_assessment = (
        is_missing_ad_copy_assessment_question(
            question
        )
    )
    matches_seller_contact_return_obstruction = (
        is_seller_contact_required_return_obstruction_notice_question(
            question
        )
    )
    matches_customer_service_return_obstruction = (
        is_customer_service_approval_return_obstruction_notice_question(
            question
        )
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
        elif matches_defective_exchange_only_prohibition:
            search_question = (
                "전자상거래법 제17조제3항에 따라 불량 상품이나 "
                "표시·광고 또는 계약 내용과 다르게 공급된 상품은 "
                "공급받은 날부터 3개월 이내이면서 그 사실을 안 "
                "날부터 30일 이내에 청약철회할 수 있는지, 판매자가 "
                "동일 상품으로만 교환하도록 강제하고 환불을 "
                "일률적으로 금지할 수 있는지, 제18조에 따라 "
                "상품 반환 후 3영업일 이내 대금을 환급하고 "
                "계약 내용과 다른 상품의 반환 비용을 판매자가 "
                "부담해야 하는지, 제35조에 따라 소비자에게 불리한 "
                "약정은 효력이 없는지"
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
        elif matches_review_data_privacy:
            search_question = (
                "개인정보 보호법 제2조의 개인정보와 개인정보 처리 "
                "정의, 제3조의 목적 제한·최소 처리·익명 또는 "
                "가명처리 원칙, 제15조의 개인정보 수집·이용 및 "
                "당초 수집 목적과 합리적으로 관련된 추가 이용에 "
                "따라 쇼핑몰 리뷰 데이터를 분석할 때 개인정보 "
                "문제가 있나요?"
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
        elif matches_return_penalty_deduction:
            search_question = (
                "전자상거래법 제18조에 따라 단순 변심에 따른 "
                "청약철회의 반환 비용은 소비자가 부담할 수 있지만 "
                "판매자가 청약철회를 이유로 위약금이나 손해배상을 "
                "청구할 수 없는지, 상품 가격이나 결제 금액의 "
                "20퍼센트를 모든 반품에 일률적으로 공제할 수 "
                "있는지, 상품 일부 사용·소비가 있는 경우에도 "
                "법령상 허용 범위와 실제 상태를 확인해야 하는지, "
                "상품이 표시·광고 또는 계약 내용과 다른 경우의 "
                "반환 비용은 판매자가 부담하는지, 제35조에 따라 "
                "소비자에게 불리한 약정은 효력이 없는지"
            )
        elif matches_forced_store_credit_refund:
            search_question = (
                "전자상거래법 제18조에 따라 적법한 청약철회로 "
                "재화가 반환되면 판매자는 반환받은 날부터 "
                "3영업일 이내에 이미 지급받은 대금을 환급하고, "
                "신용카드 등으로 결제한 경우 결제업자에게 대금 "
                "청구 정지나 결제 취소를 지체 없이 요청해야 "
                "하는지, 소비자의 선택 없이 결제 취소나 금전 "
                "환급 대신 쇼핑몰 적립금·포인트·마일리지·예치금으로 "
                "환불금을 강제 전환할 수 있는지, 제35조에 따라 "
                "소비자에게 불리한 약정은 효력이 없는지"
            )
        elif matches_stockout_store_credit_only:
            search_question = (
                "전자상거래법 제15조에 따라 품절 등으로 주문받은 "
                "상품을 공급하기 곤란한 경우 소비자에게 언제 "
                "알려야 하고, 선결제 대금은 언제까지 환급해야 "
                "하나요? 판매자가 품절 상품의 결제대금을 "
                "적립금이나 포인트로만 지급하도록 정할 수 있나요?"
            )
        elif matches_excessive_refund_delay_notice:
            search_question = (
                "전자상거래법 제18조에 따라 재화를 반품한 경우 "
                "판매자는 재화를 반환받은 날부터 3영업일 이내에 "
                "대금을 환급해야 하나요? 반품 상품 확인 후 "
                "30일 이내 환불한다고 정할 수 있나요? 환급 지연 "
                "시 지연배상금과 제35조의 소비자에게 불리한 "
                "계약 금지는 어떻게 적용되나요?"
            )
        elif matches_actual_measurement_mismatch_exchange_only:
            search_question = (
                "전자상거래법 제17조제3항에 따라 실제 상품의 "
                "치수가 상세페이지·사이즈표에 표시된 치수와 "
                "명확히 다르고 상품 선택이나 착용에 영향을 주는 "
                "경우 표시·광고 또는 계약 내용과 다르게 공급된 "
                "것으로 보아 공급일부터 3개월 이내이면서 안 "
                "날부터 30일 이내에 청약철회할 수 있는지, 측정 "
                "위치·방법·소재 신축성·생산 과정에 따른 경미한 "
                "오차와 계약 불일치에 해당하는 명확한 치수 차이를 "
                "구체적으로 판단해야 하는지, 판매자가 교환만을 "
                "강제하면서 환불을 배제할 수 있는지, 제18조에 "
                "따라 상품 반환 후 3영업일 이내 대금을 환급하고 "
                "반환 비용을 판매자가 부담해야 하는지, 제35조에 "
                "따라 소비자에게 불리한 약정은 효력이 없는지"
            )
        elif matches_screen_color_mismatch_prohibition:
            search_question = (
                "전자상거래법 제17조제3항에 따라 상세페이지 화면에 "
                "표시된 색상이나 주문한 색상과 실제 배송 상품의 "
                "색상이 명확히 다른 경우 표시·광고 또는 계약 "
                "내용과 다르게 공급된 것으로 보아 공급일부터 "
                "3개월 이내이면서 안 날부터 30일 이내에 "
                "청약철회할 수 있는지, 촬영 조명·카메라·모니터 "
                "설정에 따른 경미한 색상 차이와 상품 선택에 영향을 "
                "주는 명확한 색상 불일치를 구체적으로 판단해야 "
                "하는지, 제18조에 따라 상품 반환 후 3영업일 이내 "
                "대금을 환급하고 반환 비용을 판매자가 부담해야 "
                "하는지, 제35조에 따라 소비자에게 불리한 약정은 "
                "효력이 없는지"
            )
        elif matches_mismatch_refund_prohibition:
            search_question = (
                "전자상거래법 제17조제3항에 따라 상품이 "
                "표시·광고 또는 계약 내용과 다르게 제공된 경우의 "
                "청약철회 기간과, 제18조에 따른 대금 환급 및 "
                "반환 비용 부담은 어떻게 되나요? 쇼핑몰이 "
                "상품 설명과 실제 상품이 달라도 환불 불가라고 "
                "표시할 수 있나요?"
            )
        elif matches_light_color_return_prohibition:
            search_question = (
                "전자상거래법 제17조제2항에 따라 소비자 책임의 "
                "오염·훼손 또는 사용으로 상품 가치가 현저히 감소한 "
                "경우 단순 변심 청약철회가 제한될 수 있지만, "
                "흰색·아이보리·화이트 등 밝은 색상이라는 사실만으로 "
                "오염 여부와 관계없이 반품을 일률적으로 금지할 수 "
                "있는지, 실제 오염·사용 흔적·훼손과 현저한 가치 "
                "감소를 구체적으로 판단해야 하는지, 제17조제3항에 "
                "따라 상품 불량·색상 오배송·표시광고 또는 계약 "
                "내용과 다른 경우의 청약철회권을 색상만으로 "
                "배제할 수 있는지, 제35조에 따라 소비자에게 "
                "불리한 약정은 효력이 없는지"
            )
        elif matches_worn_product_return_prohibition:
            search_question = (
                "전자상거래법 제17조제2항에 따라 소비자의 사용으로 "
                "상품 가치가 현저히 감소한 경우 단순 변심 "
                "청약철회가 제한될 수 있지만, 사이즈·핏·착용감 "
                "확인을 위한 짧은 시착이나 한 번의 착용만으로 "
                "항상 현저한 가치 감소가 인정되는지, 외출·장시간 "
                "착용으로 오염·냄새·주름·늘어남·변형이 발생한 "
                "경우에는 제한될 수 있는지, 제17조제3항에 따라 "
                "상품 불량 또는 표시·광고·계약 내용과 다른 경우의 "
                "청약철회권을 착용만으로 배제할 수 있는지, "
                "제35조에 따라 소비자에게 불리한 약정은 효력이 "
                "없는지"
            )
        elif matches_tag_removed_return_prohibition:
            search_question = (
                "전자상거래법 제17조제2항에 따라 소비자 책임으로 "
                "상품이 훼손되거나 사용으로 가치가 현저히 감소한 "
                "경우 단순 변심 청약철회가 제한될 수 있지만, "
                "상품 택·태그·라벨 제거만으로 항상 훼손 또는 "
                "현저한 가치 감소가 인정되는지, 제17조제3항에 따라 "
                "상품 불량 또는 표시·광고·계약 내용과 다른 경우의 "
                "청약철회권을 택 제거만으로 배제할 수 있는지, "
                "제35조에 따라 소비자에게 불리한 약정은 효력이 "
                "없는지"
            )
        elif matches_opened_package_prohibition:
            search_question = (
                "전자상거래법 제17조제2항에 따라 상품 내용을 "
                "확인하기 위한 포장 훼손은 청약철회 제한 사유에서 "
                "제외되고, 실제 사용·소비로 상품 가치가 현저히 "
                "감소한 경우나 복제가 가능한 상품의 포장 훼손은 "
                "제한될 수 있는지, 포장을 개봉한 경우 반품 및 "
                "환불이 불가능하다고 일률적으로 표시할 수 있는지, "
                "제35조에 따라 소비자에게 불리한 약정은 효력이 "
                "없는지"
            )
        elif matches_discounted_return_prohibition_notice:
            search_question = (
                "전자상거래법 제17조에 따라 쿠폰 사용이나 할인 "
                "혜택을 적용한 사실 자체가 독립적인 청약철회 제한 "
                "사유인지, 법정 제한 사유가 없다면 7일 이내 "
                "청약철회할 수 있는지, 상품이 표시 광고 또는 계약 "
                "내용과 다른 경우 3개월 및 30일 기간이 적용되는지, "
                "제18조제9항과 제10항에 따라 단순 변심 반환 비용은 "
                "소비자가 부담하고 계약 불일치 반환 비용은 판매자가 "
                "부담하는지, 제35조에 따라 쿠폰·할인 혜택 적용 "
                "상품의 반품과 환불을 일률적으로 금지한 소비자에게 "
                "불리한 약정은 효력이 없는지"
            )
        elif matches_short_return_period:
            search_question = (
                "전자상거래법 제17조에 따른 통신판매 청약철회 "
                "기간은 원칙적으로 7일인데, 쇼핑몰이 반품 가능 "
                "기간을 상품 수령 또는 배송 완료 후 "
                "1시간에서 167시간 또는 1일에서 6일 이내로만 "
                "일률적으로 줄일 수 있는지, 상품이 표시·광고 또는 "
                "계약 내용과 다른 경우의 3개월 및 30일 기간도 "
                "줄일 수 있는지, 제35조에 따라 소비자에게 불리한 "
                "약정은 효력이 없는지"
            )
        elif matches_blanket_return_prohibition:
            search_question = (
                "전자상거래법 제17조의 7일 이내 청약철회 원칙과 "
                "법정 제한 사유, 상품이 표시·광고 또는 계약 내용과 "
                "다른 경우의 3개월 및 30일 청약철회 기간, 제18조의 "
                "상품 반환 후 3영업일 이내 환급과 반품 비용 부담, "
                "제35조의 소비자에게 불리한 계약 금지에 따라 "
                "쇼핑몰이 모든 상품의 반품과 환불을 일률적으로 "
                "금지할 수 있는지"
            )
        elif (
            matches_explicit_ad_copy_assessment
            and is_domestic_sales_rank_ad_copy_question(
                question
            )
        ):
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 거짓·과장 "
                "및 부당하게 비교하는 표시·광고 금지와 제5조의 "
                "표시·광고 내용 실증 의무에 따라 국내 판매 1위라는 "
                "문구를 사용하려면 조사 기간, 시장과 판매채널의 "
                "범위, 상품 카테고리, 판매수량 또는 매출액 기준, "
                "비교 대상과 데이터 출처를 객관적으로 확인할 수 "
                "있어야 하나요?"
            )
        elif (
            matches_explicit_ad_copy_assessment
            and is_comparative_multiplier_ad_copy_question(
                question
            )
        ):
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 부당하게 "
                "비교하는 표시·광고 금지와 제5조의 표시·광고 내용 "
                "실증 의무에 따라 타사 제품보다 보정 효과가 2배 "
                "뛰어나다는 문구를 사용하려면 비교 제품, 평가 항목, "
                "측정 단위, 동일한 시험 조건, 표본 수, 기준값과 "
                "배수 산출 방식에 관한 객관적인 자료가 필요한가요?"
            )
        elif (
            matches_explicit_ad_copy_assessment
            and is_universal_numeric_waist_appearance_ad_copy_question(
                question
            )
        ):
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 "
                "부당한 표시·광고 행위 금지와 제5조의 표시·광고 "
                "내용 실증 의무에 따라 누구나 입으면 허리가 "
                "5cm 가늘어 보인다는 문구처럼 모든 착용자에게 "
                "동일한 정량적 시각 효과가 나타난다고 표시하려면 "
                "평가 대상, 체형, 제품 사이즈, 촬영 조건, 비교 "
                "방법 및 객관적인 조사 자료가 필요한가요?"
            )
        elif (
            matches_explicit_ad_copy_assessment
            and is_laundry_shrinkage_ad_copy_question(
                question
            )
        ):
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 "
                "부당한 표시·광고 행위 금지와 제5조의 표시·광고 "
                "내용 실증 의무에 따라 세탁해도 절대 줄어들지 "
                "않는다는 상품 성능 문구를 사용하려면 세탁 온도, "
                "세탁 방식, 건조 조건, 시험 횟수와 수축률에 관한 "
                "객관적인 시험 자료가 필요한가요?"
            )
        elif (
            matches_explicit_ad_copy_assessment
            and is_full_natural_material_ad_copy_question(
                question
            )
        ):
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 "
                "부당한 표시·광고 행위 금지와 제5조의 표시·광고 "
                "내용 실증 의무에 따라 천연가죽 100%처럼 소재와 "
                "함량에 관한 사실을 표시하려면 실제 소재 구성, "
                "적용 범위 및 객관적인 확인 자료가 필요한가요?"
            )
        elif matches_explicit_ad_copy_assessment:
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조에 따라 "
                "소비자를 속이거나 소비자로 하여금 잘못 알게 할 "
                "우려가 있는 거짓·과장의 표시·광고 또는 "
                "기만적인 표시·광고에 해당하는 판단 기준은 "
                "무엇인가요?"
            )
        elif matches_missing_ad_copy_assessment:
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조에 따른 "
                "거짓·과장의 표시·광고, 기만적인 표시·광고, "
                "부당하게 비교하는 표시·광고 및 비방적인 "
                "표시·광고의 금지 기준은 무엇인가요?"
            )
        elif matches_platform_restricted_expression:
            search_question = (
                "표시·광고의 공정화에 관한 법률 제3조의 "
                "거짓·과장 광고, 기만적인 광고, 부당하게 비교하는 "
                "광고, 비방적인 광고와 전자상거래법 제21조의 "
                "거짓·과장 또는 기만적인 방법을 사용한 소비자 "
                "유인 및 청약철회 방해에 해당하는 온라인 쇼핑몰 "
                "상품명·광고·상세페이지의 제한 표현은 무엇인가요?"
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
                "전자상거래법 제17조에 따라 주문제작 상품이라는 "
                "이유만으로 청약철회를 일률적으로 제한할 수 있는지, "
                "7일 이내 청약철회 원칙과 소비자 책임의 훼손·사용에 "
                "따른 가치 감소 등 법정 제한 사유, 불량 또는 "
                "표시 광고·계약 내용과 다르게 제작된 경우의 "
                "3개월 및 30일 청약철회 기간, 제35조의 소비자에게 "
                "불리한 약정 무효 기준"
            )
        elif is_packaging_opening_return_question(question):
            search_question = (
                "상품의 내용이나 상태를 확인하기 위해 포장을 뜯은 "
                "경우에도 쇼핑몰이 반품을 거절할 수 있나요?"
            )
        elif matches_seller_contact_return_obstruction:
            search_question = (
                "전자상거래법 제17조에 따른 소비자의 청약철회와 "
                "환급 권리를 판매자와 사전 통화하거나 연락한 경우로만 "
                "제한할 수 있는지, 연락 없이 반송했더라도 판매자가 "
                "상품을 정상적으로 반환받은 경우 사전 통화가 없다는 "
                "이유만으로 환불을 거절할 수 있는지, 제21조의 "
                "청약철회 방해 금지와 제35조의 소비자에게 불리한 "
                "약정 금지가 어떻게 적용되는지"
            )
        elif matches_customer_service_return_obstruction:
            search_question = (
                "전자상거래법 제17조에 따른 소비자의 청약철회 "
                "의사표시를 고객센터 전화 접수로만 제한하거나 "
                "판매자의 내부 검토·승인 전까지 반품을 인정하지 "
                "않을 수 있는지, 제21조의 청약철회 방해 금지와 "
                "제35조의 소비자에게 불리한 약정 금지가 어떻게 "
                "적용되는지"
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


    if matches_review_data_privacy:
        search_top_k = REVIEW_PRIVACY_SEARCH_TOP_K
    elif (
        matches_platform_restricted_expression
        or matches_seller_contact_return_obstruction
        or matches_customer_service_return_obstruction
    ):
        search_top_k = PLATFORM_EXPRESSION_SEARCH_TOP_K
    else:
        search_top_k = SEARCH_TOP_K

    search_result = search_documents(
        question=search_question,
        top_k=search_top_k,
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
                generator=streaming_generator,
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

    # 불량 상품의 동일 상품 교환만 허용하고 환불을
    # 전면 금지하는 일반 문구도 제17조·제18조·제35조에 따라
    # 구체적으로 답한다.
    if matches_defective_exchange_only_prohibition:
        source_documents = (
            ensure_discounted_return_prohibition_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_defective_exchange_only_refund_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "defective_product_exchange_only_"
                "refund_prohibition_notice"
            ),
            "sources": source_documents[:3],
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
                generator=streaming_generator,
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

    # 리뷰 데이터 분석 질문은 일반 검색 점수 필터가 비어도
    # 검증된 답변과 실제 개인정보 보호법 검색 근거를 반환한다.
    if matches_review_data_privacy:
        raw_source_documents = sanitize_source_documents(
            initial_documents
        )

        source_candidates = merge_review_privacy_documents(
            relevant_documents,
            searched_documents,
            raw_source_documents,
        )

        article_2_document = (
            _select_exact_review_privacy_article(
                source_candidates,
                "article_2",
            )
        )

        # 제2조가 일반 검색에서 빠지면 제2조만 정확히 별도 검색한다.
        if article_2_document is None:
            article_2_result = search_documents(
                question=(
                    "개인정보 보호법 제2조 정의 개인정보란 "
                    "다른 정보와 쉽게 결합하여 개인을 알아볼 수 "
                    "있는 정보, 개인정보 처리란 수집 생성 연계 "
                    "연동 기록 저장 보유 가공 편집 검색 출력 "
                    "정정 복구 이용 제공 공개 파기"
                ),
                top_k=REVIEW_PRIVACY_ARTICLE_2_TOP_K,
            )

            article_2_documents = sanitize_source_documents(
                article_2_result.get("documents", [])
            )

            article_2_document = (
                _select_exact_review_privacy_article(
                    article_2_documents,
                    "article_2",
                )
            )

            source_candidates = merge_review_privacy_documents(
                source_candidates,
                article_2_documents,
            )

        source_documents = select_review_data_privacy_sources(
            source_candidates
        )

        # 제2조 검색 후에도 직접 근거가 3개 미만이면
        # 제15조·제16조·제18조를 한 번 보충 검색한다.
        if len(source_documents) < 3:
            supplement_result = search_documents(
                question=(
                    "개인정보 보호법 제15조 개인정보 수집 이용, "
                    "제16조 개인정보 수집 제한과 최소 수집, "
                    "제18조 개인정보 목적 외 이용 제공 제한"
                ),
                top_k=REVIEW_PRIVACY_SEARCH_TOP_K,
            )

            supplement_documents = sanitize_source_documents(
                supplement_result.get("documents", [])
            )

            source_candidates = merge_review_privacy_documents(
                source_candidates,
                supplement_documents,
            )

            source_documents = select_review_data_privacy_sources(
                source_candidates
            )

        source_documents = _prepend_review_privacy_article_2(
            source_documents,
            article_2_document,
        )

        answer = build_review_data_privacy_analysis_answer()

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "review_data_privacy_analysis",
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

    # 실제 광고 문구가 있으면 문구의 위험 표현을 직접 검토하고
    # 표시광고법 제3조를 근거로 반환한다.
    if matches_explicit_ad_copy_assessment:
        raw_source_documents = sanitize_source_documents(
            initial_documents
        )

        source_candidates = [
            *raw_source_documents,
            *searched_documents,
            *relevant_documents,
        ]

        ad_copy = extract_explicit_ad_copy(question)
        copy_label = detect_explicit_copy_label(question)

        # 세일·할인 상품이라는 이유만으로 교환·반품·환불을
        # 전면 제한하는 문구는 표시광고법 일반 답변보다
        # 전자상거래법 제17조·제18조·제35조를 우선 적용한다.
        if (
            matches_discounted_return_prohibition_notice
            and ad_copy is not None
        ):
            source_documents = (
                ensure_discounted_return_prohibition_sources(
                    source_candidates
                )
            )

            answer = (
                build_discounted_product_return_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "discounted_product_return_prohibition_notice"
                ),
                "sources": source_documents[:3],
            }

        # 판매자와 사전 통화·연락하지 않았다는 이유만으로
        # 반송 상품의 환불을 거절하는 문구는 일반 반품 금지와
        # 고객센터 승인형 문구보다 먼저 처리한다.
        if (
            matches_seller_contact_return_obstruction
            and ad_copy is not None
        ):
            source_documents = (
                ensure_customer_service_obstruction_sources(
                    source_candidates
                )
            )

            answer = (
                build_seller_contact_required_return_obstruction_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "seller_contact_required_"
                    "return_obstruction_notice"
                ),
                "sources": source_documents[:3],
            }

        # 고객센터 전화 접수만 인정하거나 내부 검토·승인을
        # 반품의 필수 조건으로 정한 문구는 일반 표시광고와
        # 일반 반품 방해 답변보다 먼저 처리한다.
        if (
            matches_customer_service_return_obstruction
            and ad_copy is not None
        ):
            source_documents = (
                ensure_customer_service_obstruction_sources(
                    source_candidates
                )
            )

            answer = (
                build_customer_service_approval_return_obstruction_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "customer_service_approval_"
                    "return_obstruction_notice"
                ),
                "sources": source_documents[:3],
            }

        # 반품 시 상품 가격의 일정 비율을 위약금으로
        # 공제하는 문구는 일반 표시광고와 반품 비용 문구보다
        # 먼저 처리하고 제18조·제35조를 반환한다.
        penalty_percentage = extract_return_penalty_percentage(
            question
        )

        if (
            matches_return_penalty_deduction
            and penalty_percentage is not None
            and ad_copy is not None
        ):
            source_documents = ensure_return_penalty_sources(
                source_candidates
            )

            answer = build_return_penalty_deduction_notice_answer(
                ad_copy=ad_copy,
                percentage=penalty_percentage,
                copy_label=copy_label,
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "return_penalty_deduction_notice",
                "sources": select_return_penalty_sources(
                    source_documents
                )[:2],
            }

        # 반품 시 상품 가격의 일정 비율을 위약금으로
    # 공제하는 일반 문구도 제18조·제35조로 답한다.
    if matches_return_penalty_deduction:
        penalty_percentage = extract_return_penalty_percentage(
            question
        )

        if penalty_percentage is not None:
            source_documents = ensure_return_penalty_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )

            ad_copy = (
                extract_explicit_ad_copy(question)
                or question.strip()
            )

            answer = build_return_penalty_deduction_notice_answer(
                ad_copy=ad_copy,
                percentage=penalty_percentage,
                copy_label=detect_explicit_copy_label(question),
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "return_penalty_deduction_notice",
                "sources": select_return_penalty_sources(
                    source_documents
                )[:2],
            }

    # 결제 취소·금전 환급 대신 적립금 지급만을
        # 강제하는 문구는 일반 표시광고 및 품절 적립금 문구보다
        # 먼저 처리하고 제18조·제35조를 반환한다.
        if (
            matches_forced_store_credit_refund
            and ad_copy is not None
        ):
            source_documents = ensure_refund_delay_notice_sources(
                source_candidates
            )

            answer = build_forced_store_credit_refund_notice_answer(
                ad_copy=ad_copy,
                copy_label=copy_label,
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "forced_store_credit_refund_notice",
                "sources": select_refund_delay_notice_sources(
                    source_documents
                )[:2],
            }

        # 품절 상품의 결제대금을 적립금으로만 처리하는 문구는
        # 전자상거래법 제15조를 일반 광고 검토보다 우선 적용한다.
        if (
            matches_stockout_store_credit_only
            and ad_copy is not None
        ):
            source_documents = ensure_stockout_refund_sources(
                source_candidates
            )

            answer = build_stockout_store_credit_only_notice_answer(
                ad_copy=ad_copy,
                copy_label=copy_label,
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "stockout_store_credit_only_notice",
                "sources": select_stockout_refund_sources(
                    source_documents
                )[:1],
            }

        # 반품 상품의 환급 기한을 법정 3영업일보다 길게
        # 정한 문구는 제18조·제35조를 일반 광고 검토보다
        # 우선 적용한다.
        refund_delay_days = extract_excessive_refund_delay_days(
            question
        )

        if (
            matches_excessive_refund_delay_notice
            and refund_delay_days is not None
            and ad_copy is not None
        ):
            source_documents = ensure_refund_delay_notice_sources(
                source_candidates
            )

            answer = build_excessive_refund_delay_notice_answer(
                ad_copy=ad_copy,
                days=refund_delay_days,
                copy_label=copy_label,
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "excessive_refund_delay_notice",
                "sources": select_refund_delay_notice_sources(
                    source_documents
                )[:2],
            }

        # 실제 치수가 상세페이지 치수와 다른 경우에도
        # 교환만 허용하거나 환불을 금지하는 문구는 일반 불일치와
        # 표시광고 답변보다 먼저 처리하고 제17조·제18조·제35조를
        # 반환한다.
        if (
            matches_actual_measurement_mismatch_exchange_only
            and ad_copy is not None
        ):
            source_documents = (
                ensure_discounted_return_prohibition_sources(
                    source_candidates
                )
            )

            answer = (
                build_actual_measurement_mismatch_exchange_only_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "actual_measurement_mismatch_"
                    "exchange_only_notice"
                ),
                "sources": source_documents[:3],
            }

        # 실제 치수가 상세페이지 치수와 다른 경우에도
    # 교환만 허용하거나 환불을 금지하는 일반 문구는
    # 제17조·제18조·제35조로 답한다.
    if matches_actual_measurement_mismatch_exchange_only:
        source_documents = (
            ensure_discounted_return_prohibition_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_actual_measurement_mismatch_exchange_only_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "actual_measurement_mismatch_"
                "exchange_only_notice"
            ),
            "sources": source_documents[:3],
        }

    # 화면 표시 색상과 실제 상품 색상이 다른 경우에도
        # 환불을 금지하는 문구는 일반 불일치·반품 전면 금지보다
        # 먼저 처리하고 제17조·제18조·제35조를 반환한다.
        if (
            matches_screen_color_mismatch_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_discounted_return_prohibition_sources(
                    source_candidates
                )
            )

            answer = (
                build_screen_actual_color_mismatch_refund_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "screen_actual_color_mismatch_"
                    "refund_prohibition_notice"
                ),
                "sources": source_documents[:3],
            }

        # 상품 설명·광고 또는 계약 내용과 다른 경우의
        # 환불을 금지하는 문구는 제17조제3항과 제18조를
        # 일반적인 과장광고·반품 전면 금지보다 우선 적용한다.
        if (
            matches_mismatch_refund_prohibition
            and ad_copy is not None
        ):
            source_documents = ensure_mismatch_refund_sources(
                source_candidates
            )

            answer = (
                build_mismatch_refund_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "mismatch_refund_prohibition_notice"
                ),
                "sources": select_mismatch_refund_sources(
                    source_documents
                )[:2],
            }

        # 불량 상품의 동일 상품 교환만 허용하고 환불을
        # 전면 금지하는 문구는 일반 반품 금지보다 먼저 처리하고,
        # 제17조·제18조·제35조 근거를 반환한다.
        if (
            matches_defective_exchange_only_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_discounted_return_prohibition_sources(
                    source_candidates
                )
            )

            answer = (
                build_defective_exchange_only_refund_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "defective_product_exchange_only_"
                    "refund_prohibition_notice"
                ),
                "sources": source_documents[:3],
            }

        # 흰색·아이보리 등 밝은 색상만으로 모든 반품을
        # 제한하는 문구는 일반적인 반품 전면 금지보다 먼저 처리하고,
        # 전자상거래법 제17조·제35조 근거를 반환한다.
        if (
            matches_light_color_return_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_short_return_period_sources(
                    source_candidates
                )
            )

            answer = (
                build_light_color_product_return_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "light_color_product_return_prohibition_notice"
                ),
                "sources": source_documents[:2],
            }

        # 착용·시착 사실만으로 모든 반품을 제한하는 문구는
        # 일반적인 반품 전면 금지보다 먼저 처리하고,
        # 전자상거래법 제17조·제35조 근거를 반환한다.
        if (
            matches_worn_product_return_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_short_return_period_sources(
                    source_candidates
                )
            )

            answer = (
                build_worn_product_return_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "worn_product_return_prohibition_notice",
                "sources": source_documents[:2],
            }

        # 택·태그·라벨 제거만으로 모든 반품을 제한하는
        # 문구는 일반적인 반품 전면 금지보다 먼저 처리하고,
        # 전자상거래법 제17조·제35조 근거를 반환한다.
        if (
            matches_tag_removed_return_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_short_return_period_sources(
                    source_candidates
                )
            )

            answer = (
                build_tag_removed_return_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "tag_removed_return_prohibition_notice",
                "sources": source_documents[:2],
            }

        # 포장 개봉만으로 모든 반품을 제한하는 문구는
        # 일반적인 반품 전면 금지보다 구체적인 제17조제2항의
        # 포장 확인 예외를 우선 적용한다.
        if (
            matches_opened_package_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_short_return_period_sources(
                    source_candidates
                )
            )

            answer = (
                build_opened_package_return_prohibition_notice_answer(
                    ad_copy=ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "opened_package_return_prohibition_notice"
                ),
                "sources": source_documents[:2],
            }

        # 법정 7일보다 짧은 반품·청약철회 기간 문구는
        # 표시광고법의 일반 답변보다 전자상거래법 제17조·제35조를
        # 우선 적용한다.
        short_return_details = (
            extract_short_return_period_details(
                question
            )
        )

        if (
            matches_short_return_period
            and short_return_details is not None
            and ad_copy is not None
        ):
            _, short_return_period_label = (
                short_return_details
            )

            source_documents = (
                ensure_short_return_period_sources(
                    source_candidates
                )
            )

            answer = build_short_return_period_notice_answer(
                ad_copy=ad_copy,
                period_label=short_return_period_label,
                copy_label=copy_label,
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "short_return_period_notice",
                "sources": source_documents[:2],
            }

        # 모든 상품의 반품·환불을 일률적으로 금지하는 문구는
        # 일반 표시광고 답변보다 전자상거래법상 청약철회·환급
        # 기준을 우선 적용하고 제17조·제18조·제35조를 반환한다.
        if (
            matches_blanket_return_prohibition
            and ad_copy is not None
        ):
            source_documents = (
                ensure_discounted_return_prohibition_sources(
                    source_candidates
                )
            )

            answer = (
                build_blanket_return_prohibition_ad_copy_answer(
                    ad_copy,
                    copy_label=copy_label,
                )
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": (
                    "ad_copy_blanket_return_refund_prohibition"
                ),
                "sources": source_documents[:3],
            }

        matches_domestic_sales_rank_ad_copy = (
            ad_copy is not None
            and is_domestic_sales_rank_ad_copy(
                ad_copy
            )
        )

        matches_comparative_multiplier_ad_copy = (
            ad_copy is not None
            and is_comparative_multiplier_ad_copy(
                ad_copy
            )
        )

        matches_numeric_waist_appearance_ad_copy = (
            ad_copy is not None
            and is_universal_numeric_waist_appearance_ad_copy(
                ad_copy
            )
        )

        matches_laundry_shrinkage_ad_copy = (
            ad_copy is not None
            and is_laundry_shrinkage_ad_copy(
                ad_copy
            )
        )

        matches_natural_material_ad_copy = (
            ad_copy is not None
            and is_full_natural_material_ad_copy(
                ad_copy
            )
        )

        matches_free_shipping_ad_copy = (
            ad_copy is not None
            and is_unconditional_free_shipping_ad_copy(
                ad_copy
            )
        )

        if matches_domestic_sales_rank_ad_copy:
            source_documents = (
                ensure_product_performance_claim_sources(
                    source_candidates
                )
            )
        elif matches_comparative_multiplier_ad_copy:
            source_documents = (
                ensure_product_performance_claim_sources(
                    source_candidates
                )
            )
        elif matches_numeric_waist_appearance_ad_copy:
            source_documents = (
                ensure_product_performance_claim_sources(
                    source_candidates
                )
            )
        elif matches_laundry_shrinkage_ad_copy:
            source_documents = (
                ensure_product_performance_claim_sources(
                    source_candidates
                )
            )
        elif matches_natural_material_ad_copy:
            source_documents = ensure_natural_material_sources(
                source_candidates
            )
        elif matches_free_shipping_ad_copy:
            source_documents = ensure_free_shipping_ad_copy_sources(
                source_candidates
            )
        else:
            source_documents = select_platform_expression_sources(
                source_candidates
            )

            if len(source_documents) < 2:
                supplement_result = search_documents(
                    question=(
                        "표시광고법 제3조 부당한 표시 광고 행위의 금지 "
                        "소비자를 속이거나 잘못 알게 할 우려가 있는 "
                        "거짓 과장 표시 광고와 기만적인 표시 광고"
                    ),
                    top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
                )

                supplement_documents = sanitize_source_documents(
                    supplement_result.get("documents", [])
                )

                source_documents = select_platform_expression_sources(
                    [
                        *source_candidates,
                        *supplement_documents,
                    ]
                )

        if ad_copy is None:
            answer = build_missing_ad_copy_assessment_answer()
            intent = "ad_copy_assessment_missing_text"
        else:
            answer = build_explicit_ad_copy_assessment_answer(
                ad_copy,
                copy_label=copy_label,
            )
            if matches_domestic_sales_rank_ad_copy:
                intent = (
                    "ad_copy_domestic_sales_rank_claim"
                )
            elif matches_comparative_multiplier_ad_copy:
                intent = (
                    "ad_copy_comparative_multiplier_claim"
                )
            elif matches_numeric_waist_appearance_ad_copy:
                intent = (
                    "ad_copy_numeric_waist_appearance_claim"
                )
            elif matches_laundry_shrinkage_ad_copy:
                intent = (
                    "ad_copy_laundry_shrinkage_claim"
                )
            elif matches_natural_material_ad_copy:
                intent = (
                    "ad_copy_natural_material_composition"
                )
            elif matches_free_shipping_ad_copy:
                intent = (
                    "ad_copy_unconditional_free_shipping"
                )
            else:
                intent = "ad_copy_assessment"

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": intent,
            "sources": (
                select_product_performance_claim_sources(
                    source_documents
                )[:2]
                if matches_domestic_sales_rank_ad_copy
                else (
                    select_product_performance_claim_sources(
                        source_documents
                    )[:2]
                    if matches_comparative_multiplier_ad_copy
                    else (
                        select_product_performance_claim_sources(
                            source_documents
                        )[:2]
                        if matches_numeric_waist_appearance_ad_copy
                        else (
                            select_product_performance_claim_sources(
                                source_documents
                            )[:2]
                            if matches_laundry_shrinkage_ad_copy
                            else (
                                select_natural_material_sources(
                                    source_documents
                                )[:2]
                                if matches_natural_material_ad_copy
                                else (
                                    select_free_shipping_ad_copy_sources(
                                        source_documents
                                    )[:1]
                                    if matches_free_shipping_ad_copy
                                    else source_documents[:2]
                                )
                            )
                        )
                    )
                )
            ),
        }

    # 실제 광고 문구 없이 과장광고 여부만 묻는 경우에는
    # 임의로 위법 여부를 판단하지 않고 문구 입력을 요청한다.
    if matches_missing_ad_copy_assessment:
        raw_source_documents = sanitize_source_documents(
            initial_documents
        )

        source_documents = select_platform_expression_sources(
            [
                *raw_source_documents,
                *searched_documents,
                *relevant_documents,
            ]
        )

        answer = build_missing_ad_copy_assessment_answer()

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "ad_copy_assessment_missing_text",
            "sources": source_documents[:2],
        }

    # 특정 플랫폼의 제한 표현 질문은 플랫폼 내부정책을
    # 법률 문서만으로 단정하지 않고, 법률상 금지 표현을 안내한다.
    if matches_platform_restricted_expression:
        raw_source_documents = sanitize_source_documents(
            initial_documents
        )

        source_candidates = [
            *raw_source_documents,
            *searched_documents,
            *relevant_documents,
        ]

        source_documents = select_platform_expression_sources(
            source_candidates
        )

        # 직접 근거가 부족하면 핵심 법 조항을 한 번 보충 검색한다.
        if len(source_documents) < 2:
            supplement_result = search_documents(
                question=(
                    "표시광고법 제3조 부당한 표시 광고 행위의 금지 "
                    "거짓 과장 기만 부당 비교 비방 광고, "
                    "전자상거래법 제21조 금지행위 거짓 과장 "
                    "기만적인 방법 소비자 유인 청약철회 방해"
                ),
                top_k=PLATFORM_EXPRESSION_SEARCH_TOP_K,
            )

            supplement_documents = sanitize_source_documents(
                supplement_result.get("documents", [])
            )

            source_documents = select_platform_expression_sources(
                [
                    *source_candidates,
                    *supplement_documents,
                ]
            )

        answer = build_platform_restricted_expression_answer(
            extract_platform_name(question)
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "platform_restricted_expression",
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
                generator=streaming_generator,
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

    # 주문제작 상품 질문은 현재 업로드된 본법 근거만 사용한다.
    # 시행령을 사용하지 않으므로 제17조와 제35조를 직접 반환하고,
    # 제18조가 잘못 선택되는 것을 차단한다.
    if is_custom_made_return_question(question):
        source_documents = ensure_custom_made_return_sources(
            [
                *searched_documents,
                *relevant_documents,
            ]
        )

        answer = build_custom_made_return_answer()

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "custom_made_return",
            "sources": source_documents[:2],
        }

    # 결제 취소·금전 환급 대신 적립금 지급만을
    # 강제하는 일반 문구도 제18조·제35조로 답한다.
    if matches_forced_store_credit_refund:
        source_documents = ensure_refund_delay_notice_sources(
            [
                *searched_documents,
                *relevant_documents,
            ]
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = build_forced_store_credit_refund_notice_answer(
            ad_copy=ad_copy,
            copy_label=detect_explicit_copy_label(question),
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "forced_store_credit_refund_notice",
            "sources": select_refund_delay_notice_sources(
                source_documents
            )[:2],
        }

    # 품절 상품의 결제대금을 적립금으로만 처리하는
    # 일반 문구도 전자상거래법 제15조로 답한다.
    if matches_stockout_store_credit_only:
        stockout_source_candidates = [
            *searched_documents,
            *relevant_documents,
        ]

        source_documents = ensure_stockout_refund_sources(
            stockout_source_candidates
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = build_stockout_store_credit_only_notice_answer(
            ad_copy=ad_copy,
            copy_label=detect_explicit_copy_label(question),
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "stockout_store_credit_only_notice",
            "sources": select_stockout_refund_sources(
                source_documents
            )[:1],
        }

    # 반품 상품 환급 기한을 법정 기준보다 길게 정한
    # 일반 문구도 제18조·제35조로 답한다.
    if matches_excessive_refund_delay_notice:
        refund_delay_days = extract_excessive_refund_delay_days(
            question
        )

        if refund_delay_days is not None:
            refund_delay_candidates = [
                *searched_documents,
                *relevant_documents,
            ]

            source_documents = ensure_refund_delay_notice_sources(
                refund_delay_candidates
            )

            ad_copy = (
                extract_explicit_ad_copy(question)
                or question.strip()
            )

            answer = build_excessive_refund_delay_notice_answer(
                ad_copy=ad_copy,
                days=refund_delay_days,
                copy_label=detect_explicit_copy_label(question),
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "excessive_refund_delay_notice",
                "sources": select_refund_delay_notice_sources(
                    source_documents
                )[:2],
            }

    # 화면 표시 색상과 실제 상품 색상이 다른 경우에도
    # 환불을 금지하는 일반 문구는 제17조·제18조·제35조로 답한다.
    if matches_screen_color_mismatch_prohibition:
        source_documents = (
            ensure_discounted_return_prohibition_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_screen_actual_color_mismatch_refund_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "screen_actual_color_mismatch_"
                "refund_prohibition_notice"
            ),
            "sources": source_documents[:3],
        }

    # 상품 설명·광고 또는 계약 내용과 다른 경우의 환불을
    # 금지하는 일반 문구도 제17조제3항과 제18조로 답한다.
    if matches_mismatch_refund_prohibition:
        mismatch_source_candidates = [
            *searched_documents,
            *relevant_documents,
        ]

        source_documents = ensure_mismatch_refund_sources(
            mismatch_source_candidates
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_mismatch_refund_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "mismatch_refund_prohibition_notice",
            "sources": select_mismatch_refund_sources(
                source_documents
            )[:2],
        }

    # 흰색·아이보리 등 밝은 색상만으로 반품을 제한하는
    # 일반 문구도 실제 오염·훼손 기준과 제35조를 적용해 답한다.
    if matches_light_color_return_prohibition:
        source_documents = (
            ensure_short_return_period_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_light_color_product_return_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "light_color_product_return_prohibition_notice"
            ),
            "sources": source_documents[:2],
        }

    # 착용·시착 사실만으로 반품을 제한하는 일반 문구도
    # 제17조의 현저한 가치 감소 기준과 제35조를 적용해 답한다.
    if matches_worn_product_return_prohibition:
        source_documents = (
            ensure_short_return_period_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_worn_product_return_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "worn_product_return_prohibition_notice",
            "sources": source_documents[:2],
        }

    # 택·태그·라벨 제거만으로 반품을 제한하는 일반 문구도
    # 제17조의 훼손·가치 감소 기준과 제35조를 적용해 답한다.
    if matches_tag_removed_return_prohibition:
        source_documents = (
            ensure_short_return_period_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_tag_removed_return_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "tag_removed_return_prohibition_notice",
            "sources": source_documents[:2],
        }

    # 포장 개봉만으로 모든 반품을 제한하는 일반 문구도
    # 제17조의 포장 확인 예외와 제35조를 적용해 구체적으로 답한다.
    if matches_opened_package_prohibition:
        source_documents = (
            ensure_short_return_period_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_opened_package_return_prohibition_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "opened_package_return_prohibition_notice",
            "sources": source_documents[:2],
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

    # 반품·청약철회 기간을 법정 기간보다 짧게 제한하는
    # 일반 질문도 검증된 답변과 전자상거래법 근거를 반환한다.
    if matches_short_return_period:
        short_return_details = (
            extract_short_return_period_details(
                question
            )
        )

        if short_return_details is not None:
            _, short_return_period_label = (
                short_return_details
            )

            source_documents = (
                ensure_short_return_period_sources(
                    [
                        *searched_documents,
                        *relevant_documents,
                    ]
                )
            )

            ad_copy = (
                extract_explicit_ad_copy(question)
                or question.strip()
            )

            answer = build_short_return_period_notice_answer(
                ad_copy=ad_copy,
                period_label=short_return_period_label,
                copy_label=detect_explicit_copy_label(question),
            )

            if on_token is not None:
                on_token(answer)

            return {
                "question": question,
                "answer": answer,
                "intent": "short_return_period_notice",
                "sources": source_documents[:2],
            }

    # 상품 상세페이지나 약관에 일률적인 반품·환불 불가 문구를
    # 표시할 수 있는지 묻는 일반 질문도 검증된 답변과
    # 제17조·제18조·제35조 근거를 반환한다.
    if matches_blanket_return_prohibition:
        source_documents = (
            ensure_discounted_return_prohibition_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        extracted_ad_copy = extract_explicit_ad_copy(
            question
        )

        if extracted_ad_copy is not None:
            answer = (
                build_blanket_return_prohibition_ad_copy_answer(
                    extracted_ad_copy,
                    copy_label=detect_explicit_copy_label(
                        question
                    ),
                )
            )
        else:
            answer = (
                build_blanket_return_prohibition_notice_answer()
            )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": "blanket_return_prohibition",
            "sources": source_documents[:3],
        }

    # 판매자와 사전 통화·연락하지 않았다는 이유만으로
    # 환불을 거절하는 일반 문구도 전용 답변으로 처리한다.
    if matches_seller_contact_return_obstruction:
        source_documents = (
            ensure_customer_service_obstruction_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = (
            extract_explicit_ad_copy(question)
            or question.strip()
        )

        answer = (
            build_seller_contact_required_return_obstruction_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "seller_contact_required_"
                "return_obstruction_notice"
            ),
            "sources": source_documents[:3],
        }

    # 고객센터 전화 접수만 인정하거나 판매자 승인 전까지
    # 반품을 인정하지 않는 일반 질문도 전용 답변으로 처리한다.
    if matches_customer_service_return_obstruction:
        source_documents = (
            ensure_customer_service_obstruction_sources(
                [
                    *searched_documents,
                    *relevant_documents,
                ]
            )
        )

        ad_copy = extract_explicit_ad_copy(question) or question.strip()

        answer = (
            build_customer_service_approval_return_obstruction_notice_answer(
                ad_copy=ad_copy,
                copy_label=detect_explicit_copy_label(question),
            )
        )

        if on_token is not None:
            on_token(answer)

        return {
            "question": question,
            "answer": answer,
            "intent": (
                "customer_service_approval_"
                "return_obstruction_notice"
            ),
            "sources": source_documents[:3],
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
                generator=streaming_generator,
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
                generator=streaming_generator,
            )
        except Exception:
            hybrid_answer = build_wrong_item_return_cost_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        display_sources = ensure_return_cost_excerpt_sources(
            source_documents
        )

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "wrong_item_return_cost",
            "sources": (
                display_sources[:1]
                if display_sources
                else source_documents
            ),
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
                generator=streaming_generator,
            )
        except Exception:
            hybrid_answer = (
                build_carrier_blame_return_cost_answer()
            )

        hybrid_answer = clean_answer(hybrid_answer)

        display_sources = ensure_return_cost_excerpt_sources(
            source_documents
        )

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "carrier_blame_return_cost",
            "sources": (
                display_sources[:1]
                if display_sources
                else source_documents
            ),
        }

    # 불량·하자 상품의 반품 배송비 질문은 일반 반품비 질문보다
    # 먼저 처리하여 판매자 부담이라는 결론부터 안내한다.
    if matches_defective_product_return_cost:
        source_candidates = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        source_documents = ensure_return_cost_excerpt_sources(
            source_candidates
        )

        return {
            "question": question,
            "answer": build_defective_product_return_cost_answer(),
            "intent": "defective_product_return_cost",
            "sources": (
                source_documents[:1]
                if source_documents
                else source_candidates
            ),
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
                generator=streaming_generator,
            )
        except Exception:
            hybrid_answer = build_return_cost_answer()

        hybrid_answer = clean_answer(hybrid_answer)

        display_sources = ensure_return_cost_excerpt_sources(
            source_documents
        )

        return {
            "question": question,
            "answer": hybrid_answer,
            "intent": "return_cost",
            "sources": (
                display_sources[:1]
                if display_sources
                else source_documents
            ),
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
        display_sources = ensure_return_cost_excerpt_sources(
            relevant_documents
        )

        return {
            "question": question,
            "answer": build_return_cost_answer(),
            "intent": intent,
            "sources": (
                display_sources[:1]
                if display_sources
                else relevant_documents
            ),
        }

    prompt = build_prompt(
        question=question,
        documents=relevant_documents,
    )

    (
        _,
        _,
        _,
        num_predict,
    ) = _resolve_context_limits(question)

    answer = generate_answer(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        num_predict=num_predict,
        on_token=on_token,
    )

    answer = clean_answer(answer)

    return {
        "question": question,
        "answer": answer,
        "intent": intent,
        "sources": relevant_documents,
    }