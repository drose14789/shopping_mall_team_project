import React, { useState } from 'react';
import { RESULTS_DATA, RESULTS_PAGE_SIZE } from "../constants/data"; 
import { getDiagnosisType, getRecommendedAction, actionBadge } from "../utils/helpers";
import { ProductDetailModal } from "../components/InspectionModal";

export default function ResultsScreen({ setScreen, }) {
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [page, setPage] = useState(0);
    const filtered = RESULTS_DATA;
    const totalPages = Math.max(1, Math.ceil(filtered.length / RESULTS_PAGE_SIZE));
    const paged = filtered.slice(page * RESULTS_PAGE_SIZE, (page + 1) * RESULTS_PAGE_SIZE);
    const pageStart = filtered.length === 0 ? 0 : page * RESULTS_PAGE_SIZE + 1;
    const pageEnd = Math.min((page + 1) * RESULTS_PAGE_SIZE, filtered.length);
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      {/* Heading */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <button onClick={() => setScreen("history")} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-500 border transition-colors" style={{ backgroundColor: "#F8FAFC", borderColor: "#E2E8F0" }} onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#EFF6FF")} onMouseLeave={e => (e.currentTarget.style.backgroundColor = "#F8FAFC")}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            분석 이력
          </button>
          <h2 className="text-xl font-bold text-slate-800">상품 액션 추천 결과</h2>
        </div>
        <p className="text-sm text-slate-400 mt-0.5">
          분산된 상품 중 광고를 확대할 상품과 개선이 필요한 상품을 확인해보세요.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
            {
                label: "전체 분석 상품",
                count: "25개",
                bg: "#F8FAFC",
                text: "#334155",
                border: "border-slate-200",
                sub: "이번 파일 전체 기준",
                icon: "📦",
            },
            {
                label: "광고 확대 가능",
                count: "7개",
                bg: "#EFF6FF",
                text: "#1D4ED8",
                border: "border-blue-200",
                sub: "성과 우수 · 확대 검토",
                icon: "📈",
            },
            {
                label: "개선 필요 상품",
                count: "5개",
                bg: "#FFFBEB",
                text: "#92400E",
                border: "border-amber-200",
                sub: "상세·전환 개선 필요",
                icon: "🛠️",
            },
            {
                label: "축소·보류 검토",
                count: "5개",
                bg: "#FFF1F2",
                text: "#9F1239",
                border: "border-rose-200",
                sub: "광고 효율 재점검",
                icon: "📉",
            },
        ].map((s) => (<div key={s.label} className={`rounded-xl border p-4 ${s.border}`} style={{ backgroundColor: s.bg }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">{s.icon}</span>
              <p className="text-xs font-semibold text-slate-500">
                {s.label}
              </p>
            </div>
            <p className="text-2xl font-bold mb-0.5" style={{ color: s.text }}>
              {s.count}
            </p>
            <p className="text-[11px] text-slate-400">
              {s.sub}
            </p>
          </div>))}
      </div>

      {/* Result table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              상품 액션 추천 결과 목록
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              상품별 진단 유형과 추천 액션을 전체 결과 기준으로 확인할 수 있어요.
            </p>
          </div>

          <button onClick={() => setScreen("upload")} className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-500 hover:text-blue-600 transition rounded-lg hover:bg-blue-50">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            새 파일 업로드
          </button>
        </div>
        {/* Table */}
        {filtered.length === 0 ? (<div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <p className="text-sm font-semibold text-slate-500 mb-1">
              해당 조건의 상품이 없습니다
            </p>
            <p className="text-xs text-slate-400">
              다른 필터를 선택하거나 새 파일을 업로드해주세요.
            </p>
          </div>) : (<table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                {[
                "상품명",
                "카테고리",
                "진단 유형",
                "추천 액션",
                "주요 근거",
                "상세 진단",
            ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3">
                    {h}
                  </th>))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {paged.map((row) => {
                const diagnosisType = getDiagnosisType(row);
                const recommendedAction = getRecommendedAction(row);
                return (<tr key={row.name} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-3 text-xs font-medium text-slate-700 whitespace-nowrap">
                      {row.name}
                    </td>

                    <td className="px-5 py-3 text-xs text-slate-500 whitespace-nowrap">
                      {row.cat}
                    </td>

                    <td className="px-5 py-3">
                      <span className={`text-xs px-2 py-1 rounded-md border font-medium whitespace-nowrap ${actionBadge(diagnosisType)}`}>
                        {diagnosisType}
                      </span>
                    </td>

                    <td className="px-5 py-3 text-xs text-slate-600 font-semibold whitespace-nowrap">
                      {recommendedAction}
                    </td>

                    <td className="px-5 py-3 text-xs text-slate-500 max-w-[240px] truncate">
                      {row.reason}
                    </td>

                    <td className="px-5 py-3">
                      <button onClick={() => setSelectedProduct(row)} className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition px-2.5 py-1.5 rounded-lg hover:bg-blue-50 whitespace-nowrap">
                        상세 보기
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="9 18 15 12 9 6"/>
                        </svg>
                      </button>
                    </td>
                  </tr>);
            })}
            </tbody>
          </table>)}

        {/* Pagination */}
        {filtered.length > 0 && (<div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/40">
            <p className="text-[11px] text-slate-400">
              <strong className="text-slate-600">{pageStart}–{pageEnd}</strong> / 총 <strong className="text-slate-600">{filtered.length}개</strong> 상품
            </p>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${page === 0 ? "text-slate-300 border-slate-200 cursor-not-allowed" : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                이전
              </button>
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => (<button key={i} onClick={() => setPage(i)} className={`w-7 h-7 rounded-lg text-[11px] font-semibold transition ${page === i ? "bg-blue-600 text-white shadow-sm" : "text-slate-500 hover:bg-slate-100 border border-slate-200"}`}>{i + 1}</button>))}
              {totalPages > 7 && <span className="text-slate-400 text-[11px] px-1">…</span>}
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${page >= totalPages - 1 ? "text-slate-300 border-slate-200 cursor-not-allowed" : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                다음
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          </div>)}
      </div>

      {/* Back */}
      <div className="flex items-center pb-2">
        <button onClick={() => setScreen("main")} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          메인으로 돌아가기
        </button>
      </div>

      {/* 상품 상세 진단 모달 */}
      {selectedProduct && (<ProductDetailModal product={selectedProduct} onClose={() => setSelectedProduct(null)} setScreen={setScreen}/>)}
    </div>);
}