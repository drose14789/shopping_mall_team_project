import time
from urllib import response
import requests

DIAGNOSTIC_KEYWORD_MAP = {
    "핵심 확대형": ["만족도", "사이즈", "핏", "소재", "두께감", "색감", "사진일치"],
    "반품 리스크 확대 보류형": ["사이즈", "핏", "소재", "두께감", "색감", "사진일치", "품질", "불량"],
    "구매 직전 이탈형": ["가격", "혜택", "배송", "교환", "착용정보"],
    "구매·반품 복합 리스크형": ["가격", "혜택", "사이즈", "핏", "소재", "두께감", "배송", "교환"],
    "전환 효율형": ["착용정보", "가격", "혜택", "만족도"],
    "반품 주의 유지형": ["사이즈", "핏", "색감", "사진일치", "소재", "두께감", "품질", "불량"],
    "상세페이지 개선형": ["착용정보", "소재", "두께감", "사이즈", "핏", "색감", "사진일치"],
    "상세·반품 복합 개선형": ["착용정보", "사이즈", "핏", "소재", "두께감", "색감", "사진일치"],
    "숨은 효율형": ["만족도", "사이즈", "핏", "색감", "사진일치"],
    "소재 개선+반품 주의형": ["색감", "사진일치", "소재", "두께감", "사이즈", "핏", "품질", "불량"],
    "소재·구매 전환 개선형": ["착용정보", "가격", "혜택", "만족도"],
    "소재·구매·반품 복합 리스크형": ["가격", "색감", "사이즈", "핏", "소재", "두께감", "사진일치", "품질", "불량"],
    "소수 전환형": ["착용정보", "사이즈", "핏", "만족도"],
    "소수 전환+반품 리스크형": ["사이즈", "핏", "소재", "두께감", "색감", "사진일치"],
    "광고 반응 부족형": ["사진일치", "색감", "착용정보", "만족도"],
    "광고 축소형": ["소재", "두께감", "색감", "사진일치", "만족도", "품질", "불량"],
}


KEYWORD_ALIASES = {
    "만족도": ["만족도", "만족", "좋아요", "좋았어요", "마음에", "추천", "예뻐요", "이뻐요", "자주 입", "잘 입"],
    "사이즈": ["사이즈", "크다", "작다", "정사이즈", "프리사이즈", "기장", "길이", "허리", "밴딩", "수선"],
    "핏": ["핏", "실루엣", "라인", "와이드", "체형", "체형커버", "떨어지는", "넉넉", "슬림", "여리"],
    "소재": ["소재", "원단", "재질", "촉감", "부드럽", "탄탄", "찰랑", "후들", "보들", "옷감"],
    "두께감": ["두께감", "두께", "두껍", "얇", "비침", "안비쳐", "봄", "가을", "여름", "겨울"],
    "색감": ["색감", "색상", "색", "컬러", "아이보리", "베이지", "네이비", "브라운", "밤색", "고동색"],
    "사진일치": ["사진일치", "사진과", "화면과", "상세페이지", "상세 페이지", "실물", "같아요", "비슷", "그대로"],
    "품질": ["품질", "퀄리티", "마감", "박음질", "재봉", "탄탄", "고급", "완성도"],
    "불량": ["불량", "하자", "뜯어", "실밥", "오염", "냄새", "석유냄새", "구멍", "찢어"],
    "가격": ["가격", "가성비", "비싸", "저렴", "가격대", "돈", "값"],
    "혜택": ["혜택", "쿠폰", "할인", "적립", "이벤트"],
    "배송": ["배송", "빨리", "빠르", "늦", "도착", "택배"],
    "교환": ["교환", "반품", "환불", "교환반품"],
    "착용정보": ["착용정보", "착용 정보", "착용샷", "착샷", "코디", "키", "몸무게", "스펙", "입었을 때"],
}

COMMON_REVIEW_KEYWORDS = [
    "사이즈",
    "핏",
    "소재",
    "두께감",
    "색감",
    "사진일치",
    "만족도",
    "품질",
    "배송",
]

def normalize_text(text):
    return str(text or "").replace(" ", "").lower()

def review_matches_keyword(content, keyword):
    normalized_content = normalize_text(content)

    aliases = KEYWORD_ALIASES.get(keyword, [keyword])

    return any(
        normalize_text(alias) in normalized_content
        for alias in aliases
    )

def fetch_reviews_by_each_keyword(product_id, target_keywords, limit_per_keyword=5):
    """
    각 우선 키워드별로 중복 없는 최신순 리뷰를 각각 limit_per_keyword개씩 수집한다.
    진단 유형별 키워드로 리뷰가 부족하면 공통 리뷰 키워드로 보완한다.
    """
    url = "https://api.zigzag.kr/api/2/graphql/batch/GetSimpleReviewList,GetReviewSearchList,GetReviewSearchCount,GetBestReviewList,GetReviewSummary"

    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "cookie": "connect.sid=s%3Aolu_uuOC80dPrUgzP-pKgcacjd9Y3po2..."
    }

    print(f"👉 [요청하는 상품 ID/정보]: {product_id}")

    collected_review_ids = set()
    keyword_results = {}
    all_fetched_reviews = []
    next_cursor = None
    max_loops = 7

    for _ in range(max_loops):
        payload = [{
            "operationName": "GetSimpleReviewList",
            "variables": {
                "input": {
                    "product_id": str(product_id),
                    "order": "DATE_CREATED_DESC",
                    "cursor": {
                        "end_cursor": next_cursor,
                        "limit_count": 20,
                    },
                }
            },
            "query": """
            query GetSimpleReviewList($input: UxSimpleReviewListInput!) {
              ux_simple_review_list(input: $input) {
                total_count
                has_next
                end_cursor
                component_list {
                  ... on UxSimpleReviewListItem {
                    review {
                      id
                      rating
                      date_created
                      contents
                    }
                  }
                }
              }
            }
            """
        }]

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"👉 [API 응답 상태코드]: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ [API 응답 실패]: {response.text[:500]}")
                break

            data = response.json()

            result = (
                data[0]
                .get("data", {})
                .get("ux_simple_review_list", {})
            )

        except Exception as e:
            print(f"❌ 리뷰 API 요청/파싱 실패: {e}")
            break

        reviews = result.get("component_list", [])

        if not reviews:
            break

        for item in reviews:
            r_data = item.get("review")
            if r_data:
                all_fetched_reviews.append(r_data)

        if not result.get("has_next"):
            break

        next_cursor = result.get("end_cursor")
        time.sleep(0.3)

    # 1순위: 진단 유형별 키워드로 리뷰 매칭
    for kw in target_keywords:
        matched_for_this_keyword = []

        for r in all_fetched_reviews:
            r_id = r.get("id")
            content = r.get("contents", "")

            if review_matches_keyword(content, kw) and r_id not in collected_review_ids:
                matched_for_this_keyword.append({
                    "id": r_id,
                    "rating": r.get("rating"),
                    "date_created": r.get("date_created"),
                    "contents": content,
                    "match_source": "diagnostic_keyword",
                })

                collected_review_ids.add(r_id)

                if len(matched_for_this_keyword) >= limit_per_keyword:
                    break

        keyword_results[kw] = matched_for_this_keyword

    # 진단 유형 키워드로 리뷰가 충분히 잡혔는지 확인
    diagnostic_keywords_with_reviews = [
        kw for kw, reviews in keyword_results.items()
        if isinstance(reviews, list) and len(reviews) > 0
    ]

    diagnostic_review_count = sum(
        len(reviews)
        for reviews in keyword_results.values()
        if isinstance(reviews, list)
    )

    # 기준: 리뷰가 있는 진단 키워드가 3개 미만이거나 전체 리뷰 수가 3개 미만이면 공통 키워드로 보완
    needs_common_fallback = (
        len(diagnostic_keywords_with_reviews) < 3
        or diagnostic_review_count < 3
    )

    added_common_keywords = []

    # 2순위: 공통 키워드로 보완
    if needs_common_fallback:
        for common_kw in COMMON_REVIEW_KEYWORDS:
            if common_kw in keyword_results:
                continue

            matched_for_common_keyword = []

            for r in all_fetched_reviews:
                r_id = r.get("id")
                content = r.get("contents", "")

                if review_matches_keyword(content, common_kw) and r_id not in collected_review_ids:
                    matched_for_common_keyword.append({
                        "id": r_id,
                        "rating": r.get("rating"),
                        "date_created": r.get("date_created"),
                        "contents": content,
                        "match_source": "common_keyword_fallback",
                    })

                    collected_review_ids.add(r_id)

                    if len(matched_for_common_keyword) >= limit_per_keyword:
                        break

            if matched_for_common_keyword:
                keyword_results[common_kw] = matched_for_common_keyword
                added_common_keywords.append(common_kw)

            visible_keyword_count = len([
                kw for kw, reviews in keyword_results.items()
                if isinstance(reviews, list) and len(reviews) > 0
            ])

            if visible_keyword_count >= 3:
                break

    keyword_results["_meta"] = {
        "diagnostic_keywords": target_keywords,
        "diagnostic_keywords_with_reviews": diagnostic_keywords_with_reviews,
        "diagnostic_review_count": diagnostic_review_count,
        "used_common_fallback": needs_common_fallback,
        "added_common_keywords": added_common_keywords,
        "notice": (
            "진단 유형별 우선 키워드와 직접 매칭되는 리뷰가 부족해 공통 리뷰 키워드로 보완했습니다."
            if needs_common_fallback and added_common_keywords
            else ""
        ),
    }

    return keyword_results


def attach_matched_reviews_to_products(products):
    """
    상품 분석 결과 리스트에 진단 유형별 키워드 리뷰를 붙이는 함수
    """
    enriched_products = []

    for product in products:
        product_id = product.get("product_id") or product.get("상품ID")
        product_type = product.get("product_type") or product.get("진단유형")

        target_keywords = DIAGNOSTIC_KEYWORD_MAP.get(product_type, [])

        matched_reviews = {}

        if product_id and target_keywords:
            matched_reviews = fetch_reviews_by_each_keyword(
                product_id=product_id,
                target_keywords=target_keywords,
                limit_per_keyword=5,
            )

        product["matched_reviews"] = matched_reviews
        enriched_products.append(product)

    return enriched_products