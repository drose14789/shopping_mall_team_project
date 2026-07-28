import requests
import time
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import db_setting as db
import pandas as pd

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), index=True)
    rating = Column(Integer)
    contents = Column(String(2000))
    created_at = Column(DateTime)

engine = db.get_engine()

# 테이블이 존재하지 않으면 자동으로 생성
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def fetch_zigzag_reviews(product_id, cursor=None):
    url = "https://api.zigzag.kr/api/2/graphql/batch/GetSimpleReviewList,GetReviewSearchList,GetReviewSearchCount,GetBestReviewList,GetReviewSummary"
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "cookie": "connect.sid=s%3Aolu_uuOC80dPrUgzP-pKgcacjd9Y3po2..."
    }
    payload = [{
        "operationName": "GetSimpleReviewList",
        "variables": {
            "input": {
                "product_id": str(product_id),
                "order": "RATING_DESC",
                "cursor": {"end_cursor": cursor, "limit_count": 20}
            }
        },
        "query": """
        query GetSimpleReviewList($input: UxSimpleReviewListInput!) {
          ux_simple_review_list(input: $input) {total_count has_next end_cursor
            component_list {
              ... on UxSimpleReviewListItem {
                review {id rating date_created contents
                }
              }
            }
          }
        }
        """
    }]
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def save_reviews_to_db(reviews,product_id):
    """데이터를 가공하고 DB에 저장하는 함수"""
    session = Session()
    try:
        for item in reviews:
            r = item.get('review')
            if not r: continue

            # 컨텐츠가 없으면 건너뜀
            contents = r.get('contents')
            if not contents or str(contents).strip() == '':
                continue

            # 날짜 변환 (밀리초 -> datetime 객체)
            dt_obj = datetime.fromtimestamp(r['date_created'] / 1000)

            # 모델 객체 생성
            new_review = Review(
                id=str(r['id']),
                product_id=str(product_id),
                rating=r['rating'],
                contents=r['contents'],
                created_at=dt_obj
            )

            # 중복 저장을 방지하려면 merge 사용, 아니면 add
            session.merge(new_review)

        session.commit()
        print(f"DB 저장 완료: {len(reviews)}건")
    except Exception as e:
        session.rollback()
        print(f"DB 저장 중 에러 발생: {e}")
    finally:
        session.close()

def run_pipeline(product_id):
    """API 수집과 DB 저장을 순차적으로 수행하는 파이프라인"""
    next_cursor = None
    total_collected = 0

    while total_collected < 60:
        data = fetch_zigzag_reviews(product_id, next_cursor)
        print("--- 서버 응답 데이터 ---")
        print(data)
        print("------------------------")

        try:
            result = data[0]['data']['ux_simple_review_list']
        except KeyError as e:
            print(f"KeyError 발생! 데이터 구조 확인 필요: {e}")
            break

        reviews = result.get('component_list', [])

        # DB에 저장
        save_reviews_to_db(reviews, product_id)

        total_collected += len(reviews)
        print(f"진행 상황: {total_collected}개 처리 완료")

        if not result.get('has_next'):
            break

        next_cursor = result.get('end_cursor')
        time.sleep(1)


# 수집할 상품 ID 리스트 작성
def get_product_ids_from_excel(file_path):
  # 일단 헤더 없이(header=None) 전체 데이터를 그대로 읽어옵니다.
  df_raw = pd.read_excel(file_path, header=None)

  target_row_idx = None
  target_col_idx = None

  # 엑셀 전체 셀을 탐색하며 '상품'과 'id'(또는 'product')가 포함된 칸을 찾습니다.
  for r_idx in range(len(df_raw)):
    for c_idx in range(len(df_raw.columns)):
      val = str(df_raw.iloc[r_idx, c_idx]).lower()
      if ('상품' in val and 'id' in val) or ('product' in val) or ('상품번호' in val):
        target_row_idx = r_idx
        target_col_idx = c_idx
        break
    if target_row_idx is not None:
      break

  # 만약 특정 조합을 못 찾았으면 'id'나 '번호' 단어라도 찾기
  if target_row_idx is None:
    for r_idx in range(len(df_raw)):
      for c_idx in range(len(df_raw.columns)):
        val = str(df_raw.iloc[r_idx, c_idx]).lower()
        if 'id' in val or '번호' in val:
          target_row_idx = r_idx
          target_col_idx = c_idx
          break
      if target_row_idx is not None:
        break

  if target_row_idx is None:
    raise ValueError(
        "엑셀 파일 내 어디에도 '상품' 또는 'ID' 관련 키워드가 포함된 셀을 찾을"
        " 수 없습니다."
    )

  df = pd.read_excel(file_path, header=target_row_idx)
  target_col = df.columns[target_col_idx]

  print(
      f"'{target_col}' 컬럼(엑셀 {target_row_idx + 1}행)을 상품 ID 컬럼으로"
      " 자동 인식했습니다."
  )

  # 데이터 정제 후 리스트 반환
  cleaned_ids = (
      df[target_col].dropna().astype(float).astype(int).astype(str).tolist()
  )
  return cleaned_ids

# 실행 파이프라인
def run_all(file_path):
    product_ids = get_product_ids_from_excel(file_path)
    print(f"총 {len(product_ids)}개의 상품 ID를 불러왔습니다.")

    for pid in product_ids:
        print(f"\n>>> [상품 ID: {pid}] 수집 시작")
        try:
            run_pipeline(pid)
        except Exception as e:
            print(f"Error on {pid}: {e}")
        time.sleep(2)

run_all("26.04-26.06 업12.xlsx") #가져올 파일명