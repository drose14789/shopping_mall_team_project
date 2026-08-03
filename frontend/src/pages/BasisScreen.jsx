import React, { useState, useEffect, useRef } from 'react';
import {BasisSection} from "../components/common/Section";

function BasisCardHeader({ icon, title }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-800 text-sm">{title}</h3>
    </div>
  );
}

export default function BasisScreen({ setScreen }) {
  const stepLabels = [
    "파일 업로드",
    "컬럼 확인 및\n데이터 정제",
    "지표 자동\n계산",
    "시즌·카테고리\n비교",
    "16가지 유형\n분류",
    "리뷰 원인\n보조 검증",
    "오늘의 액션\n우선순위화",
    "성과 변화\n리포트",
  ];

  const metricRows = [
    {
      name: "클릭률",
      formula: "클릭수 / 노출수 × 100",
      purpose: "노출 대비 클릭 반응",
    },
    {
      name: "찜 관심도",
      formula: "찜 유저수 / 상품 상세 방문수 × 100",
      purpose: "상품 관심 표현 정도",
    },
    {
      name: "장바구니 전환율",
      formula: "장바구니 유저수 / 상품 상세 방문수 × 100",
      purpose: "구매 고려 단계 진입",
    },
    {
      name: "구매전환율",
      formula: "상품주문수 / 상품 상세 방문수 × 100",
      purpose: "실제 구매 전환",
    },
    {
      name: "반품률",
      formula: "반품건수 / 상품주문수 × 100",
      purpose: "판매 후 반품 리스크",
    },
    {
      name: "ROAS",
      formula: "주문금액 / 광고비 × 100",
      purpose: "광고비 대비 매출 효율",
    },
  ];

  const diagnosisRows = [
    ["높음", "높음", "높음", "높음", "핵심 확대형", "광고 예산 확대"],
    ["높음", "높음", "높음", "낮음", "반품 리스크 확대 보류형", "반품 원인 개선 후 확대 검토"],
    ["높음", "높음", "낮음", "높음", "구매 직전 이탈형", "가격·쿠폰·배송 혜택 점검"],
    ["높음", "높음", "낮음", "낮음", "구매·반품 복합 리스크형", "혜택 보강 + 반품 원인 개선"],
    ["높음", "낮음", "높음", "높음", "전환 효율형", "상세 상단 보완 후 유지/소액 확대"],
    ["높음", "낮음", "높음", "낮음", "반품 주의 유지형", "확대 보류 + 반품 원인 점검"],
    ["높음", "낮음", "낮음", "높음", "상세페이지 개선형", "착용컷·소재·사이즈 정보 보강"],
    ["높음", "낮음", "낮음", "낮음", "상세·반품 복합 개선형", "상세 보강 + 기대 불일치 개선"],
    ["낮음", "높음", "높음", "높음", "숨은 효율형", "썸네일·상품명 개선 후 소액 확대"],
    ["낮음", "높음", "높음", "낮음", "소재 개선+반품 주의형", "대표 이미지·소재·사이즈 설명 보강"],
    ["낮음", "높음", "낮음", "높음", "소재·구매 전환 개선형", "소재 반응 + 가격·혜택 점검"],
    ["낮음", "높음", "낮음", "낮음", "소재·구매·반품 복합 리스크형", "광고 확대 보류 + 전반 개선"],
    ["낮음", "낮음", "높음", "높음", "소수 전환형", "데이터 추가 확보 후 소액 테스트"],
    ["낮음", "낮음", "높음", "낮음", "소수 전환+반품 리스크형", "확대 보류 + 반품 원인 점검"],
    ["낮음", "낮음", "낮음", "높음", "광고 반응 부족형", "소재·상품명·상세페이지 개선 후 재집행"],
    ["낮음", "낮음", "낮음", "낮음", "광고 축소형", "광고비 축소 또는 보류"],
  ];

  const reviewKeywordRows = [
    {
      group: "사이즈·핏",
      expressions: "사이즈 작음, 큼, 핏 애매, 핏 예쁨, 라인 예쁨",
      related: "반품 리스크, 구매 불안",
    },
    {
      group: "소재·두께감",
      expressions: "소재 얇음, 재질 별로, 부드러움, 까슬거림, 비침",
      related: "상세페이지 개선, 반품 원인",
    },
    {
      group: "색감·사진 일치",
      expressions: "사진이랑 다름, 색감 다름, 실물이 예쁨",
      related: "기대 불일치, 반품 리스크",
    },
    {
      group: "착용 정보",
      expressions: "착용샷 부족, 기장감, 체형별 후기, 모델핏",
      related: "상세페이지 설득력",
    },
    {
      group: "가격·혜택",
      expressions: "가격 고민, 할인 기다림, 비쌈, 쿠폰, 무료배송",
      related: "구매 직전 이탈",
    },
    {
      group: "만족도",
      expressions: "만족, 재구매, 데일리, 추천, 별로, 후회",
      related: "확대 가능성, 상품 경쟁력",
    },
  ];

  const actionGroupRows = [
    {
      group: "예산 확대",
      types: "핵심 확대형, 숨은 효율형, 소수 전환형",
      purpose: "성과가 확인된 상품을 우선 확대 후보로 확인",
      color: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
      group: "예산 유지",
      types: "전환 효율형, 반품 주의 유지형",
      purpose: "성과는 유지하되 변동 지표를 관찰",
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
      group: "개선 필요",
      types: "구매 직전 이탈형, 상세페이지 개선형, 상세·반품 복합 개선형, 소재·구매 전환 개선형, 광고 반응 부족형",
      purpose: "광고 확대보다 상세·혜택·소재 개선을 우선",
      color: "bg-amber-50 text-amber-700 border-amber-200",
    },
    {
      group: "광고 축소",
      types: "광고 축소형, 소재·구매·반품 복합 리스크형",
      purpose: "광고비 누수를 줄이고 개선 후 재판단",
      color: "bg-rose-50 text-rose-700 border-rose-200",
    },
    {
      group: "반품 리스크",
      types: "반품 리스크 확대 보류형, 구매·반품 복합 리스크형, 소재 개선+반품 주의형, 소수 전환+반품 리스크형",
      purpose: "확대 전 반품 원인과 리뷰 키워드 우선 확인",
      color: "bg-red-50 text-red-700 border-red-200",
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      {/* Heading */}
      <div>
        <h2 className="text-xl font-bold text-slate-800">진단 기준</h2>
        <p className="text-sm text-slate-400 mt-1">
          상품 액션 추천이 어떤 데이터와 기준으로 만들어지는지 확인해보세요.
        </p>
      </div>

      {/* Hero */}
      <div
        className="rounded-2xl p-7 flex items-center justify-between overflow-hidden relative"
        style={{
          background:
            "linear-gradient(135deg, #60A5FA 0%, #93C5FD 50%, #C4B5FD 100%)",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-black/5 pointer-events-none" />
        <div className="absolute -top-12 -right-12 w-52 h-52 rounded-full bg-white/10 pointer-events-none" />

        <div className="relative z-10">
          <p
            className="text-[11px] font-semibold uppercase tracking-widest mb-2"
            style={{ color: "rgba(255,255,255,0.85)" }}
          >
            ActionFit AI 판단 기준
          </p>

          <h2
            className="text-xl font-bold mb-2"
            style={{
              color: "#fff",
              textShadow: "0 1px 6px rgba(30,58,138,0.3)",
            }}
          >
            상품 성과 데이터를 기반으로
          </h2>

          <p
            className="text-sm leading-relaxed max-w-xl"
            style={{ color: "rgba(255,255,255,0.9)" }}
          >
            광고 확대, 유지, 개선, 축소 액션을 판단하는 기준과 리뷰 원인 검증,
            오늘의 추천 액션, 성과 변화 리포트 기준까지 함께 확인할 수 있어요.
          </p>
        </div>
      </div>

      {/* 1. 진단 흐름 요약 */}
      <BasisSection
        defaultOpen
        title="진단 흐름 요약"
        desc="ActionFit AI가 상품 성과 데이터를 분석해 추천 액션을 만드는 전체 흐름입니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        }
      >
        <div className="flex items-start gap-1.5 overflow-x-auto pt-5 pb-2">
          {stepLabels.map((label, i) => (
            <div key={label} className="flex items-start gap-1.5 flex-shrink-0">
              <div className="flex flex-col items-center" style={{ width: 92 }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-2 bg-blue-50 text-blue-600 font-bold text-xs">
                  {i + 1}
                </div>

                <div className="text-[9px] font-bold px-2 py-0.5 rounded-md mb-1.5 whitespace-nowrap bg-blue-100 text-blue-600">
                  STEP {i + 1}
                </div>

                <p className="text-[11px] text-slate-600 text-center leading-snug whitespace-pre-line">
                  {label}
                </p>
              </div>

              {i < stepLabels.length - 1 && (
                <div className="flex-shrink-0 mt-4 pt-0.5">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 rounded-lg border border-blue-100 bg-blue-50">
          <p className="text-[11px] leading-relaxed text-blue-700">
            ActionFit AI는 단순히 숫자 하나만 보고 판단하지 않고, 광고 효율·구매 퍼널·반품 리스크·시즌/카테고리 맥락·리뷰 키워드·이전 분석 대비 변화를 함께 고려합니다.
          </p>
        </div>
      </BasisSection>

      {/* 2. 필수 입력 + 지표 */}
      <div className="grid grid-cols-2 gap-4">
        <BasisSection
          defaultOpen
          title="필수 입력 데이터"
          desc="아래 컬럼이 있어야 상품 액션 추천 분석을 진행할 수 있습니다."
          icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          }
        >
          <div className="flex flex-wrap gap-1.5 pt-5 mb-4">
            {[
              "상품ID",
              
              "상품명",
              "노출수",
              "클릭수",
              "광고과금액",
              "주문금액",
              "상품단가",
              "상품 상세 방문수",
              "장바구니 유저수",
              "찜 유저수",
              "상품주문수",
              "반품건수",
              "판매 사이트",
            ].map((col) => (
              <span
                key={col}
                className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium"
              >
                {col}
              </span>
            ))}
          </div>

          <div className="flex items-start gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50">
            <p className="text-[11px] text-slate-500 leading-relaxed">
              카테고리는 상품명 또는 내부 분류 기준으로 자동 분류할 수 있으며, 시즌 정보는 분석 기간 설정을 통해 자동 분류합니다.
            </p>
          </div>
        </BasisSection>

        <BasisSection
          defaultOpen
          title="자동 계산 지표"
          desc="비율 지표는 업로드된 원본 수치 데이터를 기준으로 자동 계산합니다."
          icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
              <rect x="4" y="2" width="16" height="20" rx="2" />
              <line x1="8" y1="8" x2="16" y2="8" />
            </svg>
          }
        >
          <div className="space-y-2 pt-5 mb-4">
            {metricRows.map((m) => (
              <div
                key={m.name}
                className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100"
              >
                <span className="text-[11px] font-bold text-slate-700 w-28 flex-shrink-0">
                  {m.name}
                </span>
                <code className="text-[10px] text-blue-700 font-mono bg-blue-50 px-2 py-0.5 rounded border border-blue-100 flex-1">
                  {m.formula}
                </code>
                <span className="text-[10px] text-slate-400 flex-shrink-0 hidden xl:block">
                  {m.purpose}
                </span>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-lg border border-amber-200 bg-amber-50">
            <p className="text-[11px] leading-relaxed text-amber-700">
              엑셀에 비율 컬럼이 포함되어 있어도 참고용으로만 활용되며, 분석 기준은 원본 수치로 자동 계산한 값을 우선 적용합니다.
            </p>
          </div>
        </BasisSection>
      </div>

      {/* 3. 광고 확대 추천 점수 */}
      <BasisSection
        defaultOpen
        title="광고 확대 추천 점수"
        desc="상품이 광고비를 더 써도 괜찮은지 판단하기 위한 0~100점 기준입니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="5" />
          </svg>
        }
      >
        <div className="pt-5 space-y-4">
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <p className="text-[10px] font-bold text-blue-500 uppercase tracking-wider mb-1.5">
              계산식
            </p>
            <p className="text-xs font-semibold text-blue-900 leading-relaxed">
              광고 확대 추천 점수 =
              <br />
              <span className="font-normal text-blue-700">
                클릭률 점수 × 0.15 + 찜 관심도 점수 × 0.10 + 장바구니 전환율 점수 × 0.15 + 구매전환율 점수 × 0.25 + 반품 안정성 점수 × 0.15 + ROAS 점수 × 0.20
              </span>
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold text-slate-500 mb-2">
                페널티/보정 기준
              </p>
              <div className="space-y-2">
                {[
                  "구매전환율 1% 미만 → -15점",
                  "ROAS 100 이하 또는 광고비 0으로 ROAS 판단 불가 → -10점",
                  "둘 다 해당 → 최대 -25점",
                  "클릭률은 별도 페널티가 아니라 점수와 진단 유형 분류에 반영",
                ].map((t) => (
                  <p key={t} className="text-xs text-slate-600">
                    • {t}
                  </p>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold text-slate-500 mb-2">
                최종 점수 해석
              </p>
              <div className="space-y-1.5">
                {[
                  ["80점 이상", "예산 확대 가능", "bg-blue-50 text-blue-700 border-blue-200"],
                  ["60~79점", "예산 유지 / 소액 테스트", "bg-emerald-50 text-emerald-700 border-emerald-200"],
                  ["40~59점", "개선 후 재집행", "bg-amber-50 text-amber-700 border-amber-200"],
                  ["40점 미만", "광고 축소 / 보류", "bg-rose-50 text-rose-700 border-rose-200"],
                ].map(([range, label, cls]) => (
                  <div
                    key={range}
                    className={`flex items-center justify-between px-3 py-2 rounded-lg border ${cls}`}
                  >
                    <span className="text-xs">{range}</span>
                    <span className="text-xs font-bold">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </BasisSection>

      {/* 4. 16가지 진단 유형 */}
      <BasisSection
        title="16가지 상품 상태 진단 유형"
        desc="클릭률, 장바구니 전환율, 구매전환율, 반품 안정성을 높음/낮음으로 구분해 상품 상태를 분류합니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z" />
          </svg>
        }
      >
        <div className="pt-5">
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-3 mb-4">
            <p className="text-[11px] text-blue-700 leading-relaxed">
              16가지 진단 유형은 광고 확대 추천 점수와 별개입니다. 점수는 “더 밀어도 되는지”를 판단하고, 16가지 유형은 “현재 상품 상태가 어떤 문제/기회를 갖는지”를 설명합니다.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50">
                  {["클릭률", "장바구니", "구매전환", "반품 안정성", "진단 유형", "추천 방향"].map((h) => (
                    <th
                      key={h}
                      className="text-left text-[11px] font-semibold text-slate-400 px-4 py-3 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {diagnosisRows.map((row) => (
                  <tr key={row[4]} className="hover:bg-slate-50/70">
                    {row.map((cell, i) => (
                      <td
                        key={`${row[4]}-${i}`}
                        className={`px-4 py-3 text-xs ${
                          i === 4 ? "font-bold text-slate-700" : "text-slate-500"
                        }`}
                      >
                        {i < 4 ? (
                          <span
                            className={`px-2 py-0.5 rounded-md border text-[11px] font-semibold ${
                              cell === "높음"
                                ? "bg-blue-50 text-blue-700 border-blue-200"
                                : "bg-slate-50 text-slate-500 border-slate-200"
                            }`}
                          >
                            {cell}
                          </span>
                        ) : (
                          cell
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </BasisSection>

      {/* 5. 오늘의 추천 액션 */}
      <BasisSection
        title="오늘의 추천 액션 선정 기준"
        desc="전체 상품 액션 추천 결과 중 오늘 먼저 확인해야 할 상품만 추려 실행 화면으로 제공합니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
          </svg>
        }
      >
        <div className="pt-5 space-y-4">
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-3">
            <p className="text-[11px] text-blue-700 leading-relaxed">
              오늘의 추천 액션은 전체 분석 결과를 그대로 반복하지 않고, 우선순위가 높은 상품을 1순위 카드, 2~4순위 카드, 액션별 확인 목록으로 나누어 보여줍니다.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50">
                  {["상위 액션 그룹", "포함되는 16가지 진단 유형", "목적"].map((h) => (
                    <th
                      key={h}
                      className="text-left text-[11px] font-semibold text-slate-400 px-4 py-3"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {actionGroupRows.map((row) => (
                  <tr key={row.group}>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-md border font-bold ${row.color}`}>
                        {row.group}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {row.types}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600 font-medium">
                      {row.purpose}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-[11px] text-slate-400">
            화면에서는 상위 액션 그룹을 탭으로 제공하고, 16가지 세부 진단 유형은 드롭다운 필터로 제공해 화면 복잡도를 줄입니다.
          </p>
        </div>
      </BasisSection>

      {/* 6. 리뷰 기반 원인 검증 */}
      <BasisSection
        title="리뷰 기반 원인 검증 기준"
        desc="상품 상세 진단 모달 하단에서 지표 기반 진단 결과의 원인 후보를 리뷰 키워드로 보조 검증합니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        }
      >
        <div className="pt-5 space-y-4">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-[11px] text-amber-700 leading-relaxed">
              리뷰 기반 원인 검증은 광고 확대 추천 점수나 16가지 진단 유형을 새로 판단하는 기능이 아닙니다. 이미 계산된 진단 결과를 리뷰 키워드로 보조 검증하는 역할입니다.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              ["카드 구성", "원인 후보명, 관련 리뷰 키워드, 요약 문장, 개선 힌트로 구성"],
              ["노출 기준", "상품별 진단 유형과 연결된 리뷰 카드만 최대 3개 노출"],
              ["예외 처리", "리뷰 데이터가 부족하면 리뷰 데이터 부족 안내 노출"],
            ].map(([title, desc]) => (
              <div key={title} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p className="text-xs font-bold text-slate-700 mb-1">{title}</p>
                <p className="text-[11px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50">
                  {["키워드 그룹", "리뷰 표현 예시", "연결되는 문제"].map((h) => (
                    <th
                      key={h}
                      className="text-left text-[11px] font-semibold text-slate-400 px-4 py-3"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {reviewKeywordRows.map((row) => (
                  <tr key={row.group}>
                    <td className="px-4 py-3 text-xs font-bold text-slate-700">
                      {row.group}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {row.expressions}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">
                      {row.related}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
            <p className="text-[11px] text-slate-500 leading-relaxed">
              예: “핏 미침”, “핏 예쁨”은 <strong>핏 만족</strong>으로, “사진이랑 다름”, “색감 다름”은 <strong>기대 불일치</strong>로 정규화해 표시합니다.
            </p>
          </div>
        </div>
      </BasisSection>

      {/* 7. 판매 전 시즌·카테고리 진단 */}
      <BasisSection
        title="판매 전 시즌·카테고리 진단 기준"
        desc="판매 전 진단은 개별 상품이 아니라 시즌·카테고리 조합의 판매 가능성을 판단합니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        }
      >
        <div className="pt-5 grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-[11px] font-semibold text-slate-500 mb-2">
              진단 흐름
            </p>
            <div className="space-y-2">
              {[
                "사용자가 판매 예정 시즌과 카테고리를 선택",
                "동일 시즌·동일 카테고리 기존 상품 데이터 필터링",
                "상품별 지표 계산 후 백분위 점수화",
                "시즌·카테고리 조합의 중앙값 계산",
                "카테고리 시즌 적합도 점수 산정",
                "판매 추천 / 테스트 판매 / 보류로 분류",
              ].map((t, i) => (
                <p key={t} className="text-xs text-slate-600">
                  <span className="inline-flex w-5 h-5 rounded bg-blue-50 text-blue-600 items-center justify-center text-[10px] font-bold mr-2">
                    {i + 1}
                  </span>
                  {t}
                </p>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-[11px] font-semibold text-blue-700 mb-2">
              계산식
            </p>
            <p className="text-xs text-blue-700 leading-relaxed">
              카테고리 시즌 적합도 점수 =
              <br />
              (클릭률 점수 + 찜 관심도 점수 + 장바구니 전환율 점수 + 구매전환율 점수 + 반품 안정성 점수 + ROAS 점수) / 6
            </p>

            <div className="mt-4 space-y-2">
              {[
                ["75점 이상", "판매 추천", "bg-blue-50 text-blue-700 border-blue-200"],
                ["50~74점", "테스트 판매", "bg-emerald-50 text-emerald-700 border-emerald-200"],
                ["50점 미만", "보류", "bg-rose-50 text-rose-700 border-rose-200"],
              ].map(([range, label, cls]) => (
                <div
                  key={range}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg border bg-white ${cls}`}
                >
                  <span className="text-xs">{range}</span>
                  <span className="text-xs font-bold">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </BasisSection>

      {/* 8. 성과 변화 리포트 */}
      <BasisSection
        title="액션 실행 후 성과 변화 리포트 기준"
        desc="이전 분석 파일과 새 분석 파일을 비교해 추천 이후 성과 변화를 확인합니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>
        }
      >
        <div className="pt-5 space-y-4">
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-3">
            <p className="text-[11px] text-blue-700 leading-relaxed">
              사용자가 실제로 추천 액션을 실행했는지 별도로 기록하지 않는 경우, 리포트는 “액션 효과”를 단정하지 않고 “이전 추천 이후 기간의 성과 변화”로 표현합니다.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              ["개선", "ROAS, 구매전환율, 반품 안정성 등 핵심 지표가 이전 대비 좋아진 상품"],
              ["유지", "주요 지표가 큰 하락 없이 안정적으로 유지된 상품"],
              ["추가 개선 필요", "전환, ROAS, 반품 지표 중 하나 이상이 악화되거나 기준 미달인 상품"],
            ].map(([title, desc]) => (
              <div key={title} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p className="text-xs font-bold text-slate-700 mb-1">{title}</p>
                <p className="text-[11px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-[11px] font-semibold text-slate-500 mb-2">
              리포트 요약 생성 기준
            </p>
            <p className="text-xs text-slate-600 leading-relaxed">
              매칭된 상품 수, 개선 상품 수, 유지 상품 수, 추가 개선 필요 상품 수를 비교해 “전반적으로 개선”, “전반적으로 유지”, “추가 개선 필요” 중 하나의 요약 문구를 자동 생성합니다.
            </p>
          </div>
        </div>
      </BasisSection>

      {/* 9. 데이터 부족 및 예외 처리 */}
      <BasisSection
        title="데이터 부족 및 예외 처리 기준"
        desc="표본이 부족하거나 필수 데이터가 누락된 경우 무리하게 판단하지 않습니다."
        icon={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        }
      >
        <div className="pt-5 space-y-2">
          {[
            ["필수 컬럼 누락", "분석 불가", "필수 컬럼을 추가한 뒤 다시 업로드해주세요."],
            ["노출수 또는 클릭수 0", "클릭률 계산 제외", "클릭률 계산이 어려워 일부 판단에서 제외됩니다."],
            ["광고비 0", "ROAS 계산 제한", "ROAS 판단이 어려워 보수적으로 처리합니다."],
            ["상품 상세 방문수 0", "전환율 계산 제외", "상세페이지 이후 퍼널 분석이 어렵습니다."],
            ["상품주문수 0", "반품 안정성 보수 처리", "주문 데이터가 부족해 반품 안정성은 기본값 또는 보수 점수로 처리합니다."],
            ["리뷰 데이터 부족", "리뷰 카드 미노출", "리뷰 기반 원인 검증 대신 데이터 부족 안내를 표시합니다."],
          ].map(([situation, handling, guide]) => (
            <div
              key={situation}
              className="px-3 py-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-start gap-3"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-semibold text-slate-700">
                    {situation}
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {handling}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">{guide}</p>
              </div>
            </div>
          ))}
        </div>
      </BasisSection>

      {/* 주의 사항 */}
      <div className="rounded-xl border border-slate-200 p-5 flex items-start gap-4 bg-white">
        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-600 mb-1">주의 사항</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            ActionFit AI의 진단 결과는 업로드된 상품 성과 데이터와 설정된 분석 기준을 바탕으로 한 참고용 추천입니다. 실제 매출, 광고 성과, 소비자 반응을 보장하지 않으며, 최종 광고 운영 판단은 판매자의 상품 특성, 재고, 가격, 시즌 전략 등을 함께 고려해 결정해야 합니다.
          </p>
        </div>
      </div>

      <div className="flex items-center pb-2">
        <button
          onClick={() => setScreen("main")}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          메인으로 돌아가기
        </button>
      </div>
    </div>
  );
}