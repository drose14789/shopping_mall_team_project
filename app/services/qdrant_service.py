from __future__ import annotations

from typing import Any

from search_qdrant import (
    PARENT_FILE,
    RESULT_LIMIT,
    load_services,
    read_parents,
    search,
)


_parents: dict[str, dict[str, Any]] | None = None
_client: Any | None = None
_embedder: Any | None = None
_reranker: Any | None = None


RETURN_COST_TERMS = (
    "반품비",
    "반품 비용",
    "반품 배송비",
    "반송비",
    "반송 비용",
    "반환 비용",
    "배송비 누가",
    "택배비 누가",
    "누가 부담",
)


def initialize_qdrant_service() -> None:
    """검색 데이터와 모델을 최초 한 번만 불러온다."""
    global _parents, _client, _embedder, _reranker

    if all(
        value is not None
        for value in (
            _parents,
            _client,
            _embedder,
            _reranker,
        )
    ):
        return

    print("[Qdrant Service] 부모 청크 로딩 중...")
    _parents = read_parents(PARENT_FILE)

    print("[Qdrant Service] 검색 모델 로딩 중...")
    _client, _embedder, _reranker = load_services()

    print("[Qdrant Service] 초기화 완료")


def is_return_cost_question(question: str) -> bool:
    """반품 비용 부담에 관한 질문인지 확인한다."""
    normalized_question = question.replace(" ", "")

    return any(
        term.replace(" ", "") in normalized_question
        for term in RETURN_COST_TERMS
    )


def is_return_cost_law(result: dict[str, Any]) -> bool:
    """반품 비용의 일반적인 법적 부담 기준 문서인지 확인한다."""
    text = " ".join(
        [
            str(result.get("heading", "")),
            str(result.get("source_file", "")),
            str(result.get("child_content", "")),
            str(result.get("parent_content", "")),
        ]
    )

    has_cost_rule = any(
        term in text
        for term in (
            "반환에 필요한 비용",
            "재화등의 반환에 필요한 비용",
            "재화 등의 반환에 필요한 비용",
        )
    )

    has_cost_owner = any(
        term in text
        for term in (
            "소비자가 부담",
            "통신판매업자가 부담",
            "사업자가 부담",
        )
    )

    is_specific_example = any(
        term in text
        for term in (
            "해외구매대행",
            "통관 제비용",
            "$",
            "달러",
        )
    )

    return (
        has_cost_rule
        and has_cost_owner
        and not is_specific_example
    )


def format_documents(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """검색 결과를 API 반환 형식으로 정리한다."""
    documents: list[dict[str, Any]] = []

    for rank, result in enumerate(results, start=1):
        documents.append(
            {
                "rank": rank,
                "heading": result["heading"],
                "source_file": result["source_file"],
                "parent_id": result["parent_id"],
                "child_content": result["child_content"],
                "parent_content": result["parent_content"],
                "dense_score": float(result["dense_score"]),
                "rerank_score": float(result["rerank_score"]),
                "rank_group": result.get(
                    "rank_group",
                    "reranker",
                ),
                "retrieved_by": list(
                    result.get("retrieved_by", [])
                ),
            }
        )

    return documents


def search_documents(
    question: str,
    top_k: int = RESULT_LIMIT,
) -> dict[str, Any]:
    """질문과 관련된 법률 문서를 검색한다."""
    question = " ".join(question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    if top_k < 1:
        raise ValueError("top_k는 1 이상이어야 합니다.")

    initialize_qdrant_service()

    if any(
        value is None
        for value in (
            _parents,
            _client,
            _embedder,
            _reranker,
        )
    ):
        raise RuntimeError(
            "Qdrant 검색 서비스 초기화에 실패했습니다."
        )

    # 반품 비용 질문은 일반 질문과 다른 법률 검색문을 사용한다.
    if is_return_cost_question(question):
        legal_question = (
            f"{question}\n"
            "전자상거래 등에서의 소비자보호에 관한 법률 "
            "제18조 청약철회등의 효과. "
            "재화등의 반환에 필요한 비용은 소비자가 부담한다. "
            "재화등의 내용이 표시 광고 내용과 다르거나 "
            "계약내용과 다르게 이행된 경우 반환 비용은 "
            "통신판매업자가 부담한다."
        )

        results, _ = search(
            client=_client,
            embedder=_embedder,
            reranker=_reranker,
            parents=_parents,
            question=legal_question,
            limit=20,
        )

        results = [
            result
            for result in results
            if is_return_cost_law(result)
        ]

        # 법률 문서를 찾지 못하면 특정 사례를 대신 반환하지 않는다.
        results = results[:top_k]

        return {
            "question": question,
            "intent": "return_cost",
            "documents": format_documents(results),
        }

    # 다른 질문은 기존 검색 방식 그대로 사용한다.
    results, plan = search(
        client=_client,
        embedder=_embedder,
        reranker=_reranker,
        parents=_parents,
        question=question,
        limit=top_k,
    )

    return {
        "question": plan.question,
        "intent": plan.intent,
        "documents": format_documents(results),
    }