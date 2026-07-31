import React, { useState } from 'react';

export function BasisCardHeader({ icon, title, }) {
    return (<div className="flex items-center gap-2.5 mb-1">
      <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-800 text-sm">
        {title}
      </h3>
    </div>);
}

export default function BasisScreen({ setScreen, }) {
    const stepIcons = [
        /* 파일 업로드 */
        <svg key="1" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17    8l-5-5-5 5M12 3v12"/>
    </svg>,
        /* 컬럼 확인·정제 */
        <svg key="2" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>,
        /* 지표 자동 계산 */
        <svg key="3" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2"/>
      <path d="M9 9h.01M15 9h.01M9 15h6"/>
    </svg>,
        /* 시즌·카테고리 비교 */
        <svg key="4" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>,
        /* 광고 유형 분류 */
        <svg key="5" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M16 8h-6a2 2 0 100 4h4a2 2 0 110 4H8"/>
      <path d="M12 18v-2m0-8V6"/>
    </svg>,
        /* 퍼널 병목 진단 */
        <svg key="6" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>,
        /* LLM 최종 해석 */
        <svg key="7" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
    </svg>,
    ];
    const stepLabels = [
        "파일 업로드",
        "컬럼 확인 및\n데이터 정제",
        "지표 자동\n계산",
        "시즌·카테고리\n비교",
        "광고 유형\n분류",
        "퍼널 병목\n진단",
        "LLM 최종\n해석·추천",
    ];
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      {/* Heading */}
      <div>
        <h2 className="text-xl font-bold text-slate-800">
          진단 기준
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          상품 액션 추천이 어떤 데이터와 기준으로 만들어지는지
          확인해보세요.
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
            ActionFit AI 판단 기준
          </p>
          <h2 className="text-xl font-bold mb-2" style={{
            color: "#fff",
            textShadow: "0 1px 6px rgba(30,58,138,0.3)",
        }}>
            상품 성과 데이터를 기반으로
          </h2>
          <p className="text-sm leading-relaxed max-w-md" style={{ color: "rgba(255,255,255,0.9)" }}>
            광고 확대, 유지, 개선, 축소 액션을 판단하는 기준을
            <br />
            투명하게 확인할 수 있어요.
          </p>
        </div>
        <div className="relative z-10 hidden lg:flex items-center gap-3 mr-2">
          {[
            <svg key="a" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>,
            <svg key="b" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 11 12 14 22 4"/>
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
            </svg>,
            <svg key="c" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>,
        ].map((svg, i) => (<div key={i} className="w-11 h-11 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm border border-white/30">
              {svg}
            </div>))}
        </div>
      </div>

      {/* 1. 진단 흐름 요약 */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>} title="진단 흐름 요약"/>
        <p className="text-xs text-slate-400 mb-5">
          ActionFit AI는 아래 순서로 상품 액션을 추천합니다.
        </p>
        <div className="flex items-start gap-1.5 overflow-x-auto pb-2">
          {stepLabels.map((label, i) => (<div key={i} className="flex items-start gap-1.5 flex-shrink-0">
              <div className="flex flex-col items-center" style={{ width: 88 }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-2 flex-shrink-0" style={{ backgroundColor: "#EFF6FF" }}>
                  {stepIcons[i]}
                </div>
                <div className="text-[9px] font-bold px-2 py-0.5 rounded-md mb-1.5 whitespace-nowrap" style={{
                backgroundColor: "#DBEAFE",
                color: "#2563EB",
            }}>
                  STEP {i + 1}
                </div>
                <p className="text-[11px] text-slate-600 text-center leading-snug whitespace-pre-line">
                  {label}
                </p>
              </div>
              {i < 6 && (<div className="flex-shrink-0 mt-4 pt-0.5">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2.5" strokeLinecap="round">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </div>)}
            </div>))}
        </div>
        <div className="mt-4 p-3 rounded-lg border border-blue-100" style={{ backgroundColor: "#EFF6FF" }}>
          <p className="text-[11px] leading-relaxed" style={{ color: "#1D4ED8" }}>
            ActionFit AI는 단순히 숫자 하나만 보고 판단하지
            않고, 광고 효율·구매 퍼널·반품 리스크·시즌/카테고리
            맥락을 함께 고려합니다.
          </p>
        </div>
      </div>

      {/* 2 & 3 side by side */}
      <div className="grid grid-cols-2 gap-4">
        {/* 2. 필수 입력 데이터 */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
              </svg>} title="필수 입력 데이터"/>
          <p className="text-xs text-slate-400 mb-4">
            아래 컬럼이 있어야 상품 액션 추천 분석을 진행할 수
            있습니다.
          </p>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {[
            "상품ID",
            "상품명",
            "노출수",
            "클릭수",
            "광고비",
            "상품금액",
            "주문금액",
            "상품 상세 방문수",
            "장바구니 유저수",
            "찜 유저수",
            "상품주문수",
            "반품건수",
            "판매 사이트"
        ].map((col) => (<span key={col} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium">
                {col}
              </span>))}
          </div>
          <div className="flex items-start gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50">
            <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className="text-[11px] text-slate-500">
              시즌 정보는 파일 컬럼이 없어도 분석 기간 설정을
              통해 자동 분류할 수 있습니다.
            </p>
          </div>
        </div>

        {/* 3. 자동 계산 지표 */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="4" y="2" width="16" height="20" rx="2"/>
                <line x1="8" y1="8" x2="16" y2="8"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
                <line x1="8" y1="16" x2="12" y2="16"/>
              </svg>} title="자동 계산 지표"/>
          <p className="text-xs text-slate-400 mb-4">
            비율 지표는 원본 수치 데이터를 기준으로 자동
            계산합니다.
          </p>
          <div className="space-y-2 mb-4">
            {[
            {
                name: "클릭률",
                formula: "클릭수 / 노출수 × 100",
                purpose: "노출 대비 클릭 반응",
            },
            {
                name: "ROAS",
                formula: "주문금액 / 광고비 × 100",
                purpose: "광고비 대비 매출 효율",
            },
            {
                name: "장바구니 전환율",
                formula: "장바구니 유저수 / 상세 방문수 × 100",
                purpose: "구매 고려 단계 진입",
            },
            {
                name: "구매전환율",
                formula: "상품주문수 / 상세 방문수 × 100",
                purpose: "실제 구매 전환",
            },
            {
                name: "장바구니 구매율",
                formula: "상품주문수 / 장바구니 유저수 × 100",
                purpose: "장바구니 이후 완료 여부",
            },
            {
                name: "반품률",
                formula: "반품건수 / 상품주문수 × 100",
                purpose: "판매 후 반품 리스크",
            },
        ].map((m) => (<div key={m.name} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[11px] font-bold text-slate-700 w-28 flex-shrink-0">
                  {m.name}
                </span>
                <code className="text-[10px] text-blue-700 font-mono bg-blue-50 px-2 py-0.5 rounded border border-blue-100 flex-1">
                  {m.formula}
                </code>
                <span className="text-[10px] text-slate-400 flex-shrink-0 hidden xl:block">
                  {m.purpose}
                </span>
              </div>))}
          </div>
          <div className="p-3 rounded-lg border" style={{
            backgroundColor: "#FFFBEB",
            borderColor: "#FDE68A",
        }}>
            <p className="text-[11px] leading-relaxed" style={{ color: "#B45309" }}>
              엑셀에 비율 컬럼이 포함되어 있어도 참고용으로만
              활용되며, 분석 기준은 원본 수치로 자동 계산한 값을
              우선 적용합니다.
            </p>
          </div>
        </div>
      </div>

      {/* 4. 광고 운영 유형 분류 */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>} title="광고 운영 유형 분류 기준"/>
        <p className="text-xs text-slate-400 mb-4">
          클릭률과 ROAS를 중심으로 상품을 빠르게 분류합니다.
        </p>
        <div className="overflow-x-auto rounded-xl border border-slate-100">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                {[
            "광고 운영 유형",
            "분류 기준",
            "의미",
            "추천 방향",
        ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-4 py-3">
                    {h}
                  </th>))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
            {[
            {
                type: "핵심 확대형",
                cls: "bg-blue-50 text-blue-700 border-blue-200",
                basis: "클릭률 높음 · 전환율 높음 · 반품 안정성 높음",
                meaning: "성과가 안정적으로 확인된 상품",
                direction: "광고 예산 확대 가능",
            },
            {
                type: "상세페이지 개선형",
                cls: "bg-amber-50 text-amber-700 border-amber-200",
                basis: "클릭률 높음 · 장바구니/구매 전환 낮음",
                meaning: "관심은 있으나 상세페이지 설득력이 부족한 상품",
                direction: "상세 정보, 착용컷, 혜택 보강",
            },
            {
                type: "반품 리스크형",
                cls: "bg-red-50 text-red-700 border-red-200",
                basis: "구매 전환은 있으나 반품 안정성 낮음",
                meaning: "확대 전 반품 원인 점검이 필요한 상품",
                direction: "사이즈, 소재, 색감 정보 보강",
            },
            {
                type: "광고 축소형",
                cls: "bg-rose-50 text-rose-700 border-rose-200",
                basis: "클릭률 낮음 · 전환율 낮음",
                meaning: "광고비 대비 성과가 낮은 상품",
                direction: "광고비 축소 또는 보류",
            },
        ].map((row) => (<tr key={row.type} className="hover:bg-slate-50/70 transition-colors">
                <td className="px-4 py-3" style={{ minWidth: 148 }}>
                  <span className={`text-xs px-2 py-1 rounded-md border font-medium whitespace-nowrap ${row.cls}`}>
                    {row.type}
                  </span>
                </td>

                <td className="px-4 py-3 text-xs text-slate-600">
                  {row.basis}
                </td>

                <td className="px-4 py-3 text-xs text-slate-500">
                  {row.meaning}
                </td>

                <td className="px-4 py-3 text-xs text-slate-700 font-medium">
                  {row.direction}
                </td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-start gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50">
          <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p className="text-[11px] text-slate-500">
            광고 운영 유형은 1차 분류 기준이며, 최종 추천은 상세
            진단 지표와 퍼널 병목 진단을 함께 고려합니다.
          </p>
        </div>
      </div>

      {/* 5. 광고 확대 추천 점수 */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>} title="광고 확대 추천 점수"/>
        <p className="text-xs text-slate-400 mb-4">
          상품이 광고비를 더 써도 괜찮은지 판단하기 위한 종합
          점수입니다.
        </p>

        {/* Formula card */}
        <div className="rounded-xl border border-blue-200 p-4 mb-5" style={{ backgroundColor: "#EFF6FF" }}>
          <p className="text-[10px] font-bold text-blue-500 uppercase tracking-wider mb-1.5">
            계산식
          </p>
          <p className="text-xs font-semibold text-blue-900 leading-relaxed">
            광고 확대 추천 점수 =<br />
            <span className="text-blue-700 font-normal">
              클릭률 + 찜 전환율 + 장바구니 전환율 + 구매전환율
              + 장바구니 구매율 + 반품 안정성 + ROAS 점수의 평균
            </span>
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Score items */}
          <div>
            <p className="text-[11px] font-semibold text-slate-500 mb-2">
              점수 항목
            </p>
            <div className="space-y-1.5">
              {[
            {
                item: "클릭률 점수",
                desc: "노출 대비 클릭 반응",
            },
            {
                item: "찜 전환율 점수",
                desc: "관심 표현 정도",
            },
            {
                item: "장바구니 전환율 점수",
                desc: "구매 고려 단계 진입",
            },
            {
                item: "구매전환율 점수",
                desc: "실제 구매 전환",
            },
            {
                item: "장바구니 구매율 점수",
                desc: "장바구니 이후 구매 완료",
            },
            {
                item: "반품 안정성 점수",
                desc: "반품 리스크 안정성",
            },
            {
                item: "ROAS 점수",
                desc: "광고비 대비 매출 효율",
            },
        ].map((s) => (<div key={s.item} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0"/>
                  <span className="text-xs font-medium text-slate-700 flex-1">
                    {s.item}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {s.desc}
                  </span>
                </div>))}
            </div>
          </div>

          {/* Score conversion + interpretation */}
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="text-[11px] font-semibold text-slate-500 mb-2">
                점수 변환 기준 (일반 지표)
              </p>
              <div className="space-y-1.5">
                {[
            [
                "상위 25%",
                "100점",
                "text-emerald-700",
                "bg-emerald-50",
            ],
            [
                "평균 이상",
                "75점",
                "text-blue-700",
                "bg-blue-50",
            ],
            [
                "평균 미만",
                "50점",
                "text-amber-700",
                "bg-amber-50",
            ],
            [
                "하위 25%",
                "25점",
                "text-rose-700",
                "bg-rose-50",
            ],
        ].map(([label, score, text, bg]) => (<div key={label} className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">
                      {label}
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${bg} ${text}`}>
                      {score}
                    </span>
                  </div>))}
              </div>
              <p className="text-[10px] text-slate-400 mt-2">
                * 반품 안정성은 반품률이 낮을수록 높은 점수
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="text-[11px] font-semibold text-slate-500 mb-2">
                최종 점수 해석
              </p>
              <div className="space-y-1.5">
                {[
            {
                range: "80점 이상",
                label: "예산 확대 가능",
                bg: "bg-blue-50",
                text: "text-blue-700",
                border: "border-blue-200",
            },
            {
                range: "60~79점",
                label: "예산 유지 / 소액 테스트",
                bg: "bg-emerald-50",
                text: "text-emerald-700",
                border: "border-emerald-200",
            },
            {
                range: "40~59점",
                label: "개선 후 재집행",
                bg: "bg-amber-50",
                text: "text-amber-700",
                border: "border-amber-200",
            },
            {
                range: "40점 미만",
                label: "광고 축소 / 보류",
                bg: "bg-rose-50",
                text: "text-rose-700",
                border: "border-rose-200",
            },
        ].map((s) => (<div key={s.range} className={`flex items-center justify-between px-3 py-2 rounded-lg border ${s.bg} ${s.border}`}>
                    <span className="text-xs text-slate-500">
                      {s.range}
                    </span>
                    <span className={`text-xs font-bold ${s.text}`}>
                      {s.label}
                    </span>
                  </div>))}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-start gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50">
          <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p className="text-[11px] text-slate-500">
            각 점수는 전체 상품 평균이 아니라 같은 시즌·같은
            카테고리 상품과 비교해 산정합니다.
          </p>
        </div>
      </div>

      {/* 6. 퍼널 병목 진단 */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>} title="퍼널 병목 진단 기준"/>
        <p className="text-xs text-slate-400 mb-4">
          고객이 구매 과정 중 어느 단계에서 이탈하는지 확인해
          상품별 개선 방향을 찾습니다.
        </p>

        {/* Funnel flow */}
        <div className="flex items-center gap-2 flex-wrap mb-5 p-4 rounded-xl bg-slate-50 border border-slate-100">
          {[
            "노출수",
            "클릭수",
            "상세 방문수",
            "찜/장바구니",
            "상품주문수",
            "반품건수",
        ].map((stage, i) => (<div key={stage} className="flex items-center gap-2">
              <div className="px-3 py-1.5 rounded-lg text-xs font-semibold border" style={{
                backgroundColor: "#EFF6FF",
                borderColor: "#BFDBFE",
                color: "#2563EB",
            }}>
                {stage}
              </div>
              {i < 5 && (<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2.5">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>)}
            </div>))}
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-100">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                {[
            "진단 유형",
            "판단 기준",
            "병목 구간",
            "추천 액션",
        ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-4 py-3">
                    {h}
                  </th>))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {[
            {
                type: "노출 소재 개선형",
                icon: "🖼️",
                basis: "노출수는 충분하지만 클릭률이 낮음",
                funnel: "노출 → 클릭",
                action: "썸네일·상품명·대표 이미지·가격 노출 개선",
                color: "bg-violet-50 text-violet-700 border-violet-200",
            },
            {
                type: "상세페이지 개선형",
                icon: "📝",
                basis: "상세 방문수는 많지만 장바구니 전환율이 낮음",
                funnel: "상세페이지 → 장바구니",
                action: "착용컷·소재감·혜택 정보 보강",
                color: "bg-amber-50 text-amber-700 border-amber-200",
            },
            {
                type: "구매 직전 이탈형",
                icon: "🛒",
                basis: "장바구니 전환율은 높지만 장바구니 구매율이 낮음",
                funnel: "장바구니 → 구매",
                action: "쿠폰·무료배송·가격 혜택·리마인드 광고 검토",
                color: "bg-orange-50 text-orange-700 border-orange-200",
            },
            {
                type: "반품 리스크형",
                icon: "↩️",
                basis: "주문수는 많지만 반품률이 높음",
                funnel: "구매 → 반품",
                action: "사이즈표·모델 착용 정보·색감·소재 설명 보강",
                color: "bg-rose-50 text-rose-700 border-rose-200",
            },
            {
                type: "성과 안정형",
                icon: "✅",
                basis: "구매전환율이 높고 반품률이 낮으며 ROAS 평균 이상",
                funnel: "병목 없음",
                action: "광고비 확대 또는 유지 테스트",
                color: "bg-emerald-50 text-emerald-700 border-emerald-200",
            },
        ].map((row) => (<tr key={row.type} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3" style={{ minWidth: 160 }}>
                    <span className={`text-xs px-2 py-1 rounded-md border font-medium whitespace-nowrap ${row.color} inline-flex items-center gap-1.5`}>
                      <span>{row.icon}</span>
                      {row.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-[180px]">
                    {row.basis}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[11px] font-mono font-semibold text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded whitespace-nowrap">
                      {row.funnel}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {row.action}
                  </td>
                </tr>))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 7 & 8 side by side */}
      <div className="grid grid-cols-2 gap-4">
        {/* 7. 시즌·카테고리 비교 기준 */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>} title="시즌·카테고리 비교 기준"/>
          <p className="text-xs text-slate-400 mb-4">
            상품 성과는 전체 평균이 아니라 같은 시즌·같은
            카테고리 안에서 비교합니다.
          </p>

          <div className="p-3 rounded-lg border border-blue-100 mb-4" style={{ backgroundColor: "#EFF6FF" }}>
            <p className="text-[11px] leading-relaxed" style={{ color: "#1D4ED8" }}>
              반팔 티셔츠는 여름 시즌 상품과 비교하고, 니트는
              겨울 시즌 상품과 비교해야 더 정확한 판단이
              가능합니다.
            </p>
          </div>

          <p className="text-[11px] font-semibold text-slate-500 mb-2">
            시즌 분류 기준
          </p>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {[
            {
                season: "봄 🌸",
                months: "3월~5월",
                bg: "bg-pink-50",
                border: "border-pink-200",
                text: "text-pink-700",
            },
            {
                season: "여름 ☀️",
                months: "6월~8월",
                bg: "bg-amber-50",
                border: "border-amber-200",
                text: "text-amber-700",
            },
            {
                season: "가을 🍂",
                months: "9월~11월",
                bg: "bg-orange-50",
                border: "border-orange-200",
                text: "text-orange-700",
            },
            {
                season: "겨울 ❄️",
                months: "12월~2월",
                bg: "bg-blue-50",
                border: "border-blue-200",
                text: "text-blue-700",
            },
        ].map((s) => (<div key={s.season} className={`px-3 py-2 rounded-lg border ${s.bg} ${s.border}`}>
                <p className={`text-xs font-bold ${s.text}`}>
                  {s.season}
                </p>
                <p className="text-[10px] text-slate-400">
                  {s.months}
                </p>
              </div>))}
          </div>

          <p className="text-[11px] font-semibold text-slate-500 mb-2">
            카테고리 비교 예시
          </p>
          <div className="space-y-1.5">
            {[
            "원피스는 원피스 카테고리 평균과 비교",
            "블라우스는 블라우스 카테고리 평균과 비교",
            "티셔츠는 티셔츠 카테고리 평균과 비교",
        ].map((ex) => (<div key={ex} className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-3.5 h-3.5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                {ex}
              </div>))}
          </div>
          <div className="mt-3 flex items-start gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50">
            <svg className="flex-shrink-0 mt-0.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className="text-[11px] text-slate-500">
              시즌과 카테고리 기준을 함께 적용하면 단순 평균
              비교보다 상품 특성에 맞는 진단이 가능합니다.
            </p>
          </div>
        </div>

        {/* 8. 데이터 부족 및 예외 처리 */}
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <BasisCardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>} title="데이터 부족 및 예외 처리 기준"/>
          <p className="text-xs text-slate-400 mb-4">
            표본이 부족하거나 필수 데이터가 누락된 경우,
            무리하게 판단하지 않고 데이터 부족 또는 확인 필요
            상태로 안내합니다.
          </p>
          <div className="space-y-2">
            {[
            {
                situation: "필수 컬럼 누락",
                handling: "분석 불가",
                guide: "필수 컬럼을 추가한 뒤 다시 업로드해주세요.",
                color: "border-rose-200 bg-rose-50",
                badge: "bg-rose-100 text-rose-700",
            },
            {
                situation: "노출수 또는 클릭수 0",
                handling: "클릭률 계산 제외",
                guide: "클릭률 계산이 어려워 일부 판단에서 제외됩니다.",
                color: "border-amber-200 bg-amber-50",
                badge: "bg-amber-100 text-amber-700",
            },
            {
                situation: "광고비 0",
                handling: "ROAS 계산 제외",
                guide: "광고비가 없어 광고 효율 판단에서 제외됩니다.",
                color: "border-amber-200 bg-amber-50",
                badge: "bg-amber-100 text-amber-700",
            },
            {
                situation: "상품 상세 방문수 0",
                handling: "전환율 계산 제외",
                guide: "상세페이지 이후 퍼널 분석이 어렵습니다.",
                color: "border-amber-200 bg-amber-50",
                badge: "bg-amber-100 text-amber-700",
            },
            {
                situation: "장바구니 유저수 0",
                handling: "장바구니 구매율 제외",
                guide: "장바구니 이후 구매 판단이 제한됩니다.",
                color: "border-slate-200 bg-slate-50",
                badge: "bg-slate-100 text-slate-600",
            },
            {
                situation: "상품주문수 0",
                handling: "반품률 계산 제외",
                guide: "주문 데이터가 없어 반품률 판단이 어렵습니다.",
                color: "border-slate-200 bg-slate-50",
                badge: "bg-slate-100 text-slate-600",
            },
            {
                situation: "카테고리·시즌 누락",
                handling: "비교 기준 부족",
                guide: "시즌·카테고리 기준 비교가 제한됩니다.",
                color: "border-slate-200 bg-slate-50",
                badge: "bg-slate-100 text-slate-600",
            },
            {
                situation: "데이터 표본 부족",
                handling: "낮은 확신도 표시",
                guide: "데이터가 부족해 추가 분석이 필요합니다.",
                color: "border-blue-200 bg-blue-50",
                badge: "bg-blue-100 text-blue-700",
            },
        ].map((row) => (<div key={row.situation} className={`px-3 py-2.5 rounded-lg border ${row.color} flex items-start gap-3`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-semibold text-slate-700">
                      {row.situation}
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${row.badge}`}>
                      {row.handling}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {row.guide}
                  </p>
                </div>
              </div>))}
          </div>
        </div>
      </div>

      {/* 9. 주의 문구 */}
      <div className="rounded-xl border border-slate-200 p-5 flex items-start gap-4 bg-white">
        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-600 mb-1">
            주의 사항
          </p>
          <p className="text-xs text-slate-500 leading-relaxed">
            ActionFit AI의 진단 결과는 업로드된 상품 성과
            데이터와 설정된 분석 기준을 바탕으로 한 참고용
            추천입니다. 실제 매출, 광고 성과, 소비자 반응을
            보장하지 않으며, 최종 광고 운영 판단은 판매자의 상품
            특성, 재고, 가격, 시즌 전략 등을 함께 고려해
            결정해야 합니다.
          </p>
        </div>
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
    </div>);
}