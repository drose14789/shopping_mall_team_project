import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");

const INPUT_PATH = path.join(ROOT_DIR, "src", "data", "preSaleBaseRows.json");
const OUTPUT_PATH = path.join(ROOT_DIR, "src", "data", "preSaleBaseSummary.json");

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function safeRate(numerator, denominator) {
  const n = toNumber(numerator);
  const d = toNumber(denominator);

  if (!d || d === 0) return null;

  return Number(((n / d) * 100).toFixed(4));
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

  return Number(nums[mid].toFixed(2));
}

function average(values) {
  const nums = values.map(Number).filter((v) => Number.isFinite(v));

  if (nums.length === 0) return 0;

  return Number((nums.reduce((sum, v) => sum + v, 0) / nums.length).toFixed(2));
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

function getRawMetrics(row) {
  const clickRate = safeRate(row.clicks, row.exposure) ?? 0;
  const wishRate = safeRate(row.wishUsers, row.detailVisits) ?? 0;
  const cartRate = safeRate(row.cartUsers, row.detailVisits) ?? 0;
  const purchaseRate = safeRate(row.orderCount, row.detailVisits) ?? 0;
  const returnRate = safeRate(row.returnCount, row.orderCount) ?? 0;
  const roas = safeRate(row.orderAmount, row.adCost);

  return {
    clickRate,
    wishRate,
    cartRate,
    purchaseRate,
    returnRate,
    returnStability: Math.max(0, 100 - returnRate),
    roas: roas === null ? null : roas,
    roasValid: roas !== null && toNumber(row.adCost) > 0,
  };
}

function buildGroupSummary(group) {
  const rawRows = group.rows.map(getRawMetrics);

  const clickRates = rawRows.map((r) => r.clickRate);
  const wishRates = rawRows.map((r) => r.wishRate);
  const cartRates = rawRows.map((r) => r.cartRate);
  const purchaseRates = rawRows.map((r) => r.purchaseRate);
  const returnStabilities = rawRows.map((r) => r.returnStability);
  const roasValues = rawRows.filter((r) => r.roasValid).map((r) => r.roas);

  const companies = new Set(group.rows.map((r) => r.company).filter(Boolean));
  const sourceFiles = new Set(
    group.rows.map((r) => r.sourceFileName).filter(Boolean)
  );

  return {
    season: group.season,
    category: group.category,
    sampleCount: group.rows.length,
    companyCount: companies.size,
    sourceFileCount: sourceFiles.size,
    roasValidCount: roasValues.length,
    roasInvalidCount: group.rows.length - roasValues.length,

    rawMedian: {
      clickRate: median(clickRates),
      wishRate: median(wishRates),
      cartRate: median(cartRates),
      purchaseRate: median(purchaseRates),
      returnStability: median(returnStabilities),
      roas: median(roasValues),
    },

    rawAverage: {
      clickRate: average(clickRates),
      wishRate: average(wishRates),
      cartRate: average(cartRates),
      purchaseRate: average(purchaseRates),
      returnStability: average(returnStabilities),
      roas: average(roasValues),
    },
  };
}

function main() {
  const rows = JSON.parse(fs.readFileSync(INPUT_PATH, "utf-8"));

  const groupMap = new Map();

  rows.forEach((row) => {
    const season = row.season;
    const category = normalizeCategory(row.category);

    if (!season || !category || category === "미분류") return;

    const key = `${season}__${category}`;

    if (!groupMap.has(key)) {
      groupMap.set(key, {
        season,
        category,
        rows: [],
      });
    }

    groupMap.get(key).rows.push(row);
  });

  const summaries = Array.from(groupMap.values()).map(buildGroupSummary);

  const metricBase = {
    clickRate: summaries.map((s) => s.rawMedian.clickRate),
    wishRate: summaries.map((s) => s.rawMedian.wishRate),
    cartRate: summaries.map((s) => s.rawMedian.cartRate),
    purchaseRate: summaries.map((s) => s.rawMedian.purchaseRate),
    returnStability: summaries.map((s) => s.rawMedian.returnStability),
    roas: summaries.map((s) => s.rawMedian.roas).filter((v) => v > 0),
  };

  const scoredSummaries = summaries.map((summary) => {
    const metricScores = {
      clickScore: percentileScore(
        summary.rawMedian.clickRate,
        metricBase.clickRate
      ),
      wishScore: percentileScore(summary.rawMedian.wishRate, metricBase.wishRate),
      cartScore: percentileScore(summary.rawMedian.cartRate, metricBase.cartRate),
      purchaseScore: percentileScore(
        summary.rawMedian.purchaseRate,
        metricBase.purchaseRate
      ),
      returnStabilityScore: percentileScore(
        summary.rawMedian.returnStability,
        metricBase.returnStability
      ),
      roasScore:
        summary.rawMedian.roas > 0
          ? percentileScore(summary.rawMedian.roas, metricBase.roas)
          : 50,
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
      ...summary,
      metricScores,
      fitScore,
    };
  });

  const globalMetricScores = {
    clickScore: median(scoredSummaries.map((s) => s.metricScores.clickScore)),
    wishScore: median(scoredSummaries.map((s) => s.metricScores.wishScore)),
    cartScore: median(scoredSummaries.map((s) => s.metricScores.cartScore)),
    purchaseScore: median(
      scoredSummaries.map((s) => s.metricScores.purchaseScore)
    ),
    returnStabilityScore: median(
      scoredSummaries.map((s) => s.metricScores.returnStabilityScore)
    ),
    roasScore: median(scoredSummaries.map((s) => s.metricScores.roasScore)),
  };

  const result = {
    generatedAt: new Date().toISOString(),
    totalRows: rows.length,
    totalCombinations: scoredSummaries.length,
    globalMetricScores,
    rows: scoredSummaries.sort((a, b) => {
      if (a.season !== b.season) return a.season.localeCompare(b.season);
      return a.category.localeCompare(b.category);
    }),
    topCombinations: [...scoredSummaries]
      .sort((a, b) => b.fitScore - a.fitScore)
      .slice(0, 10),
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2), "utf-8");

  console.log(`완료: ${OUTPUT_PATH}`);
  console.log(`전체 상품 행: ${result.totalRows.toLocaleString()}개`);
  console.log(`시즌·카테고리 조합: ${result.totalCombinations}개`);
}

main();