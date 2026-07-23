from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PARENT_FILE = Path(r"C:\yolo\llm\data\chunks\documents.parents.jsonl")
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "legal_chunks"
EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
CANDIDATES_PER_QUERY = 30
RERANK_LIMIT = 50
RESULT_LIMIT = 5
RERANK_BATCH_SIZE = 4
RERANK_MAX_LENGTH = 512
DEVICE: str | None = None


@dataclass(frozen=True)
class QueryVariant:
    name: str
    text: str


@dataclass(frozen=True)
class SearchPlan:
    question: str
    rerank_question: str
    intent: str | None
    variants: tuple[QueryVariant, ...]


BASE_RULES = (
    (
        ("품절", "재고 없음", "재고가 없"),
        ("재화등을 공급하지 아니한 경우", "재화 미공급"),
    ),
    (
        ("환불", "결제 취소"),
        ("대금 환급", "재화등의 대금을 환급"),
    ),
    (
        ("반품", "구매 취소", "주문 취소"),
        ("청약철회등", "재화등 반환"),
    ),
    (
        (
            "상품 설명과 실제 상품이 다르",
            "설명과 실제가 다르",
            "설명과 다르",
            "광고와 다르",
            "표시와 다르",
            "사진과 다르",
        ),
        (
            "재화등의 내용이 표시 광고 내용과 다르거나",
            "계약내용과 다르게 이행된 때",
        ),
    ),
    (
        ("반품을 방해", "반품 방해", "환불을 방해", "취소를 방해"),
        ("청약철회등을 방해하는 행위", "금지행위"),
    ),
    (
        ("반품비", "반품 비용", "반환 비용", "배송비 누가", "택배비 누가"),
        ("재화등의 반환에 필요한 비용", "반환 비용 부담"),
    ),
)

PLATFORM_TERMS = (
    "플랫폼",
    "오픈마켓",
    "마켓플레이스",
    "중개사이트",
    "통신판매중개",
)

SELLER_INFO_TERMS = (
    "판매자 정보",
    "판매자정보",
    "판매자의 정보",
    "판매자 정보를",
    "사업자 정보",
    "사업자정보",
    "사업자의 정보",
    "사업자 정보를",
    "판매자 신원",
    "판매자의 신원",
    "판매자 연락처",
    "판매자의 연락처",
    "판매자가 누구",
)

SELLER_TERMS = (
    "판매자",
    "사업자",
)

SELLER_DETAIL_TERMS = (
    "정보",
    "신원",
    "연락처",
    "주소",
    "전화번호",
    "성명",
)

PERSONAL_TERMS = (
    "개인 판매자",
    "개인판매자",
    "개인 간 거래",
    "개인간 거래",
    "중고 거래",
    "중고거래",
    "개인이 판매",
)

PERSONAL_SCOPE_TERMS = (
    "사업자가 아닌 개인",
    "개인 판매자",
    "개인 간 거래",
    "제20조의4",
)

SIMPLE_CHANGE_TERMS = (
    "단순 변심",
    "단순변심",
    "마음이 바뀌",
    "그냥 반품",
)

RETURN_TERMS = (
    "반품",
    "청약철회",
    "구매 취소",
    "주문 취소",
)

SIMPLE_CHANGE_DOCUMENT_TYPE_BONUS = {
    "law": 0.06,
    "standard_terms": 0.04,
    "guideline": 0.03,
    "dispute_resolution": 0.02,
    "product_notice": 0.00,
}


def normalize(text: str) -> str:
    return "".join(
        character.lower()
        for character in str(text)
        if character.isalnum()
    )


def has_any(
    text: str,
    terms: tuple[str, ...],
) -> bool:
    key = normalize(text)

    return any(
        normalize(term) in key
        for term in terms
    )


def is_seller_info_question(
    question: str,
) -> bool:
    """
    '판매자 정보'뿐 아니라 '판매자의 정보'처럼
    조사가 들어간 표현도 판매자 정보 질문으로 인식합니다.
    """
    if has_any(
        question,
        SELLER_INFO_TERMS,
    ):
        return True

    return (
        has_any(
            question,
            SELLER_TERMS,
        )
        and has_any(
            question,
            SELLER_DETAIL_TERMS,
        )
    )


def detect_intent(question: str) -> str | None:
    if (
        has_any(question, SIMPLE_CHANGE_TERMS)
        and has_any(question, RETURN_TERMS)
    ):
        return "simple_change_return"

    if not (
        has_any(question, PLATFORM_TERMS)
        and is_seller_info_question(question)
    ):
        return None

    return (
        "personal_seller_info"
        if has_any(question, PERSONAL_TERMS)
        else "business_seller_info"
    )


def dedupe_variants(
    variants: list[QueryVariant],
) -> tuple[QueryVariant, ...]:
    result: list[QueryVariant] = []
    seen: set[str] = set()

    for variant in variants:
        key = normalize(variant.text)

        if key and key not in seen:
            seen.add(key)
            result.append(variant)

    return tuple(result)


def build_plan(question: str) -> SearchPlan:
    question = " ".join(question.split())

    if not question:
        raise ValueError("질문이 비어 있습니다.")

    added: list[str] = []

    for triggers, legal_terms in BASE_RULES:
        if has_any(question, triggers):
            added.extend(legal_terms)

    added = list(dict.fromkeys(added))

    variants = [
        QueryVariant(
            name="original",
            text=question,
        )
    ]

    if added:
        variants.append(
            QueryVariant(
                name="expanded",
                text=(
                    f"{question}\n"
                    f"관련 법률 표현: {'; '.join(added)}"
                ),
            )
        )

    intent = detect_intent(question)
    rerank_question = question

    if intent == "business_seller_info":
        variants.append(
            QueryVariant(
                name="seller_info_law",
                text=(
                    "전자상거래법 제20조 통신판매중개자의 의무와 책임 "
                    "통신판매중개의뢰자가 사업자인 경우 성명 상호 주소 전화번호 등 "
                    "신원정보를 확인하여 청약 전에 소비자에게 제공"
                ),
            )
        )

        rerank_question = (
            f"{question}\n"
            "일반 온라인 플랫폼이 사업자인 판매자의 신원정보를 "
            "소비자에게 제공할 의무에 관한 문서를 찾는다."
        )

    elif intent == "personal_seller_info":
        variants.append(
            QueryVariant(
                name="personal_seller_law",
                text=(
                    "전자상거래법 제20조의4 개인 간 거래 통신판매중개업자 "
                    "개인 판매자 신원정보 확인 분쟁 시 신원정보와 거래내역 제공"
                ),
            )
        )

        rerank_question = (
            f"{question}\n"
            "개인 판매자 또는 개인 간 거래에서 플랫폼의 신원정보 "
            "확인과 분쟁 시 정보 제공 의무에 관한 문서를 찾는다."
        )

    elif intent == "simple_change_return":
        variants.append(
            QueryVariant(
                name="withdrawal_law",
                text=(
                    "전자상거래법 제17조 청약철회 재화를 공급받은 날부터 "
                    "7일 이내 단순 변심 반품 가능 청약철회 제한 사유"
                ),
            )
        )

        rerank_question = (
            f"{question}\n"
            "소비자가 단순 변심으로 반품할 수 있는지, "
            "청약철회 가능 기한과 제한 사유를 직접 규정한 문서를 찾는다."
        )

    return SearchPlan(
        question=question,
        rerank_question=rerank_question,
        intent=intent,
        variants=dedupe_variants(variants),
    )


def read_parents(
    path: Path,
) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(
            f"부모 청크 파일이 없습니다: {path}"
        )

    parents: dict[str, dict[str, Any]] = {}

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON 오류: {path}:{line_number}"
                ) from error

            parent_id = row.get("id")
            content = row.get("content")

            if (
                not isinstance(parent_id, str)
                or not parent_id.strip()
            ):
                raise ValueError(
                    f"부모 id 오류: line={line_number}"
                )

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                raise ValueError(
                    f"부모 content 오류: line={line_number}"
                )

            if parent_id in parents:
                raise ValueError(
                    f"중복 부모 id: {parent_id}"
                )

            parents[parent_id] = row

    if not parents:
        raise ValueError("부모 청크가 없습니다.")

    return parents


def load_services() -> tuple[Any, Any, Any]:
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import (
            CrossEncoder,
            SentenceTransformer,
        )
    except ImportError as error:
        raise SystemExit(
            "설치 필요: "
            "python -m pip install -U "
            "qdrant-client sentence-transformers"
        ) from error

    client = QdrantClient(
        url=QDRANT_URL
    )

    if not client.collection_exists(
        COLLECTION_NAME
    ):
        raise ValueError(
            f"Qdrant 컬렉션이 없습니다: "
            f"{COLLECTION_NAME}"
        )

    embedder = SentenceTransformer(
        EMBED_MODEL,
        device=DEVICE,
    )

    reranker = CrossEncoder(
        RERANK_MODEL,
        device=DEVICE,
        max_length=RERANK_MAX_LENGTH,
    )

    return client, embedder, reranker


def heading_text(
    metadata: dict[str, Any],
) -> str:
    value = metadata.get(
        "heading_path",
        [],
    )

    if isinstance(value, list):
        return " > ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return (
        value.strip()
        if isinstance(value, str)
        else ""
    )


def point_to_candidate(
    point: Any,
) -> dict[str, Any] | None:
    payload = point.payload or {}
    metadata = payload.get(
        "metadata",
        {},
    )

    if not isinstance(metadata, dict):
        metadata = {}

    parent_id = payload.get("parent_id")
    content = payload.get("content")

    if (
        not isinstance(parent_id, str)
        or not isinstance(content, str)
        or not content.strip()
    ):
        return None

    child_id = (
        payload.get("id")
        or payload.get("chunk_id")
        or str(point.id)
    )

    heading = heading_text(metadata)

    source_file = str(
        metadata.get(
            "source_file",
            payload.get("source_file", ""),
        )
        or ""
    )

    document_type = str(
        metadata.get(
            "document_type",
            "",
        )
        or ""
    )

    passage = "\n\n".join(
        value
        for value in (
            source_file,
            heading,
            content,
        )
        if value
    )

    return {
        "child_id": str(child_id),
        "parent_id": parent_id,
        "child_content": content.strip(),
        "source_file": source_file,
        "document_type": document_type,
        "heading": heading,
        "passage": passage,
        "dense_score": float(point.score),
        "fusion_score": 0.0,
        "retrieved_by": [],
        "rerank_score": 0.0,
    }


def retrieve_candidates(
    client: Any,
    embedder: Any,
    variants: tuple[QueryVariant, ...],
) -> list[dict[str, Any]]:
    vectors = embedder.encode(
        [
            variant.text
            for variant in variants
        ],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    merged: dict[
        str,
        dict[str, Any],
    ] = {}

    for variant, vector in zip(
        variants,
        vectors,
        strict=True,
    ):
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=(
                vector
                .astype("float32")
                .tolist()
            ),
            limit=CANDIDATES_PER_QUERY,
            with_payload=True,
            with_vectors=False,
        )

        for rank, point in enumerate(
            response.points,
            start=1,
        ):
            candidate = point_to_candidate(point)

            if candidate is None:
                continue

            current = merged.setdefault(
                candidate["child_id"],
                candidate,
            )

            current["dense_score"] = max(
                current["dense_score"],
                candidate["dense_score"],
            )

            current["fusion_score"] += (
                1.0 / (60.0 + rank)
            )

            if (
                variant.name
                not in current["retrieved_by"]
            ):
                current["retrieved_by"].append(
                    variant.name
                )

    candidates = list(
        merged.values()
    )

    candidates.sort(
        key=lambda item: (
            item["fusion_score"],
            item["dense_score"],
        ),
        reverse=True,
    )

    return candidates[:RERANK_LIMIT]


def rerank_candidates(
    reranker: Any,
    question: str,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    scores = reranker.predict(
        [
            (
                question,
                candidate["passage"],
            )
            for candidate in candidates
        ],
        batch_size=RERANK_BATCH_SIZE,
        show_progress_bar=False,
    )

    for candidate, score in zip(
        candidates,
        scores,
        strict=True,
    ):
        candidate["rerank_score"] = (
            float(score.item())
            if hasattr(score, "item")
            else float(score)
        )

    return sorted(
        candidates,
        key=lambda item: (
            item["rerank_score"],
            item["dense_score"],
            item["fusion_score"],
        ),
        reverse=True,
    )


def sort_by_document_type_bonus(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    단순 변심 반품의 보조 문서에만 문서 유형 가산점을 적용합니다.

    rerank 관련성을 가장 중요하게 유지하면서,
    점수가 비슷한 문서 사이에서 법률과 약관을 조금 우대합니다.
    문서를 제외하거나 법률을 무조건 앞세우지는 않습니다.
    """
    for candidate in candidates:
        document_type = str(
            candidate.get(
                "document_type",
                "",
            )
            or ""
        )

        bonus = (
            SIMPLE_CHANGE_DOCUMENT_TYPE_BONUS.get(
                document_type,
                0.0,
            )
        )

        candidate["document_type_bonus"] = bonus
        candidate["priority_score"] = (
            candidate["rerank_score"]
            + bonus
        )

    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["priority_score"],
            candidate["rerank_score"],
            candidate["dense_score"],
            candidate["fusion_score"],
        ),
        reverse=True,
    )

def is_personal_scope(
    candidate: dict[str, Any],
) -> bool:
    return has_any(
        candidate["passage"],
        PERSONAL_SCOPE_TERMS,
    )


def is_direct_business_duty(
    candidate: dict[str, Any],
) -> bool:
    text = candidate["passage"]

    required = (
        "통신판매중개의뢰자가 사업자인 경우",
        "신원정보",
        "청약이 이루어지기 전까지",
        "소비자에게 제공",
    )

    return all(
        has_any(
            text,
            (term,),
        )
        for term in required
    )


def is_primary_withdrawal_law(
    candidate: dict[str, Any],
) -> bool:
    """
    전자상거래법 제17조 청약철회 조항인지 확인합니다.
    """
    heading = candidate.get(
        "heading",
        "",
    )

    source_file = candidate.get(
        "source_file",
        "",
    )

    text = candidate["passage"]

    exact_heading = (
        "제17조" in heading
        and "청약철회" in heading
        and "소비자보호에 관한 법률" in source_file
    )

    content_signature = (
        has_any(
            text,
            (
                "통신판매업자와 재화등의 구매에 관한 계약",
            ),
        )
        and has_any(
            text,
            ("제13조제2항",),
        )
        and has_any(
            text,
            (
                "날부터 7일",
                "7일 이내",
            ),
        )
        and has_any(
            text,
            ("청약철회",),
        )
    )

    return exact_heading or content_signature


def is_direct_simple_change_right(
    candidate: dict[str, Any],
) -> bool:
    """
    단순 변심 반품의 권리와 기한을 직접 설명하는 문서인지 확인합니다.

    법률 원문의 '날부터 7일'과 약관의 '7일 이내'를 모두 허용합니다.
    단순히 관련 정보를 표시하라는 문서는 보조 결과로 둡니다.
    """
    text = candidate["passage"]

    has_deadline = has_any(
        text,
        (
            "7일 이내",
            "날부터 7일",
            "공급받거나 재화등의 공급이 시작된 날부터 7일",
        ),
    )

    has_right = has_any(
        text,
        (
            "청약철회",
            "청약의 철회",
        ),
    )

    has_start_point = has_any(
        text,
        (
            "재화를 공급받",
            "재화 등을 공급받",
            "재화등을 공급받",
            "서면을 받은 날",
            "공급이 시작된 날",
        ),
    )

    return (
        has_deadline
        and has_right
        and has_start_point
    )


def rerank_for_plan(
    reranker: Any,
    plan: SearchPlan,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if plan.intent == "business_seller_info":
        direct = [
            candidate
            for candidate in candidates
            if is_direct_business_duty(
                candidate
            )
        ]

        personal = [
            candidate
            for candidate in candidates
            if (
                is_personal_scope(candidate)
                and candidate not in direct
            )
        ]

        support = [
            candidate
            for candidate in candidates
            if (
                candidate not in direct
                and candidate not in personal
            )
        ]

        groups = (
            direct,
            support,
            personal,
        )

    elif plan.intent == "personal_seller_info":
        personal = [
            candidate
            for candidate in candidates
            if is_personal_scope(
                candidate
            )
        ]

        support = [
            candidate
            for candidate in candidates
            if candidate not in personal
        ]

        groups = (
            personal,
            support,
        )

    elif plan.intent == "simple_change_return":
        primary = [
            candidate
            for candidate in candidates
            if is_primary_withdrawal_law(
                candidate
            )
        ]

        direct = [
            candidate
            for candidate in candidates
            if (
                candidate not in primary
                and is_direct_simple_change_right(
                    candidate
                )
            )
        ]

        support = [
            candidate
            for candidate in candidates
            if (
                candidate not in primary
                and candidate not in direct
            )
        ]

        for candidate in primary:
            candidate["rank_group"] = (
                "primary_law"
            )

        for candidate in direct:
            candidate["rank_group"] = (
                "direct_right"
            )

        for candidate in support:
            candidate["rank_group"] = (
                "support"
            )

        groups = (
            primary,
            direct,
            support,
        )

    else:
        groups = (
            candidates,
        )

    ranked: list[
        dict[str, Any]
    ] = []

    for group in groups:
        ranked_group = rerank_candidates(
            reranker,
            plan.rerank_question,
            group,
        )

        is_simple_change_support_group = (
            plan.intent == "simple_change_return"
            and bool(ranked_group)
            and ranked_group[0].get("rank_group")
            == "support"
        )

        if is_simple_change_support_group:
            ranked_group = sort_by_document_type_bonus(
                ranked_group
            )

        ranked.extend(
            ranked_group
        )

    return ranked


def select_parents(
    candidates: list[dict[str, Any]],
    parents: dict[str, dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    results: list[
        dict[str, Any]
    ] = []

    used: set[str] = set()

    for candidate in candidates:
        parent_id = candidate["parent_id"]

        if parent_id in used:
            continue

        parent = parents.get(parent_id)

        if parent is None:
            raise ValueError(
                "부모 청크를 찾을 수 없습니다: "
                f"{parent_id}"
            )

        parent_metadata = parent.get(
            "metadata",
            {},
        )

        parent_document_type = ""

        if isinstance(
            parent_metadata,
            dict,
        ):
            parent_document_type = str(
                parent_metadata.get(
                    "document_type",
                    "",
                )
                or ""
            )

        results.append(
            {
                **candidate,
                "document_type": (
                    candidate.get(
                        "document_type",
                        "",
                    )
                    or parent_document_type
                ),
                "parent_content": parent["content"],
            }
        )

        used.add(parent_id)

        if len(results) >= limit:
            break

    return results


def search(
    client: Any,
    embedder: Any,
    reranker: Any,
    parents: dict[str, dict[str, Any]],
    question: str,
    limit: int,
) -> tuple[
    list[dict[str, Any]],
    SearchPlan,
]:
    plan = build_plan(question)

    candidates = retrieve_candidates(
        client,
        embedder,
        plan.variants,
    )

    ranked = rerank_for_plan(
        reranker,
        plan,
        candidates,
    )

    return (
        select_parents(
            ranked,
            parents,
            limit,
        ),
        plan,
    )


def print_results(
    results: list[dict[str, Any]],
    plan: SearchPlan,
) -> None:
    print("\n[검색 질문]")

    for variant in plan.variants:
        print(
            f"- {variant.name}: "
            f"{variant.text}"
        )

    print(
        f"- intent: "
        f"{plan.intent or '-'}"
    )

    if not results:
        print("검색 결과가 없습니다.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            "\n"
            + "=" * 88
        )

        print(
            f"[{rank}] rerank score : "
            f"{result['rerank_score']:.4f}"
        )

        print(
            "    rank group   : "
            f"{result.get('rank_group', 'reranker')}"
        )

        print(
            "    dense score  : "
            f"{result['dense_score']:.4f}"
        )

        print(
            "    retrieved by : "
            f"{', '.join(result['retrieved_by'])}"
        )

        print(
            "    document type: "
            f"{result.get('document_type') or '-'}"
        )

        if "priority_score" in result:
            print(
                "    type bonus   : "
                f"{result.get('document_type_bonus', 0.0):.4f}"
            )

            print(
                "    priority score: "
                f"{result['priority_score']:.4f}"
            )

        print(
            "    source_file  : "
            f"{result['source_file']}"
        )

        print(
            "    heading      : "
            f"{result['heading']}"
        )

        print(
            "    parent_id    : "
            f"{result['parent_id']}"
        )

        print(
            "-" * 88,
            "\n[검색된 자식 청크]",
            sep="",
        )

        print(
            result["child_content"]
        )

        print(
            "-" * 88,
            "\n[확장된 부모 청크]",
            sep="",
        )

        print(
            result["parent_content"].strip()
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qdrant 법률 문서 검색 검증"
    )

    parser.add_argument(
        "--question",
        type=str,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=RESULT_LIMIT,
    )

    return parser.parse_args()


def main() -> int:
    print(
        f"script     : "
        f"{Path(__file__).resolve()}"
    )

    print(
        "search mode: "
        "multi-query Qdrant + BGE reranker\n"
    )

    args = parse_args()

    if not (
        1
        <= args.top_k
        <= RERANK_LIMIT
    ):
        raise ValueError(
            "top-k는 "
            f"1~{RERANK_LIMIT} "
            "범위여야 합니다."
        )

    parents = read_parents(
        PARENT_FILE
    )

    (
        client,
        embedder,
        reranker,
    ) = load_services()

    print(
        f"parents    : "
        f"{len(parents)}"
    )

    print(
        f"collection : "
        f"{COLLECTION_NAME}"
    )

    print(
        f"embedder   : "
        f"{EMBED_MODEL}"
    )

    print(
        f"reranker   : "
        f"{RERANK_MODEL}"
    )

    if args.question:
        results, plan = search(
            client,
            embedder,
            reranker,
            parents,
            args.question,
            args.top_k,
        )

        print_results(
            results,
            plan,
        )

        return 0

    print(
        "종료하려면 q를 입력하세요."
    )

    while True:
        question = input(
            "\n질문: "
        ).strip()

        if question.lower() in {
            "q",
            "quit",
            "exit",
        }:
            return 0

        if question:
            results, plan = search(
                client,
                embedder,
                reranker,
                parents,
                question,
                args.top_k,
            )

            print_results(
                results,
                plan,
            )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )