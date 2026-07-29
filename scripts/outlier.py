import pandas as pd
import os
from sqlalchemy import text
import scripts.db_setting as db


def process_data_to_db(input_file, output_path, mapping_file, engine):
    mapping = pd.read_excel(mapping_file)
    mapping_dict = dict(zip(mapping.iloc[:, 0], mapping.iloc[:, 1]))

    all_total_results = []
    all_outlier_results = []
    os.makedirs(output_path, exist_ok=True)

    mean_cols = [
        "주문금액", "노출수", "광고비 비중", "광고과금액", "상품클릭률", "구매전환율",
        "상품주문수", "주문수량", "클릭수", "상품 상세 방문수", "상품 찜 유저수",
        "장바구니 유저수", "장바구니 전환율", "반품건수", "반품률",
        "ROAS", "찜전환율", "상품단가", "반품안정성"
    ]

    db_column_map = {
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
        '반품안정성': 'return_stability'
    }

    # DB 테이블 초기화
    with engine.begin() as conn:
        for tbl in ["outlier_stats", "total_stats"]:
            try:
                conn.execute(text(f"TRUNCATE TABLE {tbl}"))
                print(f"-> 기존 {tbl} 테이블 데이터 초기화 완료")
            except Exception as e:
                conn.execute(text(f"DELETE FROM {tbl}"))
                print(f"-> 기존 {tbl} 테이블 데이터 삭제 완료")

    if os.path.exists(input_file):
        df = pd.read_csv(input_file)
        cat_col_name = df.columns[0]
        quarter_col = "분기"

        df[cat_col_name] = df[cat_col_name].replace(mapping_dict)

        for col in mean_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "").str.replace("%", "")
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        if not df.empty:
            # 전체 데이터 기준 평균 산출 후 리스트에 담기
            total_result_korean = df.groupby([cat_col_name, quarter_col], as_index=False)[mean_cols].mean()
            total_result_korean = total_result_korean.rename(columns={cat_col_name: 'category', quarter_col: 'quarter'})
            all_total_results.append(total_result_korean.copy())

            # 상위 10% 필터링 후 평균 산출 후 리스트에 담기
            thresholds = df.groupby([cat_col_name, quarter_col])['주문금액'].transform(lambda x: x.quantile(0.9))
            df_top = df[df['주문금액'] > thresholds]

            if not df_top.empty:
                outlier_result_korean = df_top.groupby([cat_col_name, quarter_col], as_index=False)[mean_cols].mean()
                outlier_result_korean = outlier_result_korean.rename(
                    columns={cat_col_name: 'category', quarter_col: 'quarter'})
                all_outlier_results.append(outlier_result_korean.copy())
                print(f"-> {input_file} 처리 완료: 전체 및 상위 10% 데이터 집계 완료")

    # 루프 종료 후 전체/분기 통합 데이터 계산 및 최종 DB 적재 (total_stats)
    if all_total_results:
        base_total_df = pd.concat(all_total_results, ignore_index=True)
        q_totals = base_total_df.groupby('quarter', as_index=False)[mean_cols].mean()
        q_totals['category'] = q_totals['quarter'].apply(lambda q: f"전체_Q{q}")
        q_totals['quarter'] = q_totals['quarter'].astype(str)

        all_total_row = base_total_df[mean_cols].mean().to_frame().T
        all_total_row['category'] = "전체"
        all_total_row['quarter'] = "전체"

        final_total_df = pd.concat([base_total_df, q_totals, all_total_row], ignore_index=True)

        with engine.begin() as conn:
            try:
                final_total_df.rename(columns=db_column_map).to_sql("total_stats", conn, if_exists="append",
                                                                    index=False)
                print("-> total_stats 최종 통합 데이터 DB 적재 완료")
            except Exception as e:
                print(f"-> total_stats DB 적재 실패: {e}")
                raise e

        final_total_df.to_excel(os.path.join(output_path, "통합_분기별_전체평균_병합.xlsx"), index=False)

    # 루프 종료 후 전체/분기 통합 데이터 계산 및 최종 DB 적재 (outlier_stats)
    if all_outlier_results:
        base_outlier_df = pd.concat(all_outlier_results, ignore_index=True)
        q_outliers = base_outlier_df.groupby('quarter', as_index=False)[mean_cols].mean()
        q_outliers['category'] = q_outliers['quarter'].apply(lambda q: f"전체_Q{q}")
        q_outliers['quarter'] = q_outliers['quarter'].astype(str)

        all_outlier_row = base_outlier_df[mean_cols].mean().to_frame().T
        all_outlier_row['category'] = "전체"
        all_outlier_row['quarter'] = "전체"

        final_outlier_df = pd.concat([base_outlier_df, q_outliers, all_outlier_row], ignore_index=True)

        with engine.begin() as conn:
            try:
                final_outlier_df.rename(columns=db_column_map).to_sql("outlier_stats", conn, if_exists="append",
                                                                      index=False)
                print("-> outlier_stats 최종 통합 데이터 DB 적재 완료")
            except Exception as e:
                print(f"-> outlier_stats DB 적재 실패: {e}")
                raise e

        final_outlier_df.to_excel(os.path.join(output_path, "통합_분기별_상위결과_병합.xlsx"), index=False)

    print(f"\n모든 데이터가 성공적으로 DB 및 CSV로 저장되었습니다!")


def process_data_to_db_median(input_path, output_path, mapping_file, engine):
    mapping = pd.read_excel(mapping_file)
    mapping_dict = dict(zip(mapping.iloc[:, 0], mapping.iloc[:, 1]))
    all_results_korean = []
    os.makedirs(output_path, exist_ok=True)

    target_cols = [
        "주문금액", "노출수", "광고비 비중", "광고과금액", "상품클릭률", "구매전환율",
        "상품주문수", "주문수량", "클릭수", "상품 상세 방문수", "상품 찜 유저수",
        "장바구니 유저수", "장바구니 전환율", "반품건수", "반품률",
        "ROAS", "찜전환율", "상품단가", "반품안정성"
    ]

    db_column_map = {
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
        '반품안정성': 'return_stability'
    }

    with engine.begin() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE median_stats"))
            print("-> 기존 median_stats 테이블 데이터 초기화 완료")
        except Exception as e:
            conn.execute(text("DELETE FROM median_stats"))
            print("-> 기존 median_stats 테이블 데이터 삭제 완료")

    if os.path.exists(input_path):
        df = pd.read_csv(input_path)
        cat_col_name = df.columns[0]
        quarter_col = "분기"

        df[cat_col_name] = df[cat_col_name].replace(mapping_dict)

        # 타겟 컬럼들을 명시적으로 숫자형으로 변환 (문자열 섞임 방지)
        for col in target_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "").str.replace("%", "").str.strip()
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        print(f"-> [디버깅] 전체 행 수: {len(df)}, '광고과금액' > 0 인 행 수: {len(df[df['광고과금액'] > 0])}")

        df_filtered = df[df['광고과금액'] > 0].copy()
        if not df_filtered.empty:
            df_filtered['median_val'] = df_filtered.groupby([cat_col_name, quarter_col])['광고과금액'].transform('median')
            df_filtered['diff'] = (df_filtered['광고과금액'] - df_filtered['median_val']).abs()
            idx = df_filtered.groupby([cat_col_name, quarter_col])['diff'].idxmin()
            result_korean_raw = df_filtered.loc[idx].drop(columns=['median_val', 'diff'])

            result_korean_raw = result_korean_raw.rename(columns={cat_col_name: 'category', quarter_col: 'quarter'})

            essential_cols = ['category', 'quarter'] + target_cols
            valid_cols = [col for col in essential_cols if col in result_korean_raw.columns]

            result_clean = result_korean_raw[valid_cols].copy()
            all_results_korean.append(result_clean)
            print(f"-> {input_path} 처리 완료: {len(result_clean)}개 카테고리/분기 데이터 집계 완료")
        else:
            print(f"-> [경고] '광고과금액'이 0보다 큰 데이터가 존재하지 않아 중간치 계산을 건너뜁니다.")

    if all_results_korean:
        base_median_df = pd.concat(all_results_korean, ignore_index=True)
        q_medians = base_median_df.groupby('quarter', as_index=False)[target_cols].mean()
        q_medians['category'] = q_medians['quarter'].apply(lambda q: f"전체_Q{q}")
        q_medians['quarter'] = q_medians['quarter'].astype(str)

        all_median_row = base_median_df[target_cols].mean().to_frame().T
        all_median_row['category'] = "전체"
        all_median_row['quarter'] = "전체"

        final_median_df = pd.concat([base_median_df, q_medians, all_median_row], ignore_index=True)

        with engine.begin() as conn:
            try:
                final_median_df.rename(columns=db_column_map).to_sql("median_stats", conn, if_exists="append",
                                                                     index=False)
                print("-> median_stats 최종 통합 데이터 DB 적재 완료")
            except Exception as e:
                print(f"-> DB 적재 실패: {e}")
                raise e

        save_name = "통합_분기별_중간치_결과_병합.xlsx"
        save_file_path = os.path.join(output_path, save_name)
        final_median_df.to_excel(save_file_path, index=False)
        print(f"\n모든 데이터가 성공적으로 '{save_file_path}' 파일로 저장되었습니다!")


if __name__ == "__main__":
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

    engine = db.get_engine()

    # 공통 경로 설정 (data/analyze_data/input 및 output)
    target_input_file = os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'input', 'total_data_cleaned.csv')
    target_output_path = os.path.join(PROJECT_ROOT, 'data', 'processed_stats')
    target_mapping_file = os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'input', '카테고리 컬럼 통합.xlsx')

    process_data_to_db(
        target_input_file,
        target_output_path,
        target_mapping_file,
        engine
    )

    process_data_to_db_median(
        target_input_file,
        target_output_path,
        target_mapping_file,
        engine
    )