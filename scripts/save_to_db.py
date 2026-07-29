import os
import pandas as pd
from sqlalchemy import text
import scripts.db_setting as db


# 테이블 생성 DDL 스크립트
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS category_correlations (
    category VARCHAR(255) NOT NULL,
    quarter VARCHAR(20) NOT NULL,
    indicator_1 VARCHAR(100) NOT NULL,
    indicator_2 VARCHAR(100) NOT NULL,
    correlation_value DECIMAL(10, 4),
    PRIMARY KEY (category, quarter, indicator_1, indicator_2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS total_stats (
    category VARCHAR(255),
    quarter VARCHAR(20),
    order_amount DOUBLE PRECISION,
    exposure_cnt DOUBLE PRECISION,
    ad_cost_ratio DOUBLE PRECISION,
    ad_cost DOUBLE PRECISION,
    click_rate DOUBLE PRECISION,
    conv_rate DOUBLE PRECISION,
    order_cnt DOUBLE PRECISION,
    order_qty DOUBLE PRECISION,
    click_cnt DOUBLE PRECISION,
    visit_cnt DOUBLE PRECISION,
    wish_cnt DOUBLE PRECISION,
    cart_user_cnt DOUBLE PRECISION,
    cart_conv_rate DOUBLE PRECISION,
    return_cnt DOUBLE PRECISION,
    return_rate DOUBLE PRECISION,
    roas DOUBLE PRECISION,
    wish_conv_rate DOUBLE PRECISION,
    unit_price DOUBLE PRECISION,
    return_stability DOUBLE PRECISION,
    PRIMARY KEY (category, quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS outlier_stats (
    category VARCHAR(255),
    quarter VARCHAR(20),
    order_amount DOUBLE PRECISION,
    exposure_cnt DOUBLE PRECISION,
    ad_cost_ratio DOUBLE PRECISION,
    ad_cost DOUBLE PRECISION,
    click_rate DOUBLE PRECISION,
    conv_rate DOUBLE PRECISION,
    order_cnt DOUBLE PRECISION,
    order_qty DOUBLE PRECISION,
    click_cnt DOUBLE PRECISION,
    visit_cnt DOUBLE PRECISION,
    wish_cnt DOUBLE PRECISION,
    cart_user_cnt DOUBLE PRECISION,
    cart_conv_rate DOUBLE PRECISION,
    return_cnt DOUBLE PRECISION,
    return_rate DOUBLE PRECISION,
    roas DOUBLE PRECISION,
    wish_conv_rate DOUBLE PRECISION,
    unit_price DOUBLE PRECISION,
    return_stability DOUBLE PRECISION,
    PRIMARY KEY (category, quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS median_stats (
    category VARCHAR(255),
    quarter VARCHAR(20),
    order_amount DOUBLE PRECISION,
    exposure_cnt DOUBLE PRECISION,
    ad_cost_ratio DOUBLE PRECISION,
    ad_cost DOUBLE PRECISION,
    click_rate DOUBLE PRECISION,
    conv_rate DOUBLE PRECISION,
    order_cnt DOUBLE PRECISION,
    order_qty DOUBLE PRECISION,
    click_cnt DOUBLE PRECISION,
    visit_cnt DOUBLE PRECISION,
    wish_cnt DOUBLE PRECISION,
    cart_user_cnt DOUBLE PRECISION,
    cart_conv_rate DOUBLE PRECISION,
    return_cnt DOUBLE PRECISION,
    return_rate DOUBLE PRECISION,
    roas DOUBLE PRECISION,
    wish_conv_rate DOUBLE PRECISION,
    unit_price DOUBLE PRECISION,
    return_stability DOUBLE PRECISION,
    PRIMARY KEY (category, quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# 한글 -> DB 영문 컬럼 매핑 사전
COLUMN_MAP = {
    '카테고리': 'category',
    '분기': 'quarter',
    '지표1': 'indicator_1',
    '지표2': 'indicator_2',
    '상관계수': 'correlation_value',
    '주문금액': 'order_amount',
    '노출수': 'exposure_cnt',
    '광고비 비중': 'ad_cost_ratio',
    '광고과금액': 'ad_cost',
    '상품클릭률': 'click_rate',
    '구매전환율': 'conv_rate',
    '상품주문수': 'order_cnt',
    '주문수량': 'order_qty',
    '클릭수': 'click_cnt',
    '상품 상세 방문수': 'visit_cnt',
    '상품 찜 유저수': 'wish_cnt',
    '장바구니 유저수': 'cart_user_cnt',
    '장바구니 전환율': 'cart_conv_rate',
    '반품건수': 'return_cnt',
    '반품률': 'return_rate',
    'ROAS': 'roas',
    '찜전환율': 'wish_conv_rate',
    '상품단가': 'unit_price',
    '반품안정성': 'return_stability',
}


def init_db_tables(engine):
  """테이블이 없을 경우 생성"""
  print(">>> 1. DB 테이블 생성/확인 중...")
  with engine.begin() as conn:
    for statement in CREATE_TABLES_SQL.split(';'):
      if statement.strip():
        conn.execute(text(statement))
  print("-> 4개 테이블 생성/확인 완료!\n")


def import_excel_to_db(folder_path, engine):
  """엑셀 파일 4개를 읽어 DB에 적재"""
  init_db_tables(engine)

  # [파일명, DB 테이블명] 매핑 정보
  file_table_mapping = [
      ('통합_분기별_상관관계_병합.xlsx', 'category_correlations'),
      ('통합_분기별_전체평균_병합.xlsx', 'total_stats'),
      ('통합_분기별_상위결과_병합.xlsx', 'outlier_stats'),
      ('통합_분기별_중간치_결과_병합.xlsx', 'median_stats'),
  ]

  print('>>> 2. 엑셀 데이터 DB 적재 시작...')

  for file_name, table_name in file_table_mapping:
    file_path = os.path.join(folder_path, file_name)

    if not os.path.exists(file_path):
      print(f"[경고] '{file_name}' 파일이 존재하지 않아 건너뜁니다.")
      continue

    try:
      # 엑셀 파일 읽기
      df = pd.read_excel(file_path)

      # 컬럼명 한글 -> 영문 변환
      df = df.rename(columns=COLUMN_MAP)

      # 데이터 입력 시 기존 데이터 초기화 후 재적재
      with engine.begin() as conn:
        try:
          conn.execute(text(f'TRUNCATE TABLE {table_name}'))
        except Exception:
          conn.execute(text(f'DELETE FROM {table_name}'))

        df.to_sql(table_name, conn, if_exists='append', index=False)

      print(
          f"-> [{table_name}] 적재 완료 (파일명: {file_name} / 총 {len(df)}건)"
      )

    except Exception as e:
      print(f"[오류] {file_name} -> {table_name} 적재 중 에러 발생: {e}")

  print('\n모든 데이터가 성공적으로 DB에 저장되었습니다!')


if __name__ == '__main__':
  engine = db.get_engine()

  # 엑셀 파일들이 존재하는 폴더 경로 입력 (필요 시 수정)
  EXCEL_FOLDER_PATH = 'data/processed_stats'

  import_excel_to_db(EXCEL_FOLDER_PATH, engine)