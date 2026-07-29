import os
import re
import db_setting as db
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# DB 엔진 연결
engine = db.get_engine()

# 기본 폰트 설정 및 한글 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 시각화 대상 카테고리
target_categories = [
    '전체',
    '전체_Q가을',
    '전체_Q겨울',
    '전체_Q봄',
    '전체_Q여름',
    '가디건>4차없음'
]

# 결과 이미지를 저장할 폴더 생성
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
output_dir = os.path.join(PROJECT_ROOT, 'data', 'visualizations')

if not os.path.exists(output_dir):
  os.makedirs(output_dir)

def get_safe_filename(name):
    # 윈도우 파일명에 쓸 수 없는 문자들(\, /, :, *, ?, ", <, >, |)을 언더바(_)로 강제 치환
    return re.sub(r'[\\/:\*\?"<>\|]', '_', str(name))

# 1. 상관관계 히트맵 (Heatmap)

def plot_correlation_heatmap_by_quarter(category, safe_cat_name, quarter):
  # category가 '전체'일 때는 quarter도 '전체'일 때만 조회되도록 조건 보정
  if category == '전체' and quarter != '전체':
      return  # '전체' 카테고리는 계절별 히트맵을 그리지 않고 '전체' 분기만 처리
  if category.startswith('전체_Q') and quarter != category.replace('전체_Q', ''):
      return  # '전체_Q가을'은 '가을' 분기만 처리하고 나머지는 건너뜀

  query = f"""
        SELECT indicator_1, indicator_2, correlation_value
        FROM category_correlations
        WHERE category = '{category}' AND quarter = '{quarter}'
    """
  print(f"[DEBUG 쿼리 실행] category: [{category}], quarter: [{quarter}]")
  df = pd.read_sql(query, engine)
  print(f"[DEBUG 조회 결과 건수]: {len(df)}건")

  if df.empty:
    print(f'--> [{category} - {quarter}] 데이터가 없어 히트맵을 건너뜁니다.')
    return

  heatmap_data = df.pivot(
      index='indicator_1', columns='indicator_2', values='correlation_value'
  )

  fig, ax = plt.subplots(figsize=(12, 10))
  sns.heatmap(
      heatmap_data,
      annot=True,
      fmt='.2f',
      cmap='coolwarm',
      vmin=-1,
      vmax=1,
      center=0,
      square=True,
      linewidths=0.8,
      linecolor='white',
      annot_kws={'size': 9, 'weight': 'bold'},
      cbar_kws={'shrink': 0.7, 'label': '상관계수'},
  )

  # 타이틀 및 축 레이블 디자인 정돈
  plt.title(
      f'상관관계 분석 히트맵\n[{category}] ({quarter})',
      fontsize=16,
      pad=20,
      fontweight='bold',
  )
  plt.xticks(fontsize=10, rotation=45, ha='right')
  plt.yticks(fontsize=10)

  plt.tight_layout()
  plt.savefig(f'{output_dir}/heatmap_{safe_cat_name}_{quarter}.png', dpi=300)
  plt.close()

# 2. 구매 깔때기 분석 (Funnel)

def plot_purchase_funnel(category, safe_cat_name):
  query = f"SELECT exposure_cnt, click_cnt, cart_user_cnt, order_cnt FROM total_stats WHERE category = '{category}'"
  df = pd.read_sql(query, engine)
  if df.empty:
    return

  means = df.mean()
  values = [
      100.0,
      (means['click_cnt'] / means['exposure_cnt']) * 100,
      (means['cart_user_cnt'] / means['click_cnt']) * 100,
      (means['order_cnt'] / means['cart_user_cnt']) * 100,
  ]
  stages = ['노출', '클릭률', '장바구니 전환율', '주문 전환율']

  plt.figure(figsize=(10, 5))
  ax = sns.barplot(
      x=values, y=stages, hue=stages, palette='Blues_r', legend=False
  )

  # 바 내부에 퍼센트 텍스트 강조 배치
  for i, v in enumerate(values):
    ax.text(
        max(v / 2, 5),
        i,
        f'{v:.2f}%',
        va='center',
        ha='left',
        fontsize=12,
        fontweight='bold',
        color='white' if v > 20 else 'black',
    )

  plt.title(
      f'구매 단계별 전환율 퍼넬: {category}',
      fontsize=15,
      pad=20,
      fontweight='bold',
  )
  plt.xlabel('전환 비율 (%)', fontsize=11)
  plt.xlim(0, 110)
  plt.grid(axis='x', linestyle='--', alpha=0.3)
  plt.tight_layout()
  plt.savefig(f'{output_dir}/funnel_rate_{safe_cat_name}.png', dpi=300)
  plt.close()



# 3. 지표 산점도 + 회귀선

def plot_correlation_scatter(
        category, safe_cat_name, x_col='ad_cost', y_col='order_amount'
):
    print(f'[{category}] 3. 산점도 및 회귀선 시각화 중...')

    # 만약 '전체' 카테고리라면 모든 분기 데이터를 다 가져오고,
    # '전체_Q가을' 같은 특정 시즌 통합본이라면 해당 시즌의 세부 데이터(개별 카테고리들)를 가져옴
    if category == '전체':
        query = f"SELECT `{x_col}`, `{y_col}`, quarter FROM total_stats WHERE category != '전체' AND quarter != '전체'"
    elif category.startswith('전체_Q'):
        target_q = category.replace('전체_Q', '')
        query = f"SELECT `{x_col}`, `{y_col}`, quarter FROM total_stats WHERE category != '전체' AND quarter = '{target_q}'"
    else:
        query = f"SELECT `{x_col}`, `{y_col}`, quarter FROM total_stats WHERE category = '{category}'"

    try:
        df = pd.read_sql(query, engine)
        if df.empty or len(df) < 2:
            print(f'--> [{category}] 산점도 생성을 건너뜁니다: 데이터 부족 (조회 건수: {len(df)}건)')
            return

        plt.figure(figsize=(9, 7))

        # 산점도 스타일링 (통합 데이터의 경우 quarter로 색상 구분)
        sns.scatterplot(
            data=df,
            x=x_col,
            y=y_col,
            hue='quarter',
            s=120,
            palette='Set2',
            alpha=0.8,
        )

        # 회귀선 스타일링
        sns.regplot(
            data=df,
            x=x_col,
            y=y_col,
            scatter=False,  # 산점도는 위에서 scatterplot으로 처리했으므로 선만 그림
            color='#e74c3c',
            line_kws={'linewidth': 2.5, 'linestyle': '--'},
        )

        plt.title(
            f'광고비 vs 주문금액 상관성: {category}',
            fontsize=15,
            pad=20,
            fontweight='bold',
        )
        plt.xlabel('광고과금액 (ad_cost)', fontsize=11)
        plt.ylabel('주문금액 (order_amount)', fontsize=11)
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.legend(title='분기', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/scatter_{safe_cat_name}.png', dpi=300)
        plt.close()
        print(f"-> [{category}] 산점도 저장 완료")
    except Exception as e:
        print(f'--> [{category}] 산점도 생성을 건너뜁니다: {e}')


# 4. 전체 통합 4분면 전략 매트릭스

def plot_quadrant_matrix():
  query = """SELECT category, exposure_cnt, conv_rate, quarter FROM total_stats WHERE category != '전체' AND quarter != '전체'
          """
  df = pd.read_sql(query, engine)

  if df.empty:
    return

  g = sns.FacetGrid(df, col='quarter', col_wrap=2, height=4.5, aspect=1.2)
  g.map(sns.scatterplot, 'exposure_cnt', 'conv_rate', alpha=0.7, s=80, color='#3498db')

  mean_conv = df['conv_rate'].mean()
  mean_exp = df['exposure_cnt'].mean()

  # 각 서브플롯에 기준선(평균선) 추가
  g.map(plt.axhline, y=mean_conv, color='#e74c3c', linestyle='--', linewidth=1.5)
  g.map(plt.axvline, x=mean_exp, color='#2980b9', linestyle='--', linewidth=1.5)

  g.fig.subplots_adjust(top=0.9)
  g.fig.suptitle(
      '카테고리별 노출수 vs 구매전환율 4분면 분석',
      fontsize=18,
      fontweight='bold',
  )

  plt.savefig(f'{output_dir}/4분면 전략 매트릭스.png', dpi=300)
  plt.close()


# 5. 분기별 ROI 추이

def plot_roi_by_quarter():
  query = """
        SELECT quarter, SUM(ad_cost) as total_ad_cost, SUM(order_amount) as total_sales
        FROM total_stats
        WHERE quarter != '전체'
        GROUP BY quarter
        ORDER BY quarter
    """
  df = pd.read_sql(query, engine)

  if df.empty:
    return

  df['roi'] = df['total_sales'] / df['total_ad_cost']

  plt.figure(figsize=(9, 5))
  sns.lineplot(
      data=df,
      x='quarter',
      y='roi',
      marker='o',
      markersize=9,
      linewidth=3,
      color='#27ae60',
  )

  # 데이터 포인트 위에 수치 라벨 추가
  for i, row in df.iterrows():
    plt.text(
        i,
        row['roi'] + (df['roi'].max() * 0.02),
        f'{row["roi"]:.2f}배',
        horizontalalignment='center',
        size=10,
        weight='bold',
    )

  plt.title(
      '분기별 전체 광고 효율 (ROI) 추이',
      fontsize=15,
      pad=20,
      fontweight='bold',
  )
  plt.xlabel('분기', fontsize=11)
  plt.ylabel('ROI (매출 / 광고비)', fontsize=11)
  plt.grid(True, linestyle='--', alpha=0.5)
  plt.tight_layout()
  plt.savefig(f'{output_dir}/분기별 광고효율.png', dpi=300)
  plt.close()


# 6. 기준 지표별 상관관계 수평 막대 차트

def plot_target_correlation_barplot(category, safe_cat_name, target_indicator='주문금액', quarter=None):
    if quarter:
        q_filter = f"AND quarter = '{quarter}'"
        file_suffix = f"{safe_cat_name}_{quarter}"
        title_suffix = f"({category} - {quarter})"
    else:
        q_filter = ""
        file_suffix = safe_cat_name
        title_suffix = f"({category})"

    query = f"""
        SELECT indicator_2, AVG(correlation_value) as correlation_value
        FROM category_correlations
        WHERE category = '{category}' AND indicator_1 = '{target_indicator}' {q_filter}
        GROUP BY indicator_2
        HAVING indicator_2 != '{target_indicator}'
        ORDER BY correlation_value ASC
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        print(f"--> [{category}] 상관관계 막대 그래프를 위한 데이터가 없습니다.")
        return

    df = df.sort_values(by='correlation_value', ascending=True)

    plt.figure(figsize=(10, 8))

    colors = ['#AFF0EFFF' if x < 0.7 else '#F52A2AFF' for x in df['correlation_value']]
    bars = plt.barh(df['indicator_2'], df['correlation_value'], color=colors, height=0.6)

    for bar in bars:
        width = bar.get_width()
        ha_pos = 'left' if width >= 0 else 'right'
        offset = 0.01 if width >= 0 else -0.01

        plt.text(
            width + offset,
            bar.get_y() + bar.get_height() / 2,
            f'{width:.2f}',
            va='center',
            ha=ha_pos,
            fontsize=10,
            fontweight='bold'
        )

    plt.title(f'{target_indicator} 성장 핵심 지표 {title_suffix}', fontsize=16, pad=20, fontweight='bold')
    plt.xlabel('상관계수', fontsize=11)
    plt.xlim(-0.3, 1.1)
    plt.axvline(0, color='gray', linewidth=0.8, linestyle='--')
    plt.grid(axis='x', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/target_barplot_{file_suffix}.png', dpi=300)
    plt.close()
    print(f"-> [{category}] 상관관계 수평 막대 차트 저장 완료")


print('=== PPT용 시각화 자동화 프로그램 시작 (디자인 업그레이드 버전) ===')

quarter = ['여름', '가을', '겨울', '봄', '전체']

for category in target_categories:
  safe_cat_name = get_safe_filename(category)
  plot_correlation_scatter(category, safe_cat_name)
  plot_purchase_funnel(category, safe_cat_name)
  plot_target_correlation_barplot(category, safe_cat_name, target_indicator='주문금액')

  for q in quarter:
    plot_correlation_heatmap_by_quarter(category, safe_cat_name, q)

plot_quadrant_matrix()
plot_roi_by_quarter()

print('\n=== 모든 시각화 자료 고품질 저장 완료 ===')
