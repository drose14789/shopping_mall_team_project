from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests


QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "legal_chunks"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHILD_FILE = (
    PROJECT_ROOT
    / "data"
    / "chunks"
    / "documents.children.jsonl"
)

SCROLL_LIMIT = 256
UPDATE_BATCH_SIZE = 100
REQUEST_TIMEOUT_SECONDS = 60


def read_child_document_types(
    path: Path,
) -> dict[str, str]:
    """
    자식 청크 ID별 document_type을 읽습니다.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"자식 청크 파일을 찾을 수 없습니다: {path}"
        )

    document_types: dict[str, str] = {}

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path.name} {line_number}번째 줄의 "
                    "JSON 형식이 올바르지 않습니다."
                ) from error

            chunk_id = record.get("id")
            metadata = record.get("metadata", {})
            document_type = metadata.get("document_type")

            if not isinstance(chunk_id, str) or not chunk_id:
                raise ValueError(
                    f"{path.name} {line_number}번째 줄에 "
                    "유효한 id가 없습니다."
                )

            if (
                not isinstance(document_type, str)
                or not document_type
            ):
                raise ValueError(
                    f"{path.name} {line_number}번째 줄에 "
                    "metadata.document_type이 없습니다."
                )

            if chunk_id in document_types:
                raise ValueError(
                    f"중복 자식 청크 ID가 있습니다: {chunk_id}"
                )

            document_types[chunk_id] = document_type

    return document_types


def scroll_all_points() -> list[dict[str, Any]]:
    """
    Qdrant 컬렉션의 모든 포인트를 payload와 함께 읽습니다.
    """
    endpoint = (
        f"{QDRANT_URL}/collections/"
        f"{COLLECTION_NAME}/points/scroll"
    )

    points: list[dict[str, Any]] = []
    offset: str | int | None = None

    while True:
        body: dict[str, Any] = {
            "limit": SCROLL_LIMIT,
            "with_payload": True,
            "with_vector": False,
        }

        if offset is not None:
            body["offset"] = offset

        response = requests.post(
            endpoint,
            json=body,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        response_data = response.json()
        result = response_data.get("result", {})
        batch = result.get("points", [])

        if not isinstance(batch, list):
            raise RuntimeError(
                "Qdrant scroll 응답의 points 형식이 "
                "올바르지 않습니다."
            )

        points.extend(batch)

        offset = result.get("next_page_offset")

        if offset is None:
            break

    return points


def build_update_plan(
    points: list[dict[str, Any]],
    document_types: dict[str, str],
) -> tuple[
    dict[str, list[str | int]],
    dict[str, str | None],
]:
    """
    document_type별 Qdrant 포인트 ID 목록을 만듭니다.
    """
    point_ids_by_type: dict[
        str,
        list[str | int],
    ] = defaultdict(list)

    existing_types_by_chunk: dict[
        str,
        str | None,
    ] = {}

    qdrant_chunk_ids: set[str] = set()

    for point in points:
        qdrant_point_id = point.get("id")
        payload = point.get("payload", {})

        if qdrant_point_id is None:
            raise ValueError(
                "Qdrant 포인트에 id가 없습니다."
            )

        if not isinstance(payload, dict):
            raise ValueError(
                f"포인트 {qdrant_point_id}의 payload가 "
                "올바르지 않습니다."
            )

        chunk_id = payload.get("id")
        metadata = payload.get("metadata", {})

        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError(
                f"포인트 {qdrant_point_id}의 payload.id가 "
                "올바르지 않습니다."
            )

        if chunk_id in qdrant_chunk_ids:
            raise ValueError(
                f"Qdrant에 중복 payload.id가 있습니다: "
                f"{chunk_id}"
            )

        qdrant_chunk_ids.add(chunk_id)

        if chunk_id not in document_types:
            raise ValueError(
                "JSONL에서 찾을 수 없는 Qdrant 청크가 "
                f"있습니다: {chunk_id}"
            )

        expected_type = document_types[chunk_id]

        existing_type: str | None = None

        if isinstance(metadata, dict):
            value = metadata.get("document_type")

            if isinstance(value, str):
                existing_type = value

        existing_types_by_chunk[chunk_id] = existing_type

        if existing_type != expected_type:
            point_ids_by_type[expected_type].append(
                qdrant_point_id
            )

    missing_in_qdrant = sorted(
        set(document_types) - qdrant_chunk_ids
    )

    if missing_in_qdrant:
        preview = "\n".join(
            f"- {chunk_id}"
            for chunk_id in missing_in_qdrant[:10]
        )

        raise ValueError(
            "Qdrant에서 찾을 수 없는 JSONL 자식 청크가 "
            f"{len(missing_in_qdrant)}개 있습니다.\n"
            f"{preview}"
        )

    return dict(point_ids_by_type), existing_types_by_chunk


def print_preview(
    points: list[dict[str, Any]],
    document_types: dict[str, str],
    point_ids_by_type: dict[
        str,
        list[str | int],
    ],
    existing_types_by_chunk: dict[
        str,
        str | None,
    ],
) -> None:
    """
    수정 전 검증 결과와 예정 작업을 출력합니다.
    """
    expected_counts = Counter(
        document_types.values()
    )

    existing_counts = Counter(
        value
        for value in existing_types_by_chunk.values()
        if value is not None
    )

    missing_count = sum(
        value is None
        for value in existing_types_by_chunk.values()
    )

    update_count = sum(
        len(point_ids)
        for point_ids in point_ids_by_type.values()
    )

    print("=" * 72)
    print("Qdrant document_type 반영 사전 검사")
    print("=" * 72)
    print(f"JSONL 자식 청크 수: {len(document_types)}")
    print(f"Qdrant 포인트 수: {len(points)}")
    print(
        "현재 document_type 없음: "
        f"{missing_count}"
    )
    print(f"수정 예정 포인트 수: {update_count}")

    print("\n[JSONL 기준 document_type 개수]")
    for document_type, count in sorted(
        expected_counts.items()
    ):
        print(f"- {document_type}: {count}")

    print("\n[Qdrant 현재 document_type 개수]")
    if existing_counts:
        for document_type, count in sorted(
            existing_counts.items()
        ):
            print(f"- {document_type}: {count}")
    else:
        print("- 아직 document_type이 없습니다.")

    print("\n[반영 예정 개수]")
    if point_ids_by_type:
        for document_type, point_ids in sorted(
            point_ids_by_type.items()
        ):
            print(
                f"- {document_type}: "
                f"{len(point_ids)}"
            )
    else:
        print("- 모든 포인트가 이미 최신 상태입니다.")


def chunked(
    values: list[str | int],
    size: int,
):
    """
    포인트 ID 목록을 지정한 크기로 나눕니다.
    """
    for start in range(0, len(values), size):
        yield values[start:start + size]


def apply_updates(
    point_ids_by_type: dict[
        str,
        list[str | int],
    ],
) -> None:
    """
    metadata 내부에 document_type만 추가하거나 갱신합니다.
    """
    endpoint = (
        f"{QDRANT_URL}/collections/"
        f"{COLLECTION_NAME}/points/payload"
    )

    total_updated = 0

    for document_type, point_ids in sorted(
        point_ids_by_type.items()
    ):
        for point_id_batch in chunked(
            point_ids,
            UPDATE_BATCH_SIZE,
        ):
            body = {
                "payload": {
                    "document_type": document_type,
                },
                "key": "metadata",
                "points": point_id_batch,
            }

            response = requests.post(
                endpoint,
                params={"wait": "true"},
                json=body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            result = response.json()

            if result.get("status") != "ok":
                raise RuntimeError(
                    "Qdrant payload 수정 응답이 "
                    f"정상이 아닙니다: {result}"
                )

            total_updated += len(point_id_batch)

            print(
                f"[반영] {document_type}: "
                f"{total_updated}개 누적"
            )

    print(f"\n총 {total_updated}개 포인트 반영 완료")


def verify_updates(
    document_types: dict[str, str],
) -> None:
    """
    반영 후 모든 포인트의 document_type을 검증합니다.
    """
    points = scroll_all_points()

    actual_counts: Counter[str] = Counter()
    mismatches: list[str] = []

    for point in points:
        payload = point.get("payload", {})
        chunk_id = payload.get("id")
        metadata = payload.get("metadata", {})

        actual_type = (
            metadata.get("document_type")
            if isinstance(metadata, dict)
            else None
        )

        expected_type = document_types.get(chunk_id)

        if actual_type != expected_type:
            mismatches.append(
                f"{chunk_id}: "
                f"예상={expected_type}, 실제={actual_type}"
            )
        elif isinstance(actual_type, str):
            actual_counts[actual_type] += 1

    if mismatches:
        preview = "\n".join(
            f"- {item}"
            for item in mismatches[:10]
        )

        raise RuntimeError(
            f"검증 실패: {len(mismatches)}개 불일치\n"
            f"{preview}"
        )

    print("\n[반영 후 검증]")
    for document_type, count in sorted(
        actual_counts.items()
    ):
        print(f"- {document_type}: {count}")

    print("검증 결과: PASS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "JSONL의 document_type을 Qdrant "
            "metadata payload에 반영합니다."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "사전 검사 후 실제 Qdrant payload를 "
            "수정합니다."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        document_types = read_child_document_types(
            CHILD_FILE
        )

        points = scroll_all_points()

        (
            point_ids_by_type,
            existing_types_by_chunk,
        ) = build_update_plan(
            points=points,
            document_types=document_types,
        )

        print_preview(
            points=points,
            document_types=document_types,
            point_ids_by_type=point_ids_by_type,
            existing_types_by_chunk=existing_types_by_chunk,
        )

        if not args.apply:
            print(
                "\n현재는 미리보기만 실행했습니다."
            )
            print(
                "실제 반영 명령:"
            )
            print(
                "python scripts\\"
                "update_qdrant_document_type.py "
                "--apply"
            )
            return 0

        if not point_ids_by_type:
            print(
                "\n수정할 포인트가 없습니다."
            )
            verify_updates(document_types)
            return 0

        print("\nQdrant payload 반영을 시작합니다.")
        apply_updates(point_ids_by_type)
        verify_updates(document_types)

        return 0

    except requests.RequestException as error:
        print(
            "Qdrant 요청 중 오류가 발생했습니다."
        )
        print(f"상세: {error}")
        return 1

    except Exception as error:
        print("처리 중 오류가 발생했습니다.")
        print(f"상세: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())