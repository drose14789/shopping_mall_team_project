import React from "react";
import { actionBadge } from "../utils/helpers";

export default function DetailScreen({ setScreen, }) {
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      {/* Heading */}
      <div className="flex items-center gap-3">
        <button onClick={() => setScreen("results")} className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50 transition flex-shrink-0">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            링이 앵글 프릴 블라우스
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            블라우스 · 2026.05.20 분석 기준
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`text-sm px-3 py-1.5 rounded-lg border font-semibold ${actionBadge("예산 확대")}`}>
            예산 확대
          </span>
          <span className="text-xs px-2 py-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 font-semibold">
            우선순위 높음
          </span>
        </div>
      </div>

      {/* 최종 판단 요약 */}
      <div className="rounded-xl p-5 border border-blue-200" style={{
            background: "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 60%, #EDE9FE 100%)",
        }}>
        <p className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: "#3B82F6" }}>
          최종 판단 요약
        </p>
        <p className="text-sm font-semibold text-slate-800 leading-relaxed mb-1">
          이 상품은 현재 광고 예산을 늘려 더 많은 노출과 클릭을
          확보할 가치가 있습니다.
        </p>
        <p className="text-xs text-slate-500 leading-relaxed">
          ROAS 4.2로 업종 평균(2.8) 대비 높은 수익성을 유지하고
          있으며, 클릭률은 상위 15%에 위치합니다. 반품률은
          3.2%로 낮은 편이며, 장바구니 전환율이 꾸준히 상승
          중입니다.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* 광고 예산 판단 근거 */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            광고 예산 판단 근거
          </p>
          <div className="space-y-2.5">
            {[
            {
                label: "ROAS",
                value: "4.2",
                benchmark: "업종 평균 2.8",
                positive: true,
            },
            {
                label: "클릭률(CTR)",
                value: "2.7%",
                benchmark: "업종 평균 1.8%",
                positive: true,
            },
            {
                label: "구매전환율",
                value: "3.1%",
                benchmark: "업종 평균 2.4%",
                positive: true,
            },
            {
                label: "반품률",
                value: "3.2%",
                benchmark: "업종 평균 5.1%",
                positive: true,
            },
            {
                label: "광고비 비중",
                value: "18%",
                benchmark: "권고 기준 25% 이하",
                positive: true,
            },
        ].map((m) => (<div key={m.label} className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${m.positive ? "bg-emerald-100" : "bg-rose-100"}`}>
                  {m.positive ? (<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>) : (<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#e11d48" strokeWidth="3" strokeLinecap="round">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>)}
                </div>
                <span className="text-xs text-slate-500 flex-1">
                  {m.label}
                </span>
                <span className="text-sm font-bold text-slate-800">
                  {m.value}
                </span>
                <span className="text-[10px] text-slate-400 text-right">
                  {m.benchmark}
                </span>
              </div>))}
          </div>
        </div>

        {/* 주요 지표 요약 */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            주요 지표 요약
          </p>
          <div className="grid grid-cols-2 gap-3">
            {[
            {
                label: "노출수",
                value: "45,678",
                sub: "전월 대비 +8%",
            },
            {
                label: "클릭수",
                value: "1,234",
                sub: "전월 대비 +11%",
            },
            {
                label: "광고비",
                value: "₩12,000",
                sub: "예산 소진율 92%",
            },
            {
                label: "주문금액",
                value: "₩45,000",
                sub: "ROAS 4.2 기준",
            },
            {
                label: "상품주문수",
                value: "38건",
                sub: "전월 대비 +5건",
            },
            {
                label: "장바구니 유저",
                value: "96명",
                sub: "장바구니 전환율 7.8%",
            },
        ].map((m) => (<div key={m.label} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <p className="text-[10px] text-slate-400 font-semibold mb-0.5">
                  {m.label}
                </p>
                <p className="text-sm font-bold text-slate-800">
                  {m.value}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {m.sub}
                </p>
              </div>))}
          </div>
        </div>
      </div>

      {/* 광고 확대 추천 점수 */}
      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
          광고 확대 추천 점수
        </p>
        <div className="flex items-center gap-6">
          <div className="flex-shrink-0 flex flex-col items-center">
            <div className="relative w-20 h-20">
              <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3"/>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#2563EB" strokeWidth="3" strokeDasharray="87 13" strokeLinecap="round"/>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xl font-bold text-blue-700">
                  87
                </span>
                <span className="text-[9px] text-slate-400">
                  / 100
                </span>
              </div>
            </div>
            <p className="text-xs font-semibold text-blue-700 mt-2">
              확대 권장
            </p>
          </div>
          <div className="flex-1 space-y-2.5">
            {[
            {
                label: "수익성 지표",
                score: 92,
                color: "#2563EB",
            },
            {
                label: "성장 가능성",
                score: 85,
                color: "#7C3AED",
            },
            {
                label: "광고 효율",
                score: 88,
                color: "#059669",
            },
            {
                label: "리스크 수준",
                score: 78,
                color: "#D97706",
            },
        ].map((s) => (<div key={s.label} className="flex items-center gap-3">
                <span className="text-xs text-slate-500 w-24 flex-shrink-0">
                  {s.label}
                </span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{
                width: `${s.score}%`,
                backgroundColor: s.color,
            }}/>
                </div>
                <span className="text-xs font-bold text-slate-700 w-7 text-right">
                  {s.score}
                </span>
              </div>))}
          </div>
        </div>
      </div>

      {/* 퍼널 흐름 진단 */}
      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
          퍼널 흐름 진단
        </p>
        <div className="flex items-stretch gap-3">
          {[
            {
                stage: "노출",
                value: "45,678",
                rate: null,
                status: "good",
            },
            {
                stage: "클릭",
                value: "1,234",
                rate: "CTR 2.7%",
                status: "good",
            },
            {
                stage: "상세 방문",
                value: "980",
                rate: "79.4%",
                status: "good",
            },
            {
                stage: "장바구니",
                value: "96",
                rate: "9.8%",
                status: "warn",
            },
            {
                stage: "구매",
                value: "38",
                rate: "39.6%",
                status: "good",
            },
        ].map((f, i) => (<div key={f.stage} className="flex items-center gap-3 flex-1">
              <div className={`flex-1 rounded-xl p-3 border text-center ${f.status === "good" ? "bg-blue-50 border-blue-200" : "border-amber-200"}`} style={f.status === "warn"
                ? { backgroundColor: "#FFFBEB" }
                : {}}>
                <p className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${f.status === "good" ? "text-blue-500" : "text-amber-600"}`}>
                  {f.stage}
                </p>
                <p className={`text-sm font-bold ${f.status === "good" ? "text-blue-800" : "text-amber-800"}`}>
                  {f.value}
                </p>
                {f.rate && (<p className={`text-[10px] mt-0.5 ${f.status === "good" ? "text-blue-500" : "text-amber-600"}`}>
                    {f.rate}
                  </p>)}
              </div>
              {i < 4 && (<svg className="flex-shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>)}
            </div>))}
        </div>
        <div className="mt-3 flex items-start gap-2 p-3 rounded-lg border" style={{
            backgroundColor: "#FFFBEB",
            borderColor: "#FDE68A",
        }}>
          <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p className="text-xs leading-relaxed" style={{ color: "#92400E" }}>
            <strong>병목 구간:</strong> 상세 방문 → 장바구니
            전환율이 9.8%로 업종 평균(14.2%) 대비 낮습니다.
            상세페이지 개선 후 광고를 더 확대하면 효율이 높아질
            수 있습니다.
          </p>
        </div>
      </div>


      {/* Back */}
      <div className="flex items-center pb-2">
        <button onClick={() => setScreen("results")} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          결과 목록으로 돌아가기
        </button>
      </div>
    </div>);
}