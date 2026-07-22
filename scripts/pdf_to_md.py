from pathlib import Path

import pymupdf


BASE_DIR = Path(__file__).resolve().parent.parent

# 이번에 변환할 PDF 파일 하나
PDF_FILE = (BASE_DIR / "data" / "pdf" / "소 비 자 분 쟁 해 결 기 준.pdf")

# 결과가 저장될 폴더
OUTPUT_DIR = (BASE_DIR / "data" / "markdown" / "raw")


def pdf_to_md():
    if not PDF_FILE.exists():
        print("PDF 파일을 찾을 수 없습니다.")
        print("찾은 경로:", PDF_FILE)
        return

    pages = []

    with pymupdf.open(PDF_FILE) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True).strip()

            pages.append(
                f"<!-- page: {page_number} -->\n\n{text}"
            )

    output_file = OUTPUT_DIR / f"{PDF_FILE.stem}_원본.md"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        "\n\n".join(pages) + "\n",
        encoding="utf-8"
    )

    print("변환 완료:", output_file)


if __name__ == "__main__":
    pdf_to_md()