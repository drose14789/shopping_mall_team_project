from __future__ import annotations

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PARENT_FILE = (
    PROJECT_ROOT
    / "data"
    / "chunks"
    / "documents.parents.jsonl"
)

CHILD_FILE = (
    PROJECT_ROOT
    / "data"
    / "chunks"
    / "documents.children.jsonl"
)


DOCUMENT_TYPE_BY_SOURCE_FILE = {
    "2015_6._26._개정+(전자상거래+표준약관).hwp_정리본.md": (
        "standard_terms"
    ),
    "개인정보 보호법(법률)(제20897호)(20251002)_정리본.md": (
        "law"
    ),
    "소비자분쟁해결기준_정리본.md": (
        "dispute_resolution"
    ),
    (
        "전자상거래 등에서의 상품 등의 정보제공에 관한 "
        "고시(공정거래위원회고시)(제2022-15호)(20230101)_정리본.md"
    ): "product_notice",
    (
        "전자상거래 등에서의 소비자보호 "
        "지침(공정거래위원회고시)(제2025-8호)(20251024)_정리본.md"
    ): "guideline",
    (
        "전자상거래 등에서의 소비자보호에 관한 "
        "법률(법률)(제21312호)(20260120)_정리본.md"
    ): "law",
    (
        "표시ㆍ광고의 공정화에 관한 "
        "법률(법률)(제20712호)(20250121)_정리본.md"
    ): "law",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """
    JSONL 파일을 한 줄씩 읽어 목록으로 반환합니다.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {path}"
        )

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON 형식 오류: {path.name} "
                    f"{line_number}번째 줄"
                ) from error

            records.append(record)

    return records


def validate_source_files(
    records: list[dict[str, Any]],
    path: Path,
) -> None:
    """
    모든 source_file이 사전에 정의된 매핑에 있는지 확인합니다.
    """
    source_files = {
        record.get("metadata", {}).get("source_file")
        for record in records
    }

    missing_source_files = sorted(
        source_file
        for source_file in source_files
        if source_file not in DOCUMENT_TYPE_BY_SOURCE_FILE
    )

    if missing_source_files:
        missing_text = "\n".join(
            f"- {source_file}"
            for source_file in missing_source_files
        )

        raise ValueError(
            f"{path.name}에서 document_type 매핑이 없는 "
            f"문서를 찾았습니다.\n{missing_text}"
        )


def add_document_type(
    records: list[dict[str, Any]],
) -> Counter[str]:
    """
    각 레코드의 metadata에 document_type을 추가합니다.
    """
    type_counts: Counter[str] = Counter()

    for record in records:
        metadata = record.setdefault("metadata", {})
        source_file = metadata.get("source_file")

        document_type = DOCUMENT_TYPE_BY_SOURCE_FILE[
            source_file
        ]

        metadata["document_type"] = document_type
        type_counts[document_type] += 1

    return type_counts


def create_backup(path: Path) -> Path:
    """
    원본 파일을 같은 폴더에 타임스탬프가 포함된 이름으로 백업합니다.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(
        f"{path.name}.{timestamp}.bak"
    )

    shutil.copy2(path, backup_path)

    return backup_path


def write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    """
    임시 파일에 먼저 저장한 뒤 원본 파일을 안전하게 교체합니다.
    """
    temp_path = path.with_suffix(
        f"{path.suffix}.tmp"
    )

    with temp_path.open("w", encoding="utf-8") as file:
        for record in records:
            json.dump(
                record,
                file,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            file.write("\n")

    temp_path.replace(path)


def update_file(path: Path) -> None:
    """
    한 JSONL 파일을 검증하고 백업한 뒤 갱신합니다.
    """
    print(f"\n[처리 시작] {path}")

    records = read_jsonl(path)
    validate_source_files(records, path)

    type_counts = add_document_type(records)

    backup_path = create_backup(path)
    write_jsonl(path, records)

    print(f"[레코드 수] {len(records)}")
    print(f"[백업 파일] {backup_path}")

    print("[document_type 개수]")
    for document_type, count in sorted(
        type_counts.items()
    ):
        print(f"- {document_type}: {count}")

    print(f"[처리 완료] {path.name}")


def main() -> None:
    """
    부모·자식 청크 파일 모두에 document_type을 추가합니다.
    """
    print("=" * 72)
    print("청크 메타데이터 document_type 추가")
    print("=" * 72)

    update_file(PARENT_FILE)
    update_file(CHILD_FILE)

    print("\n" + "=" * 72)
    print("전체 처리 완료")
    print("=" * 72)


if __name__ == "__main__":
    main()