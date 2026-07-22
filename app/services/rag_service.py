from __future__ import annotations

import re
from typing import Any

from app.services.ollama_service import generate_answer
from app.services.qdrant_service import search_documents


SEARCH_TOP_K = 5
MAX_CONTEXT_DOCUMENTS = 3
MIN_RERANK_SCORE = 0.1
RELATIVE_SCORE_RATIO = 0.25
MAX_DOCUMENT_LENGTH = 4000


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
    """
    상품 설명 불일치 반품 기한 질문에 사용할 검증된 답변이다.

    검색 결과는 sources로 그대로 반환하고, 기간을 Ollama가
    잘못 조합하지 않도록 답변 문장만 통제한다.
    """
    return (
        "상품이 표시·광고 내용과 다르거나 계약 내용과 다르게 "
        "이행된 경우에는 상품을 공급받은 날부터 3개월 이내이면서, "
        "그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 "
        "청약철회를 해야 합니다.\n\n"
        "두 기간 중 어느 하나라도 지나면 청약철회가 어려울 수 "
        "있으므로, 상품의 불일치를 확인한 뒤 가능한 한 빨리 "
        "판매자에게 반품 의사를 알리는 것이 좋습니다."
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
    """
    반품 방해 질문은 금지행위를 허용행위로 반대로 설명하지 않도록
    검증된 문장으로 반환한다.
    """
    return (
        "쇼핑몰은 거짓 또는 과장된 사실을 알리거나 기만적인 "
        "방법을 사용하여 소비자의 청약철회나 계약 해지를 "
        "방해해서는 안 됩니다.\n\n"
        "반품 절차를 고의로 어렵게 만들거나, 정당한 근거 없이 "
        "추가 비용을 요구하여 소비자가 반품을 포기하도록 만드는 "
        "행위도 청약철회를 방해하는 행위에 해당할 수 있습니다. "
        "이런 경우에는 반품 요청 내역과 안내 화면, 상담 기록 등을 "
        "보관해 두는 것이 좋습니다."
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


def is_business_seller_info_question(question: str) -> bool:
    """사업자 판매자의 신원정보 제공 질문과 자연어 변형을 확인한다."""
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

    platform_terms = (
        "플랫폼",
        "오픈마켓",
        "쇼핑몰",
        "통신판매중개",
        "마켓",
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


def is_return_cost_question(question: str) -> bool:
    """반품 배송비 부담 주체를 묻는 자연어 질문을 확인한다."""
    normalized = normalize_text(question)

    return_terms = (
        "반품",
        "청약철회",
        "돌려보",
        "돌려주",
        "환불",
    )

    cost_terms = (
        "반품비",
        "반품배송비",
        "배송비",
        "택배비",
        "반환비용",
        "반송비",
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
    """반품 배송비 부담 원칙을 검증된 문장으로 반환한다."""
    return (
        "마음에 들지 않는다는 이유의 단순 변심 반품이라면, "
        "상품을 반환하는 데 필요한 택배비는 소비자가 부담합니다.\n\n"
        "다만 상품이 표시·광고 내용과 다르거나 계약 내용과 다르게 "
        "이행된 경우에는 판매자가 반환 비용을 부담합니다. "
        "판매자는 단순 변심 반품에 대해 반환 비용 외의 별도 "
        "위약금이나 손해배상을 청구할 수 없습니다."
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

    # 자연어 변형 질문은 검색 전에 표준 질문으로 변환한다.
    # 사용자에게 표시되는 원래 질문은 그대로 유지한다.
    search_question = question

    if is_mismatch_deadline_question(question):
        search_question = (
            "상품 설명과 실제 상품이 다르면 "
            "언제까지 반품할 수 있나요?"
        )
    elif is_return_obstruction_question(question):
        search_question = "쇼핑몰이 반품을 방해하면 어떻게 되나요?"
    elif is_business_seller_info_question(question):
        search_question = (
            "플랫폼은 판매자 정보를 소비자에게 "
            "제공해야 하나요?"
        )
    elif is_return_cost_question(question):
        search_question = "반품 배송비는 누가 부담하나요?"
    elif is_change_of_mind_return_question(question):
        search_question = "단순 변심으로도 반품할 수 있나요?"

    search_result = search_documents(
        question=search_question,
        top_k=SEARCH_TOP_K,
    )

    searched_documents = search_result["documents"]
    intent = search_result.get("intent")

    relevant_documents = select_relevant_documents(
        searched_documents
    )

    # 상품 불일치 변형 질문은 점수 필터 결과가 비어 있어도
    # 이미 검증된 기한 답변을 반환한다.
    if is_mismatch_deadline_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_mismatch_deadline_answer(),
            "intent": "mismatch_return_deadline",
            "sources": source_documents,
        }

    # 반품 방해 변형 질문은 점수 필터 결과가 비어 있어도
    # 이미 검증된 금지행위 답변을 반환한다.
    if is_return_obstruction_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_return_obstruction_answer(),
            "intent": "return_obstruction",
            "sources": source_documents,
        }

    # 판매자 신원정보 변형 질문은 점수 필터 결과가 비어 있어도
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

    # 반품비 변형 질문은 해외구매대행 사례 등이 섞이지 않도록
    # 점수 필터 결과와 관계없이 검증된 답변을 반환한다.
    if is_return_cost_question(question):
        source_documents = (
            relevant_documents
            if relevant_documents
            else searched_documents[:MAX_CONTEXT_DOCUMENTS]
        )

        return {
            "question": question,
            "answer": build_return_cost_answer(),
            "intent": "return_cost",
            "sources": source_documents,
        }

    # 단순 변심 변형 질문은 점수 필터 결과가 비어 있어도
    # 이미 검증된 답변을 반환한다.
    if is_change_of_mind_return_question(question):
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