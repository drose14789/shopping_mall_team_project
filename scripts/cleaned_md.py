import re
from pathlib import Path


# =========================================================
# 파일 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "raw"
    / "표시ㆍ광고의 공정화에 관한 법률(법률)(제20712호)(20250121)_원본.md"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "표시ㆍ광고의 공정화에 관한 법률(법률)(제20712호)(20250121)_정리본.md"
)


DOCUMENT_TITLE = " 표시ㆍ광고의 공정화에 관한 법률 ( 약칭: 표시광고법 )"

DOCUMENT_INFO = [
    "시행 2025. 1. 21."
    "법률 제20712호"
    "2025. 1. 21., 타법개정",
    "공정거래위원회 소비자정책총괄과",
]


# =========================================================
# 정규식
# =========================================================

# 제1조(목적)
# 제 1 조 ( 목적 )
# ### 제1조(목적)
# 제16조 삭제 <2005. 3. 31.>
ARTICLE_PATTERN = re.compile(
    r"^\s*"
    r"(?:#{1,6}\s*)?"
    r"제\s*(\d+)\s*조"
    r"(?:\s*의\s*(\d+))?"
    r"\s*"
    r"(?:"
    r"\(\s*([^)]*?)\s*\)"
    r"|"
    r"(삭제(?:\s*<[^>]+>)?)"
    r")"
    r"\s*(.*)$"
)

# 제1장 총칙
CHAPTER_PATTERN = re.compile(
    r"^\s*"
    r"(?:#{1,6}\s*)?"
    r"제\s*(\d+)\s*장"
    r"(?:\s+(.*?))?"
    r"\s*$"
)

# 부칙 또는 부칙 <제2025-8호, 2025. 10. 24.>
SUPPLEMENT_PATTERN = re.compile(
    r"^\s*"
    r"(?:#{1,6}\s*)?"
    r"부칙"
    r"(?:\s*(<[^>]+>))?"
    r"\s*$"
)

# 항 번호
PARAGRAPH_PATTERN = re.compile(
    r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]"
)

# 호 번호
NUMBER_ITEM_PATTERN = re.compile(
    r"^\d+(?:의\d+)?\.\s*"
)

# 목 번호
KOREAN_ITEM_PATTERN = re.compile(
    r"^[가-하]\.\s*"
)


# =========================================================
# 페이지 요소 제거
# =========================================================

def remove_page_elements(text: str) -> str:
    """
    PDF/HWP 변환 과정에서 들어간 페이지 관련 요소만 제거합니다.
    본문은 삭제하지 않습니다.
    """

    text = re.sub(
        r"<!--\s*page:\s*\d+\s*-->",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"(?m)^\s*-\s*\d+\s*-\s*$",
        "",
        text,
    )

    text = re.sub(
        r"(?m)^\s*법제처\s+\d+\s+국가법령정보센터\s*$",
        "",
        text,
    )

    return text


# =========================================================
# 문단 처리
# =========================================================

def is_structure_line(line: str) -> bool:
    """
    현재 줄이 새로운 문단을 시작하는 구조인지 확인합니다.
    """

    return bool(
        ARTICLE_PATTERN.match(line)
        or CHAPTER_PATTERN.match(line)
        or SUPPLEMENT_PATTERN.match(line)
        or PARAGRAPH_PATTERN.match(line)
        or NUMBER_ITEM_PATTERN.match(line)
        or KOREAN_ITEM_PATTERN.match(line)
        or line.startswith("※")
        or line.startswith("[")
    )


def join_wrapped_lines(lines: list[str]) -> str:
    """
    문장 중간의 줄바꿈은 공백으로 연결합니다.

    기존처럼 공백 없이 붙이지 않기 때문에
    '이약관은', '이용함에있어' 같은 문제가 줄어듭니다.
    """

    cleaned = [
        line.strip()
        for line in lines
        if line.strip()
    ]

    return " ".join(cleaned)


def normalize_article_heading(
    match: re.Match,
) -> tuple[str, str]:
    """
    조문 제목을 Markdown 형식으로 변환합니다.
    제목과 같은 줄에 붙어 있던 본문도 반환합니다.
    """

    article_number = match.group(1)
    sub_number = match.group(2)
    article_title = match.group(3)
    deleted_title = match.group(4)
    remaining_body = match.group(5).strip()

    article_name = f"제{article_number}조"

    if sub_number:
        article_name += f"의{sub_number}"

    if article_title:
        heading = (
            f"### {article_name}"
            f"({article_title.strip()})"
        )
    else:
        heading = (
            f"### {article_name} "
            f"{deleted_title.strip()}"
        )

    return heading, remaining_body


# =========================================================
# 본문 정리
# =========================================================

def clean_document(text: str) -> tuple[str, list[str]]:
    text = remove_page_elements(text)

    lines = text.splitlines()

    output_blocks: list[str] = []
    paragraph_buffer: list[str] = []
    found_articles: list[str] = []

    document_started = False

    def flush_paragraph() -> None:
        if not paragraph_buffer:
            return

        paragraph = join_wrapped_lines(
            paragraph_buffer
        )

        if paragraph:
            output_blocks.append(paragraph)

        paragraph_buffer.clear()

    for original_line in lines:
        line = original_line.strip()

        if not line:
            flush_paragraph()
            continue

        article_match = ARTICLE_PATTERN.match(line)

        if article_match:
            flush_paragraph()

            document_started = True

            heading, remaining_body = (
                normalize_article_heading(
                    article_match
                )
            )

            output_blocks.append(heading)
            found_articles.append(heading)

            if remaining_body:
                paragraph_buffer.append(
                    remaining_body
                )

            continue

        chapter_match = CHAPTER_PATTERN.match(line)

        if chapter_match:
            flush_paragraph()

            document_started = True

            chapter_number = chapter_match.group(1)
            chapter_title = (
                chapter_match.group(2) or ""
            ).strip()

            heading = f"## 제{chapter_number}장"

            if chapter_title:
                heading += f" {chapter_title}"

            output_blocks.append(heading)
            continue

        supplement_match = SUPPLEMENT_PATTERN.match(line)

        if supplement_match:
            flush_paragraph()

            # 조문을 하나도 찾지 못한 상태에서
            # 부칙만 발견되면 잘못된 결과이므로 중단
            if not found_articles:
                raise ValueError(
                    "제1조부터 조문을 찾지 못했습니다.\n"
                    "부칙만 인식되어 출력을 중단합니다.\n"
                    "원본의 조문 제목 형식을 확인하세요."
                )

            document_started = True

            supplement_info = (
                supplement_match.group(1) or ""
            ).strip()

            heading = "## 부칙"

            if supplement_info:
                heading += f" {supplement_info}"

            output_blocks.append(heading)
            continue

        # 첫 조문이나 장이 나오기 전의 원본 제목,
        # 파일 정보, 반복 머리말은 새 제목으로 교체하므로 제외
        if not document_started:
            continue

        if is_structure_line(line):
            flush_paragraph()
            paragraph_buffer.append(line)
        else:
            paragraph_buffer.append(line)

    flush_paragraph()

    header = [
        f"# {DOCUMENT_TITLE}",
        "",
        *[
            f"- {item}"
            for item in DOCUMENT_INFO
        ],
    ]

    result = (
        "\n".join(header)
        + "\n\n"
        + "\n\n".join(output_blocks)
        + "\n"
    )

    return result, found_articles


# =========================================================
# 실행 및 검증
# =========================================================

def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "원본 파일을 찾을 수 없습니다.\n"
            f"{INPUT_FILE}"
        )

    original_text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    cleaned_text, found_articles = (
        clean_document(original_text)
    )

    article_numbers = []

    for heading in found_articles:
        match = re.search(
            r"제(\d+)조",
            heading
        )

        if match:
            article_numbers.append(
                int(match.group(1))
            )

    print("찾은 조문 수:", len(found_articles))
    print("찾은 조문 번호:", article_numbers)

    # 이 표준약관은 제1조부터 제24조까지 있어야 함
    expected_articles = list(
        range(1, 25)
    )

    if article_numbers != expected_articles:
        raise ValueError(
            "조문 검증 실패\n"
            f"예상 조문: {expected_articles}\n"
            f"발견 조문: {article_numbers}\n\n"
            "정리본을 저장하지 않았습니다."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        cleaned_text,
        encoding="utf-8"
    )

    print("\n정리 완료")
    print("저장 파일:", OUTPUT_FILE)
    print("제1조부터 제24조까지 확인 완료")


if __name__ == "__main__":
    main()