import { useEffect, useState } from "react";
import { DiagIllustration } from '../components/common/Icons';
import PRE_SALE_SUMMARY from "../data/preSaleBaseSummary.json";

const ANALYSIS_HISTORY_KEY = "actionfit_analysis_history";
const MIN_SAMPLE_SIZE = 5;

const SEASON_ORDER = ["봄", "여름", "가을", "겨울"];

const DIAG_CATEGORY_OPTIONS = [
  "가디건>4차없음",
  "기타",
  "기타 상의",
  "니트/스웨터",
  "니트/스웨터>라운드니트",
  "니트/스웨터>브이넥니트",
  "데님/청바지>부츠컷",
  "데님/청바지>와이드팬츠",
  "바지",
  "바지>반바지",
  "바지>슬랙스",
  "바지>와이드팬츠",
  "바지>캐주얼바지",
  "셔츠/남방/블라우스>블라우스",
  "셔츠/남방/블라우스>셔츠/남방",
  "스커트>롱스커트",
  "스커트>미니스커트",
  "스커트>미디스커트",
  "스커트>스커트",
  "신발",
  "요가/피트니스>트랙팬츠",
  "원피스>롱원피스",
  "원피스>미니원피스",
  "원피스>미디원피스",
  "재킷>가죽/스웨이드재킷",
  "재킷>재킷(그외소재)",
  "점퍼>바람막이/아노락",
  "청바지",
  "투피스/세트>팬츠세트",
  "티셔츠>긴소매티셔츠",
  "티셔츠>민소매/나시",
  "티셔츠>반소매티셔츠",
  "후드/맨투맨>맨투맨/스웨트셔츠",
  "후드/맨투맨>후드집업",
];

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function safeRate(numerator, denominator) {
  const n = toNumber(numerator);
  const d = toNumber(denominator);

  if (!d || d === 0) return null;

  return Number(((n / d) * 100).toFixed(2));
}

function median(values) {
  const nums = values
    .map(Number)
    .filter((v) => Number.isFinite(v))
    .sort((a, b) => a - b);

  if (nums.length === 0) return 0;

  const mid = Math.floor(nums.length / 2);

  if (nums.length % 2 === 0) {
    return Number(((nums[mid - 1] + nums[mid]) / 2).toFixed(2));
  }

  return nums[mid];
}

function percentileScore(value, allValues, higherIsBetter = true) {
  const values = allValues
    .map(Number)
    .filter((v) => Number.isFinite(v));

  if (values.length <= 1) return 50;

  const target = Number(value);

  if (!Number.isFinite(target)) return 50;

  const count = values.filter((v) =>
    higherIsBetter ? v <= target : v >= target
  ).length;

  return Math.round((count / values.length) * 100);
}



function normalizeCategory(value) {
  if (!value) return "미분류";

  return (
    String(value)
      .trim()
      .replace(/\s*>\s*/g, ">") || "미분류"
  );
}


function getJudgement(score, sampleCount, roasInvalidCount, metricScores = {}) {
  const confidence =
    sampleCount < MIN_SAMPLE_SIZE ||
    roasInvalidCount / Math.max(sampleCount, 1) >= 0.4
      ? "낮음"
      : "보통 이상";

  const weakMetrics = [];

  if ((metricScores.clickScore ?? 50) < 55) weakMetrics.push("클릭률");
  if ((metricScores.wishScore ?? 50) < 55) weakMetrics.push("찜 관심도");
  if ((metricScores.cartScore ?? 50) < 55) weakMetrics.push("장바구니 전환율");
  if ((metricScores.purchaseScore ?? 50) < 55) weakMetrics.push("구매전환율");
  if ((metricScores.returnStabilityScore ?? 50) < 55) weakMetrics.push("반품 안정성");
  if ((metricScores.roasScore ?? 50) < 55) weakMetrics.push("ROAS");

  const strongMetrics = [];

  if ((metricScores.clickScore ?? 0) >= 70) strongMetrics.push("클릭 반응");
  if ((metricScores.wishScore ?? 0) >= 70) strongMetrics.push("찜 관심도");
  if ((metricScores.cartScore ?? 0) >= 70) strongMetrics.push("장바구니 반응");
  if ((metricScores.purchaseScore ?? 0) >= 70) strongMetrics.push("구매전환");
  if ((metricScores.returnStabilityScore ?? 0) >= 70) strongMetrics.push("반품 안정성");
  if ((metricScores.roasScore ?? 0) >= 70) strongMetrics.push("ROAS");

  if (score >= 75) {
    return {
      type: "판매 추천",
      message:
        "선택한 시즌·카테고리 조합은 기존 데이터 기준 판매 적합도가 높은 편입니다. 유사 상품군에서 관심 반응과 구매 흐름이 비교적 안정적으로 확인되어, 판매 등록을 적극 검토할 수 있습니다.",
      actions: [
        "상품 등록을 진행하고 대표 상품으로 운영합니다.",
        "초기 광고는 소액으로 시작하되, 클릭률과 구매전환율이 유지되면 예산을 단계적으로 확대합니다.",
        "상세페이지 상단에는 시즌 키워드와 착용 상황을 명확하게 배치합니다.",
        "성과가 빠르게 확인되면 같은 카테고리의 유사 디자인이나 색상 옵션을 추가로 테스트합니다.",
      ],
      strengths:
        strongMetrics.length > 0
          ? [
              `${strongMetrics.join(", ")} 지표가 강점으로 확인됩니다.`,
              "기존 기준 데이터에서 판매 적합도가 높은 편입니다.",
              "초기 테스트 이후 확대 운영을 검토할 수 있습니다.",
            ]
          : [
              "기존 기준 데이터에서 판매 적합도가 높은 편입니다.",
              "전반적인 지표 균형이 양호합니다.",
              "초기 테스트 이후 확대 운영을 검토할 수 있습니다.",
            ],
      cautions: [
        "초기부터 과도한 광고비를 쓰기보다 반응을 확인하며 증액하는 것이 좋습니다.",
        "실제 상품의 가격, 소재, 모델컷 완성도에 따라 성과가 달라질 수 있습니다.",
        "동일 카테고리 내 경쟁 상품이 많은 경우 대표 이미지 차별화가 필요합니다.",
      ],
      confidence,
    };
  }

  if (score >= 50) {
    return {
      type: "테스트 판매",
      message:
        "선택한 시즌·카테고리 조합은 일정 수준의 판매 가능성이 있으나 일부 지표 확인이 필요합니다. 대량 등록보다는 소량 판매 또는 소액 광고 테스트로 반응을 확인하는 것이 좋습니다.",
      actions: [
        "먼저 소량 등록으로 시장 반응을 확인합니다.",
        "대표 이미지, 상품명 키워드, 가격대를 1차 테스트합니다.",
        "찜·장바구니 반응이 생기면 상세페이지 구성과 옵션을 보완합니다.",
        "구매전환율이 안정적으로 올라오면 광고 예산을 소폭 확대합니다.",
      ],
      strengths:
        strongMetrics.length > 0
          ? [
              `${strongMetrics.join(", ")} 지표에서 긍정 신호가 있습니다.`,
              "완전 보류보다는 테스트 운영을 해볼 만한 수준입니다.",
              "초기 반응을 보고 빠르게 개선 방향을 잡을 수 있습니다.",
            ]
          : [
              "완전 보류보다는 테스트 운영을 해볼 만한 수준입니다.",
              "일부 판매 가능성이 확인됩니다.",
              "초기 반응을 보고 개선 방향을 잡을 수 있습니다.",
            ],
      cautions:
        weakMetrics.length > 0
          ? [
              `${weakMetrics.join(", ")} 지표는 추가 확인이 필요합니다.`,
              "대량 등록이나 큰 광고비 집행은 아직 이릅니다.",
              "대표 이미지와 가격 반응을 먼저 확인하는 것이 좋습니다.",
            ]
          : [
              "대량 등록이나 큰 광고비 집행은 아직 이릅니다.",
              "초기 테스트 없이 바로 확대 운영하기에는 불확실성이 있습니다.",
              "대표 이미지와 가격 반응을 먼저 확인하는 것이 좋습니다.",
            ],
      confidence,
    };
  }

  return {
    type: "보류",
    message:
      "선택한 시즌·카테고리 조합은 기존 데이터 기준 판매 적합도가 낮은 편입니다. 해당 시즌에 바로 판매하기보다 상품 구성, 가격, 시즌성 키워드, 대체 카테고리를 재검토하는 것이 좋습니다.",
    actions: [
      "바로 판매하기보다 대체 시즌 또는 유사 카테고리를 먼저 검토합니다.",
      "상품 콘셉트, 가격, 대표 이미지 경쟁력을 다시 점검합니다.",
      "같은 상품을 판매한다면 다른 시즌이나 다른 카테고리 포지션으로 테스트합니다.",
      "광고 집행보다는 상품 구성 개선 후 재진단하는 것이 좋습니다.",
    ],
    strengths:
      strongMetrics.length > 0
        ? [
            `${strongMetrics.join(", ")} 지표는 일부 긍정적으로 볼 수 있습니다.`,
            "즉시 확대 전 리스크를 미리 확인할 수 있습니다.",
          ]
        : [
            "즉시 확대 전 리스크를 미리 확인할 수 있습니다.",
            "판매 전 단계에서 손실 가능성을 줄일 수 있습니다.",
          ],
    cautions:
      weakMetrics.length > 0
        ? [
            `${weakMetrics.join(", ")} 지표가 낮게 나타났습니다.`,
            "현재 조건에서는 판매 적합도가 낮은 편입니다.",
            "광고비를 먼저 쓰기보다 상품 방향 재검토가 필요합니다.",
          ]
        : [
            "현재 조건에서는 판매 적합도가 낮은 편입니다.",
            "광고비를 먼저 쓰기보다 상품 방향 재검토가 필요합니다.",
            "대체 시즌 또는 유사 카테고리 검토가 필요합니다.",
          ],
    confidence,
  };
}

function getSummaryRows() {
  return PRE_SALE_SUMMARY?.rows || [];
}

function getRepresentativeFromSummaryRows(rows) {
  const metricScores = {
    clickScore: median(rows.map((r) => r.metricScores.clickScore)),
    wishScore: median(rows.map((r) => r.metricScores.wishScore)),
    cartScore: median(rows.map((r) => r.metricScores.cartScore)),
    purchaseScore: median(rows.map((r) => r.metricScores.purchaseScore)),
    returnStabilityScore: median(
      rows.map((r) => r.metricScores.returnStabilityScore)
    ),
    roasScore: median(rows.map((r) => r.metricScores.roasScore)),
  };

  const fitScore = Math.round(
    (metricScores.clickScore +
      metricScores.wishScore +
      metricScores.cartScore +
      metricScores.purchaseScore +
      metricScores.returnStabilityScore +
      metricScores.roasScore) /
      6
  );

  return {
    metricScores,
    fitScore,
    sampleCount: rows.reduce((sum, row) => sum + toNumber(row.sampleCount), 0),
    roasInvalidCount: rows.reduce(
      (sum, row) => sum + toNumber(row.roasInvalidCount),
      0
    ),
  };
}

function calculatePreSaleDiagnosis({ season, category }) {
  const summaryRows = getSummaryRows();

  if (summaryRows.length === 0) {
    return {
      ok: false,
      noData: true,
      message:
        "분석 가능한 요약 기준 데이터가 없습니다. preSaleBaseSummary.json 파일이 정상적으로 생성되었는지 확인해주세요.",
    };
  }

  const exactRows = summaryRows.filter(
    (row) => row.season === season && row.category === category
  );

  let selectedSummaryRows = exactRows;
  let basisType = "exact";

  if (selectedSummaryRows.length === 0) {
    selectedSummaryRows = summaryRows.filter((row) => row.category === category);
    basisType = "same_category";
  }

  if (selectedSummaryRows.length === 0) {
    selectedSummaryRows = summaryRows.filter((row) => row.season === season);
    basisType = "same_season";
  }

  if (selectedSummaryRows.length === 0) {
    selectedSummaryRows = summaryRows;
    basisType = "all";
  }

  const representative = getRepresentativeFromSummaryRows(selectedSummaryRows);

  const exactSampleCount = exactRows.reduce(
    (sum, row) => sum + toNumber(row.sampleCount),
    0
  );

  const allMetricAverage =
    PRE_SALE_SUMMARY.globalMetricScores ||
    getRepresentativeFromSummaryRows(summaryRows).metricScores;

  const judgement = getJudgement(
    representative.fitScore,
    representative.sampleCount,
    representative.roasInvalidCount,
    representative.metricScores
  );

  const topCombinations = [...summaryRows]
    .sort((a, b) => b.fitScore - a.fitScore)
    .slice(0, 5);

    const getMetricCompare = (selectedScore, baseScore) => {
      const diff = selectedScore - baseScore;
    
      if (diff >= 5) {
        return {
          good: true,
          verdict: "양호",
          description: "전체 기준보다 5점 이상 높음",
        };
      }
    
      if (diff <= -5) {
        return {
          good: false,
          verdict: "낮음",
          description: "전체 기준보다 5점 이상 낮음",
        };
      }
    
      return {
        good: null,
        verdict: "보통",
        description: "전체 기준과 비슷한 수준",
      };
    };
    
    const clickCompare = getMetricCompare(
      representative.metricScores.clickScore,
      allMetricAverage.clickScore
    );
    
    const wishCompare = getMetricCompare(
      representative.metricScores.wishScore,
      allMetricAverage.wishScore
    );
    
    const cartCompare = getMetricCompare(
      representative.metricScores.cartScore,
      allMetricAverage.cartScore
    );
    
    const purchaseCompare = getMetricCompare(
      representative.metricScores.purchaseScore,
      allMetricAverage.purchaseScore
    );
    
    const returnCompare = getMetricCompare(
      representative.metricScores.returnStabilityScore,
      allMetricAverage.returnStabilityScore
    );
    
    const roasCompare = getMetricCompare(
      representative.metricScores.roasScore,
      allMetricAverage.roasScore
    );

    const selectedExactSummary = exactRows[0] || null;

const sameCategorySeasonRows = summaryRows
  .filter((row) => row.category === category)
  .sort((a, b) => {
    const seasonDiff =
      SEASON_ORDER.indexOf(a.season) - SEASON_ORDER.indexOf(b.season);

    if (seasonDiff !== 0) return seasonDiff;

    return b.fitScore - a.fitScore;
  });

const compareCombinations =
  sameCategorySeasonRows.length > 0
    ? sameCategorySeasonRows.map((combo) => ({
        label:
          combo.season === season && combo.category === category
            ? "선택한 조합"
            : "같은 카테고리 다른 시즌",
        season: combo.season,
        category: combo.category,
        sampleCount: combo.sampleCount,
        fitScore: combo.fitScore,
        metricScores: combo.metricScores,
      }))
    : [
        {
          label: "선택한 조합",
          season,
          category,
          sampleCount: representative.sampleCount,
          fitScore: representative.fitScore,
          metricScores: representative.metricScores,
        },
      ];

  return {
    ok: true,
    noData: false,
    score: representative.fitScore,
    relativeScore: percentileScore(
      representative.fitScore,
      summaryRows.map((row) => row.fitScore)
    ),
    verdict: judgement.type,
    summary: judgement.message,
    actions: judgement.actions,
    strengths: judgement.strengths,
    cautions: judgement.cautions,
    confidence: judgement.confidence,

    sampleCount: representative.sampleCount,
    originalSampleCount: representative.sampleCount,
    exactSampleCount,
    roasInvalidCount: representative.roasInvalidCount,
    basisType,

    metricScores: representative.metricScores,
    topCombinations,
    compareCombinations,

    metrics: [
      {
        label: "클릭률",
        catAvg: `${representative.metricScores.clickScore}점`,
        allAvg: `${allMetricAverage.clickScore}점`,
        good: clickCompare.good,
        verdict: clickCompare.verdict,
        description: clickCompare.description,
      },
      {
        label: "찜 관심도",
        catAvg: `${representative.metricScores.wishScore}점`,
        allAvg: `${allMetricAverage.wishScore}점`,
        good: wishCompare.good,
        verdict: wishCompare.verdict,
        description: wishCompare.description,
      },
      {
        label: "장바구니 전환율",
        catAvg: `${representative.metricScores.cartScore}점`,
        allAvg: `${allMetricAverage.cartScore}점`,
        good: cartCompare.good,
        verdict: cartCompare.verdict,
        description: cartCompare.description,
      },
      {
        label: "구매전환율",
        catAvg: `${representative.metricScores.purchaseScore}점`,
        allAvg: `${allMetricAverage.purchaseScore}점`,
        good: purchaseCompare.good,
        verdict: purchaseCompare.verdict,
        description: purchaseCompare.description,
      },
      {
        label: "반품 안정성",
        catAvg: `${representative.metricScores.returnStabilityScore}점`,
        allAvg: `${allMetricAverage.returnStabilityScore}점`,
        good: returnCompare.good,
        verdict: returnCompare.verdict,
        description: returnCompare.description,
      },
      {
        label: "ROAS",
        catAvg: `${representative.metricScores.roasScore}점`,
        allAvg: `${allMetricAverage.roasScore}점`,
        good: roasCompare.good,
        verdict: roasCompare.verdict,
        description: roasCompare.description,
      },
    ],
  };
}

function getDiagOptions() {
  return {
    seasons: SEASON_ORDER,
    categories: DIAG_CATEGORY_OPTIONS,
  };
}

export default function DiagScreen({ setScreen, }) {
  const [category, setCategory] = useState("");
  const [season, setSeason] = useState("");
  const [budget, setBudget] = useState("");
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [noData, setNoData] = useState(false);
  const [result, setResult] = useState(null);
  const [showTopCombinations, setShowTopCombinations] = useState(false);
  const [options, setOptions] = useState({
    seasons: [],
    categories: [],
  });
  useEffect(() => {
    setOptions(getDiagOptions());
  }, []);

  const canDiag = category !== "" && season !== "";

  const handleDiag = () => {
    if (!canDiag) return;
  
    const summaryRows = getSummaryRows();
  
    console.log("판매 전 요약 조합 개수:", summaryRows.length);
    console.log("전체 원본 상품 행 수:", PRE_SALE_SUMMARY.totalRows);
    console.log("선택 시즌:", season);
    console.log("선택 카테고리:", category);
    console.log(
      "정확히 일치하는 요약 데이터:",
      summaryRows.filter(
        (row) => row.season === season && row.category === category
      )
    );
  
    const diagnosis = calculatePreSaleDiagnosis({
      season,
      category,
    });
  
    console.log("판매 전 진단 결과:", diagnosis);
  
    setResult(diagnosis);
    setNoData(!diagnosis.ok);
    setShowResult(true);
    setShowTopCombinations(false);
  };

    const verdictStyle = (v) => v === "판매 추천"
        ? {
            bg: "bg-emerald-50",
            border: "border-emerald-200",
            text: "text-emerald-700",
            dot: "#059669",
        }
        : v === "테스트 판매"
            ? {
                bg: "bg-amber-50",
                border: "border-amber-200",
                text: "text-amber-700",
                dot: "#D97706",
            }
            : {
                bg: "bg-rose-50",
                border: "border-rose-200",
                text: "text-rose-700",
                dot: "#E11D48",
            };
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      {/* Heading */}
      <div>
        <h2 className="text-xl font-bold text-slate-800">
          판매 전 카테고리 진단
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          판매 예정 카테고리와 시즌을 선택하면, 기존 상품 성과
          데이터를 기준으로 판매 가능성을 진단해요.
        </p>
      </div>

      {/* Hero */}
      <div className="rounded-2xl p-7 flex items-center justify-between overflow-hidden relative" style={{
            background: "linear-gradient(135deg, #60A5FA 0%, #93C5FD 50%, #C4B5FD 100%)",
        }}>
        <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-black/5 pointer-events-none"/>
        <div className="absolute -top-12 -right-12 w-52 h-52 rounded-full bg-white/10 pointer-events-none"/>
        <div className="relative z-10">
          <p className="text-[11px] font-semibold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.85)" }}>
            Step 1
          </p>
          <h2 className="text-xl font-bold mb-2" style={{
            color: "#fff",
            textShadow: "0 1px 6px rgba(30,58,138,0.3)",
        }}>
            판매 예정 조건 입력
          </h2>
          <p className="text-sm leading-relaxed max-w-sm" style={{ color: "rgba(255,255,255,0.9)" }}>
            판매하려는 카테고리와 시즌을 선택하면
            <br />
            카테고리 시즌 적합도와 추천 운영 방향을 확인할 수
            있어요.
          </p>
        </div>
        <div className="relative z-10 hidden lg:block">
          <DiagIllustration />
        </div>
      </div>

      {/* Input + Criteria side by side */}
      <div className="grid grid-cols-2 gap-4">
        {/* Input card */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <h3 className="font-semibold text-slate-800 text-sm mb-4">
            판매 조건 입력
          </h3>

          {/* Category */}
          <div className="mb-4 relative">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              판매 예정 카테고리{" "}
              <span className="text-rose-500">*</span>
            </label>

            <button
              type="button"
              onClick={() => setCategoryOpen((prev) => !prev)}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-left text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition flex items-center justify-between"
            >
              <span className={category ? "text-slate-700" : "text-slate-400"}>
                {category || "카테고리를 선택해주세요"}
              </span>

              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={`text-slate-400 transition-transform ${
                  categoryOpen ? "rotate-180" : ""
                }`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {categoryOpen && (
              <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-50 max-h-72 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg">
                <button
                  type="button"
                  onClick={() => {
                    setCategory("");
                    setCategoryOpen(false);
                    setShowResult(false);
                  }}
                  className="w-full px-3 py-2.5 text-left text-sm text-slate-400 hover:bg-slate-50 border-b border-slate-100"
                >
                  카테고리를 선택해주세요
                </button>

                {options.categories.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => {
                      setCategory(c);
                      setCategoryOpen(false);
                      setShowResult(false);
                    }}
                    className={`w-full px-3 py-2.5 text-left text-sm transition ${
                      category === c
                        ? "bg-blue-50 text-blue-700 font-semibold"
                        : "text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Season */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-2">
              판매 예정 시즌{" "}
              <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-4 gap-2">
            {options.seasons.map((s) => (<button key={s} onClick={() => setSeason(s)} className={`py-2.5 rounded-lg text-sm font-semibold border transition-all ${season === s ? "border-blue-400 text-blue-700" : "border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600"}`} style={season === s
                ? { backgroundColor: "#EFF6FF" }
                : { backgroundColor: "#F8FAFC" }}>
                  {s === "봄"
                ? "🌸"
                : s === "여름"
                    ? "☀️"
                    : s === "가을"
                        ? "🍂"
                        : "❄️"}{" "}
                  {s}
                </button>))}
            </div>
          </div>

          {/* Note */}
          <div className="p-3 rounded-lg border border-blue-100 mb-4" style={{ backgroundColor: "#EFF6FF" }}>
            <p className="text-[11px] leading-relaxed" style={{ color: "#1D4ED8" }}>
              카테고리와 시즌은 적합도 점수 계산에 사용되며,
              예상 광고 예산은 추천 액션을 구체화하는
              참고값으로만 활용됩니다.
            </p>
          </div>

          <button onClick={handleDiag} disabled={!canDiag} className="w-full flex items-center justify-center gap-2 py-3 text-sm font-bold text-white rounded-xl transition-all" style={canDiag
            ? {
                backgroundColor: "#2563EB",
                boxShadow: "0 4px 14px rgba(37,99,235,0.25)",
            }
            : {
                backgroundColor: "#E2E8F0",
                color: "#94A3B8",
                cursor: "not-allowed",
            }} onMouseEnter={(e) => {
            if (canDiag)
                e.currentTarget.style.backgroundColor =
                    "#1D4ED8";
        }} onMouseLeave={(e) => {
            if (canDiag)
                e.currentTarget.style.backgroundColor =
                    "#2563EB";
        }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            진단 시작하기
          </button>
        </div>

        {/* Criteria card */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <h3 className="font-semibold text-slate-800 text-sm mb-1">
            진단 기준
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            판매 전 진단은 같은 시즌·같은 카테고리의 기존 성과
            데이터를 기준으로 계산됩니다.
          </p>

          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            진단 지표
          </p>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {[
            "클릭률",
            "구매 전환율",
            "장바구니 전환율",
            "찜 관심도",
            "반품 안정성",
            "ROAS",
        ].map((m) => (<span key={m} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium">
                {m}
              </span>))}
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 mb-4">
            <p className="text-[11px] font-semibold text-slate-500 mb-1">
              계산식
            </p>
            <p className="text-xs text-slate-600 leading-relaxed">
            카테고리 시즌 적합도 점수 =<br />
            <span className="text-slate-500">
              (클릭률 점수 + 찜 관심도 점수 + 장바구니 전환율 점수 + 구매전환율 점수 + 반품 안정성 점수 + ROAS 점수) / 6
            </span>
            </p>
          </div>

          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            점수 해석
          </p>
          <div className="space-y-1.5 mb-4">
            {[
            {
                range: "75점 이상",
                label: "판매 추천",
                bg: "bg-emerald-50",
                text: "text-emerald-700",
                border: "border-emerald-200",
            },
            {
                range: "50~74점",
                label: "테스트 판매",
                bg: "bg-amber-50",
                text: "text-amber-700",
                border: "border-amber-200",
            },
            {
                range: "50점 미만",
                label: "보류",
                bg: "bg-rose-50",
                text: "text-rose-700",
                border: "border-rose-200",
            },
        ].map((s) => (<div key={s.label} className={`flex items-center justify-between px-3 py-2 rounded-lg border ${s.bg} ${s.border}`}>
                <span className="text-xs text-slate-500">
                  {s.range}
                </span>
                <span className={`text-xs font-bold ${s.text}`}>
                  {s.label}
                </span>
              </div>))}
          </div>

          <div className="p-3 rounded-lg border" style={{
            backgroundColor: "#FFFBEB",
            borderColor: "#FDE68A",
        }}>
            <p className="text-[11px] leading-relaxed" style={{ color: "#B45309" }}>
              ⚠️ 이 진단은 기존 상품 성과 데이터를 기반으로 한
              참고용 판단이며, 실제 판매 성과를 보장하지
              않습니다.
            </p>
          </div>
        </div>
      </div>

      {/* Result area */}
      {showResult && (<>
          {noData ? (
            /* Empty / insufficient data state */
            <div className="bg-white rounded-xl border border-slate-100 p-10 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-2xl bg-amber-50 flex items-center justify-center mb-4 text-2xl">
                ⚠️
              </div>
              <p className="text-base font-semibold text-slate-700 mb-2">
                진단 기준 데이터가 부족합니다.
              </p>
              <p className="text-sm text-slate-400 leading-relaxed mb-6 max-w-md">
                {result?.message ||
                  "선택한 카테고리와 시즌에 대한 기존 분석 데이터가 충분하지 않아 정확한 진단이 어렵습니다."}
              </p>
              <div className="flex flex-wrap gap-2 justify-center mb-6">
                {[
                    "유사 카테고리 기준으로 참고 진단하기",
                    "다른 시즌 선택하기",
                    "상품 성과 데이터를 추가 업로드하기",
                ].map((t) => (<span key={t} className="text-xs bg-slate-100 text-slate-600 border border-slate-200 px-3 py-1.5 rounded-lg">
                    {t}
                  </span>))}
              </div>
              <button onClick={() => setScreen("upload")} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white rounded-xl transition" style={{
                    backgroundColor: "#2563EB",
                    boxShadow: "0 4px 14px rgba(37,99,235,0.25)",
                }} onMouseEnter={(e) => (e.currentTarget.style.backgroundColor =
                    "#1D4ED8")} onMouseLeave={(e) => (e.currentTarget.style.backgroundColor =
                    "#2563EB")}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                </svg>
                상품 성과 파일 업로드하기
              </button>
            </div>) : (<>
              {/* Result summary cards */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800 text-sm">
                    진단 결과
                  </h3>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <span>{category}</span>
                    <span>·</span>
                    <span>{season} 시즌</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  {/* Score card */}
                  <div className={`rounded-xl border p-5 ${verdictStyle(result.verdict).bg} ${verdictStyle(result.verdict).border}`}>
                    <p className="text-xs font-semibold text-slate-500 mb-3">
                      카테고리 시즌 적합도
                    </p>
                    <div className="flex items-end gap-2 mb-2">
                      <span className="text-4xl font-bold" style={{
                    color: verdictStyle(result.verdict)
                        .dot,
                }}>
                        {result.score}
                      </span>
                      <span className="text-sm text-slate-400 mb-1">
                        / 100점
                      </span>
                    </div>
                    <span className={`text-sm font-bold px-3 py-1 rounded-lg inline-block ${verdictStyle(result.verdict).bg} ${verdictStyle(result.verdict).text} border ${verdictStyle(result.verdict).border}`}>
                      {result.verdict}
                    </span>
                    <div className="mt-3 text-[11px] text-slate-500 leading-relaxed">
                      <p>
                        분석 표본:{" "}
                        <strong className="text-slate-700">
                          {result.sampleCount?.toLocaleString?.() || result.sampleCount}개
                        </strong>
                      </p>
                      <p>
                        계산 방식:{" "}
                        <strong className="text-slate-700">
                          전체 원본 데이터 사전 집계
                        </strong>
                      </p>
                      {result.exactSampleCount !== undefined && (
                        <p>
                          정확히 일치한 표본:{" "}
                          <strong className="text-slate-700">
                            {result.exactSampleCount.toLocaleString()}개
                          </strong>
                        </p>
                      )}
                    </div>
                  </div>
                  {/* Strengths */}
                  <div className="bg-white rounded-xl border border-emerald-100 p-5">
                    <p className="text-xs font-semibold text-slate-500 mb-3">
                      성과 강점
                    </p>
                    <div className="space-y-2">
                      {result.strengths.map((s) => (<div key={s} className="flex items-center gap-2">
                          <div className="w-4 h-4 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="3">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                          </div>
                          <span className="text-xs text-slate-700">
                            {s}
                          </span>
                        </div>))}
                    </div>
                  </div>
                  {/* Cautions */}
                  <div className="bg-white rounded-xl border border-amber-100 p-5">
                    <p className="text-xs font-semibold text-slate-500 mb-3">
                      주의 포인트
                    </p>
                    <div className="space-y-2">
                      {result.cautions.map((c) => (<div key={c} className="flex items-center gap-2">
                          <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0" style={{
                        backgroundColor: "#FEF3C7",
                    }}>
                            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="3" strokeLinecap="round">
                              <path d="M12 9v4M12 17h.01"/>
                            </svg>
                          </div>
                          <span className="text-xs text-slate-700">
                            {c}
                          </span>
                        </div>))}
                    </div>
                  </div>
                </div>
                {/* Verdict explanation */}
                <div
                  className={`mt-3 p-4 rounded-xl border ${
                    result.verdict === "판매 추천"
                      ? "border-emerald-200 bg-emerald-50"
                      : result.verdict === "테스트 판매"
                        ? "border-amber-200 bg-amber-50"
                        : "border-rose-200 bg-rose-50"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center text-lg flex-shrink-0 ${
                        result.verdict === "판매 추천"
                          ? "bg-emerald-100"
                          : result.verdict === "테스트 판매"
                            ? "bg-amber-100"
                            : "bg-rose-100"
                      }`}
                    >
                      {result.verdict === "판매 추천"
                        ? "✅"
                        : result.verdict === "테스트 판매"
                          ? "🧪"
                          : "⚠️"}
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-xs font-bold text-slate-500">
                          진단 유형 설명
                        </p>
                        <span
                          className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                            result.verdict === "판매 추천"
                              ? "bg-emerald-100 text-emerald-700"
                              : result.verdict === "테스트 판매"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-rose-100 text-rose-700"
                          }`}
                        >
                          {result.verdict}
                        </span>
                      </div>

                      <p className="text-xs text-slate-700 leading-relaxed">
                        {result.summary}
                      </p>

                      <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                        이 설명은 위의 카테고리 시즌 적합도 점수와 진단 유형을 해석한 내용입니다.
                      </p>
                    </div>
                  </div>
                </div>
                {result.basisType !== "exact" && (
                  <div className="mt-3 p-3 rounded-lg border border-amber-200 bg-amber-50">
                    <p className="text-[11px] leading-relaxed text-amber-700">
                      선택한 시즌·카테고리와 완전히 일치하는 표본이 부족해{" "}
                      {result.basisType === "same_category"
                        ? "같은 카테고리의 전체 시즌 데이터"
                        : result.basisType === "same_season"
                          ? "같은 시즌의 전체 카테고리 데이터"
                          : "전체 기준 데이터"}를 함께 참고해 진단했습니다.
                    </p>
                  </div>
                )}
              </div>

              {/* Metrics table */}
              <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100">
                  <h3 className="font-semibold text-slate-800 text-sm">
                    세부 지표 비교
                  </h3>
                </div>
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50">
                    {[
                      "지표",
                      "선택 조합 점수",
                      "전체 조합 기준 점수",
                      "판단",
                    ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3">
                          {h}
                        </th>))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {result.metrics.map((m) => (<tr key={m.label} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-5 py-3 text-xs font-medium text-slate-700">
                          {m.label}
                        </td>
                        <td className="px-5 py-3 text-sm font-bold text-slate-800">
                          {m.catAvg}
                        </td>
                        <td className="px-5 py-3 text-xs text-slate-400">
                          {m.allAvg}
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-1.5">
                          <div
                            className={`w-3.5 h-3.5 rounded-full flex items-center justify-center flex-shrink-0 ${
                              m.good === true
                                ? "bg-emerald-100"
                                : m.good === false
                                  ? "bg-rose-100"
                                  : "bg-amber-100"
                            }`}
                          >
                            {m.good === true ? (
                              <svg
                                width="8"
                                height="8"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="#059669"
                                strokeWidth="3"
                              >
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : m.good === false ? (
                              <svg
                                width="8"
                                height="8"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="#e11d48"
                                strokeWidth="3"
                                strokeLinecap="round"
                              >
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                              </svg>
                            ) : (
                              <span className="text-[9px] font-bold text-amber-600">!</span>
                            )}
                          </div>

                          <div>
                            <span
                              className={`text-xs font-semibold ${
                                m.good === true
                                  ? "text-emerald-700"
                                  : m.good === false
                                    ? "text-rose-600"
                                    : "text-amber-600"
                              }`}
                            >
                              {m.verdict}
                            </span>
                            {m.description && (
                              <p className="text-[10px] text-slate-400 mt-0.5">
                                {m.description}
                              </p>
                            )}
                          </div>
                          </div>
                        </td>
                      </tr>))}
                  </tbody>
                </table>
              </div>

              {/* Selected combination comparison */}
              <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-800 text-sm">
                  같은 카테고리 시즌별 비교
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  사용자가 선택한 카테고리를 기준으로 시즌별 적합도와 세부 지표를 비교합니다.
                </p>
                </div>

                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50">
                      {[
                        "구분",
                        "시즌",
                        "카테고리",
                        "표본 수",
                        "적합도",
                        "클릭",
                        "찜",
                        "장바구니",
                        "구매",
                        "반품",
                        "ROAS",
                      ].map((h) => (
                        <th
                          key={h}
                          className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-4 py-3"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-50">
                    {(result.compareCombinations || []).map((combo, index) => {
                      const isSelected = combo.label === "선택한 조합";

                      return (
                        <tr
                          key={`${combo.label}-${combo.season}-${combo.category}-${index}`}
                          className={isSelected ? "bg-blue-50/60" : "hover:bg-slate-50"}
                        >
                          <td className="px-4 py-3 text-xs font-bold">
                            <span
                              className={`px-2 py-1 rounded-lg ${
                                isSelected
                                  ? "bg-blue-100 text-blue-700"
                                  : "bg-slate-100 text-slate-500"
                              }`}
                            >
                              {combo.label}
                            </span>
                          </td>

                          <td className="px-4 py-3 text-xs font-semibold text-slate-700">
                            {combo.season}
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.category}
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-500">
                            {combo.sampleCount?.toLocaleString?.() || combo.sampleCount}개
                          </td>

                          <td className="px-4 py-3 text-xs font-bold text-blue-700">
                            {combo.fitScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.clickScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.wishScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.cartScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.purchaseScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.returnStabilityScore}점
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {combo.metricScores?.roasScore}점
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Recommended direction */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-800 text-sm mb-4">
                  추천 운영 방향
                </h3>
                <div className="space-y-3">
                {(result.actions || []).map((action, i) => (<div key={i} className="flex items-start gap-3">
                      <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[11px]" style={{
                        backgroundColor: "#EFF6FF",
                        color: "#2563EB",
                    }}>
                        {i + 1}
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {action}
                      </p>
                    </div>))}
                  {budget && (<div className="mt-2 p-3 rounded-lg border border-blue-100" style={{ backgroundColor: "#EFF6FF" }}>
                      <p className="text-[11px] leading-relaxed" style={{ color: "#1D4ED8" }}>
                        💡 예상 일 광고 예산이{" "}
                        <strong>{budget}</strong>인 경우,
                        초기에는 전체 예산을 한 번에 쓰기보다
                        3~5일간 소액 테스트를 진행하고 성과가
                        안정적일 때 확대하는 것을 추천합니다.
                      </p>
                    </div>)}
                </div>
              </div>

              {/* Optional top combinations */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-slate-800 text-sm">
                      다른 시즌·카테고리 상위 조합
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      선택한 조합 진단과는 별개로, 전체 기준 데이터에서 적합도가 높은 조합을 참고용으로 확인할 수 있습니다.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowTopCombinations((prev) => !prev)}
                    className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition flex items-center gap-2"
                  >
                    {showTopCombinations ? "접기" : "참고 조합 보기"}

                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      className={`transition-transform ${
                        showTopCombinations ? "rotate-180" : ""
                      }`}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                </div>

                {!showTopCombinations && (
                  <div className="mt-4 p-3 rounded-lg border border-slate-100 bg-slate-50">
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      이 영역은 사용자가 선택한 조합을 진단하는 핵심 결과가 아니라, 다른 조합이 궁금할 때만 확인하는 참고 정보입니다.
                    </p>
                  </div>
                )}

                {showTopCombinations && (
                  <div className="mt-4 overflow-hidden rounded-xl border border-slate-100">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-slate-50">
                          {["순위", "시즌", "카테고리", "표본 수", "적합도"].map((h) => (
                            <th
                              key={h}
                              className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3"
                            >
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-50">
                        {(result.topCombinations || []).map((combo, index) => (
                          <tr key={`${combo.season}-${combo.category}`}>
                            <td className="px-5 py-3 text-xs text-slate-500">
                              {index + 1}
                            </td>

                            <td className="px-5 py-3 text-xs font-semibold text-slate-700">
                              {combo.season}
                            </td>

                            <td className="px-5 py-3 text-xs text-slate-600">
                              {combo.category}
                            </td>

                            <td className="px-5 py-3 text-xs text-slate-500">
                              {combo.sampleCount?.toLocaleString?.() || combo.sampleCount}개
                            </td>

                            <td className="px-5 py-3 text-xs font-bold text-blue-700">
                              {combo.fitScore}점
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    <div className="px-5 py-3 border-t border-slate-100 bg-amber-50">
                      <p className="text-[11px] text-amber-700 leading-relaxed">
                        이 추천 조합은 전체 데이터에서 적합도가 높은 조합을 보여주는 참고 정보이며, 사용자가 선택한 상품 방향을 대체하라는 의미는 아닙니다.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {result.confidence === "낮음" && (
                <div className="mt-3 p-3 rounded-lg border border-amber-200 bg-amber-50">
                  <p className="text-[11px] leading-relaxed text-amber-700">
                    선택한 시즌·카테고리 조합의 표본 수가 적거나 ROAS 계산이 제한된 상품이 많아 낮은 확신도로 표시됩니다.
                  </p>
                </div>
              )}

              {/* Data basis */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-800 text-sm mb-3">
                  분석 기준
                </h3>
                <div className="space-y-1.5 mb-3">
                {[
                  "서비스에 저장된 전체 기본 상품 성과 데이터를 시즌·카테고리 조합별로 사전 집계해 활용",
                  `선택 조건: ${season} 시즌 · ${category}`,
                  "선택한 시즌·카테고리 조합의 집계 점수를 산출하고, 전체 기준 상위 조합과 함께 비교",
                  "클릭률, 찜 관심도, 장바구니 전환율, 구매전환율, 반품 안정성, ROAS를 종합해 점수화",
                  "LLM 없이 코드 기준 템플릿으로 판매 추천 / 테스트 판매 / 보류를 자동 분류",
                ].map((t) => (<div key={t} className="flex items-center gap-2 text-xs text-slate-500">
                      <svg className="flex-shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      {t}
                    </div>))}
                </div>
                <div className="p-3 rounded-lg border" style={{
                    backgroundColor: "#FFFBEB",
                    borderColor: "#FDE68A",
                }}>
                  <p className="text-[11px] leading-relaxed" style={{ color: "#B45309" }}>
                    이 기능은 판매 가능성을 참고하기 위한 사전
                    진단이며, 실제 매출이나 광고 성과를 보장하지
                    않습니다.
                  </p>
                </div>
              </div>
            </>)}
        </>)}

      <div className="flex items-center pb-2">
        <button onClick={() => setScreen("main")} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          메인으로 돌아가기
        </button>
      </div>
    </div>);
}