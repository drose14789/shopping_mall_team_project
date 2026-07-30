from app.schemas.score_schema import ProductExcelRow
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import text
import os
import scripts.db_setting as db
from datetime import datetime


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


def ensure_evaluation_table_exists(engine):
  """evaluation_results 테이블이 없으면 자동으로 생성 (client_uuid 및 분석 시간 포함)"""
  create_table_query = text("""
                            CREATE TABLE IF NOT EXISTS evaluation_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        client_uuid VARCHAR(100),
        product_name VARCHAR(255),
        product_id VARCHAR(100),
        category VARCHAR(100),
        quarter VARCHAR(50),
        exposure_count INT,
        click_count INT,
        visit_count INT,
        wish_user_count INT,
        cart_user_count INT,
        order_count INT,
        return_count INT,
        ad_spend FLOAT,
        order_amount FLOAT,
        unit_price FLOAT,
        calc_click_rate FLOAT,
        calc_wish_conv FLOAT,
        calc_cart_conv FLOAT,
        calc_conv_rate FLOAT,
        calc_return_stability FLOAT,
        calc_roas FLOAT,
        score_click_rate FLOAT,
        score_wish_conv FLOAT,
        score_cart_conv FLOAT,
        score_conv_rate FLOAT,
        score_return_stability FLOAT,
        score_roas FLOAT,
        weight_unit_price FLOAT,
        weight_cart_conv FLOAT,
        weight_conv_rate FLOAT,
        weight_return_stability FLOAT,
        weight_roas FLOAT,
        total_score FLOAT,
        recommended_ad_spend FLOAT,
        product_type VARCHAR(100),
        created_at DATETIME
    )
  """)
  with engine.begin() as conn:
    conn.execute(create_table_query)


def evaluate_single_excel_file(user_excel_path, engine, client_uuid: str = "default_user"):
    """단일 엑셀 파일을 읽어 기존 평가를 수행하고 client_uuid와 분석 시간을 함께 저장"""
    # 테이블 존재 여부 확인 및 생성 (uuid 컬럼 포함)
    ensure_evaluation_table_exists(engine)

    user_df = validate_and_read_excel(user_excel_path)
    file_results = []

    # 분석 시간 통일을 위해 함수 실행 시점의 타임스탬프 생성 (시간순 정렬용)
    analysis_time = datetime.now()

    for idx, row in user_df.iterrows():
        if pd.isna(row.get('카테고리')) or pd.isna(row.get('노출수')):
            continue

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
            'unit_price': item_price_val,
        }

        weight_query = text("""
                            SELECT indicator_1, indicator_2, correlation_value
                            FROM category_correlations
                            WHERE category = :category
                              AND quarter = :quarter
                            """)

        with engine.connect() as conn:
            weight_df = pd.read_sql(weight_query, conn, params={"category": category_name, "quarter": quarter_val})
            
            if weight_df.empty:
                fallback_query = text("""
                                      SELECT indicator_1, indicator_2, correlation_value
                                      FROM category_correlations
                                      WHERE category = '전체'
                                        AND quarter = :quarter
                                      """)
                weight_df = pd.read_sql(fallback_query, conn, params={"quarter": quarter_val})

        raw_weights = {}
        indicator_mapping = {
            '구매전환율': 'conv_rate',
            '장바구니전환율': 'cart_conv_rate',
            '상품단가': 'unit_price',
            'ROAS': 'roas',
            '반품안정성': 'return_stability'
        }

        for _, w_row in weight_df.iterrows():
            ind1 = w_row['indicator_1']
            ind2 = w_row['indicator_2']

            # 💡 핵심: 자기 자신과의 상관관계(1.0)는 가중치 계산에서 제외!
            if ind1 == ind2:
                continue

            corr_val = abs(float(w_row['correlation_value'])) if pd.notnull(w_row['correlation_value']) else 0.0

            ind1_key = indicator_mapping.get(ind1)
            ind2_key = indicator_mapping.get(ind2)

            if ind1_key:
                raw_weights[ind1_key] = max(raw_weights.get(ind1_key, 0.0), corr_val)
            if ind2_key:
                raw_weights[ind2_key] = max(raw_weights.get(ind2_key, 0.0), corr_val)

        default_fallback_weights = {
            'unit_price': 0.20,
            'cart_conv_rate': 0.20,
            'conv_rate': 0.30,
            'return_stability': 0.15,
            'roas': 0.15,
        }

        if len(raw_weights) >= 3:
            total_corr_sum = sum(raw_weights.values())
            if total_corr_sum > 0:
                dynamic_weights = {k: v / total_corr_sum for k, v in raw_weights.items()}
                for k in default_fallback_weights.keys():
                    if k not in dynamic_weights:
                        dynamic_weights[k] = default_fallback_weights[k]

                s_sum = sum(dynamic_weights.values())
                dynamic_weights = {k: v / s_sum for k, v in dynamic_weights.items()}
            else:
                dynamic_weights = default_fallback_weights
        else:
            dynamic_weights = default_fallback_weights

        ideal_value_query = 'SELECT click_rate, wish_conv_rate, cart_conv_rate, conv_rate, return_stability, roas, unit_price FROM ideal_value_stats'
        with engine.connect() as conn:
            pool_df = pd.read_sql(text(ideal_value_query), conn)

        total_market_query = 'SELECT click_rate, wish_conv_rate, cart_conv_rate, conv_rate, return_stability, roas, unit_price FROM total_stats'
        with engine.connect() as conn:
            total_pool_df = pd.read_sql(text(total_market_query), conn)

        feedback = {}
        metric_labels = {
            'click_rate': '상품클릭률',
            'wish_conv_rate': '찜전환율',
            'cart_conv_rate': '장바구니전환율',
            'conv_rate': '구매전환율',
            'return_stability': '반품안정성',
            'roas': 'ROAS',
            'unit_price': '상품단가',
        }

        for col, label in metric_labels.items():
            user_val = user_metrics[col]
            if col == 'unit_price':
                total_series_price = total_pool_df[
                    'unit_price'].dropna() if 'unit_price' in total_pool_df.columns else pd.Series()
                if len(total_series_price) > 0:
                    mean_p = total_series_price.mean()
                    if user_val < mean_p * 0.6:
                        feedback[label] = '시장 평균 대비 합리적인 가성비 포지션입니다. 상세페이지에서 가격 메리트를 강조해보세요.'
                    elif user_val > mean_p * 1.4:
                        feedback[label] = '시장 평균 대비 고가 프리미엄 포지션입니다. 고품질 어필 포인트가 중요합니다.'
                    else:
                        feedback[label] = '시장 주력 가격대(메인스트림)에 안정적으로 안착해 있는 가격 포지션입니다.'
                else:
                    feedback[label] = '시장 단가 데이터가 부족합니다.'
                continue

            series = pool_df[col].dropna()
            if len(series) == 0:
                feedback[label] = '비교할 시장 데이터가 부족합니다.'
                continue

            benchmark_val = series.mean()
            if col in ['click_rate', 'wish_conv_rate', 'cart_conv_rate', 'conv_rate']:
                benchmark_val = benchmark_val * 100

            achievement_rate = (user_val / benchmark_val * 100) if benchmark_val > 0 else 0.0
            final_score = round(achievement_rate, 1)

            if final_score >= 100:
                feedback[label] = f'상위 10% 그룹 평균 대비 {final_score}% 수준으로 매우 우수합니다!'
            elif final_score >= 70:
                feedback[label] = f'상위 10% 그룹 평균의 {final_score}% 수준으로 양호합니다.'
            else:
                feedback[label] = f'상위 10% 그룹 평균의 {final_score}% 수준으로 개선이 필요합니다.'

        percentile_scores = {}
        for col in metric_labels.keys():
            user_val = user_metrics[col]
            total_series = total_pool_df[col].dropna() if col in total_pool_df.columns else pd.Series()

            if len(total_series) > 0:
                if col == 'unit_price':
                    top_mean = total_series[total_series >= total_series.quantile(0.80)].mean()
                    top_mean = top_mean if not pd.isna(top_mean) and top_mean > 0 else total_series.mean()
                    diff_ratio = abs(user_val - top_mean) / top_mean if top_mean > 0 else 0.0
                    percentile_scores[col] = round(max(0.0, 100.0 - (diff_ratio * 100.0)), 1)
                else:
                    percentile_scores[col] = round((total_series < user_val).mean() * 100, 1)
            else:
                percentile_scores[col] = 50.0

        evaluation_metrics = {
            'unit_price': '상품단가',
            'cart_conv_rate': '장바구니전환율',
            'conv_rate': '구매전환율',
            'return_stability': '반품안정성',
            'roas': 'ROAS',
        }

        total_score = sum(
            percentile_scores.get(col, 50.0) * dynamic_weights[col]
            for col in evaluation_metrics.keys()
        )

        penalty = 0.0
        if user_metrics['conv_rate'] < 1.0:
            penalty += 15.0
        if user_metrics['roas'] <= 100.0:
            penalty += 10.0
        total_score = max(0.0, total_score - penalty)
        total_score = round(total_score, 2)

        product_type = classify_product_type(
            click_score=percentile_scores.get('click_rate', 50.0),
            cart_score=percentile_scores.get('cart_conv_rate', 50.0),
            conv_score=percentile_scores.get('conv_rate', 50.0),
            return_score=percentile_scores.get('return_stability', 50.0),
        )

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
            'client_uuid': [client_uuid],  # 👈 전달받은 client_uuid 추가
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
            'unit_price': [float(item_price_val)],
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
            'weight_unit_price': [dynamic_weights['unit_price']],
            'weight_cart_conv': [dynamic_weights['cart_conv_rate']],
            'weight_conv_rate': [dynamic_weights['conv_rate']],
            'weight_return_stability': [dynamic_weights['return_stability']],
            'weight_roas': [dynamic_weights['roas']],
            'total_score': [total_score],
            'recommended_ad_spend': [recommended_ad_spend],
            'product_type': [product_type],
            'created_at': [analysis_time],  # 👈 시간순 정렬을 위한 분석 시간 추가
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    excel_file_path = os.path.join(root_dir, "data", "test", "샘플 템플릿.xlsx")

    try:
        results = evaluate_single_excel_file(
            user_excel_path=excel_file_path,
            engine=db.get_engine(),
            client_uuid="test_uuid_12345"  # 테스트용 UUID 전달
        )
        import json

        print(json.dumps(results, ensure_ascii=False, indent=4))
    except Exception as e:
        print(f"실행 중 에러 발생: {e}")