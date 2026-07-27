from typing import List
from fastapi import APIRouter, File, UploadFile
import tempfile
import os
from app.services.score_service import evaluate_single_excel_file
import scripts.db_setting as db

router = APIRouter(prefix="/score", tags=["Score Evaluation"])


@router.post("/evaluate-multiple")
async def evaluate_multiple_files(files: List[UploadFile] = File(...)):
  engine = db.get_engine()
  all_results = []

  for file in files:
    # 임시 파일을 생성하여 업로드된 파일 내용을 잠시 담았다가 분석 후 자동 삭제
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = tmp.name

    try:
      # 기존에 만들어둔 단일 파일 분석 함수를 재사용하여 각각 분석
      file_results = evaluate_single_excel_file(tmp_path, engine)
      all_results.extend(file_results)
    finally:
      # 분석이 끝나면 임시 파일 삭제
      if os.path.exists(tmp_path):
        os.unlink(tmp_path)

  return {
      "message": f"총 {len(files)}개 파일 분석 완료",
      "total_items": len(all_results),
      "results": all_results,
  }