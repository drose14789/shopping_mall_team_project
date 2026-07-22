from __future__ import annotations

import re
import unicodedata
from pathlib import Path


# =========================================================
# 경로 설정
# =========================================================

BASE_DIR = Path(r"C:\yolo\llm")

INPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "raw"
    / "표시ㆍ광고의 공정화에 관한 법률(법률)(제20712호)(20250121)_원본.md"
)

OUTPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "표시ㆍ광고의 공정화에 관한 법률(법률)(제20712호)(20250121)_정리본.md"
)


# =========================================================
# 문서 정보
# =========================================================

LAW_TITLE = "표시·광고의 공정화에 관한 법률"
LAW_SHORT_NAME = "표시광고법"

EXPECTED_ARTICLES = [
    "제1조",
    "제2조",
    "제3조",
    "제4조",
    "제4조의2",
    "제5조",
    "제6조",
    "제7조",
    "제7조의2",
    "제7조의3",
    "제7조의4",
    "제7조의5",
    "제8조",
    "제9조",
    "제10조",
    "제11조",
    "제12조",
    "제13조",
    "제14조",
    "제14조의2",
    "제15조",
    "제16조",
    "제16조의2",
    "제17조",
    "제18조",
    "제19조",
    "제20조",
]


# =========================================================
# 정규식
# =========================================================

PAGE_COMMENT_PATTERN = re.compile(
    r"^\s*<!--\s*page:\s*\d+\s*-->\s*$",
    flags=re.IGNORECASE,
)

PAGE_FOOTER_PATTERN = re.compile(
    r"^법제처\s+\d+\s+국가법령정보센터$"
)

CHAPTER_PATTERN = re.compile(
    r"^제\d+장\s+.+"
)

ARTICLE_PATTERN = re.compile(
    r"^제\d+조(?:의\d+)?"
    r"(?=\s*(?:\(|삭제|<|$))"
)

ARTICLE_KEY_PATTERN = re.compile(
    r"^###\s+"
    r"(?P<article>제\d+조(?:의\d+)?)"
    r"(?=\s*(?:\(|삭제|<|$))",
    flags=re.MULTILINE,
)

PARAGRAPH_PATTERN = re.compile(
    r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]"
)

NUMBERED_ITEM_PATTERN = re.compile(
    r"^\d+\.\s+"
)

KOREAN_ITEM_PATTERN = re.compile(
    r"^[가-하]\.\s+"
)

AMENDMENT_PATTERN = re.compile(
    r"^\[(?:전문개정|본조신설|본조개정|제목개정|시행일)[^\]]*\]$"
)

SUPPLEMENT_PATTERN = re.compile(
    r"^부칙\b"
)


# =========================================================
# 문자 정리
# =========================================================

def normalize_text(text: str) -> str:
    """문서 전체의 문자와 줄바꿈을 정규화한다."""

    text = unicodedata.normalize("NFC", text)

    text = text.replace("\ufeff", "")
    text = text.replace("\u00a0", " ")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    replacements = {
        "ㆍ": "·",
        "•": "·",
        "표시 · 광고": "표시·광고",
        "표시· 광고": "표시·광고",
        "표시 ·광고": "표시·광고",
        "상품 등": "상품등",
        "사업자 등": "사업자등",
        "A / S": "A/S",
    }

    for before, after in replacements.items():
        text = text.replace(before, after)

    return text


def normalize_line(line: str) -> str:
    """한 줄 안의 연속 공백을 정리한다."""

    line = line.strip()
    line = re.sub(r"[ \t]+", " ", line)

    return line


# =========================================================
# 불필요한 줄 판별
# =========================================================

def is_noise_line(line: str) -> bool:
    """페이지 번호, 반복 제목, 머리말과 꼬리말을 제거한다."""

    if not line:
        return True

    if PAGE_COMMENT_PATTERN.fullmatch(line):
        return True

    if PAGE_FOOTER_PATTERN.fullmatch(line):
        return True

    normalized_title = line.replace("ㆍ", "·").strip()

    if normalized_title == LAW_TITLE:
        return True

    return False


# =========================================================
# 구조 시작 줄 판별
# =========================================================

def is_new_block(line: str) -> bool:
    """새 문단 또는 새 구조가 시작되는 줄인지 확인한다."""

    patterns = (
        CHAPTER_PATTERN,
        ARTICLE_PATTERN,
        PARAGRAPH_PATTERN,
        NUMBERED_ITEM_PATTERN,
        KOREAN_ITEM_PATTERN,
        AMENDMENT_PATTERN,
        SUPPLEMENT_PATTERN,
    )

    return any(
        pattern.match(line)
        for pattern in patterns
    )


# =========================================================
# 줄 단위 데이터를 논리 문단으로 결합
# =========================================================

def build_logical_blocks(
    lines: list[str],
) -> tuple[list[str], str | None, str | None]:
    """
    PDF 변환 과정에서 잘린 줄을 하나의 논리적인 문단으로 합친다.

    반환값:
    - 본문 블록
    - 시행 및 법률 정보
    - 담당 부서 정보
    """

    blocks: list[str] = []

    enactment_info: str | None = None
    department_info: str | None = None

    current_block = ""

    for raw_line in lines:
        line = normalize_line(raw_line)

        if not line:
            continue

        if is_noise_line(line):
            continue

        normalized_line = line.replace("ㆍ", "·")

        # 제목과 약칭이 같이 표시된 줄
        if (
            LAW_TITLE in normalized_line
            and "약칭" in normalized_line
        ):
            continue

        # 시행일 및 법률 번호
        if normalized_line.startswith("[시행 "):
            enactment_info = normalized_line
            continue

        # 담당 부서
        if normalized_line.startswith("공정거래위원회"):
            department_info = normalized_line
            continue

        if is_new_block(normalized_line):
            if current_block:
                blocks.append(current_block.strip())

            current_block = normalized_line
            continue

        if current_block:
            current_block += " " + normalized_line
        else:
            current_block = normalized_line

    if current_block:
        blocks.append(current_block.strip())

    return blocks, enactment_info, department_info


# =========================================================
# 조문 제목과 본문 분리
# =========================================================

def split_article_block(
    block: str,
) -> tuple[str, str]:
    """
    조문 제목과 조문 본문을 분리한다.

    예:
    제1조(목적) 이 법은 ...
    -> 제1조(목적)
    -> 이 법은 ...
    """

    deleted_match = re.match(
        r"^(제\d+조(?:의\d+)?)\s+"
        r"(삭제(?:\s*<[^>]+>)?)$",
        block,
    )

    if deleted_match:
        article = deleted_match.group(1)
        deleted_text = deleted_match.group(2)

        return f"{article} {deleted_text}", ""

    titled_match = re.match(
        r"^(제\d+조(?:의\d+)?)"
        r"(\([^)]*\))"
        r"\s*(.*)$",
        block,
    )

    if titled_match:
        article = titled_match.group(1)
        title = titled_match.group(2)
        body = titled_match.group(3).strip()

        return f"{article}{title}", body

    basic_match = re.match(
        r"^(제\d+조(?:의\d+)?)\s*(.*)$",
        block,
    )

    if basic_match:
        article = basic_match.group(1)
        body = basic_match.group(2).strip()

        return article, body

    return block, ""


# =========================================================
# Markdown 구조 변환
# =========================================================

def format_markdown(
    blocks: list[str],
    enactment_info: str | None,
    department_info: str | None,
) -> str:

    output: list[str] = [
        f"# {LAW_TITLE}",
        "",
        f"- 약칭: {LAW_SHORT_NAME}",
    ]

    if enactment_info:
        output.append(f"- 법령 정보: {enactment_info}")

    if department_info:
        output.append(f"- 담당: {department_info}")

    output.extend(
        [
            "",
            "> 국가법령정보센터 원문을 Markdown 구조로 정리한 문서입니다.",
            "",
        ]
    )

    for block in blocks:
        # 장
        if CHAPTER_PATTERN.match(block):
            output.extend(
                [
                    f"## {block}",
                    "",
                ]
            )
            continue

        # 조문
        if ARTICLE_PATTERN.match(block):
            heading, body = split_article_block(block)

            output.extend(
                [
                    f"### {heading}",
                    "",
                ]
            )

            if body:
                output.extend(
                    [
                        body,
                        "",
                    ]
                )

            continue

        # 부칙
        if SUPPLEMENT_PATTERN.match(block):
            output.extend(
                [
                    f"## {block}",
                    "",
                ]
            )
            continue

        # 개정 정보
        if AMENDMENT_PATTERN.match(block):
            output.extend(
                [
                    f"> {block}",
                    "",
                ]
            )
            continue

        # 호 목록
        if NUMBERED_ITEM_PATTERN.match(block):
            output.extend(
                [
                    block,
                    "",
                ]
            )
            continue

        # 목 목록
        if KOREAN_ITEM_PATTERN.match(block):
            output.extend(
                [
                    f"   - {block}",
                    "",
                ]
            )
            continue

        # 항
        if PARAGRAPH_PATTERN.match(block):
            output.extend(
                [
                    block,
                    "",
                ]
            )
            continue

        # 일반 문단
        output.extend(
            [
                block,
                "",
            ]
        )

    result = "\n".join(output)

    # 빈 줄이 과도하게 반복되는 현상 제거
    result = re.sub(
        r"\n{3,}",
        "\n\n",
        result,
    )

    return result.strip() + "\n"


# =========================================================
# 조문 검증
# =========================================================

def validate_articles(markdown_text: str) -> None:
    """실제 Markdown 조문 제목을 기준으로 검증한다."""

    found_articles = [
        match.group("article")
        for match in ARTICLE_KEY_PATTERN.finditer(markdown_text)
    ]

    print(f"찾은 조문 수: {len(found_articles)}")
    print(f"찾은 조문: {found_articles}")

    missing_articles = [
        article
        for article in EXPECTED_ARTICLES
        if article not in found_articles
    ]

    unexpected_articles = [
        article
        for article in found_articles
        if article not in EXPECTED_ARTICLES
    ]

    if missing_articles:
        raise ValueError(
            "조문 검증 실패\n"
            f"누락된 조문: {missing_articles}"
        )

    if unexpected_articles:
        raise ValueError(
            "조문 검증 실패\n"
            f"예상하지 않은 조문: {unexpected_articles}"
        )

    if found_articles != EXPECTED_ARTICLES:
        raise ValueError(
            "조문 순서 검증 실패\n"
            f"예상 순서: {EXPECTED_ARTICLES}\n"
            f"발견 순서: {found_articles}"
        )

    print("조문 검증 완료: 총 27개 조문이 정상입니다.")


# =========================================================
# 장 검증
# =========================================================

def validate_chapters(markdown_text: str) -> None:
    """제1장부터 제5장까지 존재하는지 확인한다."""

    found_chapters = re.findall(
        r"(?m)^##\s+(제\d+장)\s+",
        markdown_text,
    )

    expected_chapters = [
        "제1장",
        "제2장",
        "제3장",
        "제4장",
        "제5장",
    ]

    if found_chapters != expected_chapters:
        raise ValueError(
            "장 검증 실패\n"
            f"예상 장: {expected_chapters}\n"
            f"발견 장: {found_chapters}"
        )

    print("장 검증 완료: 제1장부터 제5장까지 정상입니다.")


# =========================================================
# 실행
# =========================================================

def main() -> None:
    if not INPUT_MD_FILE.exists():
        raise FileNotFoundError(
            "입력 Markdown 파일을 찾을 수 없습니다.\n"
            f"확인 경로: {INPUT_MD_FILE}"
        )

    source_text = INPUT_MD_FILE.read_text(
        encoding="utf-8-sig"
    )

    normalized_text = normalize_text(source_text)

    blocks, enactment_info, department_info = (
        build_logical_blocks(
            normalized_text.splitlines()
        )
    )

    cleaned_markdown = format_markdown(
        blocks=blocks,
        enactment_info=enactment_info,
        department_info=department_info,
    )

    validate_articles(cleaned_markdown)
    validate_chapters(cleaned_markdown)

    OUTPUT_MD_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MD_FILE.write_text(
        cleaned_markdown,
        encoding="utf-8",
    )

    print()
    print("Markdown 정리가 완료되었습니다.")
    print(f"입력 파일: {INPUT_MD_FILE}")
    print(f"출력 파일: {OUTPUT_MD_FILE}")


if __name__ == "__main__":
    main()