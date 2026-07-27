from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Final

from app.services.answer_validator import (
    validate_and_repair_answer,
)
from app.services.legal_rules import (
    get_legal_rule,
)
from app.services.ollama_service import generate_answer


MAX_DOCUMENT_LENGTH: Final[int] = 4000
MAX_CONTEXT_DOCUMENTS: Final[int] = 3


HYBRID_ANSWER_SYSTEM_PROMPT: Final[str] = """
당신은 온라인 쇼핑몰 법률 및 정책 안내 챗봇입니다.

다음 원칙을 반드시 지키세요.

1. 제공된 핵심 결론의 의미를 바꾸지 마세요.
2. 세부 조건과 기간은 검색 문서에 직접 있는 내용만 사용하세요.
3. 검색 문서에 없는 예외, 보증기간, 수리 횟수, 감가상각 기준을
   만들어내지 마세요.
4. 질문에 제품 종류가 없다면 특정 품목별 해결기준을 적용하지 마세요.
5. 환불을 요구할 수 있다는 표현과 환불이 확정된다는 표현을
   구분하세요.
6. 서로 다른 절차인 청약철회 기간, 상품 반환 후 환급 기한,
   품절 환급 기한을 혼동하지 마세요.
7. 답변 본문에 출처 번호, 파일명, 문서명을 쓰지 마세요.
8. 같은 내용을 반복하지 말고 2~3문단 이내로 작성하세요.
9. 검색 문서가 핵심 결론의 세부 조건을 뒷받침하지 못하면,
   확인 가능한 범위까지만 설명하세요.
""".strip()


@dataclass(frozen=True)
class HybridAnswerPlan:
    """고정 핵심 결론과 검색 근거를 결합하기 위한 계획."""

    question: str
    intent: str
    core_conclusion: str
    document_count: int
    prompt: str
    supported: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def can_build_hybrid_answer(
    intent: str | None,
) -> bool:
    """legal_rules.py에 등록된 intent인지 확인한다."""
    return get_legal_rule(intent) is not None


def _get_document_content(
    document: dict[str, Any],
) -> str:
    """Qdrant 결과에서 사용할 본문 필드를 안전하게 가져온다."""
    for key in (
        "parent_content",
        "child_content",
        "content",
        "text",
        "excerpt",
        "snippet",
    ):
        value = str(document.get(key, "")).strip()

        if value:
            return value[:MAX_DOCUMENT_LENGTH]

    return ""


def _clean_source_label(value: object) -> str:
    """출처 제목에 남은 Markdown 표 기호를 제거한다."""
    return str(value).strip().strip("|").strip()


def build_source_context(
    documents: list[dict[str, Any]],
) -> str:
    """검색 문서를 답변 생성용 근거 문맥으로 변환한다."""
    context_parts: list[str] = []

    for document in documents[:MAX_CONTEXT_DOCUMENTS]:
        content = _get_document_content(document)

        if not content:
            continue

        heading = _clean_source_label(
            document.get("heading", "")
        )

        source_file = _clean_source_label(
            document.get("source_file", "")
        )

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


def build_hybrid_answer_prompt(
    question: str,
    intent: str,
    documents: list[dict[str, Any]],
) -> str:
    """legal_rules.py의 규칙과 검색 근거로 프롬프트를 만든다."""
    cleaned_question = " ".join(str(question).split())

    if not cleaned_question:
        raise ValueError("질문을 입력해주세요.")

    rule = get_legal_rule(intent)

    if rule is None:
        raise ValueError(
            f"지원하지 않는 하이브리드 intent입니다: {intent}"
        )

    context = build_source_context(documents)

    return f"""
아래 사용자 질문에 답변하세요.

[사용자 질문]
{cleaned_question}

[반드시 유지할 핵심 결론]
{rule.core_conclusion}

[이 질문의 추가 작성 규칙]
{rule.guidance}

[검색된 근거 문서]
{context if context else "사용할 수 있는 근거 문서가 없습니다."}

[작성 방법]
- 첫 문단에는 핵심 결론을 간결하게 제시하세요.
- 다음 문단에는 검색 문서에서 직접 확인되는 조건이나 기간만
  설명하세요.
- 검색 문서로 확인되지 않는 조건은 추가하지 마세요.
- 특정 품목이 확인되지 않았다는 이유로 관련 없는 품목 기준을
  나열하지 마세요.
- 문서 근거가 부족하면 핵심 결론 뒤에 추가 조건을 억지로
  만들지 마세요.
""".strip()


def create_hybrid_answer_plan(
    question: str,
    intent: str,
    documents: list[dict[str, Any]],
) -> HybridAnswerPlan:
    """생성 전 확인이나 테스트에 사용할 답변 계획을 반환한다."""
    rule = get_legal_rule(intent)

    if rule is None:
        return HybridAnswerPlan(
            question=" ".join(str(question).split()),
            intent=intent,
            core_conclusion="",
            document_count=0,
            prompt="",
            supported=False,
        )

    usable_documents = [
        document
        for document in documents[:MAX_CONTEXT_DOCUMENTS]
        if _get_document_content(document)
    ]

    return HybridAnswerPlan(
        question=" ".join(str(question).split()),
        intent=intent,
        core_conclusion=rule.core_conclusion,
        document_count=len(usable_documents),
        prompt=build_hybrid_answer_prompt(
            question=question,
            intent=intent,
            documents=usable_documents,
        ),
        supported=True,
    )


def clean_generated_answer(answer: str) -> str:
    """Ollama 답변의 불필요한 공백과 줄바꿈을 정리한다."""
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


def build_hybrid_answer(
    question: str,
    intent: str,
    documents: list[dict[str, Any]],
    generator: Callable[..., str] | None = None,
    validation_documents: list[dict[str, Any]] | None = None,
) -> str:
    """
    legal_rules.py의 핵심 결론과 검색 문서를 결합해 답변을 만든다.

    generator를 전달하지 않으면 기존 Ollama generate_answer를 사용한다.
    """
    plan = create_hybrid_answer_plan(
        question=question,
        intent=intent,
        documents=documents,
    )

    if not plan.supported:
        raise ValueError(
            f"지원하지 않는 하이브리드 intent입니다: {intent}"
        )

    resolved_validation_documents = (
        validation_documents
        if validation_documents is not None
        else documents
    )

    if plan.document_count == 0:
        validation_result = validate_and_repair_answer(
            intent=intent,
            answer=plan.core_conclusion,
            documents=resolved_validation_documents,
            core_conclusion=plan.core_conclusion,
        )

        return validation_result.answer

    resolved_generator = (
        generator
        if generator is not None
        else generate_answer
    )

    answer = resolved_generator(
        prompt=plan.prompt,
        system_prompt=HYBRID_ANSWER_SYSTEM_PROMPT,
    )

    cleaned_answer = clean_generated_answer(answer)

    validation_result = validate_and_repair_answer(
        intent=intent,
        answer=cleaned_answer,
        documents=resolved_validation_documents,
        core_conclusion=plan.core_conclusion,
    )

    return validation_result.answer