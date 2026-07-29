import pandas as pd
import glob
import os
import re
import numpy as np


def load_and_merge_and_save(folder_path, output_path):
    """1단계: 데이터를 불러와서 정제하고 'total_data_cleaned.csv'로 저장"""
    files = glob.glob(os.path.join(folder_path, "*.*"))
    target_files = [f for f in files if f.endswith(('.csv', '.xls', '.xlsx'))
                    and not os.path.basename(f).startswith('~$')
                    and 'total_data_cleaned' not in os.path.basename(f).lower()]
    df_list = []
    season_map = {'1-3': '겨울', '4-6': '봄', '7-9': '여름', '10-12': '가을'}

    for file in target_files:
        if file.endswith('.csv'):
            df = pd.read_csv(file, header=3)
        else:
            df = pd.read_excel(file, header=3)

        # 컬럼명 공백 제거
        df.columns = df.columns.str.strip()

        # 파일 이름에서 월 정보를 유연하게 찾는 정규식 (예: 7-9, 07-09 등)
        filename = os.path.basename(file)
        month_match = re.search(r'(\d{1,2})-(\d{1,2})', filename)

        if month_match:
            start = int(month_match.group(1))
            end = int(month_match.group(2))
            season = season_map.get(f"{start}-{end}", "계절?")
        else:
            season = "계절?"
        df['분기'] = f"{season}"

        category_col = '카테고리(3>4차)'
        if category_col in df.columns:
            df = df.dropna(subset=[category_col])

        df_list.append(df)

    if not df_list:
        raise ValueError("읽어들인 데이터가 없습니다. 폴더 경로를 확인해주세요.")

    df_total = pd.concat(df_list, ignore_index=True)
    print("처음 합친 직후 행 개수:", len(df_total))

    # 숫자형 데이터 변환
    calc_cols = ["주문금액", "광고과금액", "상품 찜 유저수", "상품 상세 방문수", "주문수량", "반품률"]
    for col in calc_cols:
        if col in df_total.columns:
            df_total[col] = df_total[col].astype(str).str.replace(",", "").str.replace("%", "")
            df_total[col] = pd.to_numeric(df_total[col], errors="coerce").fillna(0)

    df_total['광고비 비중'] = np.where(df_total['주문금액'] > 0, df_total['광고과금액'] / df_total['주문금액'], 0)
    df_total['ROAS'] = np.where(df_total['광고과금액'] > 0, df_total['주문금액'] / df_total['광고과금액'], 0)
    df_total['찜전환율'] = np.where(df_total['상품 상세 방문수'] > 0, df_total['상품 찜 유저수'] / df_total['상품 상세 방문수'], 0)
    df_total['상품단가'] = np.where(df_total['주문수량'] > 0, df_total['주문금액'] / df_total['주문수량'], 0)
    df_total['반품안정성'] = 100 - (df_total['반품률'] * 100)

    df_total[['ROAS', '찜전환율', '상품단가', '반품안정성']] = df_total[['ROAS', '찜전환율', '상품단가', '반품안정성']].replace([np.inf, -np.inf], 0).fillna(0)

    # 1차 상품ID 필터 (4번 미만 삭제)
    id_col = "*상품ID"
    if id_col in df_total.columns:
        valid_ids = df_total[id_col].value_counts()
        valid_ids = valid_ids[valid_ids >= 4].index
        df_total = df_total[df_total[id_col].isin(valid_ids)].reset_index(drop=True)
    print("1차 상품ID 필터 후 행 개수:", len(df_total))

    # 여름 데이터 중 조건에 맞는 행 삭제
    df_total = df_total[
        ~(
                (df_total["광고과금액"] == 0) &
                (df_total["주문금액"] == 0) &
                (df_total["분기"] == "여름")
        )
    ].reset_index(drop=True)
    print("여름 조건 삭제 후 행 개수:", len(df_total))

    # 2차 상품ID 필터
    if id_col in df_total.columns:
        counts = df_total[id_col].value_counts()
        valid_ids = counts[counts >= 4].index
        df_total = df_total[df_total[id_col].isin(valid_ids)].reset_index(drop=True)
    print("최종 정제 완료 후 행 개수:", len(df_total))

    # 결과 CSV 저장
    os.makedirs(output_path, exist_ok=True)
    save_path = os.path.join(output_path, 'total_data_cleaned.csv')
    df_total.to_csv(save_path, index=False, encoding='utf-8-sig')
    print("✅ 데이터 클리닝 완료 및 'total_data_cleaned.csv' 저장 완료!")


def analyze_and_save_counts(input_folder, output_excel_path):
    """2단계: 방금 생성된 'total_data_cleaned.csv' 또는 폴더 내 파일을 읽어 분석 수행"""
    target_file = os.path.join(input_folder, 'total_data_cleaned.csv')

    if not os.path.exists(target_file):
        print(f"경고: 분석할 'total_data_cleaned.csv' 파일을 찾을 수 없습니다. 경로: {target_file}")
        return

    with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
        try:
            try:
                df_all = pd.read_csv(target_file, encoding='utf-8-sig')
            except:
                df_all = pd.read_csv(target_file, encoding='cp949')

            # 주요 항목별 개수 집계
            target_col = '카테고리(3>4차)'
            if target_col in df_all.columns:
                counts = df_all[target_col].value_counts().reset_index()
                counts.columns = ['항목', '개수']
                counts.to_excel(writer, sheet_name='카테고리별_집계', index=False)
                print(f"저장 성공: 카테고리별_집계 (총 {len(counts)}개 항목)")
            else:
                # 컬럼이 없을 경우 첫 번째 컬럼 기준으로 집계
                first_col = df_all.columns[0]
                counts = df_all[first_col].value_counts().reset_index()
                counts.columns = ['항목', '개수']
                counts.to_excel(writer, sheet_name='기본_집계', index=False)
                print(f"저장 성공: 기본_집계 (총 {len(counts)}개 항목)")

        except Exception as e:
            print(f"파일 분석 에러: {e}")

    print(f"\n작업 완료: '{output_excel_path}' 파일 확인 바랍니다.")
    # 나온 분석결과_종류및개수 엑셀파일을 통해 어떤 카테고리별로 나눌것인지 수기로 확인 필요 -> 카테고리 컬럼 통합.xlsx 에 저장

if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

    origin_path = os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'origin_data')
    output_path = os.path.join(PROJECT_ROOT, 'data', 'analyze_data', 'input')

    # [1단계] 데이터 정제 및 total_data_cleaned.csv 저장 (정상 수치 도출)
    load_and_merge_and_save(origin_path, output_path)

    # [2단계] 방금 만들어진 total_data_cleaned.csv를 기반으로 엑셀 분석 수행
    result_excel_path = os.path.join(output_path, '분석결과_종류및개수.xlsx')
    analyze_and_save_counts(output_path, result_excel_path)