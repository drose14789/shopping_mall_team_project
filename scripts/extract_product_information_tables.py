from __future__ import annotations

import os

# PaddleOCR/PaddlePaddle를 import하기 전에 설정해야 합니다.
# Windows CPU 환경에서 oneDNN과 PIR 변환이 충돌하는 문제를 피합니다.
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

import csv
import re
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from paddleocr import PaddleOCR


# =========================================================
# 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_FILE = (
    BASE_DIR
    / "data"
    / "pdf"
    / "전자상거래 등에서의 상품 등의 정보제공에 관한 고시(공정거래위원회고시)(제2022-15호)(20230101).pdf"
)

CLEANED_MD_FILE = (
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
    / "전자상거래_상품정보제공고시_표복원_정리본.md"
)

DEBUG_DIR = (
    BASE_DIR
    / "data"
    / "ocr_debug"
    / "product_information_tables"
)

REPORT_FILE = DEBUG_DIR / "ocr_report.csv"


# =========================================================
# 문서에 있는 40개 품목
# =========================================================

PRODUCT_NAMES = [
    "의류",
    "구두 / 신발",
    "가방",
    "패션잡화 (모자 / 벨트 / 액세서리 등)",
    "침구류 / 커튼",
    "가구 (침대 / 소파 / 싱크대 / DIY제품 등)",
    "영상가전 (TV류)",
    "가정용 전기제품 (냉장고 / 세탁기 / 식기세척기 / 전자레인지 등)",
    "계절가전 (에어컨 / 온풍기 등)",
    "사무용기기 (컴퓨터 / 노트북 / 프린터 등)",
    "광학기기 (디지털카메라 / 캠코더 등)",
    "소형전자 (MP3 / 전자사전 등)",
    "휴대형 통신기기 (휴대폰 / 태블릿 등)",
    "내비게이션",
    "자동차용품 (자동차부품 / 기타 자동차용품 등)",
    "의료기기",
    "주방용품",
    "화장품",
    "귀금속 / 보석 / 시계류",
    "농수축산물",
    "가공식품",
    "건강기능식품",
    "어린이제품",
    "악기",
    "스포츠용품",
    "서적",
    "호텔 / 펜션 예약",
    "여행패키지",
    "항공권",
    "자동차 대여 서비스 (렌터카)",
    "물품대여 서비스 (정수기, 비데, 공기청정기 등)",
    "물품대여 서비스 (서적, 유아용품, 행사용품 등)",
    "디지털 콘텐츠 (음원, 게임, 인터넷강의 등)",
    "상품권 / 쿠폰",
    "모바일 쿠폰",
    "영화ㆍ공연",
    "생활화학제품",
    "살생물제품",
    "기타 용역",
    "기타 재화",
]


# =========================================================
# 설정
# =========================================================

# PDF의 3~15페이지가 품목별 표 구간입니다.
START_PAGE_INDEX = 2   # 0부터 시작하므로 실제 PDF 3페이지
END_PAGE_INDEX = 14   # 실제 PDF 15페이지

# 이 PDF의 표 이미지는 폭 599px입니다.
MIN_IMAGE_WIDTH = 500
MIN_IMAGE_HEIGHT = 100

# 원본 표 이미지가 약 96~103dpi이므로 확대 후 OCR합니다.
UPSCALE_RATIO = 4

# 낮추면 글자를 더 많이 살리지만 오인식도 늘어날 수 있습니다.
MIN_OCR_SCORE = 0.45

# 이 값보다 낮으면 검토 보고서에 기록합니다.
LOW_CONFIDENCE_SCORE = 0.70


# =========================================================
# 환경 확인
# =========================================================

def get_package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "설치되지 않음"


def print_ocr_environment() -> None:
    paddle_version = get_package_version("paddlepaddle")
    paddleocr_version = get_package_version("paddleocr")
    paddlex_version = get_package_version("paddlex")

    print("OCR 실행 환경")
    print(f"- paddlepaddle: {paddle_version}")
    print(f"- paddleocr: {paddleocr_version}")
    print(f"- paddlex: {paddlex_version}")
    print("- oneDNN/MKLDNN: 비활성화")

    if paddle_version == "3.3.0":
        print(
            "주의: PaddlePaddle 3.3.0은 CPU oneDNN 오류가 보고된 버전입니다.\n"
            "현재 코드는 oneDNN을 끄고 실행하지만 같은 오류가 계속되면\n"
            "다음 명령으로 3.2.2를 설치하세요.\n"
            "pip uninstall paddlepaddle -y\n"
            "pip install paddlepaddle==3.2.2"
        )


# =========================================================
# 유틸리티
# =========================================================

def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{label}을 찾을 수 없습니다.\n{path.resolve()}"
        )


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def safe_filename(value: str) -> str:
    """Windows 파일명에서 사용할 수 없는 문자를 제거합니다."""

    value = re.sub(r'[<>:"/\\|?*]', "_", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.rstrip(". ")


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    저해상도 표 이미지를 OCR하기 쉽게 확대하고 보정합니다.
    원본 이미지에는 영향을 주지 않습니다.
    """

    gray = ImageOps.grayscale(image)

    gray = gray.resize(
        (
            gray.width * UPSCALE_RATIO,
            gray.height * UPSCALE_RATIO,
        ),
        Image.Resampling.LANCZOS,
    )

    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.5)
    gray = gray.filter(ImageFilter.SHARPEN)

    return gray.convert("RGB")


def is_repeated_table_header(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)

    return (
        "전자상거래" in compact
        and "상품" in compact
        and "정보제공" in compact
        and "고시" in compact
    )


def group_ocr_lines(
    texts: list[str],
    scores: list[float],
    boxes: list[list[int]],
) -> list[tuple[str, float]]:
    """
    OCR 결과가 한 줄에서 여러 조각으로 나뉜 경우
    y좌표를 기준으로 같은 줄끼리 합칩니다.
    """

    items: list[dict[str, Any]] = []

    for text, score, box in zip(texts, scores, boxes):
        text = normalize_space(str(text))

        if not text or float(score) < MIN_OCR_SCORE:
            continue

        if len(box) != 4:
            continue

        x0, y0, x1, y1 = map(float, box)

        items.append({
            "text": text,
            "score": float(score),
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "center_y": (y0 + y1) / 2,
            "height": max(y1 - y0, 1),
        })

    if not items:
        return []

    items.sort(key=lambda item: (item["center_y"], item["x0"]))

    median_height = float(
        np.median([item["height"] for item in items])
    )

    row_tolerance = max(median_height * 0.65, 10.0)

    rows: list[list[dict[str, Any]]] = []

    for item in items:
        if not rows:
            rows.append([item])
            continue

        current_row = rows[-1]
        row_center = sum(
            element["center_y"]
            for element in current_row
        ) / len(current_row)

        if abs(item["center_y"] - row_center) <= row_tolerance:
            current_row.append(item)
        else:
            rows.append([item])

    output: list[tuple[str, float]] = []

    for row in rows:
        row.sort(key=lambda item: item["x0"])

        joined_text = normalize_space(
            " ".join(item["text"] for item in row)
        )

        average_score = sum(
            item["score"] for item in row
        ) / len(row)

        if not joined_text or is_repeated_table_header(joined_text):
            continue

        output.append((joined_text, average_score))

    return output


def clean_ocr_line(text: str) -> str:
    """
    Markdown에 넣기 위한 최소 정리만 수행합니다.
    법적 의미가 달라질 수 있는 임의 교정은 하지 않습니다.
    """

    text = normalize_space(text)

    text = re.sub(
        r"^(\d+(?:-\d+)?)[\s]*[.)]\s*",
        r"\1. ",
        text,
    )

    text = re.sub(
        r"^[•·●○]\s*",
        "",
        text,
    )

    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    return text.strip()


def lines_to_markdown(
    item_number: int,
    product_name: str,
    lines: list[tuple[str, float]],
) -> str:
    blocks = [
        f"#### ({item_number}) {product_name}",
        "",
    ]

    for text, _score in lines:
        text = clean_ocr_line(text)

        if not text:
            continue

        if re.match(r"^\d+(?:-\d+)?\.\s+", text):
            blocks.append(text)
        else:
            blocks.append(f"- {text}")

    return "\n".join(blocks).rstrip()


# =========================================================
# PDF 표 이미지 추출
# =========================================================

def extract_product_table_images(
    pdf_path: Path,
) -> list[dict[str, Any]]:
    """
    PDF 3~15페이지에서 표시 순서대로 표 이미지를 수집합니다.

    이 문서에는 해당 구간에 품목 표 40개와
    추가 예시 이미지 1개가 있으므로 앞의 40개만 사용합니다.
    """

    document = fitz.open(pdf_path)
    candidates: list[dict[str, Any]] = []

    try:
        if document.page_count <= END_PAGE_INDEX:
            raise ValueError(
                "PDF 페이지 수가 예상보다 적습니다.\n"
                f"전체 페이지 수: {document.page_count}"
            )

        for page_index in range(
            START_PAGE_INDEX,
            END_PAGE_INDEX + 1,
        ):
            page = document[page_index]

            for info in page.get_image_info(xrefs=True):
                width = int(info["width"])
                height = int(info["height"])
                xref = int(info["xref"])
                bbox = fitz.Rect(info["bbox"])

                if (
                    width < MIN_IMAGE_WIDTH
                    or height < MIN_IMAGE_HEIGHT
                    or xref <= 0
                ):
                    continue

                candidates.append({
                    "page_index": page_index,
                    "page_number": page_index + 1,
                    "y0": float(bbox.y0),
                    "xref": xref,
                    "width": width,
                    "height": height,
                })

        candidates.sort(
            key=lambda item: (
                item["page_index"],
                item["y0"],
            )
        )

        if len(candidates) < len(PRODUCT_NAMES):
            raise ValueError(
                "품목 표 이미지를 40개 찾지 못했습니다.\n"
                f"발견한 이미지 수: {len(candidates)}"
            )

        product_candidates = candidates[:len(PRODUCT_NAMES)]
        extracted: list[dict[str, Any]] = []

        for item_number, candidate in enumerate(
            product_candidates,
            start=1,
        ):
            extracted_data = document.extract_image(
                candidate["xref"]
            )

            image = Image.open(
                BytesIO(extracted_data["image"])
            ).convert("RGB")

            extracted.append({
                **candidate,
                "item_number": item_number,
                "product_name": PRODUCT_NAMES[item_number - 1],
                "image": image,
            })

        return extracted

    finally:
        document.close()


# =========================================================
# OCR
# =========================================================

def create_ocr() -> PaddleOCR:
    """
    한국어·영문·숫자가 섞인 표를 인식하기 위한 OCR 객체입니다.

    Windows CPU 환경의 oneDNN/PIR 충돌을 피하기 위해
    enable_mkldnn을 반드시 False로 설정합니다.
    """

    return PaddleOCR(
        lang="korean",
        ocr_version="PP-OCRv5",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
        enable_mkldnn=False,
        cpu_threads=4,
    )


def extract_result_data(result: Any) -> dict[str, Any]:
    """PaddleOCR 3.x 결과 객체에서 OCR 데이터 사전을 꺼냅니다."""

    result_json = result.json

    if callable(result_json):
        result_json = result_json()

    if not isinstance(result_json, dict):
        raise TypeError(
            "PaddleOCR 결과 JSON 형식이 예상과 다릅니다. "
            f"실제 형식: {type(result_json).__name__}"
        )

    data = result_json.get("res", result_json)

    if not isinstance(data, dict):
        raise TypeError(
            "PaddleOCR 결과의 res 형식이 예상과 다릅니다. "
            f"실제 형식: {type(data).__name__}"
        )

    return data


def predict_single_image(
    ocr: PaddleOCR,
    processed: Image.Image,
    item_number: int,
    product_name: str,
) -> list[Any]:
    """한 이미지에 OCR을 실행하고 Paddle 오류를 읽기 쉽게 바꿉니다."""

    try:
        return list(
            ocr.predict(
                input=np.asarray(processed, dtype=np.uint8),
                text_rec_score_thresh=MIN_OCR_SCORE,
            )
        )

    except NotImplementedError as error:
        message = str(error)

        if "ConvertPirAttribute2RuntimeAttribute" in message:
            raise RuntimeError(
                "PaddlePaddle CPU oneDNN/PIR 충돌로 OCR을 실행하지 못했습니다.\n"
                f"대상: ({item_number}) {product_name}\n\n"
                "현재 코드에는 enable_mkldnn=False가 적용되어 있습니다.\n"
                "같은 오류가 계속되면 가상환경에서 다음 명령을 실행하세요.\n\n"
                "pip uninstall paddlepaddle -y\n"
                "pip install paddlepaddle==3.2.2"
            ) from error

        raise


def run_ocr(
    table_images: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    ocr = create_ocr()

    markdown_sections: list[str] = []
    report_rows: list[dict[str, Any]] = []

    total = len(table_images)

    for table in table_images:
        item_number = int(table["item_number"])
        product_name = str(table["product_name"])

        processed = preprocess_image(table["image"])

        image_path = (
            DEBUG_DIR
            / f"{item_number:02d}_{safe_filename(product_name)}.png"
        )

        processed.save(image_path)

        results = predict_single_image(
            ocr=ocr,
            processed=processed,
            item_number=item_number,
            product_name=product_name,
        )

        if not results:
            raise RuntimeError(
                f"OCR 결과가 없습니다: ({item_number}) {product_name}"
            )

        data = extract_result_data(results[0])

        texts = [
            str(text)
            for text in data.get("rec_texts", [])
        ]

        scores = [
            float(score)
            for score in data.get("rec_scores", [])
        ]

        boxes = [
            [int(value) for value in box]
            for box in data.get("rec_boxes", [])
            if len(box) == 4
        ]

        if not (len(texts) == len(scores) == len(boxes)):
            raise RuntimeError(
                "OCR 결과의 텍스트·신뢰도·좌표 개수가 서로 다릅니다.\n"
                f"대상: ({item_number}) {product_name}\n"
                f"텍스트: {len(texts)}, 신뢰도: {len(scores)}, 좌표: {len(boxes)}"
            )

        lines = group_ocr_lines(
            texts=texts,
            scores=scores,
            boxes=boxes,
        )

        if not lines:
            raise RuntimeError(
                f"인식된 본문이 없습니다: ({item_number}) {product_name}"
            )

        markdown_sections.append(
            lines_to_markdown(
                item_number=item_number,
                product_name=product_name,
                lines=lines,
            )
        )

        average_score = sum(
            score for _text, score in lines
        ) / len(lines)

        low_score_lines = [
            text
            for text, score in lines
            if score < LOW_CONFIDENCE_SCORE
        ]

        report_rows.append({
            "품목번호": item_number,
            "품목명": product_name,
            "PDF페이지": table["page_number"],
            "인식줄수": len(lines),
            "평균신뢰도": f"{average_score:.4f}",
            "낮은신뢰도줄수": len(low_score_lines),
            "낮은신뢰도문장": " | ".join(low_score_lines),
            "검토이미지": str(image_path),
        })

        print(
            f"[{item_number:02d}/{total:02d}] "
            f"{product_name} - "
            f"{len(lines)}줄, "
            f"평균 {average_score:.3f}"
        )

    return markdown_sections, report_rows


# =========================================================
# 기존 정리본에 표 복원
# =========================================================

def replace_product_section(
    cleaned_markdown: str,
    product_sections: list[str],
) -> str:
    start_marker = "### 1. 품목별 재화 등에 관한 정보"
    end_marker = "### 2. 거래조건에 관한 정보"

    start_index = cleaned_markdown.find(start_marker)
    end_index = cleaned_markdown.find(end_marker)

    if start_index < 0:
        raise ValueError(
            f"정리본에서 시작 구간을 찾지 못했습니다: {start_marker}"
        )

    if end_index < 0 or end_index <= start_index:
        raise ValueError(
            f"정리본에서 종료 구간을 찾지 못했습니다: {end_marker}"
        )

    start_body_index = start_index + len(start_marker)

    replacement = (
        "\n\n"
        + "\n\n".join(product_sections)
        + "\n\n"
    )

    result = (
        cleaned_markdown[:start_body_index]
        + replacement
        + cleaned_markdown[end_index:]
    )

    result = re.sub(
        r"\n{3,}",
        "\n\n",
        result,
    )

    return result.strip() + "\n"


def write_report(rows: list[dict[str, Any]]) -> None:
    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "품목번호",
        "품목명",
        "PDF페이지",
        "인식줄수",
        "평균신뢰도",
        "낮은신뢰도줄수",
        "낮은신뢰도문장",
        "검토이미지",
    ]

    with REPORT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def validate_output(text: str) -> None:
    headings = re.findall(
        r"^####\s+\((\d+)\)\s+",
        text,
        flags=re.MULTILINE,
    )

    expected = [
        str(number)
        for number in range(1, 41)
    ]

    if headings != expected:
        raise ValueError(
            "품목 제목 1~40 검증에 실패했습니다.\n"
            f"발견: {headings}"
        )

    if "### 2. 거래조건에 관한 정보" not in text:
        raise ValueError(
            "거래조건 구간이 사라졌습니다."
        )


# =========================================================
# 실행
# =========================================================

def main() -> None:
    print_ocr_environment()

    require_file(PDF_FILE, "PDF 파일")
    require_file(CLEANED_MD_FILE, "기존 정리본")

    DEBUG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\n1. PDF에서 품목 표 이미지를 찾습니다.")
    table_images = extract_product_table_images(
        PDF_FILE
    )

    print(
        f"   품목 표 이미지 {len(table_images)}개 확인 완료"
    )

    print("\n2. 한국어 OCR을 실행합니다.")
    product_sections, report_rows = run_ocr(
        table_images
    )

    print("\n3. 기존 정리본의 품목 구간을 교체합니다.")
    cleaned_markdown = CLEANED_MD_FILE.read_text(
        encoding="utf-8"
    )

    output_text = replace_product_section(
        cleaned_markdown=cleaned_markdown,
        product_sections=product_sections,
    )

    validate_output(output_text)

    OUTPUT_MD_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MD_FILE.write_text(
        output_text,
        encoding="utf-8",
    )

    write_report(report_rows)

    low_confidence_count = sum(
        int(row["낮은신뢰도줄수"])
        for row in report_rows
    )

    print("\n완료")
    print(f"결과 파일: {OUTPUT_MD_FILE.resolve()}")
    print(f"검토 보고서: {REPORT_FILE.resolve()}")
    print(f"검토 이미지 폴더: {DEBUG_DIR.resolve()}")
    print(f"낮은 신뢰도 문장 수: {low_confidence_count}")
    print(
        "OCR 문서는 반드시 보고서의 낮은 신뢰도 문장을 "
        "원본 PDF와 대조해 검수하세요."
    )


if __name__ == "__main__":
    main()