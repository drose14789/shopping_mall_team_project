import os
import pandas as pd
import numpy as np
import scripts.db_setting as db
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler


def process_data(input_file, output_path, mapping_file, engine):
    mapping = pd.read_excel(mapping_file)
    mapping_dict = dict(zip(mapping.iloc[:, 0], mapping.iloc[:, 1]))

    # 분석 대상 컬럼 (6개로 최적화)
    mean_cols = [
        "주문금액",
        "구매전환율",
        "장바구니 전환율",
        "상품단가",
        "ROAS",
        "반품안정성"
    ]

    os.makedirs(output_path, exist_ok=True)

    # 새로운 데이터를 넣기 전에 기존 category_correlations 테이블 전체 초기화
    with engine.begin() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE category_correlations"))
            print("-> 기존 category_correlations 테이블 데이터 초기화 완료")
        except Exception as e:
            conn.execute(text("DELETE FROM category_correlations"))
            print("-> 기존 category_correlations 테이블 데이터 삭제 완료")

    all_dfs = []
    file_corrs = []

    if os.path.exists(input_file):
        df = pd.read_csv(input_file)
        cat_col_name = df.columns[0]
        quarter_col = "분기"

        df[cat_col_name] = df[cat_col_name].replace(mapping_dict)

        # 분석 대상 컬럼들을 숫자로 변환 (결측치는 0으로 채움)
        for col in mean_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "").str.replace("%", "")
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df[mean_cols] = df[mean_cols].fillna(0)
        all_dfs.append(df)

        # 카테고리별 + 분기별 상관관계 계산
        for (category_name, quarter_val), group_df in df.groupby([cat_col_name, quarter_col]):
            if len(group_df) < 3:
                continue

            group_df = group_df.copy()
            group_df[mean_cols] = group_df[mean_cols].replace([np.inf, -np.inf], 0).fillna(0)

            # 표준화 적용
            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(group_df[mean_cols])
            scaled_df = pd.DataFrame(scaled_values, columns=mean_cols)

            corr_matrix = scaled_df.corr().fillna(0)
            corr_long = corr_matrix.stack().reset_index()
            corr_long.columns = ['indicator_1', 'indicator_2', 'correlation_value']
            corr_long['category'] = category_name
            corr_long['quarter'] = str(quarter_val)
            file_corrs.append(corr_long)

            if not corr_long.empty:
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        corr_long.to_sql("category_correlations", conn, if_exists="append", index=False, chunksize=100)
                        trans.commit()
                        print(f"-> [카테고리별] {category_name} ({quarter_val}) 저장 완료")
                    except Exception as e:
                        trans.rollback()
                        print(f"-> [카테고리별] {category_name} ({quarter_val}) 저장 실패: {e}")

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df[mean_cols] = combined_df[mean_cols].replace([np.inf, -np.inf], 0).fillna(0)

        # 쿼터별 전체 통합 상관관계
        quarter_col = "분기"
        if quarter_col in combined_df.columns:
            for quarter_val, group_df in combined_df.groupby(quarter_col):
                if len(group_df) < 3:
                    continue

                scaler = StandardScaler()
                scaled_values = scaler.fit_transform(group_df[mean_cols])
                scaled_df = pd.DataFrame(scaled_values, columns=mean_cols)

                corr_matrix = scaled_df.corr().fillna(0)
                corr_long = corr_matrix.stack().reset_index()
                corr_long.columns = ['indicator_1', 'indicator_2', 'correlation_value']
                corr_long['category'] = f"전체_Q{quarter_val}"  # 구분용 명칭
                corr_long['quarter'] = str(quarter_val)
                file_corrs.append(corr_long)

                if not corr_long.empty:
                    with engine.connect() as conn:
                        trans = conn.begin()
                        try:
                            corr_long.to_sql("category_correlations", conn, if_exists="append", index=False,
                                             chunksize=100)
                            trans.commit()
                            print(f"-> [분기별 통합] Q{quarter_val} 저장 완료")
                        except Exception as e:
                            trans.rollback()
                            print(f"-> [분기별 통합] Q{quarter_val} 저장 실패: {e}")

        # 전체 데이터 상관관계
        if len(combined_df) >= 3:
            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(combined_df[mean_cols])
            scaled_df = pd.DataFrame(scaled_values, columns=mean_cols)

            corr_matrix = scaled_df.corr().fillna(0)
            corr_long = corr_matrix.stack().reset_index()
            corr_long.columns = ['indicator_1', 'indicator_2', 'correlation_value']
            corr_long['category'] = "전체"
            corr_long['quarter'] = "전체"
            file_corrs.append(corr_long)

            if not corr_long.empty:
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        corr_long.to_sql("category_correlations", conn, if_exists="append", index=False, chunksize=100)
                        trans.commit()
                        print(f"-> [전체 통합] 저장 완료")
                    except Exception as e:
                        trans.rollback()
                        print(f"-> [전체 통합] 저장 실패: {e}")

    # 결과 Excel 저장 (모든 결과 병합)
    if file_corrs:
        final_corr_df = pd.concat(file_corrs, ignore_index=True)
        save_name = "통합_분기별_상관관계_병합.xlsx"
        final_corr_df.to_excel(os.path.join(output_path, save_name), index=False)
        print(f"-> 최종 XLSX 저장 완료: {save_name}")

    print("=== 모든 처리 완료 ===")


if __name__ == "__main__":
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

    engine = db.get_engine()
    process_data(
        input_file=os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'input', 'total_data_cleaned.csv'),
        output_path=os.path.join(PROJECT_ROOT, 'data', 'processed_stats'),
        mapping_file=os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'input', '카테고리 컬럼 통합.xlsx'),
        engine=engine
    )