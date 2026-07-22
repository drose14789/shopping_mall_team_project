from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    from markdown_it import MarkdownIt
except ImportError as exc:
    raise SystemExit("markdown-it-py가 필요합니다: pip install markdown-it-py") from exc


# 사용자 설정
INPUT_DIR = Path(r"C:\yolo\llm\data\markdown\cleaned")
OUTPUT_DIR = Path(r"C:\yolo\llm\data\chunks")
OUTPUT_NAME = "documents"

CHILD_MAX_CHARS = 1400
PARENT_MAX_CHARS = 4200
OVERLAP_CHARS = 0


EXTENSIONS = {".md", ".markdown"}
TEXT_LANGS = {"", "text", "txt", "plain", "plaintext", "md", "markdown"}
FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
BOLD_LABEL_RE = re.compile(r"^[ \t]*\*\*(.+?)\*\*[ \t]*$")
HASH_LABEL_RE = re.compile(r"^[ \t]*#{1,6}[ \t]+(.+?)[ \t]*$")
SENTENCE_RE = re.compile(r"(?<=[.!?。！？])(?:[ \t]+|\n+)")
BOUNDARY_RE = re.compile(
    r"^[ \t]*(?:"
    r"제\d+조(?:의\d+)?(?:\([^)]*\))?|제\d+항|제\d+호|[가-하]목"
    r"|\d+(?:의\d+)?[.)]|\(\d+\)|[①-⑳]|[가-하ㄱ-ㅎ][.)]|[-+*·]"
    r")(?:[ \t]+|(?=[가-힣A-Za-z0-9])|$)"
)
MARKDOWN = MarkdownIt("commonmark", {"html": True})


@dataclass
class Section:
    title: str
    path: list[str]
    index: int
    start_line: int
    lines: list[str]


@dataclass
class Unit:
    text: str
    kind: str
    start_line: int
    end_line: int
    label: str = ""
    opener: str = ""
    closer: str = ""
    language: str = ""
    code_body: str = ""
    join_previous: bool = False


@dataclass
class Chunk:
    units: list[Unit]
    index: int

    @property
    def content(self) -> str:
        return render(self.units)

    @property
    def start_line(self) -> int:
        return min(unit.start_line for unit in self.units)

    @property
    def end_line(self) -> int:
        return max(unit.end_line for unit in self.units)

    @property
    def labels(self) -> list[str]:
        return list(dict.fromkeys(unit.label for unit in self.units if unit.label))


def read_md(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"UTF-8 Markdown 파일이 아닙니다: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")


def make_id(prefix: str, *values: object) -> str:
    raw = "\x1f".join(str(value) for value in values)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def render(units: Sequence[Unit]) -> str:
    parts: list[str] = []
    for unit in units:
        if not unit.text.strip():
            continue
        if parts and unit.join_previous:
            parts[-1] += unit.text
        else:
            parts.append(unit.text)
    return "\n\n".join(parts)


def full_path(section: Section) -> list[str]:
    path = [item.strip() for item in section.path if item.strip()]
    if not path or path[0] != section.title:
        path.insert(0, section.title)
    return path


def sections(text: str, fallback_title: str) -> list[Section]:
    lines = text.splitlines()
    headings: list[tuple[int, str, int, int]] = []
    tokens = MARKDOWN.parse(text)

    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.map is None or token.level != 0:
            continue
        title = tokens[index + 1].content.strip() if index + 1 < len(tokens) else ""
        if title:
            headings.append((int(token.tag[1]), title, token.map[0], token.map[1]))

    title = next((name for level, name, _, _ in headings if level == 1), fallback_title)
    if not headings:
        return [Section(title, [], 1, 1, lines)] if text.strip() else []

    result: list[Section] = []
    stack: list[str] = []
    section_index = 0

    first_start = headings[0][2]
    if first_start and any(line.strip() for line in lines[:first_start]):
        section_index += 1
        result.append(Section(title, [], section_index, 1, lines[:first_start]))

    for index, (level, name, _, heading_end) in enumerate(headings):
        stack = stack[: level - 1]
        stack.extend([""] * (level - 1 - len(stack)))
        stack.append(name)

        body_end = headings[index + 1][2] if index + 1 < len(headings) else len(lines)
        body = lines[heading_end:body_end]
        if not any(line.strip() for line in body):
            continue

        section_index += 1
        result.append(
            Section(title, [item for item in stack if item], section_index, heading_end + 1, body)
        )

    return result


def parse_fence(line: str) -> tuple[str, str] | None:
    match = FENCE_RE.match(line)
    if not match:
        return None
    marker, info = match.group(2), match.group(3).strip()
    if marker[0] == "`" and "`" in info:
        return None
    return marker, info.split(None, 1)[0].lower() if info else ""


def closes_fence(line: str, opener: str) -> bool:
    match = FENCE_RE.match(line)
    if not match or match.group(3).strip():
        return False
    marker = match.group(2)
    return marker[0] == opener[0] and len(marker) >= len(opener)


def render_code(opener: str, body: str, closer: str) -> str:
    if not body:
        return f"{opener}\n{closer}"
    return f"{opener}\n{body}{'' if body.endswith(chr(10)) else chr(10)}{closer}"


def label_of(line: str) -> str:
    for pattern in (BOLD_LABEL_RE, HASH_LABEL_RE):
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return ""


def code_units(
    body_lines: list[str],
    body_start: int,
    opener: str,
    closer: str,
    language: str,
) -> list[Unit]:
    def create(group: list[str], offset: int, label: str = "") -> Unit:
        body = "\n".join(group)
        start = body_start + offset if group else max(1, body_start - 1)
        return Unit(
            render_code(opener, body, closer),
            "code",
            start,
            start + max(0, len(group) - 1),
            label,
            opener,
            closer,
            language,
            body,
        )

    if language not in TEXT_LANGS:
        return [create(body_lines, 0)]

    boundaries = [index for index, line in enumerate(body_lines) if label_of(line)]
    if not boundaries:
        return [create(body_lines, 0)]

    starts = sorted(set([0, *boundaries, len(body_lines)]))
    return [
        create(body_lines[left:right], left, label_of(body_lines[left]))
        for left, right in zip(starts, starts[1:])
        if left < right
    ]


def indent(line: str) -> int:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    return sum(4 if char == "\t" else 1 for char in prefix)


def text_units(lines: list[str], start_line: int) -> list[Unit]:
    if not lines:
        return []

    kind = "quote" if all(line.lstrip().startswith(">") for line in lines) else "paragraph"
    result: list[Unit] = []
    current: list[str] = []
    current_start = start_line

    def flush(end_line: int) -> None:
        nonlocal current
        if current:
            unit_kind = "list" if BOUNDARY_RE.match(current[0]) else kind
            result.append(Unit("\n".join(current), unit_kind, current_start, end_line))
            current = []

    for offset, line in enumerate(lines):
        line_number = start_line + offset
        if current and BOUNDARY_RE.match(line):
            current_is_boundary = bool(BOUNDARY_RE.match(current[0]))
            if not current_is_boundary or indent(line) <= indent(current[0]):
                flush(line_number - 1)
        if not current:
            current_start = line_number
        current.append(line)

    flush(start_line + len(lines) - 1)
    return result


def units_for(section: Section) -> list[Unit]:
    result: list[Unit] = []
    paragraph: list[str] = []
    paragraph_start = section.start_line
    in_fence = False
    marker = language = opener = ""
    fence_start = section.start_line
    body: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            result.extend(text_units(paragraph, paragraph_start))
            paragraph = []

    for offset, line in enumerate(section.lines):
        line_number = section.start_line + offset

        if not in_fence:
            parsed = parse_fence(line)
            if parsed:
                flush()
                marker, language = parsed
                opener, fence_start, body, in_fence = line, line_number, [], True
                continue
            if not line.strip():
                flush()
                paragraph_start = line_number + 1
                continue
            if not paragraph:
                paragraph_start = line_number
            paragraph.append(line)
            continue

        if closes_fence(line, marker):
            result.extend(code_units(body, fence_start + 1, opener, line, language))
            marker = language = opener = ""
            body, in_fence = [], False
        else:
            body.append(line)

    flush()
    if in_fence:
        result.extend(code_units(body, fence_start + 1, opener, marker, language))
    return [unit for unit in result if unit.text.strip()]


def spans(text: str, limit: int) -> list[tuple[int, int]]:
    if not text:
        return []

    points = [0, *(match.end() for match in SENTENCE_RE.finditer(text)), len(text)]
    atoms = [(left, right) for left, right in zip(points, points[1:]) if left < right]
    result: list[tuple[int, int]] = []
    current_start = current_end = atoms[0][0]

    for left, right in atoms:
        if right - left > limit:
            if current_end > current_start:
                result.append((current_start, current_end))
            cursor = left
            while cursor < right:
                end = min(cursor + limit, right)
                if end < right:
                    boundary = max(
                        text.rfind("\n", cursor, end),
                        text.rfind(" ", cursor, end),
                        text.rfind("\t", cursor, end),
                    )
                    if boundary > cursor + limit // 2:
                        end = boundary + 1
                result.append((cursor, end))
                cursor = end
            current_start = current_end = right
            continue

        if current_end > current_start and right - current_start > limit:
            result.append((current_start, current_end))
            current_start = left
        current_end = right

    if current_end > current_start:
        result.append((current_start, current_end))
    return result


def start_line(text: str, offset: int, base: int) -> int:
    return base + text[:offset].count("\n")


def end_line(text: str, offset: int, base: int) -> int:
    return base if offset <= 0 else base + text[: offset - 1].count("\n")


def code_line_spans(unit: Unit, limit: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = current_start = 0

    for line in unit.code_body.splitlines(keepends=True):
        line_end = cursor + len(line)
        if len(render_code(unit.opener, line, unit.closer)) > limit:
            raise ValueError(
                "프로그래밍 코드 한 줄이 자식 청크 한도를 초과합니다: "
                f"line={unit.start_line}, language={unit.language or 'unknown'}"
            )
        candidate = unit.code_body[current_start:line_end]
        if cursor > current_start and len(render_code(unit.opener, candidate, unit.closer)) > limit:
            result.append((current_start, cursor))
            current_start = cursor
        cursor = line_end

    if current_start < len(unit.code_body):
        result.append((current_start, len(unit.code_body)))
    return result


def split_unit(unit: Unit) -> list[Unit]:
    if len(unit.text) <= CHILD_MAX_CHARS:
        return [unit]

    if unit.kind != "code":
        ranges = spans(unit.text, CHILD_MAX_CHARS)
        return [
            Unit(
                unit.text[left:right],
                unit.kind,
                start_line(unit.text, left, unit.start_line),
                end_line(unit.text, right, unit.start_line),
                unit.label,
                join_previous=unit.join_previous if index == 0 else True,
            )
            for index, (left, right) in enumerate(ranges)
        ]

    body_limit = CHILD_MAX_CHARS - len(render_code(unit.opener, "", unit.closer)) - 1
    if body_limit < 20:
        raise ValueError("코드 fence가 자식 청크 한도에 비해 너무 깁니다.")

    ranges = spans(unit.code_body, body_limit) if unit.language in TEXT_LANGS else code_line_spans(unit, CHILD_MAX_CHARS)
    return [
        Unit(
            render_code(unit.opener, unit.code_body[left:right], unit.closer),
            "code",
            start_line(unit.code_body, left, unit.start_line),
            end_line(unit.code_body, right, unit.start_line),
            unit.label,
            unit.opener,
            unit.closer,
            unit.language,
            unit.code_body[left:right],
        )
        for left, right in ranges
    ]


def overlap(units: Sequence[Unit]) -> list[Unit]:
    if OVERLAP_CHARS <= 0:
        return []
    selected: list[Unit] = []
    size = 0
    for unit in reversed(units):
        if size + len(unit.text) > OVERLAP_CHARS:
            break
        selected.append(unit)
        size += len(unit.text)
    return list(reversed(selected))


def same_label(current: Sequence[Unit], unit: Unit) -> bool:
    labels = {item.label for item in current if item.label}
    return (not labels and not unit.label) or (bool(unit.label) and labels == {unit.label})


def pack(units: Sequence[Unit], limit: int, use_overlap: bool = False) -> list[list[Unit]]:
    groups: list[list[Unit]] = []
    current: list[Unit] = []

    for unit in units:
        label_boundary = bool(current) and not same_label(current, unit)
        too_long = bool(current) and len(render([*current, unit])) > limit
        if label_boundary or too_long:
            groups.append(current)
            current = overlap(current) if use_overlap and not label_boundary else []
            if current and len(render([*current, unit])) > limit:
                current = []
        current.append(unit)

    if current:
        groups.append(current)
    return groups


def chunks(units: Sequence[Unit], limit: int, use_overlap: bool = False) -> list[Chunk]:
    return [Chunk(list(group), index) for index, group in enumerate(pack(units, limit, use_overlap), 1)]


def metadata(source: str, section: Section, chunk: Chunk, parent_index: int, child: bool) -> dict:
    data = {
        "source_file": source,
        "document_title": section.title,
        "heading_path": full_path(section),
        "section_index": section.index,
        "parent_index": parent_index,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "char_count": len(chunk.content),
        "semantic_labels": chunk.labels,
    }
    if child:
        data["chunk_index"] = chunk.index
    return data


def records(source: str, section: Section, units: list[Unit]) -> tuple[list[dict], list[dict]]:
    pieces = [piece for unit in units for piece in split_unit(unit)]
    parent_rows: list[dict] = []
    child_rows: list[dict] = []

    for parent in chunks(pieces, PARENT_MAX_CHARS):
        parent_id = make_id(
            "parent", source, section.index, parent.index,
            parent.start_line, parent.end_line, parent.content,
        )
        parent_rows.append(
            {
                "id": parent_id,
                "content": parent.content,
                "metadata": metadata(source, section, parent, parent.index, False),
            }
        )

        for child in chunks(parent.units, CHILD_MAX_CHARS, True):
            child_id = make_id(
                "chunk", parent_id, child.index,
                child.start_line, child.end_line, child.content,
            )
            child_rows.append(
                {
                    "id": child_id,
                    "parent_id": parent_id,
                    "content": child.content,
                    "metadata": metadata(source, section, child, parent.index, True),
                }
            )

    return parent_rows, child_rows


def balanced(text: str) -> bool:
    opened: str | None = None
    for line in text.splitlines():
        if opened is None:
            parsed = parse_fence(line)
            if parsed:
                opened = parsed[0]
        elif closes_fence(line, opened):
            opened = None
    return opened is None


def validate(parents: Sequence[dict], children: Sequence[dict]) -> None:
    if not parents or not children:
        raise ValueError("생성된 부모 또는 자식 청크가 없습니다.")

    parent_ids = {row["id"] for row in parents}
    if len(parent_ids) != len(parents):
        raise ValueError("중복된 부모 ID가 있습니다.")
    if len({row["id"] for row in children}) != len(children):
        raise ValueError("중복된 자식 ID가 있습니다.")

    parent_content = {row["id"]: row["content"] for row in parents}
    for rows, limit, name in ((parents, PARENT_MAX_CHARS, "부모"), (children, CHILD_MAX_CHARS, "자식")):
        for row in rows:
            content, meta = row["content"], row["metadata"]
            if not content.strip():
                raise ValueError(f"빈 {name} 청크입니다: {row['id']}")
            if len(content) > limit:
                raise ValueError(f"{name} 청크 길이 초과: {row['id']}")
            if not balanced(content):
                raise ValueError(f"{name} 코드 fence 오류: {row['id']}")
            if meta["start_line"] <= 0 or meta["end_line"] < meta["start_line"]:
                raise ValueError(f"{name} 줄 번호 오류: {row['id']}")
            if len(set(meta["semantic_labels"])) > 1:
                raise ValueError(f"{name} 의미 라벨 혼합: {row['id']}")

    for row in children:
        parent_id = row["parent_id"]
        if parent_id not in parent_ids:
            raise ValueError(f"존재하지 않는 parent_id: {row['id']}")
        if row["content"] not in parent_content[parent_id]:
            raise ValueError(f"부모 내용에 없는 자식 청크: {row['id']}")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def settings_ok() -> None:
    if CHILD_MAX_CHARS < 200:
        raise ValueError("CHILD_MAX_CHARS는 200 이상이어야 합니다.")
    if PARENT_MAX_CHARS <= CHILD_MAX_CHARS:
        raise ValueError("PARENT_MAX_CHARS는 CHILD_MAX_CHARS보다 커야 합니다.")
    if not 0 <= OVERLAP_CHARS < CHILD_MAX_CHARS:
        raise ValueError("OVERLAP_CHARS 범위가 올바르지 않습니다.")
    if OUTPUT_NAME in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9가-힣._-]+", OUTPUT_NAME):
        raise ValueError("OUTPUT_NAME 형식이 올바르지 않습니다.")


def markdown_files() -> list[Path]:
    if not INPUT_DIR.is_dir():
        raise ValueError(f"입력 폴더가 없습니다: {INPUT_DIR}\nINPUT_DIR을 실제 경로로 수정하세요.")
    files = sorted(path for path in INPUT_DIR.rglob("*") if path.is_file() and path.suffix.lower() in EXTENSIONS)
    if not files:
        raise ValueError(f"Markdown 파일이 없습니다: {INPUT_DIR}")
    return files


def main() -> int:
    settings_ok()
    files = markdown_files()
    parents: list[dict] = []
    children: list[dict] = []

    for path in files:
        source = path.relative_to(INPUT_DIR).as_posix()
        has_content = False
        for section in sections(read_md(path), path.stem):
            units = units_for(section)
            if not units:
                continue
            has_content = True
            parent_rows, child_rows = records(source, section, units)
            parents.extend(parent_rows)
            children.extend(child_rows)
        if not has_content:
            raise ValueError(f"청킹할 본문이 없는 Markdown 파일입니다: {path}")

    validate(parents, children)
    parent_path = OUTPUT_DIR / f"{OUTPUT_NAME}.parents.jsonl"
    child_path = OUTPUT_DIR / f"{OUTPUT_NAME}.children.jsonl"
    write_jsonl(parent_path, parents)
    write_jsonl(child_path, children)

    print(f"files   : {len(files)}")
    print(f"parents : {len(parents)} -> {parent_path}")
    print(f"children: {len(children)} -> {child_path}")
    print("validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())