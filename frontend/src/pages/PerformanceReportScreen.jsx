import React, { useMemo, useRef, useState } from "react";
import * as XLSX from "xlsx";
import { getClientUuid } from "../utils/helpers";

const METRIC_KEYS = [
  {
    key: "clickRate",
    label: "클릭률",
    goodDirection: "up",
    unit: "%",
  },
  {
    key: "wishRate",
    label: "찜 전환율",
    goodDirection: "up",
    unit: "%",
  },
  {
    key: "cartRate",
    label: "장바구니 전환율",
    goodDirection: "up",
    unit: "%",
  },
  {
    key: "purchaseRate",
    label: "구매전환율",
    goodDirection: "up",
    unit: "%",
  },
  {
    key: "roas",
    label: "ROAS",
    goodDirection: "up",
    unit: "%",
  },
  {
    key: "returnRate",
    label: "반품률",
    goodDirection: "down",
    unit: "%",
  },
];

function normalizeColumnName(value) {
  return String(value || "")
    .trim()
    .replace(/\u00A0/g, " ")
    .replace(/\s+/g, "")
    .replace(/^\*/, "")
    .replace(/[()\[\]{}]/g, "")
    .replace(/[·ㆍ]/g, "")
    .replace(/_/g, "")
    .toLowerCase();
}

const COLUMN_ALIASES = {
  productId: ["상품ID", "*상품ID", "상품 ID", "상품id", "상품번호", "product_id"],
  productName: ["상품명", "*상품명", "상품 이름", "상품명/옵션명", "옵션명"],
  category: ["카테고리", "카테고리(3>4차)", "카테고리명", "상품 카테고리"],
  exposure: ["노출수", "노출 수", "노출"],
  click: ["클릭수", "클릭 수", "클릭"],
  visit: ["상품 상세 방문수", "상품상세방문수", "상세 방문수", "상품 상세조회수"],
  wish: ["찜 유저수", "상품 찜 유저수", "찜유저수", "찜수"],
  cart: ["장바구니 유저수", "장바구니유저수", "장바구니 수", "장바구니수"],
  orderCount: ["상품주문수", "상품 주문수", "주문수", "주문 건수", "주문건수"],
  returnCount: ["반품건수", "반품 건수", "반품수"],
  adSpend: ["광고과금액", "광고 과금액", "광고비", "광고비용", "광고 비용"],
  orderAmount: ["주문금액", "주문 금액", "매출", "매출액", "결제금액"],
};

function findActualColumn(headers, aliasList) {
  const normalizedAliases = aliasList.map(normalizeColumnName);
  return headers.find((header) =>
    normalizedAliases.includes(normalizeColumnName(header))
  );
}

function findHeaderRowIndex(sheetRows) {
  const directIndex = sheetRows.findIndex((row) => {
    const normalizedCells = row.map((cell) => normalizeColumnName(cell));

    const hasProductId = normalizedCells.some((cell) =>
      ["상품id", "상품번호", "productid"].includes(cell)
    );

    const hasProductName = normalizedCells.some((cell) =>
      ["상품명", "상품이름", "상품명/옵션명", "옵션명", "productname"].includes(cell)
    );

    return hasProductId && hasProductName;
  });

  if (directIndex !== -1) return directIndex;

  return 0;
}

function cleanNumber(value) {
  const raw = String(value ?? "").trim();

  if (!raw || raw === "-" || raw.toUpperCase() === "N/A" || raw === "없음") {
    return 0;
  }

  const cleaned = raw
    .replace(/,/g, "")
    .replace(/₩/g, "")
    .replace(/원/g, "")
    .replace(/건/g, "")
    .replace(/개/g, "")
    .replace(/%/g, "")
    .replace(/\s/g, "");

  const num = Number(cleaned);
  return Number.isFinite(num) ? num : 0;
}

function safeRate(numerator, denominator) {
  if (!denominator || denominator === 0) return 0;
  return Number(((numerator / denominator) * 100).toFixed(2));
}

function getMetricValue(row, key) {
  if (key === "clickRate") return Number(row.clickRate || 0);
  if (key === "wishRate") return Number(row.wishRate || 0);
  if (key === "cartRate") return Number(row.cartRate || 0);
  if (key === "purchaseRate") return Number(row.purchaseRate || 0);
  if (key === "roas") return Number(row.roas || 0);
  if (key === "returnRate") return Number(row.returnRate || 0);

  return 0;
}

function getChangeLabel(diff, metric) {
  if (Math.abs(diff) < 0.01) return "유지";

  const isGood =
    metric.goodDirection === "up" ? diff > 0 : diff < 0;

  return isGood ? "성과 개선" : "개선 필요";
}

function getChangeBadge(diff, metric) {
  const label = getChangeLabel(diff, metric);

  if (label === "성과 개선") {
    return "bg-blue-50 text-blue-700 border-blue-200";
  }

  if (label === "개선 필요") {
    return "bg-amber-50 text-amber-700 border-amber-200";
  }

  return "bg-slate-50 text-slate-500 border-slate-200";
}

function getMainJudgement(row) {
  const purchaseDiff = row.metricChanges.purchaseRate?.diff || 0;
  const roasDiff = row.metricChanges.roas?.diff || 0;
  const returnDiff = row.metricChanges.returnRate?.diff || 0;

  if (purchaseDiff > 0 && roasDiff > 0 && returnDiff <= 0) {
    return "확대 유지";
  }

  if (purchaseDiff > 0 || roasDiff > 0) {
    return "성과 개선";
  }

  if (returnDiff > 0 || purchaseDiff < 0) {
    return "추가 개선";
  }

  return "개선 확인";
}

function getNextAction(row) {
  const judgement = getMainJudgement(row);

  if (judgement === "확대 유지") {
    return "성과가 개선되어 광고 확대 또는 예산 유지를 검토하세요.";
  }

  if (judgement === "성과 개선") {
    return "개선 효과가 확인되었습니다. 동일 방향으로 추가 테스트를 권장합니다.";
  }

  if (judgement === "추가 개선") {
    return "전환 또는 반품 지표가 약합니다. 상세페이지, 가격, 혜택을 다시 점검하세요.";
  }

  return "변화 폭이 크지 않습니다. 동일 조건으로 한 번 더 관찰하세요.";
}

async function parseComparisonFile(file) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const firstSheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[firstSheetName];

  const sheetRows = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    defval: "",
  });

  const headerRowIndex = findHeaderRowIndex(sheetRows);
  const headers = (sheetRows[headerRowIndex] || []).map((h, idx) => {
    const header = String(h || "").trim();
    return header || `__EMPTY_${idx}`;
  });

  const columnMap = Object.fromEntries(
    Object.entries(COLUMN_ALIASES).map(([key, aliases]) => [
      key,
      findActualColumn(headers, aliases),
    ])
  );

  const requiredKeys = [
    "productId",
    "productName",
    "exposure",
    "click",
    "visit",
    "cart",
    "orderCount",
    "returnCount",
    "adSpend",
    "orderAmount",
  ];

  const missingKeys = requiredKeys.filter((key) => !columnMap[key]);

  if (missingKeys.length > 0) {
    throw new Error(
      `비교 파일에 필수 컬럼이 부족합니다: ${missingKeys.join(", ")}`
    );
  }

  const dataRows = sheetRows.slice(headerRowIndex + 1);

  return dataRows
    .filter((row) => row.some((cell) => String(cell || "").trim() !== ""))
    .map((row) => {
      const obj = {};

      headers.forEach((header, index) => {
        obj[header] = row[index] ?? "";
      });

      const exposure = cleanNumber(obj[columnMap.exposure]);
      const click = cleanNumber(obj[columnMap.click]);
      const visit = cleanNumber(obj[columnMap.visit]);
      const cart = cleanNumber(obj[columnMap.cart]);
      const orderCount = cleanNumber(obj[columnMap.orderCount]);
      const returnCount = cleanNumber(obj[columnMap.returnCount]);
      const adSpend = cleanNumber(obj[columnMap.adSpend]);
      const orderAmount = cleanNumber(obj[columnMap.orderAmount]);
      const wish = columnMap.wish ? cleanNumber(obj[columnMap.wish]) : 0;

      return {
        productId: String(obj[columnMap.productId] || "").trim(),
        productName: String(obj[columnMap.productName] || "").trim(),
        category: columnMap.category ? String(obj[columnMap.category] || "").trim() : "",
        exposure,
        click,
        visit,
        cart,
        wish,
        orderCount,
        returnCount,
        adSpend,
        orderAmount,
        clickRate: safeRate(click, exposure),
        wishRate: safeRate(wish, visit),
        cartRate: safeRate(cart, visit),
        purchaseRate: safeRate(orderCount, visit),
        returnRate: safeRate(returnCount, orderCount),
        roas: safeRate(orderAmount, adSpend),
      };
    })
    .filter((row) => row.productId || row.productName);
}

function normalizeBaseRow(row) {
  return {
    productId: String(row.product_id || row.productId || "").trim(),
    productName: row.product_name || row.productName || "-",
    category: row.category || "-",
    clickRate: Number(row.calc_click_rate || row.calculatedMetrics?.click_rate || 0),
    wishRate: Number(row.calc_wish_conv || row.calculatedMetrics?.wish_conv_rate || 0),
    cartRate: Number(row.calc_cart_conv || row.calculatedMetrics?.cart_conv_rate || 0),
    purchaseRate: Number(row.calc_conv_rate || row.calculatedMetrics?.conv_rate || 0),
    returnRate:
      row.return_count && row.order_count
        ? safeRate(Number(row.return_count), Number(row.order_count))
        : Number(row.calc_return_rate || 0),
    roas: Number(row.calc_roas || row.calculatedMetrics?.roas || 0),
    productType: row.product_type || row.productType || "일반",
  };
}

function buildComparisonRows(baseRows, nextRows) {
  const baseMap = new Map();

  baseRows.forEach((row) => {
    const base = normalizeBaseRow(row);
    const key = base.productId || base.productName;
    if (key) baseMap.set(key, base);
  });

  const matched = [];

  nextRows.forEach((next) => {
    const key = next.productId || next.productName;
    const base = baseMap.get(key);

    if (!base) return;

    const metricChanges = {};

    METRIC_KEYS.forEach((metric) => {
      const before = getMetricValue(base, metric.key);
      const after = getMetricValue(next, metric.key);
      const diff = Number((after - before).toFixed(2));

      metricChanges[metric.key] = {
        before,
        after,
        diff,
        label: getChangeLabel(diff, metric),
      };
    });

    matched.push({
      productId: next.productId,
      productName: next.productName || base.productName,
      category: next.category || base.category,
      beforeType: base.productType,
      metricChanges,
      judgement: "",
      nextAction: "",
    });
  });

  return matched.map((row) => ({
    ...row,
    judgement: getMainJudgement(row),
    nextAction: getNextAction(row),
  }));
}

export default function PerformanceReportScreen({
  setScreen,
  selectedFile,
  setSelectedFile,
}) {
  const [baseRows, setBaseRows] = useState([]);
  const [baseLoading, setBaseLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState(null);
  const [comparisonRows, setComparisonRows] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isComparing, setIsComparing] = useState(false);
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [newAnalysisFileName, setNewAnalysisFileName] = useState("");
  const [isSavingAnalysis, setIsSavingAnalysis] = useState(false);
  const fileInputRef = useRef(null);
  const [hasComparedCurrentFile, setHasComparedCurrentFile] = useState(false);

  React.useEffect(() => {
    const clientUuid = getClientUuid();

    if (!clientUuid || !selectedFile) {
      setBaseRows([]);
      setBaseLoading(false);
      return;
    }

    fetch(
      `http://localhost:8000/score/results?client_uuid=${clientUuid}&file_name=${encodeURIComponent(
        selectedFile
      )}`
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error("기준 분석 결과를 불러오지 못했습니다.");
        }
        return res.json();
      })
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setBaseRows(list);
        setBaseLoading(false);
      })
      .catch((error) => {
        console.error(error);
        setErrorMessage(error.message);
        setBaseLoading(false);
      });
  }, [selectedFile]);

  const summary = useMemo(() => {
    const total = comparisonRows.length;

    const improved = comparisonRows.filter(
      (row) => row.judgement === "성과 개선" || row.judgement === "확대 유지"
    ).length;

    const needImprove = comparisonRows.filter(
      (row) => row.judgement === "추가 개선"
    ).length;

    const maintain = total - improved - needImprove;

    const matchRate =
      baseRows.length > 0 ? Math.round((total / baseRows.length) * 100) : 0;

    return {
      total,
      improved,
      needImprove,
      maintain,
      matchRate,
    };
  }, [comparisonRows, baseRows]);

  const metricAverageChanges = useMemo(() => {
    return METRIC_KEYS.map((metric) => {
      if (comparisonRows.length === 0) {
        return {
          ...metric,
          before: 0,
          after: 0,
          diff: 0,
        };
      }

      const before =
        comparisonRows.reduce(
          (sum, row) => sum + row.metricChanges[metric.key].before,
          0
        ) / comparisonRows.length;

      const after =
        comparisonRows.reduce(
          (sum, row) => sum + row.metricChanges[metric.key].after,
          0
        ) / comparisonRows.length;

      return {
        ...metric,
        before: Number(before.toFixed(2)),
        after: Number(after.toFixed(2)),
        diff: Number((after - before).toFixed(2)),
      };
    });
  }, [comparisonRows]);

  function getSeasonFromMonth(monthValue = "") {
    const month = Number(String(monthValue).split("-")[1]);
  
    if ([3, 4, 5].includes(month)) return "봄";
    if ([6, 7, 8].includes(month)) return "여름";
    if ([9, 10, 11].includes(month)) return "가을";
    if ([12, 1, 2].includes(month)) return "겨울";
  
    return "";
  }
  
  function makeBackendRows(nextRows) {
    const season = getSeasonFromMonth(periodStart);
  
    return nextRows.map((row) => {
      const unitPrice =
        row.orderCount > 0 ? Math.round(row.orderAmount / row.orderCount) : 0;
  
      return {
        상품ID: row.productId,
        상품명: row.productName || `상품_${row.productId}`,
        카테고리: row.category || "기타",
        "분석 시즌": season,
        노출수: row.exposure,
        클릭수: row.click,
        "상품 상세 방문수": row.visit,
       "찜 유저수": row.wish || 0,
        "장바구니 유저수": row.cart,
        상품주문수: row.orderCount,
        반품건수: row.returnCount,
        광고과금액: row.adSpend,
        주문금액: row.orderAmount,
        상품단가: unitPrice,
        "분석 시작월": periodStart || "",
        "분석 종료월": periodEnd || "",
      };
    });
  }
  
  function makeSafeFileName(fileName = "성과파일.xlsx") {
    const baseName = fileName.replace(/\.[^/.]+$/, "");
    const now = new Date();
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(
      2,
      "0"
    )}${String(now.getDate()).padStart(2, "0")}_${String(
      now.getHours()
    ).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}`;
  
    return `${baseName}_성과비교분석_${timestamp}.xlsx`;
  }

  async function checkAlreadyAnalyzedFile(fileName) {
    const clientUuid = getClientUuid();
  
    if (!clientUuid || !fileName) return false;
  
    const response = await fetch(
      `http://localhost:8000/score/results?client_uuid=${clientUuid}&file_name=${encodeURIComponent(
        fileName
      )}`
    );
  
    if (!response.ok) {
      return false;
    }
  
    const data = await response.json();
    const list = Array.isArray(data) ? data : data.results || [];
  
    return list.length > 0;
  }
  
  async function saveNewFileAnalysis(nextRows) {
    const clientUuid = getClientUuid();
  
    if (!clientUuid) {
      throw new Error("client_uuid를 찾을 수 없습니다.");
    }

    const originalFileName = uploadFile?.name;

  if (originalFileName) {
    const alreadyAnalyzed = await checkAlreadyAnalyzedFile(originalFileName);

    if (alreadyAnalyzed) {
      setNewAnalysisFileName(originalFileName);

      return {
        fileName: originalFileName,
        skipped: true,
        message: "이미 분석된 파일이라 DB 저장은 건너뛰었습니다.",
      };
    }
  }
  
    const backendRows = makeBackendRows(nextRows);
  
    if (backendRows.length === 0) {
      throw new Error("백엔드로 저장할 새 파일 데이터가 없습니다.");
    }
  
    const worksheet = XLSX.utils.json_to_sheet(backendRows);
    const workbook = XLSX.utils.book_new();
  
    XLSX.utils.book_append_sheet(workbook, worksheet, "analysis");
  
    const excelArray = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array",
    });
  
    const backendFileName = makeSafeFileName(uploadFile?.name);
    const backendFile = new File([excelArray], backendFileName, {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
  
    const formData = new FormData();
    formData.append("files", backendFile);
    formData.append("client_uuid", clientUuid);
  
    const response = await fetch("http://localhost:8000/score/evaluate-multiple", {
      method: "POST",
      body: formData,
    });
  
    const responseText = await response.text();
  
    let data = null;
  
    try {
      data = responseText ? JSON.parse(responseText) : null;
    } catch {
      data = responseText;
    }
  
    if (!response.ok) {
      const detail =
        typeof data === "string"
          ? data
          : data?.detail || "새 파일 분석 저장에 실패했습니다.";
  
      throw new Error(detail);
    }
  
    setNewAnalysisFileName(backendFileName);
  
    return {
      fileName: backendFileName,
      data,
    };
  }

  function handleSelectUploadFile(file) {
    setUploadFile(file || null);
    setComparisonRows([]);
    setErrorMessage("");
    setNewAnalysisFileName("");
    setHasComparedCurrentFile(false);
  }
  
  function handleRemoveUploadFile() {
    setUploadFile(null);
    setComparisonRows([]);
    setErrorMessage("");
    setNewAnalysisFileName("");
    setHasComparedCurrentFile(false);
  
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleCompare() {
    if (!uploadFile) return;
  
    if (!periodStart || !periodEnd) {
      setErrorMessage("비교 분석을 시작하려면 비교 시작월과 비교 종료월을 모두 선택해주세요.");
      return;
    }
  
    setIsComparing(true);
    setIsSavingAnalysis(true);
    setErrorMessage("");
    setNewAnalysisFileName("");
  
    try {
      const nextRows = await parseComparisonFile(uploadFile);
  
      const rows = buildComparisonRows(baseRows, nextRows);
      setComparisonRows(rows);
  
      if (rows.length === 0) {
        setErrorMessage(
          "기준 파일과 새 파일에서 매칭되는 상품을 찾지 못했습니다. 상품ID 컬럼이 같은지 확인해주세요."
        );
        return;
      }
  
      await saveNewFileAnalysis(nextRows);
      setHasComparedCurrentFile(true);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "비교 분석 중 오류가 발생했습니다.");
    } finally {
      setIsComparing(false);
      setIsSavingAnalysis(false);
    }
  }

  const canStartCompare =
  !!uploadFile &&
  !!periodStart &&
  !!periodEnd &&
  baseRows.length > 0 &&
  !isComparing &&
  !isSavingAnalysis &&
  !hasComparedCurrentFile;


  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <button
            onClick={() => setScreen("results")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-500 border bg-white hover:bg-blue-50"
          >
            ← 결과로 돌아가기
          </button>
          <h2 className="text-xl font-bold text-slate-800">
            추천 이후 성과 변화 리포트
          </h2>
        </div>
        <p className="text-sm text-slate-400 mt-0.5">
          현재 상품 액션 추천 결과와 새 3개월 성과 파일을 비교해 추천 액션 효과를 확인해요.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">기준 분석 파일</h3>
              <p className="text-xs text-slate-400 mt-1">
                현재 상품 액션 추천 결과의 기준 파일입니다.
              </p>
            </div>
            <span className="text-[11px] px-2 py-1 rounded bg-slate-100 text-slate-500 font-semibold">
              자동 고정
            </span>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-700 truncate" title={selectedFile}>
              {selectedFile || "선택된 파일 없음"}
            </p>

            <div className="grid grid-cols-3 gap-3 mt-4">
              <div>
                <p className="text-[11px] text-slate-400">분석 상품</p>
                <p className="text-sm font-bold text-slate-700">
                  {baseLoading ? "불러오는 중" : `${baseRows.length}개`}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400">비교 기준</p>
                <p className="text-sm font-bold text-slate-700">상품ID</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400">상태</p>
                <p className="text-sm font-bold text-blue-600">
                  {baseRows.length > 0 ? "준비 완료" : "대기"}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-xl bg-amber-50 border border-amber-100 p-3">
            <p className="text-[11px] text-amber-700 leading-relaxed">
              새 파일에도 같은 상품ID가 있어야 비교됩니다. 상품명이 같아도 상품ID가 다르면
              매칭률이 낮아질 수 있어요.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-bold text-slate-800">비교할 새 성과 파일</h3>
          <p className="text-xs text-slate-400 mt-1 mb-4">
            이후 3개월 성과 파일을 업로드하면 기존 파일과 자동 비교합니다.
          </p>

          <div className="rounded-xl border-2 border-dashed border-blue-200 bg-blue-50/30 p-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.csv"
              className="hidden"
              onChange={(e) => handleSelectUploadFile(e.target.files?.[0] || null)}
            />

            {!uploadFile ? (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex h-32 w-full flex-col items-center justify-center rounded-xl hover:bg-blue-50 transition"
              >
                <div className="w-10 h-10 rounded-xl bg-white border border-blue-100 flex items-center justify-center mb-2">
                  ⬆️
                </div>
                <p className="text-sm font-semibold text-blue-700">
                  새 3개월 성과 파일 업로드
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  예: 2026.04~2026.06 성과 파일
                </p>
              </button>
            ) : (
              <div className="rounded-xl bg-white border border-blue-100 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-blue-500 mb-1">
                      업로드된 비교 파일
                    </p>
                    <p className="text-sm font-bold text-slate-700 truncate" title={uploadFile.name}>
                      {uploadFile.name}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      이 파일을 기준 분석 파일과 상품ID로 비교합니다.
                    </p>
                  </div>

                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-3 py-1.5 rounded-lg border border-blue-100 bg-blue-50 text-blue-600 text-xs font-bold hover:bg-blue-100"
                    >
                      파일 변경
                    </button>

                    <button
                      type="button"
                      onClick={handleRemoveUploadFile}
                      className="px-3 py-1.5 rounded-lg border border-rose-100 bg-rose-50 text-rose-600 text-xs font-bold hover:bg-rose-100"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 mt-4">
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">
                비교 시작월
              </label>
              <input
                type="month"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">
                비교 종료월
              </label>
              <input
                type="month"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">
                분석 시즌
              </label>
              <div className="w-full rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">
                자동 분류
              </div>
            </div>
          </div>

          {uploadFile && (!periodStart || !periodEnd) && (
            <p className="mt-3 text-[11px] text-amber-600 font-medium">
              비교 분석을 시작하려면 비교 시작월과 비교 종료월을 모두 선택해주세요.
            </p>
          )}

          <button
            onClick={handleCompare}
            disabled={!canStartCompare}
            className={`mt-4 w-full rounded-xl py-3 text-sm font-bold transition ${
              !canStartCompare
                ? "bg-slate-100 text-slate-300 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            {isComparing || isSavingAnalysis
              ? "비교 및 새 파일 분석 저장 중..."
              : hasComparedCurrentFile
                ? "현재 파일 비교 완료"
                : "비교 분석 시작"}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}

      {comparisonRows.length > 0 && (
        <>
        {newAnalysisFileName && (
            <div className="rounded-xl border border-blue-100 bg-blue-50 px-5 py-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-blue-800">
                  새 성과 파일 분석 저장 완료
                </p>
                <p className="text-xs text-blue-500 mt-1">
                  분석 이력과 상품 액션 추천 결과 페이지에서 새 파일 결과를 확인할 수 있어요.
                </p>
              </div>

              <button
                onClick={() => {
                  setSelectedFile(newAnalysisFileName);
                  setScreen("results");
                }}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-bold hover:bg-blue-700"
              >
                새 파일 결과 보기
              </button>
            </div>
          )}
          <div className="grid grid-cols-4 gap-4">
            <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
              <p className="text-xs font-semibold text-blue-500">성과 개선 상품</p>
              <p className="text-2xl font-bold text-blue-700 mt-2">
                {summary.improved}개
              </p>
              <p className="text-[11px] text-blue-400 mt-1">
                전환·ROAS 개선
              </p>
            </div>

            <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
              <p className="text-xs font-semibold text-emerald-500">상태 유지 상품</p>
              <p className="text-2xl font-bold text-emerald-700 mt-2">
                {summary.maintain}개
              </p>
              <p className="text-[11px] text-emerald-400 mt-1">
                큰 변화 없음
              </p>
            </div>

            <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
              <p className="text-xs font-semibold text-amber-500">추가 개선 필요</p>
              <p className="text-2xl font-bold text-amber-700 mt-2">
                {summary.needImprove}개
              </p>
              <p className="text-[11px] text-amber-400 mt-1">
                전환·반품 재점검
              </p>
            </div>

            <div className="rounded-xl border border-purple-100 bg-purple-50 p-4">
              <p className="text-xs font-semibold text-purple-500">매칭 성공률</p>
              <p className="text-2xl font-bold text-purple-700 mt-2">
                {summary.matchRate}%
              </p>
              <p className="text-[11px] text-purple-400 mt-1">
                기존 상품 기준
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-800">
                  주요 지표 변화
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  기준 파일과 새 성과 파일의 평균 지표 변화를 비교합니다.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {metricAverageChanges.map((metric) => {
                const isGood =
                  metric.goodDirection === "up"
                    ? metric.diff >= 0
                    : metric.diff <= 0;

                return (
                  <div key={metric.key}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="font-semibold text-slate-600">
                        {metric.label}
                      </span>
                      <span
                        className={
                          isGood ? "text-blue-600 font-bold" : "text-amber-600 font-bold"
                        }
                      >
                        {metric.diff >= 0 ? "+" : ""}
                        {metric.diff}
                        {metric.unit}
                      </span>
                    </div>

                    <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          isGood ? "bg-blue-500" : "bg-amber-400"
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(8, Math.abs(metric.diff) * 8)
                          )}%`,
                        }}
                      />
                    </div>

                    <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                      <span>
                        기존 {metric.before}
                        {metric.unit}
                      </span>
                      <span>
                        이후 {metric.after}
                        {metric.unit}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800">
                상품별 액션 성과 변화
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                이전 추천 액션 이후 상품별 지표 변화와 다음 액션을 확인합니다.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[1100px]">
                <thead>
                  <tr className="bg-slate-50">
                    {[
                      "상품명",
                      "카테고리",
                      "이전 진단 유형",
                      "주요 변화",
                      "결과 판단",
                      "다음 액션",
                    ].map((header) => (
                      <th
                        key={header}
                        className="px-5 py-3 text-left text-[11px] font-semibold text-slate-400"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-50">
                  {comparisonRows.slice(0, 10).map((row, index) => {
                    const roasChange = row.metricChanges.roas;
                    const purchaseChange = row.metricChanges.purchaseRate;

                    return (
                      <tr key={`${row.productId}-${index}`} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-xs font-semibold text-slate-700 max-w-[280px]">
                          <p className="truncate" title={row.productName}>
                            {row.productName}
                          </p>
                        </td>

                        <td className="px-5 py-3 text-xs text-slate-500">
                          {row.category}
                        </td>

                        <td className="px-5 py-3">
                          <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                            {row.beforeType}
                          </span>
                        </td>

                        <td className="px-5 py-3 text-xs text-slate-500">
                          ROAS {roasChange.before} → {roasChange.after}, 구매전환{" "}
                          {purchaseChange.before} → {purchaseChange.after}
                        </td>

                        <td className="px-5 py-3">
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${getChangeBadge(
                              roasChange.diff,
                              METRIC_KEYS.find((m) => m.key === "roas")
                            )}`}
                          >
                            {row.judgement}
                          </span>
                        </td>

                        <td className="px-5 py-3 text-xs text-slate-600 font-semibold">
                          {row.nextAction}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {comparisonRows.length > 10 && (
              <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-400">
                상위 10개 상품만 미리보기로 표시합니다. 전체 {comparisonRows.length}개 상품이 비교되었습니다.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}