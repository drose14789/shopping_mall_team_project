from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

try:
    from kiwipiepy import Kiwi
except ImportError:
    Kiwi = None


BASE_DIR = Path(r"C:\yolo\llm")

DEFAULT_INPUT = (
    BASE_DIR
    / "data"
    / "markdown"
    / "raw"
    / "소 비 자 분 쟁 해 결 기 준_원본.md"
)

DEFAULT_OUTPUT = (
    BASE_DIR
    / "data"
    / "markdown"
    / "cleaned"
    / "소비자분쟁해결기준_RAG_정리본.md"
)

TITLE = "소비자분쟁해결기준"

PAGE_RE = re.compile(
    r"^\s*<!--\s*page:\s*(\d+)\s*-->\s*$",
    re.I,
)

FOOTER_RE = re.compile(r"^\s*-\s*\d+\s*-\s*$")

APPENDIX_RE = re.compile(
    r"^\s*<\s*별표\s*([ⅠⅡⅢⅣ])\s*>\s*$"
)

INDUSTRY_RE = re.compile(
    r"^\s*(\d{1,2})\.\s*(.+?)"
    r"(?:\((\d+)개\s*(업종|품종)\))?\s*$"
)

TABLE_HEADER_COMPACT = {
    "분쟁유형해결기준비고",
    "번호업종품종해당품목",
    "품목품질보증기간부품보유기간",
    "품목내용연수",
}

ARTICLE_TEXT = [
    (
        "제1조",
        "목적",
        (
            "이 고시는 「소비자기본법」 제16조제2항과 같은 법 시행령 "
            "제8조제3항의 규정에 의해 일반적 소비자분쟁해결기준에 따라 "
            "품목별 소비자분쟁해결기준을 정함으로써 소비자와 사업자"
            "(이하 “분쟁당사자”라 한다) 간에 발생한 분쟁이 원활하게 "
            "해결될 수 있도록 구체적인 합의 또는 권고의 기준을 "
            "제시하는 데 그 목적이 있다."
        ),
    ),
    (
        "제2조",
        "피해구제청구",
        (
            "분쟁당사자 간에 합의가 이루어지지 않을 경우 분쟁당사자는 "
            "중앙행정기관의 장, 시·도지사, 한국소비자원장 또는 "
            "소비자단체에게 그 피해구제를 청구할 수 있다."
        ),
    ),
    (
        "제3조",
        "품목 및 보상기준",
        (
            "이 고시에서 정하는 대상 품목, 품목별 분쟁해결기준, "
            "품목별 품질보증기간 및 부품보유기간, 품목별 내용연수표는 "
            "각각 별표 Ⅰ, 별표 Ⅱ, 별표 Ⅲ, 별표 Ⅳ와 같다."
        ),
    ),
    (
        "제4조",
        "재검토기한",
        (
            "공정거래위원회는 「훈령·예규 등의 발령 및 관리에 관한 규정"
            "(대통령훈령 제334호)」에 따라 이 고시에 대하여 "
            "2016년 1월 1일을 기준으로 매 3년이 되는 시점"
            "(매 3년째의 12월 31일까지를 말한다)마다 그 타당성을 "
            "검토하여 개선 등의 조치를 하여야 한다."
        ),
    ),
]

SUPPLEMENTS = [
    (
        "제2007-54호, 2007. 10. 17.",
        "이 규정은 2007년 10월 17일부터 시행한다.",
    ),
    (
        "제2008-3호, 2008. 2. 29.",
        "이 규정은 2008년 2월 29일부터 시행한다.",
    ),
    (
        "제2009-1호, 2009. 1. 16.",
        "이 규정은 2009년 1월 16일부터 시행한다.",
    ),
    (
        "제2009-48호, 2009. 8. 20.",
        "이 규정은 2009년 8월 21일부터 시행한다.",
    ),
    (
        "제2010-1호, 2010. 1. 29.",
        "이 규정은 2010년 1월 29일부터 시행한다.",
    ),
    (
        "제2011-10호, 2011. 12. 28.",
        "이 규정은 2011년 12월 28일부터 시행한다.",
    ),
    (
        "제2014-4호, 2014. 3. 21.",
        "이 규정은 2014년 3월 21일부터 시행한다.",
    ),
    (
        "제2015-18호, 2015. 12. 29.",
        "이 고시는 발령한 날부터 시행한다.",
    ),
    (
        "제2016-15호, 2016. 10. 26.",
        "이 고시는 2016년 10월 26일부터 시행한다.",
    ),
    (
        "제2018-2호, 2018. 2. 28.",
        "이 고시는 발령한 날부터 시행한다.",
    ),
    (
        "제2019-3호, 2019. 4. 3.",
        (
            "이 고시는 발령한 날부터 시행한다. 다만, 스마트폰 및 "
            "휴대폰에 관한 개정사항은 2020년 1월 1일부터 시행한다."
        ),
    ),
]

PROTECTED_TERMS = [
    "소비자분쟁해결기준",
    "소비자기본법",
    "분쟁당사자",
    "품질보증기간",
    "부품보유기간",
    "손해배상",
    "구입가",
    "가입비",
    "총이용요금",
    "총대행요금",
    "정액감가상각",
    "감가상각비",
    "서비스구매대금",
    "계약해제",
    "계약해지",
    "제품교환",
    "무상수리",
    "유상수리",
    "수리불가능",
    "교환불가능",
    "인터넷쇼핑몰업",
    "소셜커머스",
    "신유형상품권",
    "전자지급수단",
]

POST_FIXES = {
    "손해 배상": "손해배상",
    "구입 가": "구입가",
    "가입 비": "가입비",
    "부담 액": "부담액",
    "잔여 금": "잔여금",
    "품질 보증 기간": "품질보증기간",
    "부품 보유 기간": "부품보유기간",
    "계약 해제": "계약해제",
    "계약 해지": "계약해지",
    "제품 교환": "제품교환",
    "무상 수리": "무상수리",
    "유상 수리": "유상수리",
    "수리 불가능": "수리불가능",
    "교환 불가능": "교환불가능",
    "감가 상각": "감가상각",
    "정액 감가상각": "정액감가상각",
    "서비스 구매 대금": "서비스구매대금",
    "총 이용 요금": "총이용요금",
    "총 대행 요금": "총대행요금",
    "하자발생 한": "하자 발생한",
    "잔여 횟수": "잔여횟수",
    "총 횟수": "총횟수",
    "귀 책인": "귀책인",
    "총 비용": "총비용",
    "중개 수수료": "중개수수료",
    "국제 결혼 중개": "국제결혼중개",
    "국제결혼 상대 국가": "국제결혼 상대국가",
    "선 급한": "선급한",
    "해제 일": "해제일",
    "지연인 도로": "지연인도로",
    "지연 인도로": "지연인도로",
    "부당 대금": "부당대금",
    "계약 이행": "계약이행",
    "구매 액": "구매액",
    "제공 받고": "제공받고",
    "회원 가입 계약": "회원가입계약",
    "관리 소홀": "관리소홀",
    "결혼 정보": "결혼정보",
    "상사 채권": "상사채권",
    "소멸 시효": "소멸시효",
    "권면 금액": "권면금액",
    "상환 의무": "상환의무",
    "제공 의무": "제공의무",
    "사용 비율": "사용비율",
    "특정 매장": "특정매장",
}

KIWI = Kiwi() if Kiwi is not None else None


@dataclass
class Page:
    number: int
    lines: list[str]


@dataclass
class Record:
    label: str = ""
    issue_parts: list[str] = field(default_factory=list)
    solution_parts: list[str] = field(default_factory=list)


@dataclass
class NoteGroup:
    marker: str
    parts: list[str] = field(default_factory=list)


@dataclass
class IndustryResult:
    sequence: list[Record | tuple[str, str]]
    notes: list[NoteGroup]
    leftovers: list[str]
    ambiguous: bool


def normalize_unicode(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\ufeff", "")
    value = value.replace("\u00a0", " ")
    value = value.replace("․", "·")
    value = value.replace("‧", "·")
    value = value.replace("ㆍ", "·")
    return value


def compact(value: str) -> str:
    return re.sub(r"\s+", "", normalize_unicode(value))


def normalize_display_line(value: str) -> str:
    value = normalize_unicode(value)
    value = re.sub(r"[ \t]+", " ", value).strip()
    value = re.sub(r"\s*·\s*", "·", value)
    return value


def safe_spacing(value: str) -> str:
    """
    PDF 줄바꿈으로 붙은 문장을 복원한다.

    Kiwi가 있으면 사용하되 법률 용어와 조문 참조는 보호한다.
    Kiwi가 없어도 실행되며, 이 경우 보수적인 규칙만 적용한다.
    """

    value = normalize_unicode(value)
    value = re.sub(r"\s+", "", value).strip()

    if not value:
        return ""

    saved: dict[str, str] = {}

    def protect(text: str) -> str:
        key = f"ZZKEEP{len(saved)}ZZ"
        saved[key] = text
        return key

    def protect_match(match: re.Match[str]) -> str:
        return protect(match.group(0))

    for pattern in (
        r"제\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+(?:의\d+)?호)?",
        r"\d+(?:\.\d+)?%",
        r"\d+(?:,\d{3})*원",
        r"\d+(?:\.\d+)?㎞",
    ):
        value = re.sub(pattern, protect_match, value)

    for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
        value = value.replace(term, protect(term))

    if KIWI is not None:
        try:
            value = KIWI.space(value)
        except Exception:
            pass

    for key, original in saved.items():
        value = value.replace(key, original)

    for before, after in POST_FIXES.items():
        value = value.replace(before, after)

    value = re.sub(r"\s*([×+/=])\s*", r"\1", value)
    value = re.sub(r"(\d)\s*%", r"\1%", value)
    value = re.sub(r"\s*·\s*", "·", value)
    value = re.sub(r"\s+([,.;:!?%)\]}>])", r"\1", value)
    value = re.sub(r"([(<\[{])\s+", r"\1", value)

    return re.sub(r"\s{2,}", " ", value).strip()


def parse_pages(source: str) -> list[Page]:
    source = normalize_unicode(source)

    pages: list[Page] = []
    current_number: int | None = None
    current_lines: list[str] = []

    for line in source.splitlines():
        marker = PAGE_RE.fullmatch(line)

        if marker:
            if current_number is not None:
                pages.append(Page(current_number, current_lines))

            current_number = int(marker.group(1))
            current_lines = []
            continue

        if current_number is not None:
            current_lines.append(line.rstrip())

    if current_number is not None:
        pages.append(Page(current_number, current_lines))

    return pages


def normalize_revision(line: str) -> str | None:
    line = normalize_display_line(line)

    match = re.match(
        r"^(제정|개정)\s*"
        r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*"
        r"(.+?)고시\s*제?\s*"
        r"(\d{2,4})\s*-\s*(\d+)호$",
        line,
    )

    if not match:
        return None

    action, year, month, day, agency, notice_year, notice_no = (
        match.groups()
    )

    agency = re.sub(r"\s+", "", agency)

    return (
        f"{action} {year}. {int(month)}. {int(day)}. "
        f"{agency} 고시 제{notice_year}-{notice_no}호"
    )


def extract_revisions(pages: Sequence[Page]) -> list[str]:
    result: list[str] = []

    for line in pages[0].lines:
        if not re.match(r"^\s*(제정|개정)", line):
            continue

        revision = normalize_revision(line)

        if revision:
            result.append(revision)

    return result


def appendix_starts(pages: Sequence[Page]) -> dict[str, int]:
    result: dict[str, int] = {}

    for page in pages:
        for line in page.lines:
            match = APPENDIX_RE.fullmatch(line.strip())

            if match:
                result[match.group(1)] = page.number

    return result


def parse_industry_heading(line: str) -> tuple[int, str] | None:
    normalized = normalize_display_line(line)
    match = INDUSTRY_RE.fullmatch(normalized)

    if not match:
        return None

    number = int(match.group(1))
    title = match.group(2).strip()
    count = match.group(3)
    unit = match.group(4)

    if not 1 <= number <= 62:
        return None

    if count is None:
        if not (
            number == 12
            and compact(title) == "동물사료"
        ):
            return None
    else:
        title = f"{title}({count}개 {unit})"

    return number, title


def flatten_appendix_two(
    pages: Sequence[Page],
) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []

    for page in pages:
        if not 12 <= page.number <= 161:
            continue

        for index, line in enumerate(page.lines):
            if FOOTER_RE.fullmatch(line):
                continue

            if APPENDIX_RE.fullmatch(line.strip()):
                continue

            result.append((page.number, index, line))

    return result


def split_industry_sections(
    pages: Sequence[Page],
) -> dict[int, tuple[str, list[tuple[int, int, str]]]]:
    flat = flatten_appendix_two(pages)
    starts: list[tuple[int, int, str]] = []

    for flat_index, (_, _, line) in enumerate(flat):
        heading = parse_industry_heading(line)

        if heading:
            number, title = heading
            starts.append((flat_index, number, title))

    if [number for _, number, _ in starts] != list(range(1, 63)):
        raise ValueError(
            "별표 Ⅱ 업종 번호가 1~62 순서로 인식되지 않았습니다."
        )

    result: dict[int, tuple[str, list[tuple[int, int, str]]]] = {}

    for index, (start, number, title) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(flat)
        result[number] = (title, flat[start + 1:end])

    return result


MARKER_RE = re.compile(
    r"(?<!\S)(\d+\)|[①②③④⑤⑥⑦⑧⑨⑩]|[-·]|※)(?=\s)"
    r"|(?<![A-Za-z])o(?=\s)"
    r"|\*(?=\s)"
)


def split_chunks(line: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []

    for match in re.finditer(
        r"\S(?:.*?\S)?(?=\s{2,}|$)",
        line,
    ):
        result.append((match.start(), match.group(0)))

    return result


def split_markers(
    start: int,
    chunk: str,
) -> list[tuple[int, str | None, str]]:
    matches = list(MARKER_RE.finditer(chunk))

    if not matches:
        return [(start, None, chunk)]

    result: list[tuple[int, str | None, str]] = []

    if matches[0].start() > 0:
        before = chunk[:matches[0].start()].strip()

        if before:
            result.append((start, None, before))

    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(chunk)
        )

        result.append(
            (
                start + match.start(),
                match.group(0),
                chunk[match.end():end].strip(),
            )
        )

    return result


def table_columns(line: str) -> tuple[int, int] | None:
    if not (
        "분" in line
        and "쟁" in line
        and "해" in line
        and "비" in line
    ):
        return None

    if "결" not in line or "고" not in line:
        return None

    return line.find("해"), line.find("비")


def is_table_header(line: str) -> bool:
    return compact(line) in TABLE_HEADER_COMPACT


def detect_subheading(line: str) -> str | None:
    normalized = normalize_display_line(line)

    if not normalized:
        return None

    if re.search(r"\(\d+\s*-\s*\d+\)$", normalized):
        return safe_spacing(normalized)

    if MARKER_RE.search(line):
        return None

    tokens = normalized.split()
    content_tokens = [
        token
        for token in tokens
        if not re.fullmatch(r"\([^)]*\)", token)
    ]

    if (
        2 <= len(content_tokens) <= 10
        and all(
            len(token) == 1
            and re.match(r"[가-힣A-Za-z]", token)
            for token in content_tokens
        )
    ):
        return safe_spacing("".join(tokens))

    return None


def line_starts_issue(line: str) -> bool:
    for start, chunk in split_chunks(line):
        for _, marker, body in split_markers(start, chunk):
            if marker and (
                re.fullmatch(r"\d+\)", marker)
                or marker
                in "①②③④⑤⑥⑦⑧⑨⑩-·"
            ):
                return True

            if body.strip():
                return False

    return False


def issue_complete(parts: Sequence[str]) -> bool:
    if not parts:
        return False

    return re.search(
        r"(경우|때|하자|피해|고장|분실|도난|해지|해제|취소|"
        r"미이행|지연|중단|불량|파손|훼손|사고|이내|이후|이전|"
        r"요구|거부|발생|상태)$",
        parts[-1].strip(),
    ) is not None


def solution_needs_continuation(
    parts: Sequence[str],
    text: str,
) -> bool:
    if not parts:
        return False

    previous = parts[-1]

    if (
        previous.count("(") > previous.count(")")
        or previous.endswith(("/", "총", "잔여횟", "구입"))
    ):
        return True

    return text.startswith(
        (
            "횟수)",
            "수/",
            "가 환급",
            "액 환급",
            "후 제품교환",
            "의 20%",
            "의 10%",
            "배상",
            "환급",
        )
    )


def split_accidental_mix(
    text: str,
) -> list[tuple[str | None, str]]:
    text = text.strip()

    match = re.match(
        r"^(.*(?:환급|배상|부담|교환|수리|지급|보상))\s+"
        r"((?:해|지|취소|중단|출국|입국).+경우)$",
        text,
    )

    if match:
        return [
            ("solution", match.group(1)),
            ("issue", match.group(2)),
        ]

    match = re.match(r"^(.*?)(등을 말함\.)$", text)

    if match and len(match.group(1)) > 3:
        return [
            ("solution", match.group(1)),
            ("note", match.group(2)),
        ]

    return [(None, text)]


def parse_generic_industry(
    lines: Sequence[tuple[int, int, str]],
) -> IndustryResult:
    sequence: list[Record | tuple[str, str]] = []
    notes: list[NoteGroup] = []
    leftovers: list[str] = []

    current: Record | None = None
    pending_solution: list[str] = []
    current_note: NoteGroup | None = None
    solution_start = 28
    note_start = 41

    def flush() -> None:
        nonlocal current

        if current and (
            current.issue_parts
            or current.solution_parts
        ):
            sequence.append(current)

        current = None

    def start_record(
        label: str = "",
        issue: str = "",
    ) -> None:
        nonlocal current, pending_solution

        flush()
        current = Record(label=label)

        if issue:
            current.issue_parts.append(issue)

        if pending_solution:
            current.solution_parts.extend(pending_solution)
            pending_solution = []

    def add_note(
        marker: str | None,
        text: str,
    ) -> None:
        nonlocal current_note

        if marker:
            current_note = NoteGroup(marker=marker)
            notes.append(current_note)

        if text:
            if current_note is None:
                current_note = NoteGroup(marker="*")
                notes.append(current_note)

            current_note.parts.append(text)

    next_line_starts_issue = [False] * len(lines)
    following_state = False

    for index in range(len(lines) - 1, -1, -1):
        next_line_starts_issue[index] = following_state
        line = lines[index][2]

        if (
            not line.strip()
            or FOOTER_RE.fullmatch(line)
            or table_columns(line)
            or is_table_header(line)
        ):
            continue

        if detect_subheading(line):
            following_state = False
            continue

        following_state = line_starts_issue(line)

    for line_index, (_, _, line) in enumerate(lines):
        if not line.strip() or FOOTER_RE.fullmatch(line):
            continue

        columns = table_columns(line)

        if columns:
            solution_start, note_start = columns
            current_note = None
            continue

        if is_table_header(line):
            continue

        subheading = detect_subheading(line)

        if subheading:
            flush()
            sequence.append(("subheading", subheading))
            current_note = None
            continue

        pieces: list[tuple[int, str | None, str]] = []

        for start, chunk in split_chunks(line):
            pieces.extend(split_markers(start, chunk))

        issue_piece_indexes = [
            index
            for index, (_, marker, _) in enumerate(pieces)
            if marker
            and (
                re.fullmatch(r"\d+\)", marker)
                or marker
                in "①②③④⑤⑥⑦⑧⑨⑩-·"
            )
        ]

        for piece_index, (x, marker, body) in enumerate(pieces):
            if marker and (
                re.fullmatch(r"\d+\)", marker)
                or marker
                in "①②③④⑤⑥⑦⑧⑨⑩-·"
            ):
                # 비고 열의 점 목록은 비고로 처리한다.
                if marker == "·" and x >= note_start - 2:
                    add_note("•", body)
                    continue

                if marker == "-" and x >= note_start + 4:
                    add_note("•", body)
                    continue

                start_record(marker, body)
                continue

            if marker == "o":
                later_issue = any(
                    index > piece_index
                    for index in issue_piece_indexes
                )

                if (
                    later_issue
                    or (
                        current is not None
                        and current.solution_parts
                        and next_line_starts_issue[line_index]
                    )
                ):
                    pending_solution.append(body)
                elif current is None:
                    pending_solution.append(body)
                else:
                    current.solution_parts.append(body)

                continue

            if marker in {"*", "※"}:
                add_note(marker, body)
                continue

            for override, part in split_accidental_mix(body):
                if not part:
                    continue

                if override:
                    field_name = override
                elif solution_needs_continuation(
                    current.solution_parts if current else [],
                    part,
                ):
                    field_name = "solution"
                elif (
                    current
                    and current.issue_parts
                    and not issue_complete(current.issue_parts)
                    and re.search(r"(경우|때)$", part)
                ):
                    field_name = "issue"
                elif (
                    current_note is not None
                    and x >= solution_start + 3
                ):
                    field_name = "note"
                elif re.search(
                    r"(환급|배상|교환|수리|지급|면제|공제|"
                    r"부담|보상|반환|정산)(?:함|한다|)$",
                    part,
                ):
                    field_name = "solution"
                elif re.search(
                    r"(경우|때|하자|피해|고장|분실|도난|"
                    r"해지|해제|취소|미이행|지연|중단|불량|"
                    r"파손|훼손|사고)$",
                    part,
                ):
                    field_name = "issue"
                elif x < solution_start - 2:
                    field_name = "issue"
                elif x < note_start - 1:
                    field_name = "solution"
                else:
                    field_name = "note"

                if field_name == "note":
                    add_note(None, part)
                elif field_name == "solution":
                    if current is None:
                        pending_solution.append(part)
                    else:
                        current.solution_parts.append(part)
                else:
                    if current is None:
                        start_record("", part)
                    else:
                        current.issue_parts.append(part)

    flush()

    leftovers.extend(pending_solution)

    ambiguous = bool(leftovers)

    suspicious_solution = re.compile(
        r"(등을 말함|내용연수|별표|기준이|품목에|우선 적용)"
    )

    for item in sequence:
        if isinstance(item, tuple):
            continue

        issue = safe_spacing("".join(item.issue_parts))
        solution = safe_spacing("".join(item.solution_parts))

        if not issue:
            ambiguous = True

        if suspicious_solution.search(solution):
            ambiguous = True

        if re.search(r"경우\s+지할 경우", issue):
            ambiguous = True

    return IndustryResult(
        sequence=sequence,
        notes=notes,
        leftovers=leftovers,
        ambiguous=ambiguous,
    )


def manual_records() -> dict[int, dict]:
    """
    PDF 텍스트 레이어에서 열 순서가 뒤섞인 핵심 업종은
    원문을 직접 대조해 행 관계를 고정한다.
    """

    return {
        1: {
            "subheadings": [],
            "rows": [
                (
                    "1)",
                    "설치하자로 인해 제품에 하자가 발생하는 경우",
                    "설치비 환급 및 하자 발생한 제품에 대한 손해배상",
                ),
                (
                    "2)",
                    "사업자의 가전제품 설치하자로 인해 발생한 소비자의 재산 및 신체상의 피해",
                    "사업자가 손해배상",
                ),
            ],
            "notes": [
                "설치에 대한 품질보증기간은 1년으로 함.",
            ],
        },
        2: {
            "subheadings": [],
            "rows": [
                (
                    "1)",
                    "사업자의 귀책사유로 인한 계약해제 및 해지",
                    "",
                ),
                (
                    "-",
                    "회원가입계약 성립 후 사업자의 만남 개시 전에 해지된 경우",
                    "가입비 환급 및 가입비의 20% 배상",
                ),
                (
                    "-",
                    "1회 만남 후 해지된 경우",
                    "가입비×(잔여횟수/총횟수)+가입비의 20% 환급",
                ),
                (
                    "-",
                    "첫 번째 만난 상대방이 계약서상 기재된 소비자의 우선 희망 조건에 부합하지 않아 해지된 경우",
                    "가입비 환급 및 가입비의 20% 배상",
                ),
                (
                    "2)",
                    "소비자의 계약해제 및 해지",
                    "",
                ),
                (
                    "-",
                    "회원가입계약 성립 후 사업자의 만남 개시 전에 해지된 경우",
                    "가입비의 80% 환급",
                ),
                (
                    "-",
                    "1회 만남 후 해지된 경우",
                    "가입비의 80%×(잔여횟수/총횟수) 환급",
                ),
            ],
            "notes": [
                (
                    "가입비라 함은 계약금, 연회비 등 명칭에 관계없이 "
                    "소비자가 사업자에게 지급한 일체의 금액을 말함."
                ),
                (
                    "귀책사유란 사업자가 명백하게 객관적으로 판별할 수 "
                    "있는 사항〔예: 결혼정보, 직업, 학력, 병력(病歷) 등〕에 "
                    "관한 정보를 상대방에게 허위로 제공한 경우, 관리소홀"
                    "(3개월 내 1회도 만남을 주선하지 않은 경우), 계약서상 "
                    "기재한 우선 희망 조건(종교, 직업 등 객관적인 내용에 "
                    "한정함)에 부적합한 상대를 소개한 경우 등을 말함."
                ),
                (
                    "횟수 대신 기간으로 계약한 계약을 해지할 경우에는 "
                    "해지일까지 일할 계산한 금액으로 정산하고 해지에 "
                    "책임 있는 당사자가 상대방에게 가입비의 20%를 배상함."
                ),
            ],
        },
        4: {
            "subheadings": [],
            "rows": [
                ("1)", "중도 계약해지", ""),
                (
                    "-",
                    "사업자의 귀책인 경우",
                    (
                        "손해배상 또는 소비자의 요청 시 사업자는 소비자의 "
                        "추가 비용 부담 없이 국제결혼중개 다시 이행"
                    ),
                ),
                ("-", "소비자 사정으로 인한 계약의 해지", ""),
                (
                    "·",
                    "계약체결 후 국제결혼 행사 일정이 확정되기 전에 해지할 경우",
                    "총비용 중 중개수수료의 10%에 해당하는 금액 소비자 부담",
                ),
                (
                    "·",
                    "국제결혼 행사 일정 확정 이후 국제결혼 상대국가로 출국하기 전에 해지할 경우",
                    "총비용의 20%에 해당하는 금액 소비자 부담",
                ),
                (
                    "·",
                    "국제결혼 상대국가로 출국한 이후 맞선 보기 전에 해지할 경우",
                    "총비용의 40%에 해당하는 금액 소비자 부담",
                ),
                (
                    "·",
                    "상대 국가에서 맞선 이후 해지할 경우",
                    "총비용의 50%에 해당하는 금액 소비자 부담",
                ),
                (
                    "·",
                    "상대 국가에서 결혼이 성사된 이후 해지할 경우",
                    "총비용의 90%에 해당하는 금액 소비자 부담",
                ),
                (
                    "·",
                    "결혼을 성사하고 국내에 입국한 이후 해지할 경우",
                    "총비용 전액 소비자 부담",
                ),
            ],
            "notes": [
                (
                    "비용을 사업자가 이미 수수한 경우에 사업자는 이미 "
                    "수수한 비용에서 소비자 부담액을 공제한 나머지 금액을 "
                    "소비자에게 환급함."
                ),
            ],
        },
        23: {
            "subheadings": ["상품권", "신유형 상품권"],
            "rows": [
                (
                    "1)",
                    (
                        "금액상품권의 경우 잔액환급비율의 금액 이상에 "
                        "상당하는 물품 또는 용역을 제공받고 그 잔액을 "
                        "환급하여 줄 것을 요구하였으나 잔액환급을 거부하는 경우"
                    ),
                    "잔액 현금 환급",
                ),
                (
                    "2)",
                    (
                        "특정상품에 대하여 상품권 상환을 거부하거나 할인매장 "
                        "또는 할인기간 중이라는 이유 등으로 상품권 상환을 거부하는 경우"
                    ),
                    (
                        "해당 상품 제공의무 이행 또는 상환을 제시한 "
                        "상품권의 권면금액 전액 현금 환급"
                    ),
                ),
                (
                    "3)",
                    (
                        "상품권발행자의 영업양도 등이 있는 경우 상품권발행자의 "
                        "변경 등의 이유로 상품권 상환을 거부하는 경우"
                    ),
                    "상환의무 이행",
                ),
                (
                    "4)",
                    (
                        "유효기간은 경과하였으나 상사채권 소멸시효(5년) "
                        "이내인 상품권의 상환을 거부하는 경우"
                    ),
                    (
                        "구매액의 100분의 90에 해당하는 현금, 물품 또는 "
                        "용역의 상환의무 이행"
                    ),
                ),
                (
                    "5)",
                    (
                        "물품상품권 또는 금액상품권의 경우 물품 또는 용역의 "
                        "제공이 불가능하거나 지체되어 해당 상품권의 현금상환을 "
                        "요구하였으나 이를 거부하는 경우"
                    ),
                    "상환의무 이행",
                ),
                (
                    "신유형-1)",
                    (
                        "신유형 상품권의 구매일로부터 7일 이내에 환급을 "
                        "요구하였으나 거부하는 경우"
                    ),
                    "상품권 구매액 전액 환급",
                ),
                (
                    "신유형-2)",
                    (
                        "금액형 상품권의 경우 잔액환급비율의 금액 이상에 "
                        "상당하는 물품 등을 제공받고 그 잔액을 환급하여 줄 "
                        "것을 요구하였으나 잔액 환급을 거부하는 경우"
                    ),
                    "잔액 환급",
                ),
                (
                    "신유형-3)",
                    (
                        "발행자 등이 판매하는 물품 등을 제공받기 위해 상품권을 "
                        "제시하였으나 특별한 사유 없이 제공을 거부하거나 "
                        "할인매장 또는 할인기간 중이라는 이유 등으로 제공을 거부하는 경우"
                    ),
                    (
                        "해당 물품 등의 제공의무를 이행하거나 제시한 상품권의 "
                        "구매를 위해 소비자가 지급한 금원을 전액 환급"
                    ),
                ),
                (
                    "신유형-4)",
                    (
                        "유효기간은 경과하였으나 상사채권 소멸시효(5년) "
                        "이내 상품권 금액 등 반환을 거부하는 경우"
                    ),
                    "구매액의 100분의 90 반환",
                ),
                (
                    "신유형-5)",
                    (
                        "물품 및 용역 제공형 상품권의 경우 물품 등의 제공이 "
                        "불가능하거나 통상적인 기간보다 현저히 지체되는 경우"
                    ),
                    "동일한 금전적 가치의 신유형 상품권으로 교환 또는 구매액 반환",
                ),
            ],
            "notes": [
                (
                    "금액형 상품권은 상품권 금액잔액을 상품권 구매 시 적용된 "
                    "할인율을 고려하여 환산한 금액의 100분의 90에 해당하는 금액 반환."
                ),
                (
                    "신유형 상품권의 잔액은 구매액을 기준으로 사용비율에 따라 "
                    "계산하여 남은 비율의 금액을 말함."
                ),
                (
                    "발행자가 미리 상품권에 표시한 경우 특정매장 또는 물품 "
                    "등에 대하여 상품권 사용을 제한할 수 있음."
                ),
            ],
        },
        25: {
            "subheadings": ["소셜커머스"],
            "rows": [
                (
                    "1)",
                    "사업자의 책임 있는 사유로 인한 계약해제·해지",
                    "서비스구매대금 환급",
                ),
                ("-", "상품에 대한 허위·과장광고 또는 기망행위에 의한 판매", ""),
                ("-", "계약 내용의 임의 변경", ""),
                ("-", "사업자의 서비스 중단 또는 사이트 무단 폐쇄", ""),
                ("-", "상품 제공업자의 서비스 중단", ""),
                ("-", "상품의 결함 및 결함 상품의 배송", ""),
                (
                    "2)",
                    "사업자가 소비자의 청약 철회를 제한하거나 방해하는 행위",
                    "서비스구매대금 환급 및 서비스구매대금의 10% 배상",
                ),
                ("-", "청약 철회 거부", ""),
                ("-", "청약 철회의 제한 또는 고의적 지연", ""),
                (
                    "3)",
                    "소비자의 책임 있는 사유로 인한 계약해제·해지",
                    "서비스구매대금 환급",
                ),
                ("-", "구입 후 7일 이내", ""),
                (
                    "4)",
                    "사업자가 소비자의 쿠폰 사용을 제한하는 경우",
                    "서비스구매대금 환급 및 서비스구매대금의 10% 배상",
                ),
                ("-", "일반 이용자와 고의적으로 차별", ""),
                ("5)", "상품구매 쿠폰 유효기간", ""),
                ("-", "유효기간 명시 불명확", "서비스구매대금 환급"),
                (
                    "-",
                    "쿠폰 사용기간 내 매진",
                    "서비스구매대금 환급 및 서비스구매대금의 10% 배상",
                ),
                ("6)", "상품구매 쿠폰 관련 기타 사항", ""),
                ("-", "쿠폰 발송 지연", "서비스구매대금 환급"),
                (
                    "-",
                    "소비자가 청약 철회 기간 내에 미사용 쿠폰의 일부 환급을 요구하는 경우",
                    "서비스구매대금에서 사용 쿠폰의 서비스구매대금을 제외하고 환급",
                ),
            ],
            "notes": [
                (
                    "분쟁해결기준에 관련 기준이 있는 품목에 대해서는 "
                    "그 품목의 기준을 우선 적용함."
                ),
            ],
        },
        43: {
            "subheadings": ["인터넷쇼핑몰업"],
            "rows": [
                ("1)", "허위·과장광고에 의한 계약체결", "계약해제"),
                ("2)", "물품이나 용역의 미인도", "계약해제 및 손해배상"),
                ("3)", "계약된 인도시기보다 지연인도", ""),
                (
                    "-",
                    (
                        "지연인도로 해당 물품이나 용역이 본래의 구매목적을 "
                        "달성하지 못한 경우"
                    ),
                    "계약해제 및 손해배상",
                ),
                (
                    "-",
                    "기타(지연인도로 인한 불편 야기 등)",
                    "계약해제 또는 손해배상",
                ),
                (
                    "4)",
                    "배송과정에서 훼손되거나 다른 물품·용역이 공급된 경우",
                    "제품교환 또는 구입가 환급",
                ),
                ("5)", "부당한 대금청구", "청구취소 또는 부당대금 환급"),
                (
                    "6)",
                    "기타 사업자의 귀책사유로 인한 계약 미이행",
                    "계약이행 또는 계약해제 및 손해배상",
                ),
            ],
            "notes": [
                (
                    "계약해제의 경우 소비자가 선급한 금액에 대한 환급은 "
                    "해제일로부터 3일 이내에 실시함."
                ),
            ],
        },
    }


def clean_raw_industry_lines(
    lines: Sequence[tuple[int, int, str]],
) -> list[str]:
    result: list[str] = []

    for _, _, line in lines:
        if not line.strip() or FOOTER_RE.fullmatch(line):
            continue

        if table_columns(line) or is_table_header(line):
            continue

        subheading = detect_subheading(line)

        if subheading:
            result.append(f"**{subheading}**")
            continue

        result.append(normalize_display_line(line))

    return result


def format_manual_industry(
    data: dict,
) -> list[str]:
    output: list[str] = []

    for subheading in data.get("subheadings", []):
        output.extend(
            [
                f"#### {subheading}",
                "",
            ]
        )

    for label, issue, solution in data["rows"]:
        issue = safe_spacing(issue)
        solution = safe_spacing(solution)

        output.append(f"- **분쟁유형 {label}:** {issue}")

        if solution:
            output.append(f"  - **해결기준:** {solution}")

        output.append("")

    if data.get("notes"):
        output.extend(
            [
                "#### 비고",
                "",
            ]
        )

        for note in data["notes"]:
            output.extend(
                [
                    f"- {safe_spacing(note)}",
                    "",
                ]
            )

    return output


SOLUTION_TERMS_RE = re.compile(
    r"(환급|배상|교환|수리|지급|면제|공제|부담|보상|반환|"
    r"정산|이행|청구취소|감액|연장)"
)

UNSAFE_TEXT_RE = re.compile(
    r"(구입상으로|보 경우|등상\(|경우에는 전체를대|"
    r"제품교환 환급할|환급 구입가 환급|구입에 대해|"
    r"가의 10%|운송 사에|구입가 격|별표 Ⅳ품목별|"
    r"등을 말함|기준이|품목에 대해서는|우선 적용함)"
)


def balanced_parentheses(text: str) -> bool:
    return (
        text.count("(") == text.count(")")
        and text.count("〔") == text.count("〕")
        and text.count("{") == text.count("}")
    )


def safe_generic_record(
    label: str,
    issue: str,
    solution: str,
) -> bool:
    if not issue or UNSAFE_TEXT_RE.search(issue):
        return False

    if not balanced_parentheses(issue):
        return False

    if solution:
        if UNSAFE_TEXT_RE.search(solution):
            return False

        if not SOLUTION_TERMS_RE.search(solution):
            return False

        if not balanced_parentheses(solution):
            return False

        if re.search(r"(또는|및|에|의|를|을|한|된|서)$", solution):
            return False

        if len(solution) > 220:
            return False

    elif label in {"-", "·", "항목"}:
        return False

    return True


def safe_generic_note(note: str) -> bool:
    if not note or UNSAFE_TEXT_RE.search(note):
        return False

    if not balanced_parentheses(note):
        return False

    return len(note) <= 500


def format_generic_industry(
    result: IndustryResult,
) -> tuple[list[str], int, int]:
    output: list[str] = []
    emitted_records = 0
    skipped_items = 0

    for item in result.sequence:
        if isinstance(item, tuple):
            output.extend(
                [
                    f"#### {item[1]}",
                    "",
                ]
            )
            continue

        issue = safe_spacing("".join(item.issue_parts))
        solution = safe_spacing(
            "".join(item.solution_parts)
        )
        label = item.label or "항목"

        if not safe_generic_record(
            label,
            issue,
            solution,
        ):
            skipped_items += 1
            continue

        output.append(f"- **분쟁유형 {label}:** {issue}")

        if solution:
            output.append(f"  - **해결기준:** {solution}")

        output.append("")
        emitted_records += 1

    safe_notes: list[str] = []

    for group in result.notes:
        note = safe_spacing("".join(group.parts))

        if safe_generic_note(note):
            safe_notes.append(note)
        elif note:
            skipped_items += 1

    if safe_notes:
        output.extend(
            [
                "#### 비고",
                "",
            ]
        )

        for note in safe_notes:
            output.extend(
                [
                    f"- {note}",
                    "",
                ]
            )

    if result.leftovers:
        skipped_items += len(result.leftovers)

    return output, emitted_records, skipped_items


def format_source_fallback(
    lines: Sequence[str],
) -> list[str]:
    output = [
        "#### 원문 대조용",
        "",
        (
            "> 아래 부분은 원본 PDF 텍스트 레이어의 열 순서가 뒤섞여 "
            "자동 행 연결의 신뢰도가 낮아, 누락 방지를 위해 함께 보존했습니다."
        ),
        "",
    ]

    for line in lines:
        output.append(f"> {line}")

    output.append("")
    return output


def clean_other_appendix(
    pages: Sequence[Page],
    appendix_id: str,
    start_page: int,
    end_page: int,
    title: str,
) -> list[str]:
    """
    별표 Ⅰ·Ⅲ·Ⅳ는 원본의 표 열이 여러 페이지에 걸쳐 이어진다.
    잘못된 열 연결을 만들지 않고, 반복 머리글만 제거한 원문 대조형으로
    보존한다. 별표 Ⅱ의 분쟁 행만 별도로 구조화한다.
    """

    output = [
        f"## 별표 {appendix_id}. {title}",
        "",
        (
            "> 이 별표는 표 열의 잘못된 연결을 피하기 위해 "
            "반복 머리글과 페이지 바닥글만 제거한 원문 대조형으로 보존했습니다."
        ),
        "",
    ]

    for page in pages:
        if not start_page <= page.number <= end_page:
            continue

        page_lines: list[str] = []

        for line in page.lines:
            if not line.strip() or FOOTER_RE.fullmatch(line):
                continue

            if APPENDIX_RE.fullmatch(line.strip()):
                continue

            normalized = normalize_display_line(line)

            if compact(normalized) == compact(title):
                continue

            if is_table_header(normalized):
                continue

            page_lines.append(normalized)

        if not page_lines:
            continue

        output.extend(
            [
                f"### 원본 페이지 {page.number}",
                "",
            ]
        )

        for line in page_lines:
            output.append(f"> {line}")

        output.append("")

    return output


def build_markdown(
    source: str,
    fallback_mode: str = "ambiguous",
) -> tuple[str, dict]:
    pages = parse_pages(source)

    if len(pages) != 165:
        raise ValueError(
            f"원본 페이지 수 오류: {len(pages)}개"
        )

    if [page.number for page in pages] != list(range(1, 166)):
        raise ValueError("페이지 번호가 1~165 순서가 아닙니다.")

    revisions = extract_revisions(pages)

    if len(revisions) != 25:
        raise ValueError(
            f"제·개정 이력 수 오류: {len(revisions)}개"
        )

    starts = appendix_starts(pages)

    if starts != {
        "Ⅰ": 4,
        "Ⅱ": 12,
        "Ⅲ": 162,
        "Ⅳ": 165,
    }:
        raise ValueError(
            f"별표 시작 페이지 오류: {starts}"
        )

    industries = split_industry_sections(pages)
    manual = manual_records()

    output = [
        f"# {TITLE}",
        "",
        (
            "> 공정거래위원회 고시 제2019-3호 원본을 "
            "RAG 검색에 맞게 업종·분쟁유형·해결기준·비고 구조로 정리했습니다."
        ),
        "",
        (
            "> 원문의 문구는 유지하고 PDF 줄바꿈으로 붙거나 끊어진 "
            "부분만 복원했습니다."
        ),
        "",
        "## 제·개정 이력",
        "",
    ]

    output.extend(f"- {revision}" for revision in revisions)
    output.append("")

    output.extend(["## 본문", ""])

    for article, title, body in ARTICLE_TEXT:
        output.extend(
            [
                f"### {article}({title})",
                "",
                body,
                "",
            ]
        )

    output.extend(["## 부칙", ""])

    for heading, body in SUPPLEMENTS:
        output.extend(
            [
                f"### 부칙 <{heading}>",
                "",
                body,
                "",
            ]
        )

    output.extend(
        clean_other_appendix(
            pages,
            "Ⅰ",
            4,
            11,
            "대상 품목",
        )
    )

    output.extend(
        [
            "## 별표 Ⅱ. 품목별 해결기준",
            "",
        ]
    )

    ambiguous_industries: list[int] = []
    structured_row_count = 0

    for number in range(1, 63):
        title, lines = industries[number]
        output.extend(
            [
                f"### {number}. {normalize_display_line(title)}",
                "",
            ]
        )

        if number in manual:
            output.extend(
                format_manual_industry(manual[number])
            )
            structured_row_count += len(manual[number]["rows"])

            if fallback_mode == "all":
                ambiguous_industries.append(number)
                output.extend(
                    format_source_fallback(
                        clean_raw_industry_lines(lines)
                    )
                )

            continue

        result = parse_generic_industry(lines)
        generic_output, emitted, skipped = (
            format_generic_industry(result)
        )
        output.extend(generic_output)
        structured_row_count += emitted

        needs_fallback = result.ambiguous or skipped

        if (
            fallback_mode == "all"
            or (
                fallback_mode == "ambiguous"
                and needs_fallback
            )
        ):
            ambiguous_industries.append(number)
            output.extend(
                format_source_fallback(
                    clean_raw_industry_lines(lines)
                )
            )

    output.extend(
        clean_other_appendix(
            pages,
            "Ⅲ",
            162,
            164,
            "품목별 품질보증기간 및 부품보유기간",
        )
    )

    output.extend(
        clean_other_appendix(
            pages,
            "Ⅳ",
            165,
            165,
            "품목별 내용연수표",
        )
    )

    result_text = "\n".join(output)
    result_text = re.sub(r"\n{3,}", "\n\n", result_text)
    result_text = result_text.strip() + "\n"

    report = validate_output(
        result_text,
        ambiguous_industries,
        structured_row_count,
    )

    return result_text, report


def validate_output(
    markdown: str,
    ambiguous_industries: Sequence[int],
    structured_row_count: int,
) -> dict:
    errors: list[str] = []

    if PAGE_RE.search(markdown):
        errors.append("페이지 주석이 남아 있습니다.")

    if re.search(r"(?m)^\s*-\s*\d+\s*-\s*$", markdown):
        errors.append("페이지 바닥글이 남아 있습니다.")

    if "```text" in markdown:
        errors.append("고정 폭 코드 블록이 남아 있습니다.")

    appendix_two_start = markdown.find("## 별표 Ⅱ.")
    appendix_three_start = markdown.find("## 별표 Ⅲ.")

    appendix_two_text = markdown[
        appendix_two_start:appendix_three_start
    ]

    industry_headings = [
        int(number)
        for number in re.findall(
            r"(?m)^###\s+(\d{1,2})\.\s+",
            appendix_two_text,
        )
    ]

    if industry_headings != list(range(1, 63)):
        errors.append(
            "별표 Ⅱ 업종 헤딩이 1~62 순서가 아닙니다."
        )

    appendix_headings = re.findall(
        r"(?m)^##\s+별표\s+([ⅠⅡⅢⅣ])\.",
        markdown,
    )

    if appendix_headings != ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ"]:
        errors.append(
            f"별표 구조 오류: {appendix_headings}"
        )

    if len(re.findall(r"(?m)^###\s+부칙\s+<", markdown)) != 11:
        errors.append("부칙 수가 11개가 아닙니다.")

    if "\ufffd" in markdown:
        errors.append("깨진 문자 U+FFFD가 있습니다.")

    if errors:
        raise ValueError(
            "정리본 검증 실패\n- "
            + "\n- ".join(errors)
        )

    return {
        "pages": 165,
        "revisions": 25,
        "articles": 4,
        "supplements": 11,
        "appendices": 4,
        "industries": 62,
        "structured_rows": structured_row_count,
        "ambiguous_industries": list(ambiguous_industries),
        "page_markers_removed": True,
        "page_footers_removed": True,
        "repeated_headers_removed": True,
        "code_blocks_removed": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "소비자분쟁해결기준 원본 Markdown을 "
            "RAG용 구조화 Markdown으로 변환합니다."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--fallback-mode",
        choices=("none", "ambiguous", "all"),
        default="ambiguous",
        help=(
            "원문 대조 섹션 포함 방식: "
            "none=미포함, ambiguous=불확실 업종만, all=모든 업종"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(
            "원본 Markdown 파일을 찾을 수 없습니다.\n"
            f"확인 경로: {args.input}"
        )

    source = args.input.read_text(
        encoding="utf-8-sig"
    )

    markdown, report = build_markdown(
        source,
        fallback_mode=args.fallback_mode,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        markdown,
        encoding="utf-8",
        newline="\n",
    )

    report_path = (
        args.report
        if args.report is not None
        else args.output.with_name(
            args.output.stem + "_검수보고서.txt"
        )
    )

    report_lines = [
        "소비자분쟁해결기준 정리본 검수 결과",
        f"- 원본 페이지: {report['pages']}개",
        f"- 제·개정 이력: {report['revisions']}개",
        f"- 본문 조문: {report['articles']}개",
        f"- 부칙: {report['supplements']}개",
        f"- 별표: {report['appendices']}개",
        f"- 별표Ⅱ 업종: {report['industries']}개",
        f"- 구조화 분쟁 항목: {report['structured_rows']}개",
        (
            "- 원문 대조 섹션이 추가된 업종: "
            + (
                ", ".join(
                    map(str, report["ambiguous_industries"])
                )
                if report["ambiguous_industries"]
                else "없음"
            )
        ),
        "- 페이지 주석 제거: 완료",
        "- 페이지 바닥글 제거: 완료",
        "- 반복 표 머리글 제거: 완료",
        "- 고정 폭 코드 블록 제거: 완료",
    ]

    report_path.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("정리본 생성 완료")
    print(f"- 입력: {args.input}")
    print(f"- 출력: {args.output}")
    print(f"- 검수보고서: {report_path}")
    print(f"- 구조화 분쟁 항목: {report['structured_rows']}개")
    print(
        "- 원문 대조 섹션 업종: "
        + (
            ", ".join(
                map(str, report["ambiguous_industries"])
            )
            if report["ambiguous_industries"]
            else "없음"
        )
    )


if __name__ == "__main__":
    main()