from typing import List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import tempfile
import os
from sqlalchemy import text
from xlsxwriter import app
from app.services.score_service import evaluate_single_excel_file
import scripts.db_setting as db


router = APIRouter(prefix="/score")

@router.post("/evaluate-multiple", tags=["Excel Evaluation"])
async def evaluate_multiple_files(
    files: List[UploadFile] = File(...),
    client_uuid: str = Form(...),
):
    print(f"=== [요청 수신 성공] client_uuid: {client_uuid}, 파일 개수: {len(files)}개 ===")
    
    engine = db.get_engine()
    all_results = []

    for file in files:
        print(f"-> 처리 중인 파일 이름: {file.filename}")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name

            # 단일 파일 분석 수행
            file_results = evaluate_single_excel_file(tmp_path, engine, client_uuid=client_uuid, file_name=file.filename)
            all_results.extend(file_results)
            print(f"-> {file.filename} 분석 완료")
            
        except Exception as e:
            # 🔴 에러 발생 시 구체적인 원인을 터미널에 출력
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ [파일 분석 중 상세 에러 발생]:\n{error_detail}")
            
            # 클라이언트에게 400 에러와 함께 구체적인 원인 전달
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return {
        "message": f"총 {len(files)}개 파일 분석 완료",
        "total_items": len(all_results),
        "results": all_results,
    }

    
@router.get("/results/{id}", tags=["Score Evaluation"])
def get_evaluation_result(    
    client_uuid: str,
    file_name: str):
    try:
        engine = db.get_engine()

        with engine.connect() as connection:
            result = connection.execute(
              text("""
                  SELECT *
                  FROM evaluation_results
                  WHERE client_uuid = :client_uuid
                  AND file_name = :file_name
              """),
              {
                  "client_uuid": client_uuid,
                  "file_name": file_name
              }
          )

            row = result.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

        return dict(row._mapping)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results", tags=["Score Evaluation"])
def get_results(
    client_uuid: str,
    file_name: str
):
    try:
        engine = db.get_engine()

        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT *
                    FROM evaluation_results
                    WHERE client_uuid = :client_uuid
                    AND file_name = :file_name
                    ORDER BY id
                """),
                {
                    "client_uuid": client_uuid,
                    "file_name": file_name
                }
            )

            rows = [
                dict(row._mapping)
                for row in result
            ]

        return rows

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/history/{client_uuid}", tags=["Score History"])
def get_history_results(client_uuid: str):
    try:
        engine = db.get_engine()

        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT 
                        file_name,
                        MAX(analysis_start_time) AS analysis_start_time,
                        MAX(analysis_end_time) AS analysis_end_time,
                        MAX(quarter) AS quarter,
                        MAX(created_at) AS created_at,
                        COUNT(DISTINCT product_name) AS product_count
                    FROM evaluation_results
                    WHERE client_uuid = :client_uuid
                    GROUP BY file_name
                    ORDER BY MAX(created_at) DESC
                """),
                {
                    "client_uuid": client_uuid
                }
            )

            rows = [
                dict(row._mapping)
                for row in result
            ]

        return rows

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/summary/{client_uuid}", tags=["Score History"])
def get_history_summary(client_uuid: str):
    try:
        engine = db.get_engine()

        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        product_type,
                        COUNT(*) AS count
                    FROM evaluation_results
                    WHERE client_uuid = :client_uuid
                    AND created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                    GROUP BY product_type
                    ORDER BY count DESC
                    LIMIT 4
                """),
                {
                    "client_uuid": client_uuid
                }
            )

            rows = [
                dict(row._mapping)
                for row in result
            ]

        return rows

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )