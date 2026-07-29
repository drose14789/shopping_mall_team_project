from app.schemas.score_schema import ProductExcelRow
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import text
import os
import scripts.db_setting as db

def validate_and_read_excel(user_excel_path):
  """엑셀 파일을 읽고 필수 컬럼 및 데이터 구조를 검증"""
  try:
    user_df = pd.read_excel(user_excel_path)
  except Exception as e:
    raise HTTPException(
        status_code=400,
        detail=f"엑셀 파일을 읽는 중 오류가 발생했습니다. 파일 형식을 확인해주세요: {e}",
    )

  required_columns = [
      '카테고리',
      '노출수',
      '클릭수',
      '상품 상세 방문수',
      '상품주문수',
      '반품건수',
      '광고과금액',
      '주문금액',
      '상품단가',
  ]

  missing_columns = [col for col in required_columns if col not in user_df.columns]
  if missing_columns:
    raise HTTPException(
        status_code=400,
        detail=(
            "엑셀 파일에 필수 컬럼이 누락되었습니다. 다음 컬럼들을"
            f" 확인해주세요: {missing_columns}"
        ),
    )

  if user_df.empty:
    raise HTTPException(
        status_code=400, detail='업로드된 엑셀 파일에 데이터가 비어 있습니다.'
    )

  return user_df


def classify_product_type(click_score, cart_score, conv_score, return_score):
  """4가지 지표 점수를 (True/False) 튜플 상태키로 변환하여 유형을 매핑"""
  key = tuple(
      score >= 60 for score in (click_score, cart_score, conv_score, return_score)
  )

  type_mapping = {
      (True, True, True, True): '핵심 확대형',
      (True, True, True, False): '반품 리스크 확대 보류형',
      (True, True, False, True): '구매 직전 이탈형',
      (True, True, False, False): '구매·반품 복합 리스크형',
      (True, False, True, True): '전환 효율형',
      (True, False, True, False): '반품 주의 유지형',
      (True, False, False, True): '상세페이지 개선형',
      (True, False, False, False): '상세·반품 복합 개선형',
      (False, True, True, True): '숨은 효율형',
      (False, True, True, False): '소재 개선+반품 주의형',
      (False, True, False, True): '소재·구매 전환 개선형',
      (False, True, False, False): '소재·구매·반품 복합 리스크형',
      (False, False, True, True): '소수 전환형',
      (False, False, True, False): '소수 전환+반품 리스크형',
      (False, False, False, True): '광고 반응 부족형',
      (False, False, False, False): '광고 축소형',
  }

  return type_mapping.get(key, '유형 미분류')


def evaluate_single_excel_file(user_excel_path, engine):
  """단일 엑셀 파일을 읽어 기존 평가 로직을 수행"""
  # 총 점수 계산 가중치 조정
  fixed_weights = {
      'click_rate': 0.15,
      'wish_conv_rate': 0.10,
      'cart_conv_rate': 0.15,
      'conv_rate': 0.30,
      'return_stability': 0.15,
      'roas': 0.15,
  }

  user_df = validate_and_read_excel(user_excel_path)
  file_results = []

  for idx, row in user_df.iterrows():
    if pd.isna(row.get('카테고리')) or pd.isna(row.get('노출수')):
      continue

    # 엑셀 행 데이터 유효성 검증 및 타입 강제 변환
    try:
      row_dict = row.to_dict()
      validated_row = ProductExcelRow(**row_dict)
    except Exception as e:
      raise HTTPException(
          status_code=400,
          detail=(
              f"{idx + 2}행 데이터 형식이 올바르지 않습니다 (필수값 누락 또는"
              f" 타입 오류): {e}"
          ),
      )

    product_name_val = str(
        row.get('상품명', row.get('상품 이름', f'상품_{idx + 1}'))
    )
    category_name = validated_row.category
    quarter_val = validated_row.quarter
    product_id = str(row.get('상품 ID', ''))

    exposure = float(validated_row.exposure)
    click = float(validated_row.click)
    visit = float(validated_row.visit)
    wish = float(validated_row.wish)
    cart = float(validated_row.cart)
    order_cnt = float(validated_row.order_cnt)
    return_cnt = float(validated_row.return_cnt)
    ad_cost = float(validated_row.ad_cost)
    order_amount = float(validated_row.order_amount)
    item_price_val = float(validated_row.item_price)

    if order_cnt > 0:
      raw_return_rate = (return_cnt / order_cnt) * 100
      base_stability = max(0.0, 100.0 - raw_return_rate)
      if order_cnt < 10:
        return_stability_val = (
            base_stability * (order_cnt / 10.0)
            + 70.0 * (1.0 - (order_cnt / 10.0))
        )
      else:
        return_stability_val = base_stability
    else:
      return_stability_val = 50.0

    user_metrics = {
        'click_rate': (click / exposure * 100) if exposure > 0 else 0.0,
        'wish_conv_rate': (wish / visit * 100) if visit > 0 else 0.0,
        'cart_conv_rate': (cart / visit * 100) if visit > 0 else 0.0,
        'conv_rate': (order_cnt / visit * 100) if visit > 0 else 0.0,
        'return_stability': round(return_stability_val, 2),
        'roas': (order_amount / ad_cost * 100) if ad_cost > 0 else 0.0,
    }

    outlier_query = 'SELECT click_rate, wish_conv_rate, cart_conv_rate, conv_rate, return_stability, roas FROM outlier_stats'
    with engine.connect() as conn:
      pool_df = pd.read_sql(text(outlier_query), conn)

    feedback = {}
    metric_labels = {
        'click_rate': '상품클릭률',
        'wish_conv_rate': '찜전환율',
        'cart_conv_rate': '장바구니전환율',
        'conv_rate': '구매전환율',
        'return_stability': '반품안정성',
        'roas': 'ROAS',
    }

    for col, label in metric_labels.items():
      user_val = user_metrics[col]
      series = pool_df[col].dropna()
      if len(series) == 0:
        feedback[label] = '비교할 시장 데이터가 부족합니다.'
        continue

      benchmark_val = series.mean()
      if col in ['click_rate', 'wish_conv_rate', 'cart_conv_rate', 'conv_rate']:
        benchmark_val = benchmark_val * 100

      achievement_rate = (
          (user_val / benchmark_val * 100) if benchmark_val > 0 else 0.0
      )
      final_score = round(achievement_rate, 1)

      if final_score >= 100:
        feedback[label] = (
            f'상위 10% 그룹 평균 대비 {final_score}% 수준으로 매우 우수합니다!'
        )
      elif final_score >= 70:
        feedback[label] = (
            f'상위 10% 그룹 평균의 {final_score}% 수준으로 양호합니다.'
        )
      else:
        feedback[label] = (
            f'상위 10% 그룹 평균의 {final_score}% 수준으로 개선이 필요합니다.'
        )

    total_market_query = 'SELECT click_rate, wish_conv_rate, cart_conv_rate, conv_rate, return_stability, roas FROM total_stats'
    with engine.connect() as conn:
      total_pool_df = pd.read_sql(text(total_market_query), conn)

    percentile_scores = {}
    for col in metric_labels.keys():
      user_val = user_metrics[col]
      total_series = total_pool_df[col].dropna()
      if len(total_series) > 0:
        percentile = (total_series < user_val).mean() * 100
        percentile_scores[col] = round(percentile, 1)
      else:
        percentile_scores[col] = 50.0

    total_score = sum(
        percentile_scores[col] * fixed_weights[col]
        for col in metric_labels.keys()
    )
    # 페널티 부여 구간
    penalty = 0.0
    if user_metrics['conv_rate'] < 1.0: # 구매전환율
      penalty += 15.0
    if user_metrics['roas'] <= 100.0:  # ROAS
      penalty += 10.0
    total_score = max(0.0, total_score - penalty)
    total_score = round(total_score, 2)

    product_type = classify_product_type(
        click_score=percentile_scores.get('click_rate', 50.0),
        cart_score=percentile_scores.get('cart_conv_rate', 50.0),
        conv_score=percentile_scores.get('conv_rate', 50.0),
        return_score=percentile_scores.get('return_stability', 50.0),
    )
    # 기본 광고추천금액
    base_ad_spend = 10000.0

    def score_to_modifier(percentile):
      return (percentile - 50.0) / 25.0

    click_pct = percentile_scores.get('click_rate', 50.0)
    conv_pct = percentile_scores.get('conv_rate', 50.0)
    roas_pct = percentile_scores.get('roas', 50.0)

    click_score = max(-2.0, min(2.0, score_to_modifier(click_pct)))
    conv_score = max(-2.0, min(2.0, score_to_modifier(conv_pct)))
    roas_score = max(-2.0, min(2.0, score_to_modifier(roas_pct)))

    ad_weights = {'click_rate': 0.25, 'conv_rate': 0.35, 'roas': 0.40}
    total_modifier = (
        (click_score * ad_weights['click_rate'])
        + (conv_score * ad_weights['conv_rate'])
        + (roas_score * ad_weights['roas'])
    )

    calculated_spend = base_ad_spend + (
        item_price_val * 0.1 * total_modifier
    )
    recommended_ad_spend = round(max(0.0, calculated_spend), 2)

    result_data = {
        'product_name': [product_name_val],
        'product_id': [product_id],
        'category': [category_name],
        'quarter': [quarter_val],
        'exposure_count': [int(exposure)],
        'click_count': [int(click)],
        'visit_count': [int(visit)],
        'wish_user_count': [int(wish)],
        'cart_user_count': [int(cart)],
        'order_count': [int(order_cnt)],
        'return_count': [int(return_cnt)],
        'ad_spend': [float(ad_cost)],
        'order_amount': [float(order_amount)],
        'item_price': [float(item_price_val)],
        'calc_click_rate': [user_metrics['click_rate']],
        'calc_wish_conv': [user_metrics['wish_conv_rate']],
        'calc_cart_conv': [user_metrics['cart_conv_rate']],
        'calc_conv_rate': [user_metrics['conv_rate']],
        'calc_return_stability': [user_metrics['return_stability']],
        'calc_roas': [user_metrics['roas']],
        'score_click_rate': [percentile_scores['click_rate']],
        'score_wish_conv': [percentile_scores['wish_conv_rate']],
        'score_cart_conv': [percentile_scores['cart_conv_rate']],
        'score_conv_rate': [percentile_scores['conv_rate']],
        'score_return_stability': [percentile_scores['return_stability']],
        'score_roas': [percentile_scores['roas']],
        'weight_click_rate': [fixed_weights['click_rate']],
        'weight_wish_conv': [fixed_weights['wish_conv_rate']],
        'weight_cart_conv': [fixed_weights['cart_conv_rate']],
        'weight_conv_rate': [fixed_weights['conv_rate']],
        'weight_return_stability': [fixed_weights['return_stability']],
        'weight_roas': [fixed_weights['roas']],
        'total_score': [total_score],
        'recommended_ad_spend': [recommended_ad_spend],
        'product_type': [product_type],
    }

    result_df = pd.DataFrame(result_data)
    with engine.begin() as conn:
      try:
        result_df.to_sql(
            'evaluation_results', conn, if_exists='append', index=False
        )
      except Exception as e:
        print(f'-> DB 저장 실패: {e}')

    file_results.append({
        'row_index': idx + 2,
        'product_name': product_name_val,
        'category': category_name,
        'season': quarter_val,
        'total_score': total_score,
        'calculated_metrics': user_metrics,
        'percentile_scores': percentile_scores,
        'coaching_feedback': feedback,
        'product_type': product_type,
    })

  return file_results


if __name__ == "__main__":
    # 단일 파일 테스트용 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    excel_file_path = os.path.join(root_dir, "data", "test", "샘플 템플릿.xlsx")

    try:
        results = evaluate_single_excel_file(
            user_excel_path=excel_file_path,
            engine=db.get_engine()
        )
        import json

        print(json.dumps(results, ensure_ascii=False, indent=4))
    except Exception as e:
        print(f"실행 중 에러 발생: {e}")