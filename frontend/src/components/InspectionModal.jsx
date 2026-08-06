import React, { useState } from 'react';
import { 
    MOCK_ISSUES, 
    TABLE_ROWS, 
    PAGE_SIZE, 
    TABLE_COLS, 
    REFERENCE_ONLY_COLS, 
    STATUS_META 
} from '../constants/data';
import { actionBadge } from '../utils/helpers';
import { getDetailData } from '../utils/productDetailHelpers';


const API_BASE_URL = (
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000"
).replace(/\/$/, "");

// 같은 상품을 다시 열거나 React 개발 모드에서 Effect가 두 번 실행돼도
// 동일한 LLM 요청이 중복 실행되지 않도록 현재 브라우저 세션에서 캐시합니다.
const analysisSummaryCache = new Map();

function buildAnalysisPayload(product) {
    return {
        id: product?.id,
        product_id: product?.product_id,
        product_name: product?.product_name,
        category: product?.category,
        quarter: product?.quarter,
        product_type: product?.product_type,
        total_score: product?.total_score,

        exposure_count: product?.exposure_count,
        click_count: product?.click_count,
        visit_count: product?.visit_count,
        wish_user_count: product?.wish_user_count,
        cart_user_count: product?.cart_user_count,
        order_count: product?.order_count,
        return_count: product?.return_count,
        ad_spend: product?.ad_spend,
        order_amount: product?.order_amount,
        unit_price: product?.unit_price,

        calc_click_rate: product?.calc_click_rate,
        calc_wish_conv: product?.calc_wish_conv,
        calc_cart_conv: product?.calc_cart_conv,
        calc_conv_rate: product?.calc_conv_rate,
        calc_return_stability: product?.calc_return_stability,
        calc_roas: product?.calc_roas,

        score_click_rate: product?.score_click_rate,
        score_wish_conv: product?.score_wish_conv,
        score_cart_conv: product?.score_cart_conv,
        score_conv_rate: product?.score_conv_rate,
        score_return_stability: product?.score_return_stability,
        score_roas: product?.score_roas,

        recommended_ad_spend: product?.recommended_ad_spend,
    };
}

export function InspectionModal({ onClose, setScreen }) {
    const [selected, setSelected] = useState(0);
    const [filterStatus, setFilterStatus] = useState("all");
    const [page, setPage] = useState(0);
    const [analyzing, setAnalyzing] = useState(false);
    function handleAnalyze() {
        setAnalyzing(true);
        setTimeout(() => { onClose(); setScreen("results"); }, 1800);
    }
    const filteredIssues = filterStatus === "all" ? MOCK_ISSUES : MOCK_ISSUES.filter(m => m.status === filterStatus);
    const filteredRows = filterStatus === "all"
        ? TABLE_ROWS
        : TABLE_ROWS.filter(({ r }) => MOCK_ISSUES.some(m => m.row === r && m.status === filterStatus));
    const totalRows = 187;
    const pageCount = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
    const pagedRows = filteredRows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
    const item = MOCK_ISSUES[selected] ?? MOCK_ISSUES[0];
    const meta = STATUS_META[item.status];
    const hasError = MOCK_ISSUES.some(m => m.status === "error");
    const hasWarn = MOCK_ISSUES.some(m => m.status === "warn");
    const statusCounts = { all: MOCK_ISSUES.length };
    for (const k of Object.keys(STATUS_META)) {
        statusCounts[k] = MOCK_ISSUES.filter(m => m.status === k).length;
    }
    // Pagination based on total rows (187), not just visible issue rows
    const totalPageCount = Math.ceil(totalRows / PAGE_SIZE);
    const pageStart = page * PAGE_SIZE + 1;
    const pageEnd = Math.min((page + 1) * PAGE_SIZE, totalRows);
    return (<div className="fixed inset-0 z-50 flex items-center justify-center p-3">
      <div className="absolute inset-0 bg-slate-900/45 backdrop-blur-sm" onClick={onClose}/>

      <div className="relative bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-100" style={{ width: "90%", height: "91vh", maxWidth: 1480 }}>
        {/* ── Modal header ── */}
        <div className="flex-shrink-0 flex items-center justify-between px-7 py-4 border-b border-slate-100 bg-slate-50/60">
          <div>
            <h2 className="font-bold text-slate-800 text-base">데이터 자동 정제 및 검수 결과</h2>
            <p className="text-xs text-slate-400 mt-0.5">상품성과_20260520.xlsx · {totalRows}행 · 10개 컬럼</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-slate-100 text-slate-400 transition">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* ── Filter chips ── */}
        <div className="flex-shrink-0 flex items-center gap-2 px-7 py-3 border-b border-slate-100 bg-white">
          <span className="text-[11px] text-slate-400 font-semibold flex-shrink-0 mr-1">필터</span>
          {[["all", "전체"]].concat(Object.entries(STATUS_META).map(([k, v]) => [k, v.label])).map(([k, label]) => {
            const count = statusCounts[k] ?? 0;
            const active = filterStatus === k;
            const sm = k !== "all" ? STATUS_META[k] : null;
            return (<button key={k} onClick={() => { setFilterStatus(k); setPage(0); }} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold border transition-all whitespace-nowrap ${active
                    ? sm ? `${sm.bg} ${sm.text} ${sm.border}` : "bg-blue-700 text-white border-blue-700"
                    : "bg-white text-slate-500 border-slate-200 hover:border-slate-300 hover:bg-slate-50"}`}>
                {label}
                <span className={`text-[10px] font-bold ${active && !sm ? "text-blue-200" : active ? "" : "text-slate-400"}`}>{count}</span>
              </button>);
        })}
          <span className="ml-auto text-[11px] text-slate-400 whitespace-nowrap">
            {totalRows}행 중 이슈 포함 행 <strong className="text-slate-600">{MOCK_ISSUES.length}개</strong> 표시
          </span>
        </div>

        {/* ── Body ── */}
        <div className="flex flex-1 overflow-hidden">

          {/* LEFT — table 56% */}
          <div className="flex flex-col border-r border-slate-100" style={{ width: "56%" }}>
            <div className="flex-1 overflow-auto">
              <table className="text-xs border-collapse" style={{ minWidth: "100%" }}>
                <thead className="sticky top-0 z-10">
                  <tr className="bg-slate-100 border-b border-slate-200">
                    <th className="px-3 py-2.5 text-left text-[10px] font-bold text-slate-400 w-10 flex-shrink-0 sticky left-0 bg-slate-100">#</th>
                    {TABLE_COLS.map(h => (<th key={h} className="px-3 py-2.5 text-left text-[10px] font-bold text-slate-500 whitespace-nowrap">{h}</th>))}
                  </tr>
                </thead>
                <tbody>
                  {pagedRows.map(({ r, cells }) => (<tr key={r} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                      <td className="px-3 py-3 text-slate-400 font-mono text-[10px] bg-slate-50 border-r border-slate-100 select-none sticky left-0">{r}</td>
                      {cells.map((cell, ci) => {
                const colName = TABLE_COLS[ci];
                const flag = MOCK_ISSUES.find((m) => m.row === r && m.col === colName);
                const issueIdx = flag ? MOCK_ISSUES.indexOf(flag) : -1;
                const isReferenceOnlyCol = REFERENCE_ONLY_COLS.includes(colName);
                const bg = flag
                    ? STATUS_META[flag.status].cellBg
                    : isReferenceOnlyCol
                        ? STATUS_META.optional.cellBg
                        : "transparent";
                const chipText = flag
                    ? flag.status === "clean"
                        ? "정제"
                        : flag.status === "optional"
                            ? "참고"
                            : flag.status === "warn"
                                ? "확인"
                                : "오류"
                    : isReferenceOnlyCol
                        ? "참고"
                        : "";
                const chipMeta = flag
                    ? STATUS_META[flag.status]
                    : isReferenceOnlyCol
                        ? STATUS_META.optional
                        : null;
                return (<td key={ci} className={`px-3 py-3 whitespace-nowrap font-mono ${flag ? "cursor-pointer" : "text-slate-600"}`} style={{ backgroundColor: bg }} onClick={() => {
                        if (issueIdx >= 0)
                            setSelected(issueIdx);
                    }}>
                            <span className={flag || isReferenceOnlyCol
                        ? "font-semibold text-slate-800"
                        : ""}>
                              {cell}
                            </span>

                            {chipMeta && (<span className={`ml-1.5 text-[9px] font-bold px-1 py-0.5 rounded ${chipMeta.bg} ${chipMeta.text}`}>
                                {chipText}
                              </span>)}
                          </td>);
            })}
                    </tr>))}
                </tbody>
              </table>
            </div>

            {/* Pagination — based on totalRows */}
            <div className="flex-shrink-0 flex items-center justify-between px-6 py-3 border-t border-slate-100 bg-slate-50/50">
              <p className="text-[11px] text-slate-400">
                {pageStart}–{pageEnd} / <strong className="text-slate-600">{totalRows}</strong>행
              </p>
              <div className="flex items-center gap-1">
                <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${page === 0
            ? "text-slate-300 border-slate-150 cursor-not-allowed"
            : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                  이전
                </button>
                {Array.from({ length: Math.min(totalPageCount, 5) }, (_, i) => (<button key={i} onClick={() => setPage(i)} className={`w-7 h-7 rounded-lg text-[11px] font-semibold transition ${page === i ? "bg-blue-600 text-white shadow-sm" : "text-slate-500 hover:bg-slate-100 border border-slate-200"}`}>{i + 1}</button>))}
                {totalPageCount > 5 && <span className="text-slate-400 text-[11px] px-1">…</span>}
                <button onClick={() => setPage(p => Math.min(totalPageCount - 1, p + 1))} disabled={page >= totalPageCount - 1} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${page >= totalPageCount - 1
            ? "text-slate-300 border-slate-150 cursor-not-allowed"
            : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                  다음
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT — 44% */}
          <div className="flex flex-col overflow-hidden" style={{ width: "44%" }}>

            {/* ── Issue list (top 42%) ── */}
            <div className="flex flex-col border-b border-slate-100" style={{ height: "42%" }}>
              <div className="flex-shrink-0 flex items-center justify-between px-5 pt-4 pb-2">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">검수 항목 ({filteredIssues.length}건)</p>
              </div>
              <div className="flex-1 overflow-y-auto px-4 pb-3 space-y-1">
                {filteredIssues.map((m, i) => {
            const realIdx = MOCK_ISSUES.indexOf(m);
            const mt = STATUS_META[m.status];
            return (<button key={i} onClick={() => setSelected(realIdx)} className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs transition-all border ${selected === realIdx
                    ? "bg-blue-50 border-blue-200 shadow-sm"
                    : "hover:bg-slate-50 border-transparent hover:border-slate-200"}`}>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${mt.bg} ${mt.text} border ${mt.border} flex-shrink-0 whitespace-nowrap`}>
                        {mt.label}
                      </span>
                      <span className="text-slate-700 font-semibold whitespace-nowrap">{m.row}행</span>
                      <span className="text-slate-400 text-[10px]">·</span>
                      <span className="text-slate-500">{m.col}</span>
                      <code className="ml-auto font-mono text-slate-400 text-[10px] flex-shrink-0 truncate max-w-[90px] bg-slate-100 px-1.5 py-0.5 rounded">{m.raw}</code>
                    </button>);
        })}
              </div>
            </div>

            {/* ── Detail (bottom 58%) ── */}
            <div className="flex flex-col overflow-hidden" style={{ height: "58%" }}>
              <div className="flex-shrink-0 flex items-center gap-2.5 px-5 pt-4 pb-3 border-b border-slate-100">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">상세 정보</p>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold ${meta.bg} ${meta.text} ${meta.border}`}>
                  <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: "currentColor" }}/>
                  {meta.label}
                </span>
              </div>

              <div className="flex-1 overflow-y-auto px-5 py-4">
                <div className="space-y-0">
                  {/* Location */}
                  <div className="flex items-center gap-3 py-3 border-b border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0">위치</span>
                    <span className="text-sm font-bold text-slate-800">{item.row}행 · {item.col}</span>
                  </div>

                  {/* Raw value */}
                  <div className="flex items-center gap-3 py-3 border-b border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0">원본 값</span>
                    <code className="text-sm font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg font-mono">{item.raw}</code>
                  </div>

                  {/* Cleaned value */}
                  {item.cleaned && (<div className="flex items-center gap-3 py-3 border-b border-slate-100">
                      <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0">처리 결과</span>
                      <code className="text-sm font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg font-mono border border-blue-200">{item.cleaned}</code>
                    </div>)}

                  {/* Type */}
                  <div className="flex items-center gap-3 py-3 border-b border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0">처리 유형</span>
                    <span className={`text-xs font-semibold ${meta.text}`}>{meta.label}</span>
                  </div>

                  {/* Warn reason */}
                  {item.status === "warn" && item.reason && (<div className="flex items-start gap-3 py-3 border-b border-slate-100">
                      <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0 pt-0.5">확인 사유</span>
                      <p className="text-xs text-amber-700 leading-relaxed">{item.reason}</p>
                    </div>)}

                  {/* Note */}
                  <div className="flex items-start gap-3 py-3 border-b border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0 pt-0.5">
                      {item.status === "warn" ? "권장 처리" : item.status === "error" ? "처리 방법" : "처리 설명"}
                    </span>
                    <p className="text-xs text-slate-600 leading-relaxed">{item.note}</p>
                  </div>

                  {/* Reflect */}
                  <div className="flex items-center gap-3 py-3">
                    <span className="text-[11px] font-semibold text-slate-400 w-24 flex-shrink-0">분석 반영 여부</span>
                    <span className={`text-xs font-bold ${item.reflect === "반영 가능" ? "text-emerald-600" :
            item.reflect === "반영 불가" ? "text-rose-600" :
                item.reflect === "참고용" ? "text-slate-500" : "text-amber-600"}`}>{item.reflect}</span>
                  </div>
                </div>

                {/* Context callout */}
                {item.status === "warn" && (<div className="mt-4 rounded-xl p-3.5 border border-amber-200 bg-amber-50 flex items-start gap-2">
                    <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <p className="text-xs text-amber-800 leading-relaxed">원본 파일을 확인하고 값을 수정하거나, 정제 결과를 직접 검토해주세요.</p>
                  </div>)}
                {item.status === "error" && (<div className="mt-4 rounded-xl p-3.5 border border-rose-200 bg-rose-50 flex items-start gap-2">
                    <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#E11D48" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <p className="text-xs text-rose-800 leading-relaxed">원본 파일을 수정한 뒤 다시 업로드해야 분석을 진행할 수 있습니다.</p>
                  </div>)}
              </div>
            </div>
          </div>
        </div>

        {/* ── Footer ── */}
        <div className="flex-shrink-0 flex items-center justify-between px-7 py-3.5 border-t border-slate-100 bg-slate-50/60">
          {/* Left — interaction guide */}
          <div className="flex items-center gap-2 max-w-[55%]">
            <svg className="flex-shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className="text-[11px] text-slate-500 leading-snug">
              강조된 셀 또는 검수 항목을 클릭하면 오른쪽 상세 정보에서 <strong className="text-slate-700">원본 값과 처리 결과</strong>를 확인할 수 있습니다.
            </p>
          </div>

          {/* Right — buttons */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <button className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 border border-slate-200 bg-white hover:bg-slate-50 transition">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              정제 파일 다운로드
            </button>
            <button disabled={analyzing || hasError} className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold transition ${analyzing
            ? "bg-blue-400 text-white cursor-not-allowed"
            : hasError
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"}`} onClick={handleAnalyze}>
              {analyzing ? (<>
                  <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                  </svg>
                  분석 로딩 중…
                </>) : (<>
                  분석 시작
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                </>)}
            </button>
          </div>
        </div>
      </div>
    </div>);
}

export function ProductDetailModal({ product, onClose, setScreen }) {
    const [llmAnalysis, setLlmAnalysis] = useState(null);
    const [llmLoading, setLlmLoading] = useState(false);
    const [llmStarted, setLlmStarted] = useState(false);

    const d = {
        score: product.total_score,
        diagnosisType: product.product_type,
        actionSummary: `${product.product_type} 상품으로 분석되었습니다.`,
        recommendedAdBudget: `${Math.round(product.recommended_ad_spend).toLocaleString()}원`,

        scoreBars: [
            { label: "상품클릭률", score: product.score_click_rate },
            { label: "찜전환율", score: product.score_wish_conv },
            { label: "장바구니전환율", score: product.score_cart_conv },
            { label: "구매전환율", score: product.score_conv_rate },
            { label: "반품 안정성", score: product.score_return_stability },
            { label: "ROAS", score: product.score_roas }
        ],

        basicRawData: [
            { label: "상품명", value: product.product_name },
            { label: "카테고리", value: product.category },
            { label: "분기", value: product.quarter },
            { label: "상품ID", value: product.product_id }
        ],

        performanceRawData: [
            { label: "노출수", value: product.exposure_count?.toLocaleString() },
            { label: "클릭수", value: product.click_count?.toLocaleString() },
            { label: "상품 상세 방문", value: product.visit_count?.toLocaleString() },
            { label: "찜 유저수", value: product.wish_user_count?.toLocaleString() },
            { label: "장바구니 유저수", value: product.cart_user_count?.toLocaleString() },
            { label: "주문수", value: product.order_count?.toLocaleString() },
            { label: "반품수", value: product.return_count?.toLocaleString() },
            { label: "광고비", value: `${product.ad_spend?.toLocaleString()}원` },
            { label: "주문금액", value: `${product.order_amount?.toLocaleString()}원` },
            { label: "상품단가", value: `${product.unit_price?.toLocaleString()}원` }
        ],

        coachingFeedback: [
            {
                label: "상품클릭률",
                status: product.score_click_rate >= 70 ? "veryGood" : "weak",
                text: `상품 클릭률 ${product.calc_click_rate}% 기준으로 광고 유입 반응을 분석했습니다.`
            },
            {
                label: "찜전환율",
                status: product.score_wish_conv >= 70 ? "good" : "weak",
                text: `찜 전환율 ${product.calc_wish_conv}% 입니다.`
            },
            {
                label: "장바구니전환율",
                status: product.score_cart_conv >= 70 ? "good" : "weak",
                text: `장바구니 전환율 ${product.calc_cart_conv}% 입니다.`
            },
            {
                label: "구매전환율",
                status: product.score_conv_rate >= 70 ? "good" : "weak",
                text: `구매 전환율 ${product.calc_conv_rate}% 입니다.`
            },
            {
                label: "반품안정성",
                status: product.score_return_stability >= 70 ? "good" : "weak",
                text: `반품 안정성 ${product.calc_return_stability}% 입니다.`
            },
            {
                label: "ROAS",
                status: product.score_roas >= 70 ? "veryGood" : "weak",
                text: `ROAS ${product.calc_roas}% 기준 광고 효율을 분석했습니다.`
            }
        ],

        bottleneckCauses: [
            `${product.product_type} 진단 결과를 기반으로 주요 개선 포인트를 확인했습니다.`,
            `ROAS ${product.calc_roas}%와 구매 전환 데이터를 기준으로 광고 운영 방향을 판단했습니다.`
        ],

        actionItems: [
            { tag: "예산 테스트", text: "현재 광고 효율을 기준으로 단계적인 광고 예산 확대를 검토합니다." },
            { tag: "전환 점검", text: "구매 전환 및 반품 데이터를 지속적으로 확인합니다." }
        ],
    };

function parseMatchedReviews(value) {
  if (!value) return {};

  try {
    if (typeof value === "string") {
      return JSON.parse(value);
    }

    if (typeof value === "object") {
      return value;
    }

    return {};
  } catch (error) {
    console.error("matched_reviews 파싱 실패:", error, value);
    return {};
  }
}

function normalizeReviewData(rawReviewData) {
  if (
    rawReviewData &&
    !Array.isArray(rawReviewData) &&
    typeof rawReviewData === "object"
  ) {
    const normalized = {};

    Object.entries(rawReviewData).forEach(([keyword, reviews]) => {
      if (Array.isArray(reviews)) {
        normalized[keyword] = reviews;
      }
    });

    if (rawReviewData._meta) {
      normalized._meta = rawReviewData._meta;
    }

    return normalized;
  }

  if (Array.isArray(rawReviewData)) {
    return rawReviewData.reduce((acc, review) => {
      const keyword = review.keyword || review.keyword_name || "기타";

      if (!acc[keyword]) {
        acc[keyword] = [];
      }

      acc[keyword].push(review);
      return acc;
    }, {});
  }

  return {};
}

const rawReviewData = parseMatchedReviews(product.matched_reviews);
const reviewData = normalizeReviewData(rawReviewData);
const reviewMeta = reviewData?._meta || {};

const hasReviewData = Object.values(reviewData).some(
  (reviews) => Array.isArray(reviews) && reviews.length > 0
);

async function handleGenerateLlmAnalysis() {
  if (llmLoading) {
    return;
  }

  setLlmStarted(true);
  setLlmLoading(true);

  const cacheKey = String(
    product?.id ??
      product?.product_id ??
      product?.product_name ??
      "unknown-product"
  );

  try {
    let cached = analysisSummaryCache.get(cacheKey);

    if (!cached) {
      const request = fetch(`${API_BASE_URL}/analysis/summary`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(buildAnalysisPayload(product)),
      }).then(async (response) => {
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`AI 요약 API 오류: ${response.status} ${errorText}`);
        }

        const data = await response.json();

        const validDiagnosis =
          Array.isArray(data?.diagnosis_summary) &&
          data.diagnosis_summary.length > 0;

        const validActions =
          Array.isArray(data?.recommended_actions) &&
          data.recommended_actions.length > 0;

        if (!validDiagnosis || !validActions) {
          throw new Error("AI 요약 응답 형식이 올바르지 않습니다.");
        }

        return data;
      });

      analysisSummaryCache.set(cacheKey, request);
      cached = request;
    }

    const data = await cached;
    analysisSummaryCache.set(cacheKey, data);
    setLlmAnalysis(data);
  } catch (error) {
    analysisSummaryCache.delete(cacheKey);
    console.error("[analysis/summary] 생성 오류:", error);

    setLlmAnalysis({
      diagnosis_summary: d.bottleneckCauses,
      recommended_actions: d.actionItems,
      generated_by: "fallback",
    });
  } finally {
    setLlmLoading(false);
  }
}

const bottleneckCauses =
  llmAnalysis?.diagnosis_summary ?? d.bottleneckCauses;

const actionItems =
  llmAnalysis?.recommended_actions ?? d.actionItems;


    const scoreColor = d.score >= 80
        ? "#2563EB"
        : d.score >= 60
            ? "#059669"
            : d.score >= 40
                ? "#D97706"
                : "#E11D48";

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6" style={{
            backgroundColor: "rgba(15,23,42,0.45)",
            backdropFilter: "blur(3px)",
        }} onClick={(e) => {
            if (e.target === e.currentTarget)
                onClose();
        }}>
          <div className="bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden" style={{ width: "78%", height: "88vh", maxWidth: 1080 }}>
            {/* Modal header */}
            <div className="flex-shrink-0 flex items-start justify-between px-7 py-5 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2.5 mb-1.5">
                  <h2 className="text-base font-bold text-slate-800">
                    {product.name}
                  </h2>
                  <span className={`text-xs px-2 py-1 rounded-md border font-semibold ${actionBadge(d.diagnosisType)}`}>
                    {d.diagnosisType}
                  </span>
                  <span className="text-xs font-semibold text-rose-500">
                    총점 {d.score}점
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  카테고리: {product.cat} · 상품별 상세 진단
                </p>
              </div>
              <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition flex-shrink-0">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            {/* Modal body — scrollable */}
            <div className="flex-1 overflow-y-auto px-7 py-6 space-y-5">
              {/* 최종 진단 요약 */}
              <div className="rounded-2xl p-6 border border-blue-200 shadow-sm" style={{
                background: "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 55%, #EEF2FF 100%)",
              }}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider">
                        최종 진단 요약
                      </span>
                      <span className={`text-xs px-2.5 py-1 rounded-md border font-bold ${actionBadge(d.diagnosisType)}`}>
                        {d.diagnosisType}
                      </span>
                    </div>
                    <p className="text-base font-bold text-slate-800 leading-relaxed mb-2">
                      {d.actionSummary}
                    </p>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      클릭, 구매 전환, 찜 전환, 장바구니 전환, 구매 전환, 반품 안정성, ROAS의 점수를 함께 반영해
                      최종 진단 유형과 추천 액션을 산정했습니다.
                    </p>
                  </div>
                </div>
              </div>

              {/* 광고 추천 점수 + 권장 광고 운영 금액 */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      광고 추천 점수
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      같은 카테고리 백분위 점수와 가중치를 반영한 종합 추천 점수입니다.
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-blue-600 bg-blue-50 border border-blue-100 px-2 py-1 rounded-md">
                    매출 상관 가중치 기준
                  </span>
                </div>

                <div className="grid grid-cols-[150px_1fr_230px] gap-6 items-center">
                  <div className="flex flex-col items-center justify-center">
                    <div className="relative w-24 h-24">
                      <svg viewBox="0 0 36 36" className="w-24 h-24 -rotate-90">
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3"/>
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke={scoreColor} strokeWidth="3" strokeDasharray={`${d.score} ${100 - d.score}`} strokeLinecap="round"/>
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-2xl font-bold" style={{ color: scoreColor }}>
                          {d.score}
                        </span>
                        <span className="text-[9px] text-slate-400">
                          / 100
                        </span>
                      </div>
                    </div>
                    <p className="text-xs font-semibold mt-2" style={{ color: scoreColor }}>
                      광고 추천 점수
                    </p>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                          지표별 점수
                        </p>
                        <p className="text-[10px] text-slate-400 mt-1">
                          추천 점수 산정에 사용된 6개 지표입니다.
                        </p>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        백분위 · 가중치 기준
                      </p>
                    </div>
                    <div className="space-y-3">
                      {d.scoreBars.map((s) => (
                        <div key={s.label} className="grid grid-cols-[140px_1fr_44px] items-center gap-3">
                          <span className="text-xs text-slate-500">{s.label}</span>
                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all bg-blue-600" style={{ width: `${s.score}%` }}/>
                          </div>
                          <span className="text-xs font-bold text-slate-700 text-right">{s.score}점</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-blue-50/60 border border-blue-100 rounded-xl p-4 h-full flex flex-col justify-center">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs font-bold text-blue-700 uppercase tracking-wider">
                        권장 광고 운영 금액
                      </p>
                      <span className="text-[10px] font-bold text-blue-600 bg-white border border-blue-100 px-2 py-0.5 rounded-md">
                        참고 예산
                      </span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600 mb-2">
                      {d.recommendedAdBudget}
                    </p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      상품금액과 내부 광고 효율 계산값을 반영해 산정한 참고용 광고 운영 예산입니다.
                    </p>
                  </div>
                </div>
              </div>

              {/* 원본 데이터 요약 */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      원본 데이터 요약
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      사용자가 업로드한 파일의 원본 입력값을 확인합니다.
                    </p>
                  </div>
                  <p className="text-[10px] text-slate-400">업로드 파일 기준</p>
                </div>

                <div className="mb-4">
                  <p className="text-[11px] font-bold text-slate-400 mb-2">상품 기본 정보</p>
                  <div className="grid grid-cols-4 gap-3">
                    {d.basicRawData.map((m) => (
                      <div key={m.label} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-semibold mb-0.5">{m.label}</p>
                        <p className="text-sm font-bold text-slate-800 truncate">{m.value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-bold text-slate-400 mb-2">성과 원본 데이터</p>
                  <div className="grid grid-cols-5 gap-3">
                    {d.performanceRawData.map((m) => (
                      <div key={m.label} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-semibold mb-0.5">{m.label}</p>
                        <p className="text-sm font-bold text-slate-800 truncate">{m.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 퍼널 및 코칭 피드백 영역 */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      전환 퍼널 및 지표 피드백
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      상품의 구매 여정 단계별 흐름을 분석합니다.
                    </p>
                  </div>
                  <span className="text-[10px] font-semibold text-blue-600 bg-blue-50 border border-blue-100 px-2 py-1 rounded-md">
                    카테고리 비교 기준
                  </span>
                </div>

                {(() => {
                const getFeedback = (label) => d.coachingFeedback.find((item) => item.label === label);
                const getStatusMeta = (status) => {
                    if (status === "veryGood") {
                        return {
                            label: "매우 우수",
                            card: "bg-blue-50 border-blue-200",
                            title: "text-blue-700",
                            text: "text-blue-600",
                            softBadge: "bg-blue-50 text-blue-700 border-blue-200",
                            badge: "bg-blue-600 text-white",
                            dot: "bg-blue-500",
                            line: "bg-blue-300",
                            alert: false,
                        };
                    }
                    if (status === "good") {
                        return {
                            label: "양호",
                            card: "bg-emerald-50 border-emerald-200",
                            title: "text-emerald-700",
                            text: "text-emerald-600",
                            softBadge: "bg-emerald-50 text-emerald-700 border-emerald-200",
                            badge: "bg-emerald-600 text-white",
                            dot: "bg-emerald-500",
                            line: "bg-emerald-300",
                            alert: false,
                        };
                    }
                    if (status === "normal") {
                        return {
                            label: "보통",
                            card: "bg-slate-50 border-slate-200",
                            title: "text-slate-700",
                            text: "text-slate-500",
                            softBadge: "bg-slate-50 text-slate-600 border-slate-200",
                            badge: "bg-slate-200 text-slate-600",
                            dot: "bg-slate-400",
                            line: "bg-slate-300",
                            alert: false,
                        };
                    }
                    return {
                        label: "개선 필요",
                        card: "bg-amber-50 border-amber-300 ring-1 ring-amber-200",
                        title: "text-amber-800",
                        text: "text-amber-700",
                        softBadge: "bg-amber-50 text-amber-700 border-amber-200",
                        badge: "bg-amber-500 text-white",
                        dot: "bg-amber-500",
                        line: "bg-amber-300",
                        alert: true,
                    };
                };
                const funnelFeedbacks = [
                    {
                        step: "클릭",
                        metric: "상품클릭률",
                        desc: "노출 대비 클릭 반응",
                        feedback: getFeedback("상품클릭률"),
                    },
                    {
                        step: "찜",
                        metric: "찜전환율",
                        desc: "상세 방문 대비 관심 저장",
                        feedback: getFeedback("찜전환율"),
                    },
                    {
                        step: "장바구니",
                        metric: "장바구니전환율",
                        desc: "구매 전 관심 행동",
                        feedback: getFeedback("장바구니전환율"),
                    },
                    {
                        step: "구매",
                        metric: "구매전환율",
                        desc: "최종 구매 전환",
                        feedback: getFeedback("구매전환율"),
                    },
                ];
                const riskFeedbacks = [
                    {
                        metric: "반품안정성",
                        desc: "구매 이후 반품 리스크",
                        feedback: getFeedback("반품안정성"),
                    },
                    {
                        metric: "ROAS",
                        desc: "광고비 대비 매출 효율",
                        feedback: getFeedback("ROAS"),
                    },
                ];
                const weakSteps = funnelFeedbacks.filter((item) => item.feedback?.status === "weak");
                return (<div className="space-y-5">
                    {/* 퍼널 전환 지표 */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-[11px] font-bold text-slate-400">
                            퍼널 전환 지표
                          </p>
                          <p className="text-[10px] text-slate-400">
                            클릭 → 찜 → 장바구니 → 구매 흐름 기준
                          </p>
                        </div>

                        <div className="flex items-stretch gap-3">
                          {funnelFeedbacks.map((item, index) => {
                        const meta = getStatusMeta(item.feedback?.status);
                        return (<div key={item.metric} className="flex items-center gap-3 flex-1">
                                <div className={`relative flex-1 rounded-xl border p-4 transition ${meta.card}`}>

                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      <span className={`w-2 h-2 rounded-full ${meta.dot}`}/>
                                      <p className={`text-sm font-bold ${meta.title}`}>
                                        {item.step}
                                      </p>
                                    </div>

                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${meta.badge}`}>
                                      {meta.label}
                                    </span>
                                  </div>

                                  <p className="text-[11px] text-slate-400 font-semibold mb-1">
                                    {item.metric}
                                  </p>

                                  <p className="text-[10px] text-slate-400 mb-2">
                                    {item.desc}
                                  </p>

                                  <p className={`text-xs leading-relaxed font-medium ${meta.text}`}>
                                    {item.feedback?.text}
                                  </p>
                                </div>

                                {index < funnelFeedbacks.length - 1 && (<div className="flex-shrink-0 flex items-center">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2.5">
                                      <polyline points="9 18 15 12 9 6"/>
                                    </svg>
                                  </div>)}
                              </div>);
                    })}
                        </div>
                    </div>

                    {/* 병목 요약 */}
                    <div className={`rounded-xl border px-4 py-3 ${weakSteps.length > 0
                    ? "bg-amber-50 border-amber-200"
                    : "bg-blue-50 border-blue-100"}`}>
                        <div className="flex items-start gap-2.5">
                          <span className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${weakSteps.length > 0
                    ? "bg-amber-100 text-amber-700"
                    : "bg-blue-100 text-blue-700"}`}>
                            !
                          </span>

                          <p className={`text-xs leading-relaxed font-semibold ${weakSteps.length > 0
                    ? "text-amber-800"
                    : "text-blue-700"}`}>
                            {weakSteps.length > 0 ? (
                              <span>
                                병목 감지: <strong>{weakSteps.map((item) => item.step).join(", ")}</strong> 단계에서 상위 그룹 대비 낮은 전환 흐름이 확인됩니다.
                              </span>
                            ) : (
                              <span>
                                현재 퍼널 흐름은 전반적으로 안정적이며, 급격한 이탈 구간은 크지 않습니다.
                              </span>
                            )}
                          </p>
                        </div>
                    </div>

                    {/* 광고·리스크 보조 지표 */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-[11px] font-bold text-slate-400">
                            광고·리스크 보조 지표
                          </p>
                          <p className="text-[10px] text-slate-400">
                            광고 확대 판단 시 함께 확인하는 지표
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          {riskFeedbacks.map((item) => {
                        const meta = getStatusMeta(item.feedback?.status);
                        return (<div key={item.metric} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                                <div className="flex items-start justify-between gap-3 mb-3">
                                  <div>
                                    <p className="text-sm font-bold text-slate-700">
                                      {item.metric}
                                    </p>
                                    <p className="text-[11px] text-slate-400 mt-1">
                                      {item.desc}
                                    </p>
                                  </div>

                                  <span className={`text-[10px] font-bold px-2 py-1 rounded-md border whitespace-nowrap ${meta.softBadge}`}>
                                    {meta.label}
                                  </span>
                                </div>

                                <p className="text-xs leading-relaxed font-medium text-slate-600">
                                  {item.feedback?.text}
                                </p>
                              </div>);
                    })}
                        </div>
                    </div>
                </div>);
            })()}
              </div>

              {/* 진단 근거 요약 + 추천 액션 */}
              <div className="flex items-center justify-between gap-4 rounded-xl border border-blue-100 bg-blue-50/40 px-5 py-4">
                <div>
                  <p className="text-xs font-bold text-blue-700 uppercase tracking-wider">
                    AI 상품 운영 진단
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    버튼을 누르면 현재 상품의 분석 지표를 기반으로 진단 근거와 추천 액션을 생성합니다.
                  </p>
                </div>

                {!llmStarted ? (
                  <button
                    type="button"
                    onClick={handleGenerateLlmAnalysis}
                    className="flex-shrink-0 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition hover:bg-blue-700"
                  >
                    AI 진단 생성
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </button>
                ) : llmLoading ? (
                  <div className="flex-shrink-0 inline-flex items-center gap-2 rounded-lg bg-blue-100 px-4 py-2.5 text-xs font-bold text-blue-700">
                    <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                    </svg>
                    AI 진단 생성 중…
                  </div>
                ) : (
                  <span className="flex-shrink-0 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-[11px] font-bold text-emerald-700">
                    AI 진단 생성 완료
                  </span>
                )}
              </div>

              <div className="grid grid-cols-[0.9fr_1.1fr] gap-4">
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                  <div className="mb-3">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      진단 근거 요약
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      지표 해석 결과를 바탕으로 이 유형으로 분류된 이유를 요약합니다.
                    </p>
                  </div>

                  <div className="space-y-2.5">
                    {!llmStarted ? (
                      <div className="rounded-lg bg-slate-50 border border-dashed border-slate-200 px-3 py-5 text-center">
                        <p className="text-xs text-slate-500">
                          위의 <strong className="text-blue-600">AI 진단 생성</strong> 버튼을 눌러 시작하세요.
                        </p>
                      </div>
                    ) : llmLoading ? (
                      <div className="flex items-center gap-2.5 rounded-lg bg-slate-50 border border-slate-100 px-3 py-4">
                        <svg
                          className="animate-spin flex-shrink-0"
                          width="15"
                          height="15"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="#64748B"
                          strokeWidth="2.5"
                        >
                          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                        </svg>
                        <p className="text-xs text-slate-500">
                          상품 분석 데이터를 바탕으로 AI 진단 근거를 생성하고 있습니다.
                        </p>
                      </div>
                    ) : (
                      bottleneckCauses.map((cause, i) => (
                        <div key={i} className="flex items-start gap-2.5 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2.5">
                          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white border border-slate-200 text-[10px] font-bold text-slate-400 flex items-center justify-center">
                            {i + 1}
                          </span>
                          <p className="text-xs text-slate-600 leading-relaxed">
                            {cause}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="bg-blue-50/50 rounded-xl border border-blue-100 p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-xs font-bold text-blue-700 uppercase tracking-wider">
                        추천 액션
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        이 상품의 진단 결과를 실제 운영에서 어떻게 적용할지 정리했습니다.
                      </p>
                    </div>

                    <span className="text-[10px] font-bold text-blue-600 bg-white border border-blue-100 px-2 py-1 rounded-md">
                      운영 가이드
                    </span>
                  </div>

                  <div className="space-y-2.5">
                    {!llmStarted ? (
                      <div className="rounded-lg bg-white border border-dashed border-blue-200 px-3 py-5 text-center">
                        <p className="text-xs text-blue-600">
                          AI 진단을 시작하면 상품별 추천 액션이 표시됩니다.
                        </p>
                      </div>
                    ) : llmLoading ? (
                      <div className="flex items-center gap-2.5 bg-white rounded-lg border border-blue-100 px-3 py-4">
                        <svg
                          className="animate-spin flex-shrink-0"
                          width="15"
                          height="15"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="#2563EB"
                          strokeWidth="2.5"
                        >
                          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                        </svg>
                        <p className="text-xs text-blue-600">
                          상품별 추천 액션을 자동 생성하고 있습니다.
                        </p>
                      </div>
                    ) : (
                      actionItems.map((action, index) => (
                        <div key={`${action.tag}-${index}`} className="flex items-start gap-3 bg-white rounded-lg border border-blue-100 px-3 py-2.5">
                          <span className={`flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-md ${action.tag === "예산 테스트" || action.tag === "유지 운영" || action.tag === "전환 점검" || action.tag === "확대 보류"
                      ? "bg-blue-600 text-white"
                      : action.tag === "전환 보강" || action.tag === "소폭 개선" || action.tag === "구매 설득" || action.tag === "소재 점검"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-slate-100 text-slate-600"}`}>
                            {action.tag}
                          </span>
                          <p className="text-xs text-slate-700 leading-relaxed">
                            {action.text}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* 키워드별 실시간 고객 리뷰 및 점수별 색상·추천 문구 섹션 (안전 장치 추가 완료) */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      키워드별 고객 리뷰 분석 증거
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      최신 리뷰에서 추출한 키워드별 반응과 평점 평균입니다. (3점 미만: 빨강, 3~4점: 노랑, 4점 초과: 초록)
                    </p>
                  </div>
                </div>

                { !hasReviewData ? (
                  <div className="bg-slate-50 rounded-lg p-6 text-center text-xs text-slate-400 border border-slate-100">
                    수집된 키워드별 리뷰 데이터가 없습니다.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(reviewData).filter(([keyword, reviews]) => Array.isArray(reviews) && reviews.length > 0).map(([keyword, reviews]) => {
                      const safeReviews = Array.isArray(reviews) ? reviews : [];
                      const avgRating = safeReviews.length > 0 
                        ? (safeReviews.reduce((acc, cur) => acc + (cur?.rating || 0), 0) / safeReviews.length).toFixed(1) 
                        : 0;
                      const numAvg = parseFloat(avgRating);

                      const badgeColor = numAvg < 3
                        ? "bg-rose-50 text-rose-600 border-rose-200" 
                        : numAvg <= 4
                          ? "bg-amber-50 text-amber-600 border-amber-200" 
                          : "bg-emerald-50 text-emerald-600 border-emerald-200";

                      let recommendationText = "";
                      if (numAvg < 3) {
                        recommendationText = `⚠️ '${keyword}' 관련 고객 불만이 감지되었습니다. 상세페이지의 상품 설명 보완이나 품질 개선이 시급합니다.`;
                      } else if (numAvg <= 4) {
                        recommendationText = `⚡ '${keyword}' 반응이 보통입니다. 고객 피드백을 참고하여 사소한 개선 포인트를 점검해보세요.`;
                      } else {
                        recommendationText = `✨ '${keyword}' 반응이 매우 우수합니다! 해당 소구를 마케팅 포인트나 상세페이지 상단에 적극 활용하세요.`;
                      }

                      return (
                        <div
                          key={keyword}
                          className={`rounded-xl p-4 border ${
                            numAvg < 3
                              ? "bg-rose-50 border-rose-200"
                              : numAvg <= 4
                                ? "bg-amber-50 border-amber-200"
                                : "bg-emerald-50 border-emerald-200"
                          }`}
                        >
                          {/* 키워드 + 점수 */}
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
                              🏷️ #{keyword}
                              <span className="text-[11px] font-normal text-slate-400">
                                ({safeReviews.length}개 리뷰)
                              </span>
                            </span>

                            <span
                              className={`text-sm px-3 py-1 rounded-full border font-bold ${badgeColor}`}
                            >
                              {Array.from({ length: Math.round(numAvg) })
                                .map(() => "⭐")
                                .join("")}
                              <span className="ml-1 text-xs">
                                {avgRating}점
                              </span>
                            </span>
                          </div>


                          {/* 추천 영역 */}
                          <div
                            className={`rounded-lg p-3 mb-4 border text-xs font-semibold ${
                              numAvg < 3
                                ? "bg-white border-rose-200 text-rose-700"
                                : numAvg <= 4
                                  ? "bg-white border-amber-200 text-amber-700"
                                  : "bg-white border-emerald-200 text-emerald-700"
                            }`}
                          >
                            💡 {recommendationText}
                          </div>


                          {/* 실제 리뷰 영역 */}
                          <div className="space-y-2">
                            {safeReviews.length > 0 ? (
                              safeReviews.map((r, idx) => (
                                <div
                                  key={idx}
                                  className="bg-white rounded-lg p-3 border border-slate-100 text-xs shadow-sm"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    
                                    {/* 별점 */}
                                    <span className="text-sm tracking-wide">
                                      {Array.from({
                                        length: Math.round(r?.rating ?? 0)
                                      })
                                        .map(() => "⭐")
                                        .join("")}

                                      <span className="ml-1 text-xs text-slate-500">
                                        {r?.rating ?? 0}점
                                      </span>
                                    </span>


                                    {/* 날짜 */}
                                    <span className="text-[11px] text-slate-400">
                                      {r?.date_created
                                        ? new Date(r.date_created).toLocaleDateString()
                                        : ""}
                                    </span>

                                  </div>


                                  {/* 리뷰 내용 */}
                                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                                    {r?.contents || "내용 없음"}
                                  </p>

                                </div>
                              ))
                            ) : (
                              <p className="text-[11px] text-slate-400 py-1">
                                이 키워드와 매칭된 리뷰가 없습니다.
                              </p>
                            )}
                          </div>

                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

            </div>

            {/* Modal footer */}
            <div className="flex-shrink-0 flex items-center justify-start px-7 py-4 border-t border-slate-100 bg-slate-50/60">
              <button onClick={() => {
                onClose();
                setScreen("basis");
            }} className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                진단 기준 보기
              </button>
            </div>
          </div>
        </div>
    );
}