import { API_BASE_URL } from "../constants/api";
import React, { useState, useRef, useEffect } from "react";
import {UploadIllustration} from '../components/common/Icons'; 
import * as XLSX from "xlsx";
import { getClientUuid } from "../utils/helpers";

const SEASON_EMOJI = {
  겨울: "❄️",
  봄: "🌸",
  여름: "☀️",
  가을: "🍂",
};

function addMonthsToYearMonth(yearMonth, monthsToAdd) {
  if (!yearMonth) return "";

  const [year, month] = yearMonth.split("-").map(Number);
  const date = new Date(year, month - 1 + monthsToAdd, 1);

  const nextYear = date.getFullYear();
  const nextMonth = String(date.getMonth() + 1).padStart(2, "0");

  return `${nextYear}-${nextMonth}`;
}

function getSeasonFromMonth(month) {
  if ([1, 2, 3].includes(month)) return "겨울";
  if ([4, 5, 6].includes(month)) return "봄";
  if ([7, 8, 9].includes(month)) return "여름";
  if ([10, 11, 12].includes(month)) return "가을";
  return "";
}

function getSeasonFromPeriod(startMonth, endMonth) {
  if (!startMonth || !endMonth) return "";

  const [startYear, startM] = startMonth.split("-").map(Number);

  const months = [0, 1, 2].map((offset) => {
    const date = new Date(startYear, startM - 1 + offset, 1);
    return date.getMonth() + 1;
  });

  const seasonCounts = months.reduce((acc, month) => {
    const season = getSeasonFromMonth(month);
    acc[season] = (acc[season] || 0) + 1;
    return acc;
  }, {});

  return Object.entries(seasonCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "";
}

const OPTIONAL_COLS = [
  "카테고리",
  "시즌",
  "광고비비중",
  "클릭률",
  "찜 관심도",
  "장바구니 전환율",
  "구매전환율",
  "반품률",
  "ROAS",
];

const NUMERIC_COLS = [
  "노출수",
  "클릭수",
  "광고과금액",
  "주문금액",
  "상품 상세 방문수",
  "장바구니 유저수",
  "찜 유저수",
  "상품주문수",
  "반품건수",
];

const REQUIRED_UPLOAD_COLS = [
  "상품ID",
  "상품명",
  "노출수",
  "클릭수",
  "광고과금액",
  "주문금액",
  "상품 상세 방문수",
  "장바구니 유저수",
  "찜 유저수",
  "상품주문수",
  "반품건수",
];

function normalizeHeader(value) {
  return String(value || "").trim();
}

function normalizeValue(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function cleanNumber(value) {
  const raw = normalizeValue(value);

  if (raw === "" || raw === "-" || raw.toUpperCase() === "N/A" || raw === "없음") {
    return {
      type: "need_check",
      value: raw,
      cleanedValue: raw,
      message: "빈칸, 없음, N/A 값은 0인지 누락인지 확인이 필요합니다.",
    };
  }

  const hasPercent = raw.includes("%");

  const cleaned = raw
    .replace(/,/g, "")
    .replace(/₩/g, "")
    .replace(/원/g, "")
    .replace(/건/g, "")
    .replace(/개/g, "")
    .replace(/%/g, "")
    .replace(/\s/g, "");


  const num = Number(cleaned);

  if (!Number.isFinite(num)) {
    return {
      type: "need_check",
      value: raw,
      cleanedValue: raw,
      message: "숫자로 변환할 수 없는 값입니다.",
    };
  }

  if (hasPercent) {
    return {
      type: "need_check",
      value: raw,
      cleanedValue: num,
      message: "원본 수치 컬럼에 비율값이 들어간 것으로 보여 확인이 필요합니다.",
    };
  }

  if (raw !== String(num)) {
    return {
      type: "auto_cleaned",
      value: raw,
      cleanedValue: num,
      message: "쉼표, 통화기호, 단위 등을 제거해 자동 정제했습니다.",
    };
  }

  return {
    type: "normal",
    value: raw,
    cleanedValue: num,
    message: "정상 숫자 값입니다.",
  };
}

function makeIssue({ type, rowIndex, column, originalValue, cleanedValue, message }) {
  return {
    id: `${type}-${rowIndex}-${column}-${Math.random().toString(16).slice(2)}`,
    type,
    rowIndex,
    column,
    originalValue,
    cleanedValue,
    message,
  };
}

function typeLabel(type) {
  if (type === "auto_cleaned") return "자동 정제";
  if (type === "need_check") return "확인 필요";
  if (type === "required_error") return "필수 오류";
  if (type === "reference") return "참고";
  return "정상";
}

function safeRate(numerator, denominator) {
  if (!denominator || denominator === 0) return "";
  return Number(((numerator / denominator) * 100).toFixed(2));
}

function getCleanNumber(row, col) {
  if (!col) return 0;

  const value = row[col];
  const result = cleanNumber(value);

  return result.type === "need_check" ? 0 : Number(result.cleanedValue || 0);
}

const COLUMN_ALIASES = {
  상품ID: [
    "상품ID",
    "*상품ID",
    "상품 ID",
    "상품id",
    "상품 id",
    "상품번호",
    "상품 번호",
    "product_id",
    "product id",
  ],

  상품명: [
    "상품명",
    "*상품명",
    "상품 이름",
    "상품이름",
    "상품명/옵션명",
    "옵션명",
    "product_name",
    "product name",
  ],

  노출수: [
    "노출수",
    "노출 수",
    "노출",
    "impression",
    "impressions",
  ],

  클릭수: [
    "클릭수",
    "클릭 수",
    "클릭",
    "click",
    "clicks",
  ],

  광고과금액: [
    "광고과금액",
    "광고 과금액",
    "광고비",
    "광고 비용",
    "광고비용",
    "과금액",
    "광고 집행액",
    "ad_cost",
    "ad cost",
  ],

  주문금액: [
    "주문금액",
    "주문 금액",
    "매출",
    "매출액",
    "결제금액",
    "order_amount",
    "order amount",
  ],

  "상품 상세 방문수": [
    "상품 상세 방문수",
    "상품상세방문수",
    "상세 방문수",
    "상세페이지 방문수",
    "상품 상세조회수",
    "상품상세조회수",
    "detail_visit",
    "detail visit",
  ],

  "장바구니 유저수": [
    "장바구니 유저수",
    "장바구니유저수",
    "장바구니 수",
    "장바구니수",
    "장바구니",
    "cart_users",
    "cart users",
  ],

  "찜 유저수": [
    "찜 유저수",
    "찜유저수",
    "상품 찜 유저수",
    "상품찜유저수",
    "상품 찜수",
    "찜수",
    "wish_users",
    "wish users",
  ],

  상품주문수: [
    "상품주문수",
    "상품 주문수",
    "주문수",
    "주문 수",
    "주문건수",
    "주문 건수",
    "order_count",
    "order count",
  ],

  반품건수: [
    "반품건수",
    "반품 건수",
    "반품수",
    "반품 수",
    "return_count",
    "return count",
  ],

  "판매 사이트": [
    "판매 사이트",
    "판매사이트",
    "플랫폼",
    "판매채널",
    "채널",
  ],
};

const OPTIONAL_ALIASES = {
  카테고리: ["카테고리", "카테고리(3>4차)", "카테고리명", "상품 카테고리"],
  상품단가: ["상품단가", "상품 단가", "판매가", "단가", "price", "unit_price"],
  이미지URL: ["이미지URL", "이미지 URL", "이미지url"],
  상품등록일: ["상품등록일", "상품 등록일"],
  배송유형: ["배송유형", "배송 유형"],
  광고전환지수: ["광고전환지수", "광고 전환 지수"],
  광고비비중: ["광고비 비중", "광고비비중", "광고 비중"],
  상품클릭률: ["상품클릭률", "클릭률"],
  구매전환율: ["구매전환율"],
  장바구니전환율: ["장바구니 전환율", "장바구니전환율"],
  반품률: ["반품률"],
  주문수량: ["주문수량", "주문 수량"],
};

const REFERENCE_ONLY_COLUMNS = [
  "이미지URL",
  "이미지 URL",
  "이미지url",
  "상품등록일",
  "상품 등록일",
  "배송유형",
  "배송 유형",
  "광고전환지수",
  "광고 전환 지수",
  "광고비 비중",
  "광고비비중",
  "광고 비중",
  "주문수량",
  "주문 수량",
];

function isReferenceOnlyColumnName(header) {
  const normalizedHeader = normalizeColumnName(header);

  return REFERENCE_ONLY_COLUMNS.some(
    (name) => normalizeColumnName(name) === normalizedHeader
  );
}

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

function getAliasCandidates(canonicalName) {
  return COLUMN_ALIASES[canonicalName] || OPTIONAL_ALIASES[canonicalName] || [canonicalName];
}

function findActualColumn(headers, canonicalName) {
  const candidates = getAliasCandidates(canonicalName).map(normalizeColumnName);

  return (
    headers.find((header) => candidates.includes(normalizeColumnName(header))) || null
  );
}

function buildColumnMap(headers, requiredCols) {
  const map = {};

  requiredCols.forEach((col) => {
    map[col] = findActualColumn(headers, col);
  });

  Object.keys(OPTIONAL_ALIASES).forEach((col) => {
    map[col] = findActualColumn(headers, col);
  });

  return map;
}

function getHeaderScore(row) {
  const headers = row.map((cell) => String(cell || "").trim()).filter(Boolean);

  if (headers.length < 3) return -1;

  const allCanonicalNames = [
    ...Object.keys(COLUMN_ALIASES),
    ...Object.keys(OPTIONAL_ALIASES),
  ];

  let score = 0;

  allCanonicalNames.forEach((canonicalName) => {
    if (findActualColumn(headers, canonicalName)) {
      if (COLUMN_ALIASES[canonicalName]) {
        score += 10;
      } else {
        score += 3;
      }
    }
  });

  const joined = headers.join(" ");

  if (joined.includes("상품ID") || joined.includes("*상품ID")) score += 30;
  if (joined.includes("상품명") || joined.includes("*상품명")) score += 30;
  if (joined.includes("노출수")) score += 20;
  if (joined.includes("클릭수")) score += 20;
  if (joined.includes("광고과금액")) score += 20;

  // 제목/설명 행은 감점
  if (headers.length <= 2) score -= 50;
  if (joined.includes("상품별 성과")) score -= 50;
  if (joined.includes("자세히 살펴볼 상품")) score -= 50;

  return score;
}

function findHeaderRowIndex(sheetRows) {
  // 1순위: 상품ID + 상품명 둘 다 있는 행을 강제로 헤더로 판단
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

  // 2순위: 점수 기반 탐색
  let bestIndex = 0;
  let bestScore = -999;

  sheetRows.forEach((row, rowIndex) => {
    const score = getHeaderScore(row);

    if (score > bestScore) {
      bestScore = score;
      bestIndex = rowIndex;
    }
  });

  return bestIndex;
}

function makeCanonicalRow(originalRow, headers, columnMap, requiredCols) {
  const canonicalRow = {};
  const usedActualColumns = new Set();

  requiredCols.forEach((canonicalCol) => {
    const actualCol = columnMap[canonicalCol];

    if (actualCol) {
      canonicalRow[canonicalCol] = originalRow[actualCol] ?? "";
      usedActualColumns.add(actualCol);
    } else {
      canonicalRow[canonicalCol] = "";
    }
  });

  Object.keys(OPTIONAL_ALIASES).forEach((canonicalCol) => {
    const actualCol = columnMap[canonicalCol];

    if (actualCol) {
      canonicalRow[canonicalCol] = originalRow[actualCol] ?? "";
      usedActualColumns.add(actualCol);
    }
  });

  headers.forEach((header) => {
    if (!usedActualColumns.has(header)) {
      canonicalRow[header] = originalRow[header] ?? "";
    }
  });
  canonicalRow.__rowIndex = originalRow.__rowIndex;

  return canonicalRow;
}

function isSummaryTotalRow(row) {
  const productId = normalizeValue(row["상품ID"]);
  const productName = normalizeValue(row["상품명"]);

  const textValues = Object.values(row)
    .map((v) => normalizeValue(v))
    .join(" ");

  // 텍스트에 총계/합계/전체/total 등이 직접 들어간 경우
  const hasSummaryKeyword =
    /총계|합계|전체\s*합계|소계|total|sum/i.test(textValues);

  if (hasSummaryKeyword) return true;

  // 상품ID와 상품명이 둘 다 비어 있는데 핵심 숫자 컬럼들이 많이 채워진 경우
  // 지그재그 원본의 마지막 합산 행 같은 케이스
  const coreNumericCols = [
    "노출수",
    "클릭수",
    "광고과금액",
    "주문금액",
    "상품 상세 방문수",
    "찜 유저수",
    "장바구니 유저수",
    "상품주문수",
    "반품건수",
  ];

  const filledNumericCount = coreNumericCols.filter((col) => {
    const value = normalizeValue(row[col]);
    return value !== "" && value !== "-" && value !== "없음";
  }).length;

  if (!productId && !productName && filledNumericCount >= 3) {
    return true;
  }

  return false;
}


async function inspectFile({ file, requiredCols, startMonth, endMonth, season }) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const firstSheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[firstSheetName];

  const sheetRows = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    defval: "",
  });

  const headerRowIndex = findHeaderRowIndex(sheetRows);
  console.log("선택된 헤더 행:", headerRowIndex + 1);
  console.log("선택된 헤더:", sheetRows[headerRowIndex]);
  

  const headers = (sheetRows[headerRowIndex] || []).map((h, idx) => {
    const header = String(h || "").trim();
    return header || `__EMPTY_${idx}`;
  });

  const columnMap = buildColumnMap(headers, requiredCols);

  const dataRows = sheetRows.slice(headerRowIndex + 1);

  const originalRows = dataRows
  .map((row, rowOffset) => ({
    row,
    excelRowIndex: headerRowIndex + rowOffset + 2,
  }))
  .filter(({ row }) =>
    row.some((cell) => String(cell || "").trim() !== "")
  )
  .map(({ row, excelRowIndex }) => {
    const obj = {};

    headers.forEach((header, index) => {
      obj[header] = row[index] ?? "";
    });

    obj.__rowIndex = excelRowIndex;

    return obj;
  });

  const rawRows = originalRows
  .map((row) => makeCanonicalRow(row, headers, columnMap, requiredCols))
  .filter((row) => !isSummaryTotalRow(row));

  const issues = [];

  const missingColumns = requiredCols.filter((col) => {
    if (col === "판매 사이트") return false;
    return !columnMap[col];
  });

  missingColumns.forEach((col) => {
    issues.push(
      makeIssue({
        type: "required_error",
        rowIndex: "컬럼",
        column: col,
        originalValue: "없음",
        cleanedValue: "없음",
        message: `필수 컬럼 '${col}'을 찾을 수 없습니다. 컬럼명을 확인하거나 템플릿에 해당 컬럼을 추가해주세요.`,
      })
    );
  });

  if (!columnMap["판매 사이트"]) {
    issues.push(
      makeIssue({
        type: "auto_cleaned",
        rowIndex: "전체",
        column: "판매 사이트",
        originalValue: "컬럼 없음",
        cleanedValue: "지그재그",
        message: "원본 파일에 판매 사이트 컬럼이 없어 기본값 '지그재그'로 자동 보완했습니다.",
      })
    );
  }

  const mappedActualColumns = new Set(
    Object.values(columnMap).filter(Boolean)
  );

  const referenceColumns = headers.filter((header) => {
    // 원래 분석에 쓰지 않는 컬럼은 매핑 여부와 상관없이 참고 처리
    if (isReferenceOnlyColumnName(header)) return true;
  
    // 어떤 필수/보조 컬럼에도 매핑되지 않은 원본 컬럼도 참고 처리
    return !mappedActualColumns.has(header);
  });
  
  referenceColumns.forEach((col) => {
    issues.push(
      makeIssue({
        type: "reference",
        rowIndex: "전체",
        column: col,
        originalValue: "-",
        cleanedValue: "-",
        message: "분석 필수 컬럼이 아니므로 참고용으로만 표시합니다.",
      })
    );
  });
  let computedUnitPriceCount = 0;
  const cleanedRows = rawRows.map((row, idx) => {
    const excelRowIndex = row.__rowIndex ?? headerRowIndex + idx + 2;
    const cleanedRow = { ...row };
  
    cleanedRow.__rowIndex = excelRowIndex;

    requiredCols.forEach((col) => {
      if (col === "판매 사이트") return;
      if (col === "상품명") return;
      if (col === "카테고리") return;
      if (!columnMap[col]) return;
    
      const value = normalizeValue(row[col]);
    
      if (value === "") {
        issues.push(
          makeIssue({
            type: "required_error",
            rowIndex: excelRowIndex,
            column: col,
            originalValue: "",
            cleanedValue: "",
            message: `필수 컬럼 '${col}'의 값이 비어 있습니다. 값을 입력한 뒤 다시 업로드해주세요.`,
          })
        );
      }
    });

    NUMERIC_COLS.forEach((col) => {
      if (!Object.prototype.hasOwnProperty.call(row, col)) return;

      const result = cleanNumber(row[col]);

      if (result.type === "auto_cleaned") {
        cleanedRow[col] = result.cleanedValue;

        issues.push(
          makeIssue({
            type: "auto_cleaned",
            rowIndex: excelRowIndex,
            column: col,
            originalValue: result.value,
            cleanedValue: result.cleanedValue,
            message: result.message,
          })
        );
      }

      if (result.type === "need_check") {
        issues.push(
          makeIssue({
            type: "need_check",
            rowIndex: excelRowIndex,
            column: col,
            originalValue: result.value,
            cleanedValue: result.cleanedValue,
            message: result.message,
          })
        );
      }
    });

    const exposure = getCleanNumber(cleanedRow, "노출수");
    const click = getCleanNumber(cleanedRow, "클릭수");
    const visit = getCleanNumber(cleanedRow, "상품 상세 방문수");
    const wish = getCleanNumber(cleanedRow, "찜 유저수");
    const cart = getCleanNumber(cleanedRow, "장바구니 유저수");
    const orderCount = getCleanNumber(cleanedRow, "상품주문수");  
    const returnCount = getCleanNumber(cleanedRow, "반품건수");
    const adCost = getCleanNumber(cleanedRow, "광고과금액");
    const orderAmount = getCleanNumber(cleanedRow, "주문금액");
    const rawUnitPrice = normalizeValue(cleanedRow["상품단가"]);
    const unitPriceResult = rawUnitPrice ? cleanNumber(rawUnitPrice) : null;

    const hasValidOriginalUnitPrice =
      unitPriceResult &&
      unitPriceResult.type !== "need_check" &&
      Number(unitPriceResult.cleanedValue) > 0;

    const unitPrice = hasValidOriginalUnitPrice
      ? Number(unitPriceResult.cleanedValue)
      : orderCount > 0
        ? Math.round(orderAmount / orderCount)
        : 0;
    
    if (!hasValidOriginalUnitPrice) {
      computedUnitPriceCount += 1;
    }

    cleanedRow["분석 시작월"] = startMonth;
    cleanedRow["분석 종료월"] = endMonth;
    cleanedRow["분석 시즌"] = season;
    cleanedRow["판매 사이트"] = cleanedRow["판매 사이트"] || "지그재그";
    cleanedRow["상품단가"] = unitPrice;

    cleanedRow["클릭률"] = safeRate(click, exposure);
    cleanedRow["찜 관심도"] = safeRate(wish, visit);
    cleanedRow["장바구니 전환율"] = safeRate(cart, visit);
    cleanedRow["구매전환율"] = safeRate(orderCount, visit);
    cleanedRow["반품률"] = safeRate(returnCount, orderCount);
    cleanedRow["ROAS"] = safeRate(orderAmount, adCost);

    if (exposure === 0 && columnMap["노출수"]) {
      issues.push(
        makeIssue({
          type: "need_check",
          rowIndex: excelRowIndex,
          column: "노출수",
          originalValue: row["노출수"],
          cleanedValue: exposure,
          message: "노출수가 0이라 클릭률 계산이 제한됩니다.",
        })
      );
    }

    if (visit === 0 && columnMap["상품 상세 방문수"]) {
      issues.push(
        makeIssue({
          type: "need_check",
          rowIndex: excelRowIndex,
          column: "상품 상세 방문수",
          originalValue: row["상품 상세 방문수"],
          cleanedValue: visit,
          message: "상세 방문수가 0이라 찜/장바구니/구매전환율 계산이 제한됩니다.",
        })
      );
    }

    if (adCost === 0 && columnMap["광고과금액"]) {
      issues.push(
        makeIssue({
          type: "need_check",
          rowIndex: excelRowIndex,
          column: "광고과금액",
          originalValue: row["광고과금액"],
          cleanedValue: adCost,
          message: "광고과금액이 0이라 ROAS 계산이 제한됩니다.",
        })
      );
    }

    if (orderCount === 0 && columnMap["상품주문수"]) {
      issues.push(
        makeIssue({
          type: "need_check",
          rowIndex: excelRowIndex,
          column: "상품주문수",
          originalValue: row["상품주문수"],
          cleanedValue: orderCount,
          message: "주문수가 0이라 반품 안정성은 보수적으로 처리됩니다.",
        })
      );
    }

    return cleanedRow;
  });

  const generatedColumns = [
    "분석 시작월",
    "분석 종료월",
    "분석 시즌",
    "클릭률",
    "찜 관심도",
    "장바구니 전환율",
    "구매전환율",
    "반품률",
    "ROAS",
  ];
  
  if (!columnMap["판매 사이트"]) {
    generatedColumns.unshift("판매 사이트");
  }
  
  if (!columnMap["상품단가"] || computedUnitPriceCount > 0) {
    generatedColumns.unshift("상품단가");
  }
  
  const generatedColumnMessages = {
    "판매 사이트": "원본 파일에 판매 사이트 컬럼이 없어 기본값 '지그재그'로 자동 보완했습니다.",
    "상품단가": "상품단가가 없거나 비어 있어 주문금액 ÷ 상품주문수로 자동 계산했습니다.",
    "분석 시작월": "사용자가 선택한 분석 시작월을 기준으로 자동 생성했습니다.",
    "분석 종료월": "사용자가 선택한 분석 종료월을 기준으로 자동 생성했습니다.",
    "분석 시즌": "분석 기간을 기준으로 시즌을 자동 분류했습니다.",
    "클릭률": "노출수와 클릭수를 기준으로 자동 계산했습니다.",
    "찜 관심도": "찜 유저수와 상품 상세 방문수를 기준으로 자동 계산했습니다.",
    "장바구니 전환율": "장바구니 유저수와 상품 상세 방문수를 기준으로 자동 계산했습니다.",
    "구매전환율": "상품주문수와 상품 상세 방문수를 기준으로 자동 계산했습니다.",
    "반품률": "반품건수와 상품주문수를 기준으로 자동 계산했습니다.",
    "ROAS": "주문금액과 광고과금액을 기준으로 자동 계산했습니다.",
  };
  
  generatedColumns.forEach((col) => {
    const alreadyExists = issues.some(
      (issue) =>
        issue.type === "auto_cleaned" &&
        issue.rowIndex === "전체" &&
        issue.column === col
    );
  
    if (alreadyExists) return;
  
    issues.unshift(
      makeIssue({
        type: "auto_cleaned",
        rowIndex: "전체",
        column: col,
        originalValue: "자동 생성",
        cleanedValue: "생성 완료",
        message: generatedColumnMessages[col] || "분석을 위해 자동 생성한 컬럼입니다.",
      })
    );
  });

  const autoCleanCount = issues.filter((i) => i.type === "auto_cleaned").length;
  const needCheckCount = issues.filter((i) => i.type === "need_check").length;
  const requiredErrorCount = issues.filter((i) => i.type === "required_error").length;
  const referenceCount = issues.filter((i) => i.type === "reference").length;

  const OUTPUT_COL_ORDER = [
    "상품ID",
    "상품명",
    "카테고리",
    "분석 시즌",
    "노출수",
    "클릭수",
    "상품 상세 방문수",
    "찜 유저수",
    "장바구니 유저수",
    "상품주문수",
    "반품건수",
    "광고과금액",
    "주문금액",
    "상품단가",
    "분석 시작월",
    "분석 종료월",
    "판매 사이트",
    "클릭률",
    "찜 관심도",
    "장바구니 전환율",
    "구매전환율",
    "반품률",
    "ROAS",
  ];

  const BACKEND_REQUIRED_COLS = [
    "상품명",
    "카테고리",
    "분석 시즌",
    "노출수",
    "클릭수",
    "상품 상세 방문수",
    "찜 유저수",
    "장바구니 유저수",
    "상품주문수",
    "반품건수",
    "광고과금액",
    "주문금액",
    "상품단가",
    "분석 시작월",
    "분석 종료월",
  ];
  
  const BACKEND_NUMERIC_COLS = [
    "노출수",
    "클릭수",
    "상품 상세 방문수",
    "찜 유저수",
    "장바구니 유저수",
    "상품주문수",
    "반품건수",
    "광고과금액",
    "주문금액",
    "상품단가",
  ];
  
  const exportRows = cleanedRows.map((row) => {
    const nextRow = { ...row };
  
    // 상품명: 백엔드 필수 문자열
    if (
      nextRow["상품명"] === undefined ||
      nextRow["상품명"] === null ||
      String(nextRow["상품명"]).trim() === ""
    ) {
      nextRow["상품명"] = `상품명 미입력_${
        nextRow["상품ID"] || nextRow.__rowIndex || ""
      }`;
    }
  
    // 카테고리: 백엔드 필수 문자열
    if (
      nextRow["카테고리"] === undefined ||
      nextRow["카테고리"] === null ||
      String(nextRow["카테고리"]).trim() === ""
    ) {
      nextRow["카테고리"] = "기타";
    }
  
    // 분석 시즌/기간: 백엔드 필수 문자열
    nextRow["분석 시즌"] = nextRow["분석 시즌"] || season || "";
    nextRow["분석 시작월"] = nextRow["분석 시작월"] || startMonth || "";
    nextRow["분석 종료월"] = nextRow["분석 종료월"] || endMonth || "";
  
    // 판매 사이트는 스키마 필수는 아니지만 DB/이력용으로 유지
    nextRow["판매 사이트"] = nextRow["판매 사이트"] || "지그재그";
  
    // 상품단가: 없으면 주문금액 / 상품주문수로 계산
    const orderAmount = Number(nextRow["주문금액"] || 0);
    const orderCount = Number(nextRow["상품주문수"] || 0);
  
    if (
      nextRow["상품단가"] === undefined ||
      nextRow["상품단가"] === null ||
      nextRow["상품단가"] === "" ||
      Number(nextRow["상품단가"]) <= 0
    ) {
      nextRow["상품단가"] =
        orderCount > 0 ? Math.round(orderAmount / orderCount) : 0;
    }
  
    // 백엔드 필수 숫자값 비어 있으면 0으로 보정
    BACKEND_NUMERIC_COLS.forEach((col) => {
      if (
        nextRow[col] === undefined ||
        nextRow[col] === null ||
        nextRow[col] === ""
      ) {
        nextRow[col] = 0;
      }
    });
  
    // 백엔드 필수 문자값 비어 있으면 기본값 보정
    BACKEND_REQUIRED_COLS.forEach((col) => {
      if (
        nextRow[col] === undefined ||
        nextRow[col] === null ||
        String(nextRow[col]).trim() === ""
      ) {
        if (BACKEND_NUMERIC_COLS.includes(col)) {
          nextRow[col] = 0;
        } else if (col === "상품명") {
          nextRow[col] = `상품명 미입력_${
            nextRow["상품ID"] || nextRow.__rowIndex || ""
          }`;
        } else if (col === "카테고리") {
          nextRow[col] = "기타";
        } else if (col === "분석 시즌") {
          nextRow[col] = season || "";
        } else if (col === "분석 시작월") {
          nextRow[col] = startMonth || "";
        } else if (col === "분석 종료월") {
          nextRow[col] = endMonth || "";
        }
      }
    });
  
    return nextRow;
  });
  
  const extraCols = Object.keys(exportRows[0] || {}).filter(
    (col) => !OUTPUT_COL_ORDER.includes(col) && col !== "__rowIndex"
  );
  
  const cleanedSheet = XLSX.utils.json_to_sheet(exportRows, {
    header: [...OUTPUT_COL_ORDER, ...extraCols],
  });

  const cleanedWorkbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(cleanedWorkbook, cleanedSheet, "검수_정제결과");

  const output = XLSX.write(cleanedWorkbook, {
    bookType: "xlsx",
    type: "array",
  });

  const blob = new Blob([output], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });

  return {
    fileName: file.name,
    sheetName: firstSheetName,
    headerRowIndex,
    headers: [...OUTPUT_COL_ORDER, ...extraCols],
    originalHeaders: headers,
    rows: exportRows,
    cleanedRows: exportRows,
    issues,
    missingColumns,
    referenceColumns,
    generatedColumns,
    columnMap,
    autoCleanCount,
    needCheckCount,
    requiredErrorCount,
    referenceCount,
    canAnalyze: requiredErrorCount === 0,
    cleanedFileUrl: URL.createObjectURL(blob),
    cleanedFileName: `${file.name.replace(
      /\.(xlsx|csv)$/i,
      ""
    )}_분석완료_${new Date().toISOString().slice(0, 10)}.xlsx`,
  };
}

export default function UploadScreen({ result, setScreen, selectedFile, setSelectedFile }) {
    const [dragging, setDragging] = useState(false);
    const [uploadedAt, setUploadedAt] = useState("");
    const fileInputRef = useRef(null);
    const MAX_FILE_SIZE_MB = 50;
    const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024;
    function handleFileSelect(file) {
        if (!file)
            return;
        const allowedExtensions = [".xlsx", ".csv"];
        const fileName = file.name.toLowerCase();
        const isAllowed = allowedExtensions.some((ext) => fileName.endsWith(ext));
        if (!isAllowed) {
            alert("xlsx 또는 csv 파일만 업로드할 수 있습니다.");
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            alert(`파일 용량은 최대 ${MAX_FILE_SIZE_MB}MB까지 업로드할 수 있습니다.`);
            return;
        }
        setSelectedFile(file);
        setUploadedAt(new Date().toLocaleString("ko-KR", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }));
        setStartMonth("");
        setEndMonth("");
        setSelectedYear("");
        setSelectedMonth("");
        setValidationStarted(false);
        setValidationReady(false);
        setInspectionResult(null);
    }
    function handleTemplateDownload() {
        const link = document.createElement("a");
        link.href = "/templates/actionfit_upload_template_v2.xlsx";
        link.download = "ActionFit_AI_상품성과_업로드_템플릿.xlsx";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    function formatFileSize(bytes) {
        if (bytes === 0)
            return "0B";
        const kb = bytes / 1024;
        const mb = kb / 1024;
        if (mb >= 1) {
            return `${mb.toFixed(2)}MB`;
        }
        return `${kb.toFixed(1)}KB`;
    }
    const [startMonth, setStartMonth] = useState("");
    const [endMonth, setEndMonth] = useState("");
    const [showModal, setShowModal] = useState(false);
    const [validationStarted, setValidationStarted] = useState(false);
    const [validationReady, setValidationReady] = useState(false);
    const [inspectionResult, setInspectionResult] = useState(null);
    const [cleanseOpen, setCleanseOpen] = useState(false);
    const [examplesOpen, setExamplesOpen] = useState(false);
    async function handleValidationStart() {
      if (!selectedFile || !startMonth || !endMonth) return;
    
      setValidationStarted(true);
      setValidationReady(false);
      setInspectionResult(null);
    
      try {
        const result = await inspectFile({
          file: selectedFile,
          requiredCols: REQUIRED_UPLOAD_COLS,
          startMonth,
          endMonth,
          season,
        });
    
        setInspectionResult(result);
        setValidationReady(true);
      } catch (error) {
        console.error(error);
        alert("파일 검수 중 오류가 발생했습니다. 파일 형식 또는 컬럼명을 확인해주세요.");
        setValidationStarted(false);
        setValidationReady(false);
      }
    }
    function handleStartMonthChange(value) {
        setStartMonth(value);
        setEndMonth(addMonthsToYearMonth(value, 2));
        setValidationStarted(false);
        setValidationReady(false);
    }

    const currentYear = new Date().getFullYear();
    const MIN_YEAR = 2020;

    const YEAR_OPTIONS = Array.from(
      { length: currentYear - MIN_YEAR + 1 },
      (_, i) => currentYear - i
    );

    const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) =>
      String(i + 1).padStart(2, "0")
    );

    const [selectedYear, setSelectedYear] = useState("");
    const [selectedMonth, setSelectedMonth] = useState("");
    const [yearDropdownOpen, setYearDropdownOpen] = useState(false);
    const [monthDropdownOpen, setMonthDropdownOpen] = useState(false);

    function handleYearMonthChange(type, value) {
      const nextYear = type === "year" ? value : selectedYear;
      const nextMonth = type === "month" ? value : selectedMonth;

      if (type === "year") {
        setSelectedYear(value);
      }

      if (type === "month") {
        setSelectedMonth(value);
      }

      setValidationStarted(false);
      setValidationReady(false);

      if (!nextYear || !nextMonth) {
        setStartMonth("");
        setEndMonth("");
        return;
      }

      handleStartMonthChange(`${nextYear}-${nextMonth}`);
    }
    const season = startMonth && endMonth ? getSeasonFromPeriod(startMonth, endMonth) : "";
    const canStartValidation = !!selectedFile && !!startMonth && !!endMonth && !(validationStarted && !validationReady);
    const fmt = (v) => v.replace("-", ".");
    const hasWarn = inspectionResult ? inspectionResult.needCheckCount > 0 : false;
    const hasError = inspectionResult ? inspectionResult.requiredErrorCount > 0 : false;
    const SUMMARY_VALIDATION = inspectionResult
  ? [
      {
        label: "필수 컬럼 확인",
        status: inspectionResult.requiredErrorCount > 0 ? "오류" : "정상",
        desc:
          inspectionResult.requiredErrorCount > 0
            ? `${inspectionResult.requiredErrorCount}건의 필수 컬럼 문제가 확인되었습니다.`
            : "모든 필수 컬럼이 확인되었습니다.",
        ok: inspectionResult.requiredErrorCount === 0,
      },
      {
        label: "숫자형 데이터 자동 정제",
        status: "완료",
        desc:
          inspectionResult.autoCleanCount > 0
            ? `${inspectionResult.autoCleanCount}건의 값을 자동 정제했습니다.`
            : "자동 정제가 필요한 값이 없습니다.",
        ok: true,
      },
      {
        label: "시즌/기간 정보 확인",
        status: "정상",
        desc: `분석 기간 ${fmt(startMonth)}~${fmt(endMonth)}, ${season} 시즌으로 분류되었습니다.`,
        ok: true,
      },
      {
        label: "확인 필요 항목",
        status: inspectionResult.needCheckCount > 0 ? "경고" : "정상",
        desc:
          inspectionResult.needCheckCount > 0
            ? `${inspectionResult.needCheckCount}건의 값은 의미 확인이 필요합니다.`
            : "확인 필요 항목이 없습니다.",
        ok: inspectionResult.needCheckCount === 0,
      },
    ]
  : [];
    return (<>
      {showModal && inspectionResult && (
        <InspectionModal
          result={inspectionResult}
          onClose={() => setShowModal(false)}
          setScreen={setScreen}
          setSelectedFile={setSelectedFile}
        />
      )}

      <div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
        {/* Page heading */}
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            상품 성과 파일 업로드
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            분석할 상품 데이터 파일을 업로드해주세요.
          </p>
        </div>

        {/* Hero banner — soft blue gradient matching main screen */}
        <div className="rounded-2xl p-7 flex items-center justify-between overflow-hidden relative" style={{
            background: "linear-gradient(135deg, #3B82F6 0%, #60A5FA 55%, #93C5FD 100%)",
        }}>
          <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-transparent pointer-events-none"/>
          <div className="absolute -top-12 -right-12 w-52 h-52 rounded-full bg-white/10 pointer-events-none"/>
          <div className="relative z-10">
            <p className="text-[11px] font-semibold uppercase tracking-widest mb-2" style={{
            color: "rgba(255,255,255,0.85)",
            textShadow: "0 1px 4px rgba(30,58,138,0.25)",
        }}>
              Step 1
            </p>
            <h2 className="text-xl font-bold mb-2" style={{
            color: "#fff",
            textShadow: "0 1px 6px rgba(30,58,138,0.3)",
        }}>
              상품 성과 파일 업로드
            </h2>
            <p className="text-sm leading-relaxed max-w-md" style={{
            color: "rgba(255,255,255,0.9)",
            textShadow: "0 1px 4px rgba(30,58,138,0.2)",
        }}>
              상품 성과 분석을 위해 엑셀(xlsx) 또는 CSV 파일을
              업로드해주세요.
            </p>
          </div>
          <div className="relative z-10 hidden lg:block">
            <UploadIllustration />
          </div>
        </div>

        {/* Upload + Column guide */}
        <div className="grid grid-cols-2 gap-4">
          {/* Drop zone */}
          <div className="bg-white rounded-xl border border-slate-100 p-6">
            <h3 className="font-semibold text-slate-800 text-sm mb-4">
              파일 업로드
            </h3>

            <input ref={fileInputRef} type="file" accept=".xlsx,.csv" className="hidden" onChange={(e) => handleFileSelect(e.target.files?.[0])}/>

            {!selectedFile ? (<div onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
            }} onDragLeave={() => setDragging(false)} onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                handleFileSelect(e.dataTransfer.files?.[0]);
            }} className={`border-2 border-dashed rounded-xl p-7 flex flex-col items-center text-center transition-all ${dragging
                ? "border-blue-400 bg-blue-50"
                : "border-slate-200 hover:border-blue-300 hover:bg-slate-50/70"}`}>
                <div className="w-[52px] h-[52px] rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="1.8">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                  </svg>
                </div>
                <p className="text-slate-600 text-sm font-medium mb-1">
                  파일을 드래그 & 드롭하거나
                </p>
                <p className="text-slate-400 text-xs mb-4">
                  아래 버튼을 클릭하여 선택하세요
                </p>

                <button type="button" onClick={() => {
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                    fileInputRef.current.click();
                }
            }} className="text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition mb-4" style={{ backgroundColor: "#2563EB" }} onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1D4ED8")} onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#2563EB")}>
                  파일 선택
                </button>
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="bg-slate-100 px-2 py-0.5 rounded font-mono">
                    .xlsx
                  </span>
                  <span className="bg-slate-100 px-2 py-0.5 rounded font-mono">
                    .csv
                  </span>
                  <span>최대 50MB</span>
                </div>
              </div>) : (
        // 파일 정보 카드
        <div className="border-2 border-solid border-blue-200 bg-blue-50 rounded-xl p-7 flex flex-col items-center text-center transition-all">
                <div className="w-[52px] h-[52px] rounded-2xl bg-white flex items-center justify-center mb-4 border-blue-200 border">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="1.8">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                  </svg>
                </div>
                <p className="text-blue-700 text-sm font-medium mb-2 flex items-center gap-2">
                  <span>
                    {selectedFile.name}
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-700 rounded font-mono px-2 py-0.5 ml-1">
                    {selectedFile?.name ? selectedFile.name.split('.').pop().toLowerCase() : ""}
                  </span>
                </p>
                <p className="text-xs text-slate-600 mb-4">
                  {(selectedFile.size / (1024 * 1024) >= 1
                ? (selectedFile.size / (1024 * 1024)).toFixed(2) + " MB"
                : (selectedFile.size / 1024).toFixed(0) + " KB")}
                </p>
                <div className="flex gap-2">
                  {/* <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.csv"
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files?.[0])}
            /> */}
                  <button type="button" onClick={() => {
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                    fileInputRef.current.click();
                }
            }} className="text-white text-xs font-semibold px-4 py-2 rounded-lg transition" style={{ backgroundColor: "#2563EB" }} onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1D4ED8")} onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#2563EB")}>
                    파일 변경
                  </button>
                  <button type="button" onClick={() => {
                setSelectedFile(null);
                setUploadedAt("");
                setStartMonth("");
                setEndMonth("");
                setSelectedYear("");
                setSelectedMonth("");
                setValidationStarted(false);
                setValidationReady(false);
                setInspectionResult(null);
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                }
            }} className="text-blue-700 bg-blue-100 text-xs font-semibold px-4 py-2 rounded-lg border border-blue-200 transition hover:bg-blue-200">
                    삭제
                  </button>
                </div>
              </div>)}
          </div>


          {/* Column guide */}
          <div className="bg-white rounded-xl border border-slate-100 p-6">
            <h3 className="font-semibold text-slate-800 text-sm mb-1">
              필수 컬럼 가이드
            </h3>
            <p className="text-xs text-slate-400 mb-3">
              분석을 위해 다음 컬럼이 포함되어야 합니다.
            </p>
            <div className="flex flex-wrap gap-1.5 mb-3">
            {REQUIRED_UPLOAD_COLS.map((c) => (<span key={c} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium">
                  {c}
                </span>))}
            </div>
            {/* <p className="text-[11px] font-semibold text-slate-500 mb-1.5 mt-3">
          선택 컬럼
        </p> */}
            {/* <div className="flex flex-wrap gap-1.5 mb-3">
          {OPTIONAL_COLS.map((c) => (
            <span
              key={c}
              className="text-xs bg-slate-50 text-slate-500 border border-slate-200 px-2 py-1 rounded-lg"
            >
              {c}
            </span>
          ))}
        </div> */}
            {/* Updated amber note — softer tone */}
            <div className="p-3 rounded-lg border" style={{
            backgroundColor: "#FFFBEB",
            borderColor: "#FDE68A",
        }}>
              <p className="text-[11px] leading-relaxed" style={{ color: "#B45309" }}>
                💡 클릭률, ROAS, 구매전환율, 장바구니 전환율,
                반품률 등 비율 지표는 원본 수치 데이터를
                기준으로 자동 계산됩니다.
                <br />
                엑셀에 해당 비율 컬럼이 포함되어 있어도
                참고용으로 활용되며, 분석 기준은 자동 계산값을
                우선 적용합니다.
              </p>
            </div>
            {/* Template download */}
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex items-center gap-3 rounded-xl bg-emerald-50/70 border border-emerald-100 px-4 py-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-700">
                  샘플 템플릿 다운로드
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  필수 컬럼이 포함된 샘플 파일을 내려받아 작성할 수 있습니다.
                </p>
              </div>

              <button type="button" onClick={handleTemplateDownload} className="flex-shrink-0 flex items-center gap-1.5 bg-emerald-600 text-white text-[11px] font-semibold px-3 py-2 rounded-lg hover:bg-emerald-700 transition">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                다운로드
              </button>
            </div>
          </div>
          </div>
        </div>



        {/* 분석 기간 설정 */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2.2">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <h3 className="font-semibold text-slate-800 text-sm">
              분석 기간 설정
            </h3>
            <span className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-md border" style={{
            backgroundColor: "#EFF6FF",
            color: "#2563EB",
            borderColor: "#BFDBFE",
        }}>
              Step 2
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-5 pl-8">
            업로드한 상품 성과 데이터가 어느 기간의 데이터인지
            선택해주세요.
          </p>

          <div className="flex items-end gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              분석 시작 연도·월 선택
              </label>
              <div className="grid grid-cols-[1fr_1fr] gap-2">
              {/* 연도 선택 */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setYearDropdownOpen((prev) => !prev);
                    setMonthDropdownOpen(false);
                  }}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition flex items-center justify-between"
                >
                  <span>{selectedYear ? `${selectedYear}년` : "연도 선택"}</span>

                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    className="text-slate-400"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {yearDropdownOpen && (
                  <div className="absolute left-0 top-full z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg">
                    {YEAR_OPTIONS.map((year) => (
                      <button
                        key={year}
                        type="button"
                        onClick={() => {
                          handleYearMonthChange("year", String(year));
                          setYearDropdownOpen(false);
                        }}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 transition ${
                          String(year) === selectedYear
                            ? "bg-blue-50 text-blue-600 font-semibold"
                            : "text-slate-600"
                        }`}
                      >
                        {year}년
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* 월 선택 */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setMonthDropdownOpen((prev) => !prev);
                    setYearDropdownOpen(false);
                  }}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition flex items-center justify-between"
                >
                  <span>{selectedMonth ? `${Number(selectedMonth)}월` : "월 선택"}</span>

                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    className="text-slate-400"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {monthDropdownOpen && (
                  <div className="absolute left-0 top-full z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg">
                    {MONTH_OPTIONS.map((month) => (
                      <button
                        key={month}
                        type="button"
                        onClick={() => {
                          handleYearMonthChange("month", month);
                          setMonthDropdownOpen(false);
                        }}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 transition ${
                          month === selectedMonth
                            ? "bg-blue-50 text-blue-600 font-semibold"
                            : "text-slate-600"
                        }`}
                      >
                        {Number(month)}월
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
            </div>
            <div className="pb-3 text-slate-300">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                종료월 선택
              </label>
              <input type="month" value={endMonth} disabled className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-sm text-slate-700 cursor-not-allowed"/>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                분석 시즌
              </label>
              <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg border" style={{
            backgroundColor: "#EFF6FF",
            borderColor: "#BFDBFE",
        }}>
                <span className="text-lg leading-none">
                  {season ? SEASON_EMOJI[season] : "🗓️"}
                </span>

                <span className="text-sm font-bold" style={{ color: "#2563EB" }}>
                  {season || "시작월 선택 필요"}
                </span>
                <span className="text-[11px] ml-auto" style={{ color: "#60A5FA" }}>
                  자동 분류
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-1.5 pl-0.5">
            {[
            "업로드한 3개월 누적 상품 성과 데이터의 기간을 선택해주세요.",
            "시즌·카테고리 비교를 위해 업로드 파일의 분석 기간을 선택해주세요.",
            "겨울 1~3월, 봄 4~6월, 여름 7~9월, 가을 10~12월 기준으로 분류합니다.",
            "예: 5월을 선택하면 5~7월로 설정되며, 3개월 중 2개월이 봄 기준에 해당하므로 봄으로 자동 분류됩니다."
        ].map((t) => (<div key={t} className="flex items-center gap-2 text-xs text-slate-400">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {t}
              </div>))}
          </div>
          {!validationReady && (<div className="mt-5 flex justify-end">
              <button type="button" onClick={handleValidationStart} disabled={!canStartValidation} className={`text-sm font-semibold px-5 py-2.5 rounded-xl transition ${!canStartValidation
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"}`}>
                {validationStarted && !validationReady ? "검수 중..." : "데이터 검수 시작"}
              </button>
            </div>)}
        </div>
        {validationReady && (<div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
          {/* Card header */}
          <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">
                데이터 자동 정제 및 검수 결과
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {selectedFile
                ? `${selectedFile.name} · ${formatFileSize(selectedFile.size)} · ${uploadedAt} 업로드`
                : "업로드된 파일 없음"}
              </p>
            </div>
            <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            <button
              onClick={() => setShowModal(true)}
              disabled={!inspectionResult}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border transition disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                color: "#2563EB",
                backgroundColor: "#EFF6FF",
                borderColor: "#BFDBFE",
              }}
            >
              검수 결과 확인
            </button>
            </div>
          </div>


          <div className="px-6 py-5">
            {/* Summary stat cards */}
            <div className="grid grid-cols-4 gap-3 mb-5">
            {[
              {
                label: "자동 정제 항목",
                value: `${inspectionResult?.autoCleanCount || 0}건`,
                sub: "형식 오류 자동 변환",
                color: "border-blue-200 bg-blue-50",
                textColor: "text-blue-700",
                subColor: "text-blue-500",
              },
              {
                label: "확인 필요 항목",
                value: `${inspectionResult?.needCheckCount || 0}건`,
                sub: "의미 판단 필요",
                color: "border-amber-200",
                textColor: "text-amber-700",
                subColor: "text-amber-500",
                bgStyle: { backgroundColor: "#FFFBEB" },
              },
              {
                label: "필수 오류",
                value: `${inspectionResult?.requiredErrorCount || 0}건`,
                sub: "분석 불가 오류",
                color:
                  inspectionResult?.requiredErrorCount > 0
                    ? "border-rose-200 bg-rose-50"
                    : "border-emerald-200 bg-emerald-50",
                textColor:
                  inspectionResult?.requiredErrorCount > 0
                    ? "text-rose-700"
                    : "text-emerald-700",
                subColor:
                  inspectionResult?.requiredErrorCount > 0
                    ? "text-rose-500"
                    : "text-emerald-500",
              },
              {
                label: "분석 가능 여부",
                value: inspectionResult?.canAnalyze ? "가능" : "불가능",
                sub: inspectionResult?.canAnalyze
                  ? inspectionResult?.needCheckCount > 0
                    ? "확인 필요 항목 포함"
                    : "분석 시작 가능"
                  : "수정 후 재업로드 필요",
                color: inspectionResult?.canAnalyze
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-slate-200 bg-slate-50",
                textColor: inspectionResult?.canAnalyze ? "text-emerald-700" : "text-slate-700",
                subColor: inspectionResult?.canAnalyze ? "text-emerald-500" : "text-slate-400",
              },
            ].map((s) => (
              <div
                key={s.label}
                className={`rounded-xl border p-4 ${s.color}`}
                style={"bgStyle" in s ? s.bgStyle : undefined}
              >
                <p className="text-[11px] text-slate-500 font-semibold mb-1">
                  {s.label}
                </p>
                <p className={`text-xl font-bold ${s.textColor} mb-0.5`}>
                  {s.value}
                </p>
                <p className={`text-[10px] ${s.subColor}`}>
                  {s.sub}
                </p>
              </div>
            ))}
            </div>
            
            {inspectionResult?.issues?.filter((i) => i.type === "required_error").length > 0 && (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
                <p className="text-xs font-bold text-rose-700 mb-2">
                  필수 오류 상세
                </p>

                <div className="space-y-1.5">
                  {inspectionResult.issues
                    .filter((i) => i.type === "required_error")
                    .slice(0, 10)
                    .map((issue) => (
                      <div key={issue.id} className="text-[11px] text-rose-700 leading-relaxed">
                        • {issue.rowIndex} · {issue.column}: {issue.message}
                      </div>
                    ))}
                </div>

                {inspectionResult.issues.filter((i) => i.type === "required_error").length > 10 && (
                  <p className="text-[11px] text-rose-500 mt-2">
                    외 {inspectionResult.issues.filter((i) => i.type === "required_error").length - 10}건은 검수 결과 모달에서 확인할 수 있습니다.
                  </p>
                )}
              </div>
            )}
            
            {/* Collapsible: ActionFit AI 자동 정제 방식 */}
            <div className="rounded-xl border border-blue-100 overflow-hidden mb-4">
              <button onClick={() => setCleanseOpen(!cleanseOpen)} className="w-full flex items-center justify-between px-4 py-3 text-left transition hover:bg-blue-50/60" style={{ backgroundColor: "#EFF6FF" }}>
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                  <span className="text-[12px] font-bold" style={{ color: "#1D4ED8" }}>
                    ActionFit AI 자동 정제 방식
                  </span>
                  <span className="text-[11px] ml-1" style={{ color: "#60A5FA" }}>
                    쉼표·통화기호·단위를 자동으로 제거해
                    분석합니다.
                  </span>
                </div>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" strokeWidth="2.5" className="flex-shrink-0 transition-transform" style={{
                transform: cleanseOpen
                    ? "rotate(180deg)"
                    : "rotate(0deg)",
            }}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              {cleanseOpen && (<div className="px-4 pb-4 pt-3 bg-blue-50/30">
                  <div className="space-y-2 mb-4">
                    {[
                    "업로드한 원본 수치 데이터를 기준으로 분석 지표를 자동 계산합니다.",
                    "쉼표, 통화기호, 단위처럼 값의 의미가 변하지 않는 형식은 자동 정제됩니다.",
                    "단, 값의 의미를 판단해야 하는 항목은 사용자의 확인이 필요합니다.",
                ].map((t) => (<div key={t} className="flex items-start gap-2 text-[11px]" style={{ color: "#1D4ED8" }}>
                        <svg className="mt-0.5 flex-shrink-0" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        {t}
                      </div>))}
                  </div>

                  {/* Compact examples inside accordion */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-blue-100 bg-white p-3">
                      <p className="text-[11px] font-bold text-blue-700 mb-2">
                        자동 정제 가능 예시
                      </p>
                      <div className="space-y-1.5">
                        {[
                    ["1,234", "1234"],
                    ["₩45,000", "45000"],
                    ["45,000원", "45000"],
                    ["3건", "3"],
                ].map(([from, to]) => (<div key={from} className="flex items-center gap-1.5 text-[11px]">
                            <code className="bg-slate-50 text-slate-500 px-1.5 py-0.5 rounded border border-slate-200 font-mono">
                              {from}
                            </code>
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" strokeWidth="2">
                              <polyline points="9 18 15 12 9 6"/>
                            </svg>
                            <code className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200 font-mono">
                              {to}
                            </code>
                          </div>))}
                      </div>
                    </div>
                    <div className="rounded-lg border bg-white p-3" style={{ borderColor: "#FDE68A" }}>
                      <p className="text-[11px] font-bold mb-2" style={{ color: "#B45309" }}>
                        확인 필요 예시
                      </p>
                      <div className="space-y-2 mb-3">
                        {[
                    {
                        value: "N/A / 없음 / 빈칸",
                        desc: "0인지 누락인지 확인 필요",
                    },
                    {
                        value: "28.500",
                        desc: "소수점인지 천 단위인지 확인 필요",
                    },
                ].map((item) => (<div key={item.value} className="flex items-center gap-2 text-[11px] leading-relaxed">
                            <span className="inline-flex items-center px-2 py-1 rounded-md border bg-white font-bold whitespace-nowrap" style={{
                        color: "#B45309",
                        borderColor: "#FDE68A",
                    }}>
                              {item.value}
                            </span>

                            <span className="font-semibold" style={{ color: "#B45309" }}>
                              →
                            </span>

                            <span className="font-semibold" style={{ color: "#FF9800" }}>
                              {item.desc}
                            </span>
                          </div>))}
                      </div>
                      <div className="border-t pt-2 space-y-1" style={{ borderColor: "#FDE68A" }}>
                      <p className="text-[11px] leading-relaxed font-medium" style={{ color: "#B45309" }}>
                        노출수에 <strong>3.5%</strong> → 필수 컬럼 ·{" "}
                        <strong>확인 필요</strong>
                      </p>
                      <p className="text-[11px] leading-relaxed font-medium" style={{ color: "#B45309" }}>
                        클릭률에 <strong>3.5%</strong> → 필요없는 컬럼 ·{" "}
                        <strong>참고용 처리</strong>
                      </p>
                    </div>
                    </div>
                  </div>
                </div>)}
            </div>

            {/* Detailed validation rows */}
            <div className="space-y-2 mb-5">
              {SUMMARY_VALIDATION.map((v) => (<div key={v.label} className={`flex items-start gap-3.5 p-3 rounded-lg border ${v.ok ? "bg-emerald-50/40 border-emerald-100" : "border"}`} style={!v.ok
                    ? {
                        backgroundColor: "#FFFBEB",
                        borderColor: "#FDE68A",
                    }
                    : {}}>
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${v.ok ? "bg-emerald-100" : ""}`} style={!v.ok
                    ? { backgroundColor: "#FEF3C7" }
                    : {}}>
                    {v.ok ? (<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>) : (<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="3" strokeLinecap="round">
                        <path d="M12 9v4M12 17h.01"/>
                      </svg>)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-medium text-slate-700">
                        {v.label}
                      </span>
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${v.ok ? "bg-emerald-100 text-emerald-700" : ""}`} style={!v.ok
                    ? {
                        backgroundColor: "#FEF3C7",
                        color: "#B45309",
                    }
                    : {}}>
                        {v.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {v.desc}
                    </p>
                  </div>
                </div>))}
            </div>

            {/* Card-bottom status */}
            <div className="border-t border-slate-100 pt-5">
              <div className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border ${hasError ? "bg-rose-50 border-rose-200" : hasWarn ? "border" : "bg-emerald-50 border-emerald-100"}`} style={hasWarn && !hasError ? { backgroundColor: "#FFFBEB", borderColor: "#FDE68A" } : {}}>
                {hasError ? (<svg className="flex-shrink-0" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#e11d48" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>) : hasWarn ? (<svg className="flex-shrink-0" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>) : (<svg className="flex-shrink-0" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>)}
                <p className={`text-xs font-medium ${hasError ? "text-rose-700" : "text-slate-600"}`} style={hasWarn && !hasError ? { color: "#B45309" } : {}}>
                {hasError
                  ? "필수 컬럼 누락 또는 필수값 문제가 있어 분석을 시작할 수 없습니다. 파일을 수정한 뒤 다시 업로드해주세요."
                  : hasWarn
                    ? "확인 필요 항목이 있지만 필수 오류는 없어 분석을 진행할 수 있습니다. 단, 일부 지표는 보수적으로 계산될 수 있습니다."
                    : "자동 정제된 값은 분석에 반영됩니다. 지금 바로 분석을 시작할 수 있습니다."}
                </p>
              </div>
            </div>
          </div>
        </div>)}

        {/* Back link */}
        <div className="flex items-center pb-2">
          <button onClick={() => setScreen("main")} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            이전 단계로 돌아가기
          </button>
        </div>
      </div>
    </>);
}

function InspectionModal({ result, onClose, setScreen, setSelectedFile }) {
      // 컴포넌트 내부
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const clientUuid = getClientUuid();
    // 분석 시작 버튼 클릭 핸들러
    const handleAnalyze = async () => {
      if (!canAnalyze || !result?.cleanedFileUrl) return;

      setIsAnalyzing(true);
      try {
        // URL로부터 파일 데이터를 Blob 형태로 가져오기
        const response = await fetch(result.cleanedFileUrl);
        const blob = await response.blob();

        // 백엔드 전송을 위한 FormData 생성
        const formData = new FormData();
        const file = new File([blob], result.cleanedFileName || "cleaned_file.xlsx", {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        });
        
        formData.append("files", file);
        formData.append("client_uuid", clientUuid);

        console.log("🚀 백엔드로 전송 시작:", {
          url: `${API_BASE_URL}/score/evaluate-multiple`,
          clientUuid: clientUuid,
          fileName: file.name,
          fileSize: file.size
        });

        // FastAPI 백엔드로 요청 보내기
        const apiResponse = await fetch(`${API_BASE_URL}/score/evaluate-multiple`, {
          method: "POST",
          body: formData,
        });

        const responseText = await apiResponse.text();

        let data = null;

        try {
          data = responseText ? JSON.parse(responseText) : null;
        } catch (error) {
          data = responseText;
        }

        if (!apiResponse.ok) {
          console.error("분석 요청 실패:", {
            status: apiResponse.status,
            statusText: apiResponse.statusText,
            data,
          });

          throw new Error(
            typeof data === "string"
              ? `분석 요청 실패: ${apiResponse.status} ${data}`
              : `분석 요청 실패: ${apiResponse.status} ${
                  data?.detail || apiResponse.statusText
                }`
          );
        }

        console.log("분석 결과:", data);

        setSelectedFile(result.cleanedFileName);
        setScreen("results");


      } catch (error) {
        console.error("에러 발생:", error);
        alert(
          `파일 분석 중 오류가 발생했습니다.\n\n${
            error.message || "원인을 확인할 수 없습니다."
          }`
        );
      } finally {
        setIsAnalyzing(false);
      }
    };

  const [filter, setFilter] = useState("전체");
  const [page, setPage] = useState(1);
  const [selectedIssue, setSelectedIssue] = useState(result.issues[0] || null);
  
  const tableScrollRef = useRef(null);
  const cellRefs = useRef({});
  const headerRefs = useRef({});
  
  const [activeCellKey, setActiveCellKey] = useState("");
  const [activeColumn, setActiveColumn] = useState("");

  const pageSize = 20;
  const totalPages = Math.max(1, Math.ceil(result.rows.length / pageSize));
  const pageRows = result.rows.slice((page - 1) * pageSize, page * pageSize);

function getIssueRowNumber(issue) {
  const n = Number(issue?.rowIndex);
  return Number.isFinite(n) ? n : null;
}

function getPageByExcelRow(rowNumber) {
  const targetIndex = result.rows.findIndex(
    (row) => Number(row.__rowIndex) === Number(rowNumber)
  );

  if (targetIndex === -1) return 1;

  return Math.floor(targetIndex / pageSize) + 1;
}



function scrollToColumn(column) {
  if (!column) return;

  setActiveColumn(column);

  setTimeout(() => {
    const targetHeader = headerRefs.current[column];

    if (!targetHeader) return;

    targetHeader.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, 80);
}

function getCellKey(rowIndex, column) {
  return `${rowIndex}__${column}`;
}

function handleSelectIssue(issue) {
  setSelectedIssue(issue);

  const rowNumber = getIssueRowNumber(issue);
  const column = issue?.column;

  setActiveCellKey("");
  setActiveColumn("");

  // 행 번호가 있는 이슈: 해당 셀로 이동
  if (rowNumber && column) {
    const nextPage = getPageByExcelRow(rowNumber);
    setPage(nextPage);
    setActiveCellKey(getCellKey(rowNumber, column));
    setActiveColumn(column);
    return;
  }

  // rowIndex가 "전체", "컬럼"인 이슈: 해당 컬럼으로 이동
  if (column) {
    scrollToColumn(column);
  }
}

useEffect(() => {
  if (!selectedIssue) return;

  const rowNumber = getIssueRowNumber(selectedIssue);
  const column = selectedIssue.column;

  if (!rowNumber || !column) return;

  const cellKey = getCellKey(rowNumber, column);

  const timer = setTimeout(() => {
    const targetCell = cellRefs.current[cellKey];

    if (!targetCell) {
      scrollToColumn(column);
      return;
    }

    targetCell.scrollIntoView({
      behavior: "smooth",
      block: "center",
      inline: "center",
    });
  }, 100);

  return () => clearTimeout(timer);
}, [selectedIssue, page]);

  const filteredIssues = result.issues.filter((issue) => {
    if (filter === "전체") return true;
    if (filter === "자동 정제") return issue.type === "auto_cleaned";
    if (filter === "확인 필요") return issue.type === "need_check";
    if (filter === "필수 오류") return issue.type === "required_error";
    if (filter === "참고") return issue.type === "reference";
    return true;
  });

  const issueCounts = {
    전체: result.issues.length,
    "자동 정제": result.issues.filter((i) => i.type === "auto_cleaned").length,
    "확인 필요": result.issues.filter((i) => i.type === "need_check").length,
    "필수 오류": result.issues.filter((i) => i.type === "required_error").length,
    참고: result.issues.filter((i) => i.type === "reference").length,
  };

  function getCellIssue(rowIndex, column) {
    return result.issues.find(
      (issue) => issue.rowIndex === rowIndex && issue.column === column
    );
  }

  function isReferenceColumn(column) {
    return result.referenceColumns.includes(column);
  }

  function isGeneratedColumn(column) {
    return result.generatedColumns?.includes(column);
  }

  function issueClass(issue, column) {
    if (isGeneratedColumn(column)) {
      return "bg-blue-50 text-blue-700 ring-1 ring-blue-100";
    }
  
    if (isReferenceColumn(column)) {
      return "bg-slate-100 text-slate-400";
    }
  
    if (!issue) return "";
  
    if (issue.type === "auto_cleaned") {
      return "bg-blue-50 text-blue-700 ring-1 ring-blue-200";
    }
  
    if (issue.type === "need_check") {
      return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
    }
  
    if (issue.type === "required_error") {
      return "bg-rose-50 text-rose-700 ring-1 ring-rose-200";
    }
  
    return "";
  }


  const canAnalyze = result.canAnalyze;

  const visibleHeaders = result.headers.filter(
    (header) => header !== "__rowIndex"
  );
  
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-3">
      <div className="bg-white w-full max-w-[96vw] h-[94vh] rounded-2xl shadow-xl overflow-hidden flex flex-col">
        <div className="flex items-start justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-800">
              데이터 자동 정제 및 검수 결과
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {result.fileName} · {result.rows.length}행 · {result.headers.length}개 컬럼
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            ×
          </button>
        </div>

        <div className="flex-1 grid grid-cols-[1.45fr_0.8fr] min-h-0">
          <div className="min-w-0 min-h-0 border-r border-slate-100 flex flex-col">
            <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-2">
              {["전체", "자동 정제", "확인 필요", "필수 오류", "참고"].map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => {
                    setFilter(item);
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                    filter === item
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-slate-500 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {item}
                  <span className="ml-1 text-[10px] opacity-80">
                    {issueCounts[item] ?? 0}
                  </span>
                </button>
              ))}
            </div>

            <div ref={tableScrollRef} className="flex-1 min-h-0 overflow-auto">
              <table className="min-w-full text-xs">
              <thead className="sticky top-0 z-10 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold border-b border-slate-100 sticky left-0 bg-slate-50 z-20">
                    행
                  </th>

                  {visibleHeaders.map((header) => {
                    const isActiveColumn = activeColumn === header;
                    const generated = isGeneratedColumn(header);
                    const reference = isReferenceColumn(header);

                    return (
                      <th
                        key={header}
                        ref={(el) => {
                          if (el) {
                            headerRefs.current[header] = el;
                          }
                        }}
                        className={`px-3 py-2 text-left font-semibold border-b border-slate-100 whitespace-nowrap ${
                          generated
                            ? "bg-blue-50 text-blue-700"
                            : reference
                              ? "bg-slate-100 text-slate-400"
                              : ""
                        } ${isActiveColumn ? "ring-2 ring-blue-400" : ""}`}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>{header}</span>

                          {generated && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">
                              생성
                            </span>
                          )}

                          {reference && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-500 font-bold">
                              참고
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody>
                {pageRows.map((row, idx) => {
                  const realRowIndex =
                    row.__rowIndex ?? (page - 1) * pageSize + idx + 2;

                  return (
                    <tr key={realRowIndex} className="border-b border-slate-50">
                      <td className="px-3 py-2 text-slate-400 bg-slate-50 sticky left-0 z-10">
                        {realRowIndex}
                      </td>

                      {visibleHeaders.map((header) => {
                        const issue = getCellIssue(realRowIndex, header);
                        const reference = isReferenceColumn(header);
                        const generated = isGeneratedColumn(header);

                        const cellKey = getCellKey(realRowIndex, header);
                        const isActiveCell = activeCellKey === cellKey;
                        const isActiveColumn = activeColumn === header;

                        return (
                          <td
                            key={header}
                            ref={(el) => {
                              if (el) {
                                cellRefs.current[cellKey] = el;
                              }
                            }}
                            onClick={() => {
                              if (issue) {
                                handleSelectIssue(issue);
                                return;
                              }

                              if (reference || generated) {
                                const columnIssue = result.issues.find(
                                  (i) =>
                                    i.column === header &&
                                    (i.type === "reference" ||
                                      i.type === "auto_cleaned")
                                );

                                if (columnIssue) {
                                  handleSelectIssue(columnIssue);
                                } else {
                                  scrollToColumn(header);
                                }
                              }
                            }}
                            className={`px-3 py-2 whitespace-nowrap cursor-pointer transition ${
                              isActiveCell
                                ? "ring-2 ring-blue-400 bg-blue-50 font-bold"
                                : ""
                            } ${
                              !isActiveCell && isActiveColumn ? "bg-blue-50" : ""
                            } ${issueClass(issue, header)}`}
                          >
                            <div className="flex items-center gap-1.5">
                              <span>{String(row[header] ?? "")}</span>

                              {issue?.type === "auto_cleaned" && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">
                                  정제
                                </span>
                              )}

                              {issue?.type === "need_check" && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-bold">
                                  확인
                                </span>
                              )}

                              {reference && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-500 font-bold">
                                  참고
                                </span>
                              )}

                              {generated && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">
                                  생성
                                </span>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>

            <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between">
              <p className="text-xs text-slate-400">
                {(page - 1) * pageSize + 1}-
                {Math.min(page * pageSize, result.rows.length)} / {result.rows.length}행
              </p>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-500 disabled:opacity-40"
                >
                  이전
                </button>

                <span className="px-3 py-1.5 text-xs text-slate-500">
                  {page} / {totalPages}
                </span>

                <button
                  type="button"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-500 disabled:opacity-40"
                >
                  다음
                </button>
              </div>
            </div>
          </div>

          <div className="min-w-0 flex flex-col">
            <div className="px-5 py-4 border-b border-slate-100">
              <p className="text-xs font-bold text-slate-700 mb-3">
                검수 항목 ({filteredIssues.length}건)
              </p>
              {canAnalyze && result.needCheckCount > 0 && (
                <div className="mb-3 rounded-xl border border-blue-100 bg-blue-50 px-3 py-2.5">
                  <div className="flex items-start gap-2">
                    <div className="mt-0.5 w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center text-[10px] font-bold text-blue-600 flex-shrink-0">
                      i
                    </div>
                    <p className="text-[11px] text-blue-700 leading-relaxed">
                      확인 필요 항목이 있지만 필수 오류는 없어 분석을 진행할 수 있습니다.
                      다만 해당 값은 보수적으로 계산되거나 일부 지표 계산이 제한될 수 있습니다.
                    </p>
                  </div>
                </div>
              )}

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {filteredIssues.length === 0 ? (
                  <p className="text-xs text-slate-400">
                    해당 항목이 없습니다.
                  </p>
                ) : (
                  filteredIssues.map((issue) => (
                    <button
                      key={issue.id}
                      type="button"
                      onClick={() => handleSelectIssue(issue)}
                      className={`w-full text-left rounded-lg border px-3 py-2 transition ${
                        selectedIssue?.id === issue.id
                          ? "border-blue-300 bg-blue-50"
                          : "border-slate-100 bg-white hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            issue.type === "auto_cleaned"
                              ? "bg-blue-100 text-blue-700"
                              : issue.type === "need_check"
                              ? "bg-amber-100 text-amber-700"
                              : issue.type === "required_error"
                              ? "bg-rose-100 text-rose-700"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {typeLabel(issue.type)}
                        </span>

                        <span className="text-[11px] text-slate-400">
                          {issue.rowIndex}행 · {issue.column}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                        {issue.message}
                      </p>
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="flex-1 px-5 py-4 overflow-y-auto">
              <p className="text-xs font-bold text-slate-700 mb-3">
                상세 정보
              </p>

              {selectedIssue ? (
                <div className="rounded-xl border border-slate-100 overflow-hidden">
                  {[
                    ["위치", `${selectedIssue.rowIndex}행 · ${selectedIssue.column}`],
                    ["원본 값", String(selectedIssue.originalValue ?? "")],
                    ["처리 결과", String(selectedIssue.cleanedValue ?? "")],
                    ["처리 유형", typeLabel(selectedIssue.type)],
                    ["처리 설명", selectedIssue.message],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="grid grid-cols-[100px_1fr] border-b border-slate-100 last:border-b-0"
                    >
                      <div className="bg-slate-50 px-3 py-3 text-xs font-semibold text-slate-500">
                        {label}
                      </div>
                      <div className="px-3 py-3 text-xs text-slate-700">
                        {value}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  왼쪽 셀 또는 검수 항목을 선택하면 상세 정보가 표시됩니다.
                </p>
              )}
            </div>

            <div className="px-5 py-4 border-t border-slate-100 bg-white sticky bottom-0 z-20">
              <div className="flex items-center justify-between gap-3">
                <a
                  href={result.cleanedFileUrl}
                  download={result.cleanedFileName}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  정제 파일 다운로드
                </a>

                <button
                  type="button"
                  disabled={!canAnalyze || isAnalyzing || !clientUuid}
                  onClick={handleAnalyze}
                  className={`px-5 py-2 rounded-lg text-xs font-bold transition ${
                    canAnalyze && !isAnalyzing && clientUuid
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-slate-100 text-slate-400 cursor-not-allowed"
                  }`}
                >
                  {isAnalyzing ? "분석 중..." : "분석 시작"}
                </button>
              </div>
            </div>

              {!canAnalyze && (
                <p className="text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2 mt-3">
                  필수 오류가 있어 분석을 시작할 수 없습니다.
                  필수 컬럼 또는 필수값을 수정한 뒤 다시 업로드해주세요.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
  );
}
