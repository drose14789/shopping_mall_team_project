from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Final


SUPPORTED_INTENTS: Final[set[str]] = {
    "replacement_defective_refund",
}


PROHIBITED_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "replacement_defective_refund": (
        "단순 변심",
        "단순변심",
        "7일 이내",
        "7일이내",
        "포장 훼손",
        "포장훼손",
        "포장을 훼손",
        "가치가 현저히 감소",
        "구매 시의 배송비",
        "구매시의 배송비",
        "소비자가 부담",
        "이용자가 부담",
        "반환 비용을 부담",
        "반환비용을 부담",
    ),
}


@dataclass(frozen=True)
class EvidenceFacts:
    """검색 근거에서 확인된 필수 법률 사실."""

    has_mismatch_deadline_pair: bool
    has_refund_after_return_deadline: bool

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class AnswerValidationResult:
    """답변 검증 및 보정 결과."""

    answer: str
    is_valid: bool
    was_repaired: bool
    missing_facts: tuple[str, ...]
    prohibited_terms: tuple[str, ...]
    evidence_facts: EvidenceFacts

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_text(text: str) -> str:
    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        str(text).lower(),
    )


def clean_answer(answer: str) -> str:
    lines = [
        line.rstrip()
        for line in str(answer).strip().splitlines()
    ]

    cleaned_lines: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = not line.strip()

        if is_blank and previous_blank:
            continue

        cleaned_lines.append(line)
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


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


def build_evidence_text(
    documents: list[dict[str, Any]],
) -> str:
    return "\n".join(
        get_document_content(document)
        for document in documents
        if get_document_content(document)
    )


def extract_evidence_facts(
    intent: str,
    documents: list[dict[str, Any]],
) -> EvidenceFacts:
    """
    검색 근거에 실제로 존재하는 필수 기간과 조건만 추출한다.

    문서에 없는 기간은 필수 사실로 만들지 않으므로
    답변에 임의로 추가되지 않는다.
    """
    if intent not in SUPPORTED_INTENTS:
        return EvidenceFacts(
            has_mismatch_deadline_pair=False,
            has_refund_after_return_deadline=False,
        )

    evidence = normalize_text(
        build_evidence_text(documents)
    )

    has_mismatch_context = any(
        marker in evidence
        for marker in (
            "표시광고",
            "계약내용과다르게",
            "계약내용과달리",
        )
    )

    has_mismatch_deadline_pair = (
        has_mismatch_context
        and "청약철회" in evidence
        and "3개월" in evidence
        and "30일" in evidence
    )

    has_refund_after_return_deadline = (
        "반환받" in evidence
        and "3영업일" in evidence
        and "환급" in evidence
    )

    return EvidenceFacts(
        has_mismatch_deadline_pair=(
            has_mismatch_deadline_pair
        ),
        has_refund_after_return_deadline=(
            has_refund_after_return_deadline
        ),
    )


def find_prohibited_terms(
    intent: str,
    answer: str,
) -> tuple[str, ...]:
    terms = PROHIBITED_TERMS.get(intent, ())
    normalized_answer = normalize_text(answer)

    found = [
        term
        for term in terms
        if normalize_text(term) in normalized_answer
    ]

    return tuple(dict.fromkeys(found))


def find_missing_facts(
    intent: str,
    answer: str,
    facts: EvidenceFacts,
) -> tuple[str, ...]:
    if intent not in SUPPORTED_INTENTS:
        return ()

    normalized_answer = normalize_text(answer)
    missing: list[str] = []

    if facts.has_mismatch_deadline_pair:
        required_markers = {
            "3개월": "3개월",
            "30일": "30일",
            "사실을 안 날": "사실을안날",
            "알 수 있었던 날": "알수있었던날",
        }

        for label, marker in required_markers.items():
            if marker not in normalized_answer:
                missing.append(label)

    if facts.has_refund_after_return_deadline:
        refund_markers = {
            "상품 반환 후": "반환받",
            "3영업일": "3영업일",
            "대금 환급": "환급",
        }

        for label, marker in refund_markers.items():
            if marker not in normalized_answer:
                missing.append(label)

    return tuple(dict.fromkeys(missing))


def build_repaired_answer(
    core_conclusion: str,
    facts: EvidenceFacts,
) -> str:
    """
    검색 근거로 확인된 사실만 사용해 필수 문장을 확정적으로 조립한다.
    """
    paragraphs = [clean_answer(core_conclusion)]

    if facts.has_mismatch_deadline_pair:
        paragraphs.append(
            "온라인으로 구매한 상품이 표시·광고 또는 계약 내용과 "
            "다르게 제공된 경우에는 상품을 공급받은 날부터 "
            "3개월 이내이면서, 그 사실을 안 날 또는 알 수 있었던 "
            "날부터 30일 이내에 청약철회를 요구할 수 있습니다."
        )

    if facts.has_refund_after_return_deadline:
        paragraphs.append(
            "판매자가 상품을 반환받은 경우에는 3영업일 이내에 "
            "지급받은 대금을 환급해야 합니다."
        )

    return "\n\n".join(
        paragraph
        for paragraph in paragraphs
        if paragraph
    )


def validate_and_repair_answer(
    *,
    intent: str,
    answer: str,
    documents: list[dict[str, Any]],
    core_conclusion: str,
) -> AnswerValidationResult:
    """
    생성 답변에 필수 사실 누락이나 금지 내용이 있는지 검증한다.

    문제가 있으면 검색 근거에서 확인된 문장으로 답변을 교체한다.
    """
    cleaned = clean_answer(answer)

    if intent not in SUPPORTED_INTENTS:
        return AnswerValidationResult(
            answer=cleaned,
            is_valid=True,
            was_repaired=False,
            missing_facts=(),
            prohibited_terms=(),
            evidence_facts=EvidenceFacts(
                has_mismatch_deadline_pair=False,
                has_refund_after_return_deadline=False,
            ),
        )

    facts = extract_evidence_facts(
        intent,
        documents,
    )

    missing_facts = find_missing_facts(
        intent,
        cleaned,
        facts,
    )

    prohibited_terms = find_prohibited_terms(
        intent,
        cleaned,
    )

    needs_repair = bool(
        missing_facts
        or prohibited_terms
        or not cleaned
    )

    if needs_repair:
        repaired = build_repaired_answer(
            core_conclusion=core_conclusion,
            facts=facts,
        )

        return AnswerValidationResult(
            answer=repaired,
            is_valid=False,
            was_repaired=True,
            missing_facts=missing_facts,
            prohibited_terms=prohibited_terms,
            evidence_facts=facts,
        )

    return AnswerValidationResult(
        answer=cleaned,
        is_valid=True,
        was_repaired=False,
        missing_facts=(),
        prohibited_terms=(),
        evidence_facts=facts,
    )