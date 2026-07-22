from __future__ import annotations

import re
import unicodedata
from pathlib import Path


# =========================================================
# 파일 경로
# =========================================================

BASE_DIR = Path(r"C:\yolo\llm")

INPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "raw"
    / "전자상거래 등에서의 상품 등의 정보제공에 관한 고시(공정거래위원회고시)(제2022-15호)(20230101)_원본.md"
)

OUTPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "전자상거래 등에서의 상품 등의 정보제공에 관한 고시(공정거래위원회고시)(제2022-15호)(20230101)_정리본.md"
)


TITLE = "전자상거래 등에서의 상품 등의 정보제공에 관한 고시"


# =========================================================
# 제거할 페이지 흔적
# =========================================================

NOISE_PATTERNS = (
    re.compile(r"^법제처\s*\d*\s*국가법령정보센터$"),
    re.compile(r"^국가법령정보센터$"),
    re.compile(r"^페이지\s*\d+(?:\s*/\s*\d+)?$", re.IGNORECASE),
    re.compile(r"^[-–—]?\s*\d+\s*[-–—]?$"),
)


# =========================================================
# Markdown 제목 변환 규칙
# =========================================================

MAJOR_SECTIONS = {
    "Ⅰ. 목적": "## Ⅰ. 목적",
    "Ⅱ. 일반원칙": "## Ⅱ. 일반원칙",
    "Ⅲ. 상품 등의 정보의 내용": "## Ⅲ. 상품 등의 정보의 내용",
    "Ⅳ. 상품 등의 정보 제공 방법": "## Ⅳ. 상품 등의 정보 제공 방법",
    "IV. 상품 등의 정보 제공 방법": "## Ⅳ. 상품 등의 정보 제공 방법",
}

THIRD_LEVEL_SECTIONS = {
    "1. 품목별 재화 등에 관한 정보":
        "### 1. 품목별 재화 등에 관한 정보",

    "2. 거래조건에 관한 정보":
        "### 2. 거래조건에 관한 정보",

    "표시 예시":
        "### 표시 예시",

    "KC 인증정보 표시 예시":
        "### KC 인증정보 표시 예시",
}

TRANSACTION_SECTIONS = {
    "가. 재화 등의 공급방법 및 공급시기",

    "나. 청약철회 및 계약해제에 관한 사항",

    (
        "다. 재화 등의 교환·반품·보증과 그 대금 환불 및 "
        "환불의 지연에 따른 배상금 지급의 조건·절차"
    ),

    (
        "라. 소비자피해보상의 처리, 재화 등에 대한 불만처리 및 "
        "소비자와 사업자 사이의 분쟁처리에 관한 사항"
    ),

    "마. 거래에 관한 약관의 내용 또는 확인할 수 있는 방법",
}


# =========================================================
# 문자 및 공백 정리
# =========================================================

def normalize_characters(text: str) -> str:
    """특수문자, 줄바꿈, 공백을 정리한다."""

    text = unicodedata.normalize("NFC", text)

    text = text.replace("\ufeff", "")
    text = text.replace("\u00a0", " ")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    replacements = {
        "ㆍ": "·",
        "•": "·",
        "A / S": "A/S",
        "A/S책임자": "A/S 책임자",
        "취급시": "취급 시",
        "사용시": "사용 시",
        "표시ㆍ광고": "표시·광고",
        "교환ㆍ반품": "교환·반품",
        "취소ㆍ환불": "취소·환불",
    }

    for before, after in replacements.items():
        text = text.replace(before, after)

    # 각 줄 끝의 불필요한 공백 제거
    text = re.sub(
        r"[ \t]+$",
        "",
        text,
        flags=re.MULTILINE,
    )

    return text


# =========================================================
# 페이지 번호 및 반복 문구 제거
# =========================================================

def is_noise(line: str) -> bool:
    stripped = line.strip()

    return any(
        pattern.fullmatch(stripped)
        for pattern in NOISE_PATTERNS
    )


# =========================================================
# 제목 정리
# =========================================================

def normalize_heading(
    line: str,
    title_seen: bool,
) -> tuple[str | None, bool]:

    stripped = line.strip()

    # 기존 Markdown의 # 기호를 제거하고 제목 내용만 비교
    plain = re.sub(
        r"^#{1,6}\s*",
        "",
        stripped,
    ).strip()

    # 문서 제목
    if plain == TITLE:
        if title_seen:
            return None, title_seen

        return f"# {TITLE}", True

    # Ⅰ, Ⅱ, Ⅲ, Ⅳ
    if plain in MAJOR_SECTIONS:
        return MAJOR_SECTIONS[plain], title_seen

    # 1. 품목별 정보 / 2. 거래조건
    if plain in THIRD_LEVEL_SECTIONS:
        return THIRD_LEVEL_SECTIONS[plain], title_seen

    # (1) 의류 ~ (40) 기타 재화
    product_match = re.fullmatch(
        r"\((\d{1,2})\)\s*(.+)",
        plain,
    )

    if product_match:
        product_number = int(product_match.group(1))
        product_name = product_match.group(2).strip()

        if 1 <= product_number <= 40:
            return (
                f"#### ({product_number}) {product_name}",
                title_seen,
            )

    # 거래조건의 가, 나, 다, 라, 마
    if plain in TRANSACTION_SECTIONS:
        return f"#### {plain}", title_seen

    # 부칙
    if plain.startswith("부칙"):
        return f"## {plain}", title_seen

    return stripped, title_seen


# =========================================================
# 목록 정리
# =========================================================

def normalize_list_line(line: str) -> str:
    """목록 번호와 하위 목록의 들여쓰기를 통일한다."""

    stripped = line.strip()

    # 인용문
    if stripped.startswith(">"):
        return re.sub(
            r"^>\s*",
            "> ",
            stripped,
        )

    # 1-1. 제품명 형태
    sub_number_match = re.fullmatch(
        r"(?:[-*]\s*)?(\d+)-(\d+)\.\s*(.+)",
        stripped,
    )

    if sub_number_match:
        major_number = sub_number_match.group(1)
        minor_number = sub_number_match.group(2)
        content = sub_number_match.group(3).strip()

        return (
            f"   - {major_number}-{minor_number}. "
            f"{content}"
        )

    # - 가. 내용 형태
    korean_sub_match = re.fullmatch(
        r"[-*]\s*([가-하])\.\s*(.+)",
        stripped,
    )

    if korean_sub_match:
        korean_number = korean_sub_match.group(1)
        content = korean_sub_match.group(2).strip()

        return f"   - {korean_number}. {content}"

    # 일반 bullet
    bullet_match = re.fullmatch(
        r"[-*]\s*(.+)",
        stripped,
    )

    if bullet_match:
        return f"- {bullet_match.group(1).strip()}"

    # 일반 번호 목록
    numbered_match = re.fullmatch(
        r"(\d+)\.\s*(.+)",
        stripped,
    )

    if numbered_match:
        number = numbered_match.group(1)
        content = numbered_match.group(2).strip()

        return f"{number}. {content}"

    return stripped


# =========================================================
# 제목 전후 빈 줄 정리
# =========================================================

def add_blank_lines(lines: list[str]) -> list[str]:
    output: list[str] = []

    for line in lines:
        if not line:
            if output and output[-1] != "":
                output.append("")
            continue

        is_heading = bool(
            re.match(r"^#{1,6}\s+", line)
        )

        # 제목 앞 빈 줄
        if is_heading and output and output[-1] != "":
            output.append("")

        output.append(line)

        # 제목 뒤 빈 줄
        if is_heading:
            output.append("")

    # 마지막 빈 줄 제거
    while output and output[-1] == "":
        output.pop()

    # 연속된 빈 줄을 하나로 정리
    cleaned: list[str] = []

    for line in output:
        if (
            line == ""
            and cleaned
            and cleaned[-1] == ""
        ):
            continue

        cleaned.append(line)

    return cleaned


# =========================================================
# Markdown 전체 정리
# =========================================================

def clean_markdown(text: str) -> str:
    text = normalize_characters(text)

    title_seen = False
    cleaned_lines: list[str] = []

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()

        # 페이지 번호, 머리말, 꼬리말 제거
        if is_noise(line):
            continue

        # 빈 줄
        if not line.strip():
            cleaned_lines.append("")
            continue

        # 제목 단계 정리
        normalized, title_seen = normalize_heading(
            line,
            title_seen,
        )

        # 중복 제목이면 제거
        if normalized is None:
            continue

        # 제목이 아닐 때만 목록 정리
        if not normalized.startswith("#"):
            normalized = normalize_list_line(normalized)

        cleaned_lines.append(normalized)

    cleaned_lines = add_blank_lines(cleaned_lines)

    result = "\n".join(cleaned_lines)

    # 빈 줄이 3개 이상 연속되는 경우 2개로 축소
    result = re.sub(
        r"\n{3,}",
        "\n\n",
        result,
    )

    return result.strip() + "\n"


# =========================================================
# 품목 번호 검증
# =========================================================

def validate_result(text: str) -> None:
    product_numbers = [
        int(number)
        for number in re.findall(
            r"(?m)^#### \((\d{1,2})\)\s+",
            text,
        )
    ]

    expected_numbers = set(range(1, 41))
    actual_numbers = set(product_numbers)

    missing_numbers = sorted(
        expected_numbers - actual_numbers
    )

    duplicated_numbers = sorted(
        number
        for number in actual_numbers
        if product_numbers.count(number) > 1
    )

    if missing_numbers:
        print(
            "[경고] 누락된 품목 번호:",
            missing_numbers,
        )

    if duplicated_numbers:
        print(
            "[경고] 중복된 품목 번호:",
            duplicated_numbers,
        )

    if not missing_numbers and not duplicated_numbers:
        print(
            "[확인] 품목 (1)부터 (40)까지 "
            "모두 정상적으로 존재합니다."
        )


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

    cleaned_text = clean_markdown(source_text)

    validate_result(cleaned_text)

    OUTPUT_MD_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MD_FILE.write_text(
        cleaned_text,
        encoding="utf-8",
    )

    print()
    print("Markdown 수정 및 정리가 완료되었습니다.")
    print(f"입력 파일: {INPUT_MD_FILE}")
    print(f"출력 파일: {OUTPUT_MD_FILE}")


if __name__ == "__main__":
    main()