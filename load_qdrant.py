from __future__ import annotations

import json
import math
import uuid
from pathlib import Path


# 사용자 설정
INPUT_FILE = Path(
    r"C:\Users\M\Desktop\shopping_mall_team_project\data\embeddings\documents.children.embeddings.jsonl"
)
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "legal_chunks"
BATCH_SIZE = 64


def read_chunks(path: Path) -> tuple[list[dict], int]:
    if not path.is_file():
        raise FileNotFoundError(f"입력 파일이 없습니다: {path}")

    chunks: list[dict] = []
    ids: set[str] = set()
    dimension = 0

    with path.open("r", encoding="utf-8-sig") as file:
        for line_no, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON 오류: line={line_no}") from exc

            vector = validate_chunk(chunk, line_no)

            if chunk["id"] in ids:
                raise ValueError(f"중복 id: {chunk['id']}")
            ids.add(chunk["id"])

            if dimension == 0:
                dimension = len(vector)
            elif len(vector) != dimension:
                raise ValueError(f"임베딩 차원 불일치: line={line_no}")

            chunks.append(chunk)

    if not chunks:
        raise ValueError("저장할 청크가 없습니다.")

    return chunks, dimension


def validate_chunk(chunk: object, line_no: int) -> list[float]:
    if not isinstance(chunk, dict):
        raise ValueError(f"JSON 객체가 아닙니다: line={line_no}")

    for field in ("id", "parent_id", "content", "metadata", "embedding"):
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
    if not isinstance(chunk["embedding"], list) or not chunk["embedding"]:
        raise ValueError(f"embedding이 올바르지 않습니다: line={line_no}")

    try:
        vector = [float(value) for value in chunk["embedding"]]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"embedding에 숫자가 아닌 값이 있습니다: line={line_no}") from exc

    if not all(math.isfinite(value) for value in vector):
        raise ValueError(f"embedding에 NaN 또는 무한대가 있습니다: line={line_no}")

    return vector


def point_id(chunk_id: str) -> str:
    """청크 ID를 재실행해도 같은 Qdrant UUID로 변환한다."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def batches(items: list[dict], size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def main() -> int:
    if BATCH_SIZE < 1:
        raise ValueError("BATCH_SIZE는 1 이상이어야 합니다.")

    try:
        from qdrant_client import QdrantClient, models
    except ImportError as exc:
        raise SystemExit(
            "qdrant-client가 필요합니다.\n"
            "설치: python -m pip install -U qdrant-client"
        ) from exc

    chunks, dimension = read_chunks(INPUT_FILE)
    client = QdrantClient(url=QDRANT_URL)

    # 입력 JSONL 전체를 기준으로 컬렉션을 새로 만든다.
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=dimension,
            distance=models.Distance.COSINE,
        ),
    )

    for group in batches(chunks, BATCH_SIZE):
        points = [
            models.PointStruct(
                id=point_id(chunk["id"]),
                vector=chunk["embedding"],
                payload={
                    key: value
                    for key, value in chunk.items()
                    if key != "embedding"
                },
            )
            for chunk in group
        ]

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )

    stored = client.count(
        collection_name=COLLECTION_NAME,
        exact=True,
    ).count

    if stored != len(chunks):
        raise ValueError(
            f"저장 개수 불일치: input={len(chunks)}, qdrant={stored}"
        )

    print(f"collection: {COLLECTION_NAME}")
    print(f"dimension : {dimension}")
    print(f"points    : {stored}")
    print(f"url       : {QDRANT_URL}")
    print("validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())