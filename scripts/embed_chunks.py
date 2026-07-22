from __future__ import annotations

import json
import math
from pathlib import Path


# 사용자 설정
INPUT_FILE = Path(r"C:\yolo\llm\data\chunks\documents.children.jsonl")
OUTPUT_FILE = Path(
    r"C:\yolo\llm\data\embeddings\documents.children.embeddings.jsonl"
)

MODEL_NAME = "BAAI/bge-m3"
BATCH_SIZE = 8
DEVICE: str | None = None  # None: 자동 선택, "cpu" 또는 "cuda"


def read_chunks(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"입력 파일이 없습니다: {path}")

    chunks: list[dict] = []
    ids: set[str] = set()

    with path.open("r", encoding="utf-8-sig") as file:
        for line_no, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON 오류: {path}:{line_no}") from exc

            validate_chunk(chunk, line_no)

            if chunk["id"] in ids:
                raise ValueError(f"중복 id: {chunk['id']}")
            ids.add(chunk["id"])
            chunks.append(chunk)

    if not chunks:
        raise ValueError("임베딩할 자식 청크가 없습니다.")

    return chunks


def validate_chunk(chunk: object, line_no: int) -> None:
    if not isinstance(chunk, dict):
        raise ValueError(f"JSON 객체가 아닙니다: line={line_no}")

    for field in ("id", "parent_id", "content", "metadata"):
        if field not in chunk:
            raise ValueError(f"필수 필드 누락: line={line_no}, field={field}")

    if not isinstance(chunk["id"], str) or not chunk["id"].strip():
        raise ValueError(f"id가 올바르지 않습니다: line={line_no}")
    if not isinstance(chunk["parent_id"], str) or not chunk["parent_id"].strip():
        raise ValueError(f"parent_id가 올바르지 않습니다: line={line_no}")
    if not isinstance(chunk["content"], str) or not chunk["content"].strip():
        raise ValueError(f"content가 비어 있습니다: line={line_no}")
    if not isinstance(chunk["metadata"], dict):
        raise ValueError(f"metadata가 객체가 아닙니다: line={line_no}")


def embedding_text(chunk: dict) -> str:
    content = chunk["content"].strip()
    path = chunk["metadata"].get("heading_path", [])

    if not isinstance(path, list):
        raise ValueError(f"heading_path가 목록이 아닙니다: {chunk['id']}")

    heading = " > ".join(str(item).strip() for item in path if str(item).strip())
    return f"{heading}\n\n{content}" if heading else content


def load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "sentence-transformers가 필요합니다.\n"
            "설치: python -m pip install -U sentence-transformers"
        ) from exc

    return SentenceTransformer(MODEL_NAME, device=DEVICE)


def create_embeddings(model, texts: list[str]):
    return model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def write_result(path: Path, chunks: list[dict], vectors) -> tuple[int, int]:
    if len(chunks) != len(vectors):
        raise ValueError("청크 수와 임베딩 수가 일치하지 않습니다.")

    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    dimension = 0

    try:
        with temp.open("w", encoding="utf-8", newline="\n") as file:
            for chunk, vector in zip(chunks, vectors, strict=True):
                values = [float(value) for value in vector]

                if not values or not all(math.isfinite(value) for value in values):
                    raise ValueError(f"잘못된 임베딩: {chunk['id']}")

                if dimension == 0:
                    dimension = len(values)
                elif len(values) != dimension:
                    raise ValueError(f"임베딩 차원 불일치: {chunk['id']}")

                row = {
                    **chunk,
                    "embedding": values,
                    "embedding_metadata": {
                        "model": MODEL_NAME,
                        "dimension": dimension,
                        "normalized": True,
                    },
                }
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()

    return len(chunks), dimension


def validate_settings() -> None:
    if INPUT_FILE.resolve() == OUTPUT_FILE.resolve():
        raise ValueError("입력 파일과 출력 파일은 달라야 합니다.")
    if BATCH_SIZE < 1:
        raise ValueError("BATCH_SIZE는 1 이상이어야 합니다.")
    if not MODEL_NAME.strip():
        raise ValueError("MODEL_NAME이 비어 있습니다.")


def main() -> int:
    validate_settings()
    chunks = read_chunks(INPUT_FILE)
    texts = [embedding_text(chunk) for chunk in chunks]

    model = load_model()
    vectors = create_embeddings(model, texts)
    count, dimension = write_result(OUTPUT_FILE, chunks, vectors)

    print(f"chunks    : {count}")
    print(f"model     : {MODEL_NAME}")
    print(f"dimension : {dimension}")
    print(f"output    : {OUTPUT_FILE}")
    print("validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())