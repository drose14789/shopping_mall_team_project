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
    "광고 반응 부족형": ["사진일치", "색감", "착용 정보", "만족도"],
    "광고 축소형": ["소재", "두께감", "색감", "사진일치", "만족도", "품질", "불량"],
}

def fetch_reviews_by_each_keyword(product_id, target_keywords, limit_per_keyword=5):
    """
    각 우선 키워드별로 중복 없는 최신순 리뷰를 각각 limit_per_keyword(5)개씩 수집
    """
    url = "https://api.zigzag.kr/api/2/graphql/batch/GetSimpleReviewList,GetReviewSearchList,GetReviewSearchCount,GetBestReviewList,GetReviewSummary"
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "cookie": "connect.sid=s%3Aolu_uuOC80dPrUgzP-pKgcacjd9Y3po2..."
    }
    print(f"👉 [요청하는 상품 ID/정보]: {product_id}")
    collected_review_ids = set()  # 전체 중복 방지용 세트
    keyword_results = {}          # 키워드별 리뷰 저장 딕셔너리
    all_fetched_reviews = []
    next_cursor = None
    max_loops = 7  # 최대 140개까지 상위 풀 확보
    
    for _ in range(max_loops):
        payload = [{
            "operationName": "GetSimpleReviewList",
            "variables": {
                "input": {
                    "product_id": str(product_id),
                    "order": "DATE_CREATED_DESC",  # 최신순 정렬
                    "cursor": {"end_cursor": next_cursor, "limit_count": 20}
                }
            },
            "query": """
            query GetSimpleReviewList($input: UxSimpleReviewListInput!) {
              ux_simple_review_list(input: $input) {total_count has_next end_cursor
                component_list {
                  ... on UxSimpleReviewListItem {
                    review {id rating date_created contents}
                  }
                }
              }
            }
            """
        }]

        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"👉 [API 응답 상태코드]: {response.status_code}")
            print(f"👉 [API 응답 본문]: {response.text}")
            data = response.json()
            result = data[0]['data']['ux_simple_review_list']
        except Exception:
            break

        reviews = result.get('component_list', [])
        if not reviews:
            break

        for item in reviews:
            r_data = item.get('review')
            if r_data:
                all_fetched_reviews.append(r_data)

        if not result.get('has_next'):
            break
        next_cursor = result.get('end_cursor')
        time.sleep(0.3)

    # 각 키워드별로 순회하며 매칭되는 리뷰를 최대 5개씩 할당 (중복 제거)
    for kw in target_keywords:
        matched_for_this_keyword = []
        
        for r in all_fetched_reviews:
            r_id = r.get('id')
            content = r.get('contents', '')
            
            if kw in content and r_id not in collected_review_ids:
                matched_for_this_keyword.append({
                    "id": r_id,
                    "rating": r.get('rating'),
                    "date_created": r.get('date_created'),
                    "contents": content
                })
                collected_review_ids.add(r_id)
                
                if len(matched_for_this_keyword) >= limit_per_keyword:
                    break
                    
        keyword_results[kw] = matched_for_this_keyword

    return keyword_results