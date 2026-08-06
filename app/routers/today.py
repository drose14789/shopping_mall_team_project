from fastapi import APIRouter, HTTPException
from app.services.today_recommend import get_today_recommendations
import scripts.db_setting as db

router = APIRouter(
    prefix="/today",
    tags=["Today Recommendation"]
)

engine = db.get_engine()

@router.get("/recommend/{client_uuid}")
def get_today_recommend(client_uuid: str):
    try:
        result = get_today_recommendations(
            client_uuid=client_uuid,
            engine=engine
        )

        response = {
            "file_name": result.get("file_name"),
            "expand": [],
            "improve": [],
            "reduce": [],
            "returnRisk": []
        }

        groups = [
            ("expand", "예산 확대"),
            ("improve", "개선 필요"),
            ("reduce", "광고 축소"),
            ("returnRisk", "반품 리스크")
        ]

        for key, action_group in groups:
            for idx, item in enumerate(result[key], start=1):
                response[key].append({
                    "rank": idx,
                    "id": item["id"],
                    "product_name": item["product_name"],
                    "category": item["category"],
                    "product_type": item["product_type"],
                    "action_group": action_group,
                    **item
                })

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )