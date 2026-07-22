from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from kiwipiepy import Kiwi
except ImportError:
    Kiwi = None


BASE_DIR = Path(r"C:\yolo\llm")

INPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "raw"
    / "개인정보 보호법(법률)(제20897호)(20251002)_원본.md"
)

OUTPUT_MD_FILE = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "개인정보 보호법(법률)(제20897호)(20251002)_정리본.md"
)

LAW_TITLE = "개인정보 보호법"

EXPECTED_CHAPTERS = [f"제{i}장" for i in range(1, 11)]
EXPECTED_SECTIONS = [f"제{i}절" for i in range(1, 5)]

PAGE_RE = re.compile(
    r"^<!--\s*page:\s*\d+\s*-->$",
    re.IGNORECASE,
)

FOOTER_RE = re.compile(
    r"^법제처\s+\d+\s+국가법령정보센터$"
)

CHAPTER_RE = re.compile(
    r"^제\d+장(?:\s|$)"
)

SECTION_RE = re.compile(
    r"^제\d+절(?:\s|$)"
)

ARTICLE_RE = re.compile(
    r"^제\d+조(?:의\d+)?(?=\(|\s+삭제|$)"
)

PARAGRAPH_RE = re.compile(
    r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳](?:\s|$)"
)

NUMBERED_ITEM_RE = re.compile(
    r"^\d+(?:의\d+)?\.\s*\S"
)

# 법령의 목 번호로 실제 사용하는 글자만 허용한다.
# [가-하]로 잡으면 줄바꿈으로 생긴 '우.' 등을 목록으로 오인할 수 있다.
KOREAN_ITEM_RE = re.compile(
    r"^(가|나|다|라|마|바|사|아|자|차|카|타|파|하)\.\s+\S"
)

NOTE_RE = re.compile(
    r"^\[(?:"
    r"본조신설|전문개정|제목개정|시행일|본조개정|"
    r"단순위헌|헌법불합치|한정위헌"
    r")"
)

SUPPLEMENT_RE = re.compile(
    r"^부칙\b"
)

TOKEN_RE = re.compile(
    r"[가-힣A-Za-z0-9]+(?:·[가-힣A-Za-z0-9]+)*"
)

KIWI = Kiwi() if Kiwi is not None else None


def normalize_line(line: str) -> str:
    line = unicodedata.normalize("NFC", line)
    line = line.replace("\ufeff", "")
    line = line.replace("\u00a0", " ")
    line = line.replace("ㆍ", "·")
    line = re.sub(r"[ \t]+", " ", line.strip())

    return line


def is_noise(line: str) -> bool:
    return (
        not line
        or line == LAW_TITLE
        or PAGE_RE.fullmatch(line) is not None
        or FOOTER_RE.fullmatch(line) is not None
    )


def is_structural_start(line: str) -> bool:
    patterns = (
        CHAPTER_RE,
        SECTION_RE,
        ARTICLE_RE,
        PARAGRAPH_RE,
        NUMBERED_ITEM_RE,
        KOREAN_ITEM_RE,
        NOTE_RE,
        SUPPLEMENT_RE,
    )

    return any(
        pattern.match(line)
        for pattern in patterns
    )


def has_unclosed_markup(parts: list[str]) -> bool:
    """
    개정일 표시가 다음 줄로 넘어간 경우를 보호한다.

    예:
    <개정 2023. 3.
    14.>
    """

    text = "".join(parts)

    return (
        text.count("<") > text.count(">")
        or text.count("[") > text.count("]")
        or text.count("(") > text.count(")")
    )


def make_token_frequency(
    lines: list[str],
) -> Counter[str]:
    """
    원본에서 온전하게 등장한 단어를 수집한다.

    줄 경계에서 '개인' + '정보'처럼 나뉜 경우,
    원본 다른 위치에 '개인정보'가 있으면 붙여 쓴다.
    """

    frequency: Counter[str] = Counter()

    for line in lines:
        if is_noise(line):
            continue

        for token in TOKEN_RE.findall(line):
            if len(token) >= 2:
                frequency[token] += 1

    return frequency


def boundary_separator(
    previous: str,
    following: str,
    token_frequency: Counter[str],
) -> str:
    """
    문서 전체를 다시 띄어쓰기하지 않고,
    PDF 줄바꿈 경계 한 곳에만 공백이 필요한지 판단한다.

    이 방식으로 개인정보, 정보주체, 보호위원회,
    제1항 등의 법률 용어를 보존한다.
    """

    if not previous or not following:
        return ""

    if previous[-1] in "([{\"“‘<·/":
        return ""

    if following[0] in ".,;:!?%)]}>”’":
        return ""

    if previous[-1] in ".?!,;:>]})”’":
        return " "

    previous_match = re.search(
        r"([가-힣A-Za-z0-9]+)$",
        previous,
    )

    following_match = re.match(
        r"([가-힣A-Za-z0-9]+)",
        following,
    )

    if not previous_match or not following_match:
        return " "

    previous_word = previous_match.group(1)
    following_word = following_match.group(1)
    combined_word = previous_word + following_word

    # 원본의 다른 줄에서 온전한 단어로 등장한 경우
    if combined_word in token_frequency:
        return ""

    # 제1항, 제7조의2, 제3호 등의 법령 참조
    if (
        re.fullmatch(
            r"제?\d+(?:조|항|호|장|절)?",
            previous_word,
        )
        and re.fullmatch(
            r"(?:의\d+|조|항|호|장|절|\d+)",
            following_word,
        )
    ):
        return ""

    # 날짜가 줄 사이에서 나뉜 경우
    if previous_word.isdigit() and following_word.isdigit():
        return " "

    # 줄 시작이 독립된 접속어인 경우
    if following_word in {"및", "또는"}:
        return " "

    # '이 법', '이 경우'의 '이'는 독립된 단어
    if following_word == "이" and following.startswith("이 "):
        return " "

    # 조사나 어미가 다음 줄로 넘어간 경우
    attached_followings = {
        "의", "은", "는", "이", "가", "을", "를",
        "에", "에서", "에게", "께", "로", "으로",
        "와", "과", "도", "만", "부터", "까지",
        "보다", "처럼", "조차", "마저", "이나", "나",
    }

    if following_word in attached_followings:
        return ""

    attached_endings = {
        "다", "고", "며", "면", "서", "지",
        "도록", "거나", "는데", "지만", "므로",
        "니", "라",
    }

    if following_word in attached_endings:
        return ""

    if previous_word == "다음":
        return " "

    # 관형형이나 보조용언 앞은 띄어쓰기
    spaced_previous_endings = (
        "하여야",
        "되어야",
        "해야",
        "알려야",
        "게",
        "도록",
        "할",
        "될",
        "한",
        "하는",
        "되는",
        "있는",
        "없는",
        "받은",
        "따른",
        "관한",
        "위한",
        "정하는",
        "필요한",
        "해당하는",
        "가능한",
        "아니한",
        "같은",
    )

    if previous_word.endswith(spaced_previous_endings):
        return " "

    # Kiwi는 문서 전체가 아니라 경계 단어만 판단하는 데 사용한다.
    # 설치되지 않은 환경에서는 보수적으로 공백을 넣어 단어 합침을 방지한다.
    if KIWI is None:
        return " "

    spaced = KIWI.space(combined_word)

    unspaced_index = 0
    space_positions: set[int] = set()

    for character in spaced:
        if character.isspace():
            space_positions.add(unspaced_index)
        else:
            unspaced_index += 1

    return (
        " "
        if len(previous_word) in space_positions
        else ""
    )


def join_parts(
    parts: list[str],
    token_frequency: Counter[str],
) -> str:
    result = parts[0]

    for following in parts[1:]:
        separator = boundary_separator(
            previous=result,
            following=following,
            token_frequency=token_frequency,
        )

        result += separator + following

    result = re.sub(r"\s+", " ", result).strip()
    result = re.sub(
        r"\s+([,.;:!?%)\]}>])",
        r"\1",
        result,
    )
    result = re.sub(
        r"([(<\[{])\s+",
        r"\1",
        result,
    )
    result = result.replace("삭제<", "삭제 <")

    result = re.sub(
        r"(?<!\s)(<(?:개정|신설|삭제|시행)[^<>]*>)",
        r" \1",
        result,
    )

    # 줄 경계에서만 발생할 수 있는 보조용언 결합 교정
    replacements = {
        "하여야한다": "하여야 한다",
        "하여야하며": "하여야 하며",
        "되어야한다": "되어야 한다",
        "하게할": "하게 할",
        "게하여서는": "게 하여서는",
    }

    for before, after in replacements.items():
        result = result.replace(before, after)

    return result


def extract_header(
    lines: list[str],
) -> tuple[int, str | None, list[str]]:
    start_index = next(
        (
            index
            for index, line in enumerate(lines)
            if CHAPTER_RE.match(line)
        ),
        None,
    )

    if start_index is None:
        raise ValueError("제1장 시작 위치를 찾지 못했습니다.")

    law_info: str | None = None
    contacts: list[str] = []

    for line in lines[:start_index]:
        if is_noise(line):
            continue

        if line.startswith("[시행 "):
            law_info = line
            continue

        if line.startswith("개인정보보호위원회"):
            contacts.append(line)
            continue

        # 전화번호가 다음 줄로 넘어간 경우
        if contacts and re.fullmatch(r"[\d,\s-]+", line):
            contacts[-1] += " " + line

    return start_index, law_info, contacts


def build_blocks(
    lines: list[str],
    start_index: int,
) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines[start_index:]:
        if is_noise(line):
            continue

        if (
            current
            and not has_unclosed_markup(current)
            and is_structural_start(line)
        ):
            blocks.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def split_article(
    text: str,
) -> tuple[str, str]:
    match = re.match(
        r"^(제\d+조(?:의\d+)?)(\([^)]*\))?\s*(.*)$",
        text,
    )

    if not match:
        raise ValueError(
            f"조문 제목을 분리하지 못했습니다: {text[:100]}"
        )

    article_number = match.group(1)
    article_title = match.group(2) or ""
    body = match.group(3).strip()

    if body.startswith("삭제"):
        return f"{article_number} {body}", ""

    return article_number + article_title, body


def make_markdown(
    blocks: list[list[str]],
    law_info: str | None,
    contacts: list[str],
    token_frequency: Counter[str],
) -> str:
    output: list[str] = [
        f"# {LAW_TITLE}",
        "",
    ]

    if law_info:
        output.append(f"- 법령 정보: {law_info}")

    if contacts:
        output.append("- 담당 부서:")
        output.extend(
            f"  - {contact}"
            for contact in contacts
        )

    output.extend(
        [
            "",
            (
                "> 국가법령정보센터 원문을 "
                "장·절·조·항·호·목 구조로 정리한 문서입니다."
            ),
            "",
        ]
    )

    in_supplement = False

    for parts in blocks:
        first_line = parts[0]

        text = join_parts(
            parts=parts,
            token_frequency=token_frequency,
        )

        if CHAPTER_RE.match(first_line):
            output.extend([f"## {text}", ""])
            continue

        if SECTION_RE.match(first_line):
            output.extend([f"### {text}", ""])
            continue

        if SUPPLEMENT_RE.match(first_line):
            in_supplement = True
            text = re.sub(
                r",(?=\d{4}\.)",
                ", ",
                text,
            )
            output.extend([f"## {text}", ""])
            continue

        if ARTICLE_RE.match(first_line):
            heading, body = split_article(text)

            heading_level = (
                "###"
                if in_supplement
                else "####"
            )

            output.extend(
                [
                    f"{heading_level} {heading}",
                    "",
                ]
            )

            if body:
                output.extend([body, ""])

            continue

        if NOTE_RE.match(first_line):
            output.extend([f"> {text}", ""])
            continue

        if PARAGRAPH_RE.match(first_line):
            output.extend([text, ""])
            continue

        if NUMBERED_ITEM_RE.match(first_line):
            match = re.match(
                r"^(\d+(?:의\d+)?\.)\s*(.*)$",
                text,
            )

            if not match:
                output.extend([text, ""])
                continue

            label, body = match.groups()

            if "의" in label:
                output.extend(
                    [
                        f"- **{label}** {body}",
                        "",
                    ]
                )
            else:
                output.extend(
                    [
                        f"{label} {body}",
                        "",
                    ]
                )

            continue

        if KOREAN_ITEM_RE.match(first_line):
            output.extend(
                [
                    f"   - {text}",
                    "",
                ]
            )
            continue

        output.extend([text, ""])

    result = "\n".join(output)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip() + "\n"


def normalized_original_body(
    lines: list[str],
    start_index: int,
) -> str:
    body_lines = [
        line
        for line in lines[start_index:]
        if not is_noise(line)
    ]

    return re.sub(
        r"\s+",
        "",
        "".join(body_lines),
    )


def normalized_markdown_body(
    markdown: str,
) -> str:
    body_lines: list[str] = []
    started = False

    for line in markdown.splitlines():
        if line.startswith("## 제1장"):
            started = True

        if not started:
            continue

        normalized = line

        normalized = re.sub(
            r"^#{2,4}\s+",
            "",
            normalized,
        )
        normalized = re.sub(
            r"^>\s*",
            "",
            normalized,
        )
        normalized = re.sub(
            r"^\s*-\s+\*\*([^*]+)\*\*\s*",
            r"\1",
            normalized,
        )
        normalized = re.sub(
            r"^\s*-\s+",
            "",
            normalized,
        )

        body_lines.append(normalized)

    return re.sub(
        r"\s+",
        "",
        "".join(body_lines),
    )


def validate(
    markdown: str,
    lines: list[str],
    start_index: int,
) -> None:
    chapter_numbers = re.findall(
        r"(?m)^##\s+제(\d+)장\b",
        markdown,
    )

    chapters = [
        f"제{number}장"
        for number in chapter_numbers
    ]

    section_numbers = re.findall(
        r"(?m)^###\s+제(\d+)절\b",
        markdown,
    )

    sections = [
        f"제{number}절"
        for number in section_numbers
    ]

    main_text, supplement_text = markdown.split(
        "\n## 부칙",
        maxsplit=1,
    )

    main_articles = re.findall(
        r"(?m)^####\s+"
        r"(제\d+조(?:의\d+)?)"
        r"(?=\(|\s+삭제)",
        main_text,
    )

    supplement_articles = re.findall(
        r"(?m)^###\s+"
        r"(제\d+조(?:의\d+)?)"
        r"(?=\(|\s+삭제)",
        supplement_text,
    )

    errors: list[str] = []

    if chapters != EXPECTED_CHAPTERS:
        errors.append(f"장 오류: {chapters}")

    if sections != EXPECTED_SECTIONS:
        errors.append(f"절 오류: {sections}")

    if len(main_articles) != 144:
        errors.append(
            f"본문 조문 제목 수 오류: {len(main_articles)}"
        )

    if len(set(main_articles)) != 127:
        errors.append(
            f"고유 본문 조문 수 오류: {len(set(main_articles))}"
        )

    if supplement_articles != ["제1조", "제2조"]:
        errors.append(
            f"부칙 조문 오류: {supplement_articles}"
        )

    original_characters = normalized_original_body(
        lines=lines,
        start_index=start_index,
    )

    markdown_characters = normalized_markdown_body(markdown)

    if original_characters != markdown_characters:
        errors.append(
            "원본과 정리본의 문자 내용이 일치하지 않습니다."
        )

    forbidden_patterns = {
        "개인 정보": "개인정보가 분리됨",
        "정보 주체": "정보주체가 분리됨",
        "보호 위원회": "보호위원회가 분리됨",
        "주민 등록 번호": "주민등록번호가 분리됨",
        "본 조 신설": "본조신설이 분리됨",
        "하여야한다": "하여야 한다 띄어쓰기 오류",
        "하여야하며": "하여야 하며 띄어쓰기 오류",
        "제척된 다": "제척된다 분리 오류",
    }

    for pattern, message in forbidden_patterns.items():
        if pattern in markdown:
            errors.append(message)

    if re.search(
        r"제\d+\s+(?:조|항|호|장|절)",
        markdown,
    ):
        errors.append(
            "법령 참조 번호에 잘못된 공백이 있습니다."
        )

    if re.search(
        r"(?m)^\s*-\s+[가-하]\.\s*$",
        markdown,
    ):
        errors.append(
            "내용 없는 가짜 목 목록이 있습니다."
        )

    if errors:
        raise ValueError(
            "검증 실패\n"
            + "\n".join(errors)
        )

    duplicate_articles = {
        article
        for article, count
        in Counter(main_articles).items()
        if count > 1
    }

    print("검증 완료")
    print(f"- 장: {len(chapters)}개")
    print(f"- 절: {len(sections)}개")
    print(f"- 본문 조문 제목: {len(main_articles)}개")
    print(f"- 고유 본문 조문: {len(set(main_articles))}개")
    print(f"- 중복 시행 조문: {len(duplicate_articles)}개")
    print(f"- 부칙 조문: {len(supplement_articles)}개")
    print("- 원본 문자 내용 일치")


def main() -> None:
    if not INPUT_MD_FILE.exists():
        raise FileNotFoundError(
            "원본 Markdown 파일을 찾을 수 없습니다.\n"
            f"확인 경로: {INPUT_MD_FILE}"
        )

    source_text = INPUT_MD_FILE.read_text(
        encoding="utf-8-sig"
    )

    lines = [
        normalize_line(line)
        for line in source_text.splitlines()
    ]

    start_index, law_info, contacts = extract_header(lines)

    token_frequency = make_token_frequency(lines)

    blocks = build_blocks(
        lines=lines,
        start_index=start_index,
    )

    cleaned_markdown = make_markdown(
        blocks=blocks,
        law_info=law_info,
        contacts=contacts,
        token_frequency=token_frequency,
    )

    validate(
        markdown=cleaned_markdown,
        lines=lines,
        start_index=start_index,
    )

    OUTPUT_MD_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MD_FILE.write_text(
        cleaned_markdown,
        encoding="utf-8",
    )

    print()
    print("정리본 생성 완료")
    print(f"입력 파일: {INPUT_MD_FILE}")
    print(f"출력 파일: {OUTPUT_MD_FILE}")


if __name__ == "__main__":
    main()