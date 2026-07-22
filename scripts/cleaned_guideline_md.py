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
    / "전자상거래 등에서의 상품 등의 정보제공에 관한 고시(공정거래위원회고시)(제2022-15호)(20230101)_원본.md"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "전자상거래 등에서의 상품 등의 정보제공에 관한 고시(공정거래위원회고시)(제2022-15호)(20230101)_정리본.md"
)


DOCUMENT_TITLE = "전자상거래 등에서의 상품 등의 정보제공에 관한 고시"

DOCUMENT_INFO = [
    "시행 2023. 1. 1.",
    "공정거래위원회고시 제2022-15호",
    "2022. 8. 3., 일부개정",
    "공정거래위원회 소비자거래정책과",
]


# =========================================================
# 구조 정규식
# =========================================================

# I. 목적 및 구성
# Ⅱ. 일반사항
# Ⅲ. 권고사항
# Ⅳ. 재검토기한
SECTION_PATTERN = re.compile(
    r"^\s*"
    r"([IVXⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)"
    r"\.\s*"
    r"(.+?)"
    r"\s*$"
)

# 1. 목적
# 10. 청약철회 방해 등 관련
SUBSECTION_PATTERN = re.compile(
    r"^\s*"
    r"(\d+)"
    r"\.\s+"
    r"(.+?)"
    r"\s*$"
)

# 가. 사업자가 표시ㆍ광고를 할 때에는
KOREAN_ITEM_PATTERN = re.compile(
    r"^\s*"
    r"([가-하])"
    r"\.\s*"
    r"(.*)"
    r"$"
)

# (1) 사이버몰에서 거래가 이루어지는 경우
EXAMPLE_NUMBER_PATTERN = re.compile(
    r"^\s*"
    r"\((\d+)\)"
    r"\s*"
    r"(.*)"
    r"$"
)

SUPPLEMENT_PATTERN = re.compile(
    r"^\s*"
    r"부칙"
    r"(?:\s*(<[^>]+>))?"
    r"\s*$"
)


# =========================================================
# 페이지 요소 제거
# =========================================================

def remove_page_elements(text: str) -> str:
    """
    PDF 변환 과정에서 추가된 페이지 표시, 반복 제목,
    법제처 하단 정보를 제거합니다.
    """

    # <!-- page: 1 -->
    text = re.sub(
        r"<!--\s*page:\s*\d+\s*-->",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 법제처 1 국가법령정보센터
    text = re.sub(
        r"(?m)^\s*"
        r"법제처"
        r"\s+\d+\s+"
        r"국가법령정보센터"
        r"\s*$",
        "",
        text,
    )

    # 페이지마다 반복되는 문서 제목
    text = re.sub(
        rf"(?m)^\s*{re.escape(DOCUMENT_TITLE)}\s*$",
        "",
        text,
    )

    return text


# =========================================================
# 원본 머리말 제거
# =========================================================

def is_header_information(line: str) -> bool:
    """
    새 Markdown 머리말로 다시 만들 정보는
    원본 본문에서 제거합니다.
    """

    compact = re.sub(
        r"\s+",
        "",
        line,
    )

    header_keywords = [
        "시행2025.10.24.",
        "공정거래위원회고시제2025-8호",
        "2025.10.24.,일부개정",
        "공정거래위원회(소비자거래정책과)",
        "044-200-4454",
    ]

    return any(
        keyword in compact
        for keyword in header_keywords
    )


# =========================================================
# 문장 연결
# =========================================================

def join_wrapped_lines(lines: list[str]) -> str:
    """
    PDF 페이지 폭 때문에 나뉜 줄을 한 문단으로 연결합니다.

    글자를 임의로 붙이지 않고 공백으로 연결하므로
    원문의 단어가 서로 합쳐지는 문제를 줄입니다.
    """

    cleaned_lines = [
        re.sub(r"\s+", " ", line.strip())
        for line in lines
        if line.strip()
    ]

    result = " ".join(cleaned_lines)

    # 문장부호 앞 불필요한 공백 제거
    result = re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        result,
    )

    # 닫는 괄호 앞 공백 제거
    result = re.sub(
        r"\s+([)\]》」』〉])",
        r"\1",
        result,
    )

    # 여는 괄호 뒤 공백 제거
    result = re.sub(
        r"([(\[《「『〈])\s+",
        r"\1",
        result,
    )

    return result.strip()


# =========================================================
# 본문 정리
# =========================================================

def clean_document(text: str) -> tuple[str, list[str]]:
    text = remove_page_elements(text)

    lines = text.splitlines()

    output_blocks: list[str] = []
    paragraph_buffer: list[str] = []
    found_sections: list[str] = []

    document_started = False
    supplement_found = False

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

        # 원본 제목과 문서 정보 제거
        if is_header_information(line):
            continue

        # Ⅰ. 목적 및 구성
        section_match = SECTION_PATTERN.match(line)

        if section_match:
            flush_paragraph()

            document_started = True

            section_number = section_match.group(1)
            section_title = section_match.group(2).strip()

            # 영문 I를 한글 문서 형식의 Ⅰ로 통일
            section_number_map = {
                "I": "Ⅰ",
                "II": "Ⅱ",
                "III": "Ⅲ",
                "IV": "Ⅳ",
                "V": "Ⅴ",
            }

            section_number = section_number_map.get(
                section_number,
                section_number,
            )

            heading = (
                f"## {section_number}. "
                f"{section_title}"
            )

            output_blocks.append(heading)
            found_sections.append(section_number)

            continue

        # 부칙
        supplement_match = SUPPLEMENT_PATTERN.match(line)

        if supplement_match:
            flush_paragraph()

            document_started = True
            supplement_found = True

            supplement_info = (
                supplement_match.group(1) or ""
            ).strip()

            heading = "## 부칙"

            if supplement_info:
                heading += f" {supplement_info}"

            output_blocks.append(heading)
            continue

        # 본문 시작 전의 빈 머리말은 제외
        if not document_started:
            continue

        # 1. 목적
        subsection_match = SUBSECTION_PATTERN.match(line)

        if subsection_match:
            flush_paragraph()

            subsection_number = subsection_match.group(1)
            subsection_title = subsection_match.group(2).strip()

            output_blocks.append(
                f"### {subsection_number}. "
                f"{subsection_title}"
            )

            continue

        # <예시>
        if line == "<예시>":
            flush_paragraph()
            output_blocks.append("#### 예시")
            continue

        # 가. 내용
        korean_item_match = KOREAN_ITEM_PATTERN.match(line)

        if korean_item_match:
            flush_paragraph()

            item_number = korean_item_match.group(1)
            item_body = korean_item_match.group(2).strip()

            if item_body:
                paragraph_buffer.append(
                    f"{item_number}. {item_body}"
                )
            else:
                paragraph_buffer.append(
                    f"{item_number}."
                )

            continue

        # (1) 내용
        example_match = EXAMPLE_NUMBER_PATTERN.match(line)

        if example_match:
            flush_paragraph()

            example_number = example_match.group(1)
            example_body = example_match.group(2).strip()

            paragraph_buffer.append(
                f"({example_number}) {example_body}"
            )

            continue

        # ㅇ 예시
        if line.startswith("ㅇ"):
            flush_paragraph()

            item_body = line[1:].strip()

            paragraph_buffer.append(
                f"- {item_body}"
            )

            continue

        # ⇒ 설명
        if line.startswith("⇒"):
            flush_paragraph()
            paragraph_buffer.append(line)
            continue

        # - 반면에 등의 하위 설명
        if line.startswith("-"):
            flush_paragraph()
            paragraph_buffer.append(line)
            continue

        paragraph_buffer.append(line)

    flush_paragraph()

    if not found_sections:
        raise ValueError(
            "Ⅰ~Ⅳ 본문 구성을 찾지 못했습니다.\n"
            "정리본을 저장하지 않습니다."
        )

    if not supplement_found:
        raise ValueError(
            "부칙을 찾지 못했습니다.\n"
            "원본이 잘렸을 가능성이 있습니다."
        )

    header_blocks = [
        f"# {DOCUMENT_TITLE}",
        "\n".join(
            f"- {item}"
            for item in DOCUMENT_INFO
        ),
    ]

    result = (
        "\n\n".join(
            header_blocks + output_blocks
        ).strip()
        + "\n"
    )

    return result, found_sections


# =========================================================
# 실행 및 검증
# =========================================================

def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "원본 파일을 찾을 수 없습니다.\n"
            f"{INPUT_FILE.resolve()}"
        )

    original_text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    print("입력 파일:")
    print(INPUT_FILE.resolve())

    cleaned_text, found_sections = clean_document(
        original_text
    )

    expected_sections = [
        "Ⅰ",
        "Ⅱ",
        "Ⅲ",
        "Ⅳ",
    ]

    print("발견한 대단원:", found_sections)

    if found_sections != expected_sections:
        raise ValueError(
            "대단원 검증 실패\n"
            f"예상: {expected_sections}\n"
            f"발견: {found_sections}\n\n"
            "정리본을 저장하지 않았습니다."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        cleaned_text,
        encoding="utf-8",
    )

    print("\n정리 완료")
    print("저장 파일:")
    print(OUTPUT_FILE.resolve())
    print("Ⅰ~Ⅳ 및 부칙 확인 완료")


if __name__ == "__main__":
    main()