from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from app.services.legal_rules import (
    get_legal_rule,
)


@dataclass(frozen=True)
class AnswerValidationResult:
    answer: str
    is_valid: bool
    was_repaired: bool
    missing_facts: tuple[str, ...]
    prohibited_terms: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_text(text: str) -> str:
    """비교용으로 공백과 문장부호를 제거한다."""
    return re.sub(
        r"[^0-9a-zA-Z가-힣]",
        "",
        str(text).lower(),
    )


def clean_answer(answer: str) -> str:
    """연속된 빈 줄을 하나로 정리한다."""
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


def find_missing_facts(
    intent: str,
    answer: str,
) -> tuple[str, ...]:
    """intent 규칙에서 필수 사실 누락을 찾는다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return ()

    normalized_answer = normalize_text(answer)

    missing = [
        label
        for label, marker in rule.mandatory_markers
        if normalize_text(marker) not in normalized_answer
    ]

    return tuple(missing)


def find_prohibited_terms(
    intent: str,
    answer: str,
) -> tuple[str, ...]:
    """intent 규칙에 금지된 표현을 찾는다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return ()

    normalized_answer = normalize_text(answer)

    found = [
        term
        for term in rule.prohibited_terms
        if normalize_text(term) in normalized_answer
    ]

    return tuple(dict.fromkeys(found))


def build_canonical_answer(
    *,
    intent: str,
    core_conclusion: str | None = None,
) -> str:
    """규칙에 정의된 검증 완료 답변을 만든다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return clean_answer(core_conclusion or "")

    resolved_core_conclusion = clean_answer(
        core_conclusion
        if core_conclusion is not None
        else rule.core_conclusion
    )

    paragraphs = [resolved_core_conclusion]
    paragraphs.extend(rule.mandatory_paragraphs)

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
    core_conclusion: str | None = None,
) -> AnswerValidationResult:
    """
    필수 사실이 빠지거나 금지 표현이 포함된 경우
    legal_rules.py에 정의된 검증 완료 답변으로 교체한다.

    documents 인자는 기존 호출부 호환성을 위해 유지한다.
    """
    del documents

    cleaned_answer = clean_answer(answer)
    rule = get_legal_rule(intent)

    if rule is None:
        return AnswerValidationResult(
            answer=cleaned_answer,
            is_valid=True,
            was_repaired=False,
            missing_facts=(),
            prohibited_terms=(),
        )

    missing_facts = find_missing_facts(
        intent,
        cleaned_answer,
    )

    prohibited_terms = find_prohibited_terms(
        intent,
        cleaned_answer,
    )

    needs_repair = bool(
        not cleaned_answer
        or missing_facts
        or prohibited_terms
    )

    if not needs_repair:
        return AnswerValidationResult(
            answer=cleaned_answer,
            is_valid=True,
            was_repaired=False,
            missing_facts=(),
            prohibited_terms=(),
        )

    repaired_answer = build_canonical_answer(
        intent=intent,
        core_conclusion=(
            core_conclusion
            if core_conclusion is not None
            else rule.core_conclusion
        ),
    )

    return AnswerValidationResult(
        answer=repaired_answer,
        is_valid=False,
        was_repaired=True,
        missing_facts=missing_facts,
        prohibited_terms=prohibited_terms,
    )