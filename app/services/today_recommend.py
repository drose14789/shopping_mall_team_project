from sqlalchemy import text
import scripts.db_setting as db

engine = db.get_engine()
print (type(engine))

def get_today_recommendations(client_uuid, engine):

    with engine.connect() as conn:
        # 최신 분석 파일 + 데이터 한번에 조회
        query = text("""
            SELECT *
            FROM evaluation_results
            WHERE client_uuid = :client_uuid
            AND file_name = (
                SELECT file_name
                FROM evaluation_results
                WHERE client_uuid = :client_uuid
                ORDER BY created_at DESC
                LIMIT 1
            )
        """)

        rows = conn.execute(
            query,
            {
                "client_uuid": client_uuid
            }
        ).mappings().all()


    if not rows:
        return {
            "file_name": products[0]["file_name"],
            "expand": [],
            "improve": [],
            "reduce": [],
            "returnRisk": []
        }


    products = [dict(row) for row in rows]


    # 예산 확대 점수

    for item in products:

        item["expand_score"] = (
            item["total_score"] * 0.35
            + item["score_roas"] * 0.30
            + item["score_conv_rate"] * 0.20
            + item["score_return_stability"] * 0.15
        )


    expand_sorted = sorted(
        products,
        key=lambda x: x["expand_score"],
        reverse=True
    )

    expand = expand_sorted[:5]

    used_ids = {
        x["product_id"]
        for x in expand
    }

    # 개선 필요 점수

    improve_candidates = [
        x for x in products
        if x["product_id"] not in used_ids
    ]

    for item in improve_candidates:

        inflow_score = (
            item["score_click_rate"] * 0.4
            + item["score_wish_conv"] * 0.6
        )

        interest_score = (
            item["score_wish_conv"] * 0.4
            + item["score_cart_conv"] * 0.6
        )


        ad_burden = (
            item["ad_spend"]
            /
            max(
                p["ad_spend"]
                for p in products
            )
            * 100
            if max(p["ad_spend"] for p in products) > 0
            else 0
        )


        item["improve_score"] = (
            inflow_score * 0.35
            + interest_score * 0.25
            + (100 - item["score_conv_rate"]) * 0.25
            + ad_burden * 0.15
        )

    improve_sorted = sorted(
        improve_candidates,
        key=lambda x: x["improve_score"],
        reverse=True
    )

    improve = improve_sorted[:5]

    used_ids.update(
        x["product_id"]
        for x in improve
    )

    # 광고 축소 점수

    reduce_candidates = [
        x for x in products
        if x["product_id"] not in used_ids
    ]

    max_ad = max(
        x["ad_spend"]
        for x in products
    )

    for item in reduce_candidates:
        ad_score = (
            item["ad_spend"]
            /
            max_ad
            * 100
            if max_ad > 0 else 0
        )

        item["reduce_score"] = (
            ad_score * 0.35
            + (100 - item["score_roas"]) * 0.30
            + (100 - item["score_conv_rate"]) * 0.20
            + (100 - item["score_return_stability"]) * 0.15
        )

    reduce_sorted = sorted(
        reduce_candidates,
        key=lambda x: x["reduce_score"],
        reverse=True
    )

    reduce = reduce_sorted[:5]

    used_ids.update(
        x["product_id"]
        for x in reduce
    )

    # 반품 리스크 점수

    return_candidates = [
        x for x in products
        if x["product_id"] not in used_ids
    ]

    max_return = max(
        x["return_count"]
        for x in products
    )

    max_order = max(
        x["order_count"]
        for x in products
    )

    max_amount = max(
        x["order_amount"]
        for x in products
    )

    for item in return_candidates:
        return_count_score = (
            item["return_count"]
            /
            max_return
            * 100
            if max_return > 0 else 0
        )

        order_score = (
            item["order_count"]
            /
            max_order
            * 100
            if max_order > 0 else 0
        )

        amount_score = (
            item["order_amount"]
            /
            max_amount
            * 100
            if max_amount > 0 else 0
        )

        item["return_score"] = (
            (100 - item["score_return_stability"]) * 0.35
            + return_count_score * 0.25
            + order_score * 0.20
            + amount_score * 0.20
        )

    return_sorted = sorted(
        return_candidates,
        key=lambda x: x["return_score"],
        reverse=True
    )

    return_risk = return_sorted[:5]

    return {
        "expand": expand,
        "improve": improve,
        "reduce": reduce,
        "returnRisk": return_risk
    }


if __name__ == "__main__":
    try:
        results = get_today_recommendations(            
            client_uuid="b37027bb-a3b0-4caa-aaf4-f78125d4df93" ,
            engine=engine
        )
        print(results)
    except Exception as e:
        print(f"실행 중 에러 발생: {e}")