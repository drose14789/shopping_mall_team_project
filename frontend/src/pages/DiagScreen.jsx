import { useState } from "react";
import { DiagIllustration } from '../components/common/Icons';
import { DIAG_CATEGORIES, DIAG_SEASONS, MOCK_DIAG_RESULT } from "../constants/data";


export default function DiagScreen({ setScreen, }) {
    const [category, setCategory] = useState("");
    const [season, setSeason] = useState("");
    const [budget, setBudget] = useState("");
    const [showResult, setShowResult] = useState(false);
    const [noData, setNoData] = useState(false);
    const canDiag = category !== "" && season !== "";
    const handleDiag = () => {
        if (!canDiag)
            return;
        // Simulate no-data for '니트' + '여름' combo
        if (category === "니트" && season === "여름") {
            setNoData(true);
            setShowResult(true);
        }
        else {
            setNoData(false);
            setShowResult(true);
        }
    };
    const result = MOCK_DIAG_RESULT;
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
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              판매 예정 카테고리{" "}
              <span className="text-rose-500">*</span>
            </label>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition">
              <option value="">카테고리를 선택해주세요</option>
              {DIAG_CATEGORIES.map((c) => (<option key={c} value={c}>
                  {c}
                </option>))}
            </select>
          </div>

          {/* Season */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-2">
              판매 예정 시즌{" "}
              <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-4 gap-2">
              {DIAG_SEASONS.map((s) => (<button key={s} onClick={() => setSeason(s)} className={`py-2.5 rounded-lg text-sm font-semibold border transition-all ${season === s ? "border-blue-400 text-blue-700" : "border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600"}`} style={season === s
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

          {/* Budget */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              예상 일 광고 예산
              <span className="ml-1.5 text-[10px] font-normal text-slate-400">
                (선택)
              </span>
            </label>
            <input type="text" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="예: 30,000원" className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition"/>
            <p className="text-[11px] text-slate-400 mt-1.5">
              추천 액션 문구를 구체화하는 참고값으로만
              활용됩니다.
            </p>
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
                구매전환율 + 장바구니 전환율 + 찜 관심도 + 반품
                안정성 + ROAS 점수의 평균
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
                선택한 카테고리와 시즌에 대한 기존 분석 데이터가
                충분하지 않아 정확한 진단이 어렵습니다.
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
                {/* Summary text */}
                <div className="mt-3 p-4 rounded-xl border border-slate-100 bg-white">
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {result.summary}
                  </p>
                </div>
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
                    "카테고리 평균",
                    "전체 평균",
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
                            <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center flex-shrink-0 ${m.good ? "bg-emerald-100" : "bg-rose-100"}`}>
                              {m.good ? (<svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="3">
                                  <polyline points="20 6 9 17 4 12"/>
                                </svg>) : (<svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#e11d48" strokeWidth="3" strokeLinecap="round">
                                  <line x1="18" y1="6" x2="6" y2="18"/>
                                  <line x1="6" y1="6" x2="18" y2="18"/>
                                </svg>)}
                            </div>
                            <span className={`text-xs font-semibold ${m.good ? "text-emerald-700" : "text-rose-600"}`}>
                              {m.verdict}
                            </span>
                          </div>
                        </td>
                      </tr>))}
                  </tbody>
                </table>
              </div>

              {/* Recommended direction */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-800 text-sm mb-4">
                  추천 운영 방향
                </h3>
                <div className="space-y-3">
                  {[
                    "초기 광고 예산은 소액 테스트로 시작하고, 클릭률과 장바구니 전환율을 확인하세요.",
                    `${category} 카테고리는 착용컷과 소재감 설명이 구매 결정에 중요하므로 상세페이지에 핏, 두께감, 비침 여부를 명확히 적어주세요.`,
                    "반품 리스크를 줄이기 위해 사이즈 정보와 모델 착용 정보를 함께 제공하는 것이 좋습니다.",
                    "첫 판매 후 1~2주 내 상품 성과 파일을 다시 업로드해 실제 광고 확대 여부를 판단하세요.",
                ].map((action, i) => (<div key={i} className="flex items-start gap-3">
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

              {/* Data basis */}
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-800 text-sm mb-3">
                  분석 기준
                </h3>
                <div className="space-y-1.5 mb-3">
                  {[
                    "최근 업로드된 상품 성과 데이터 기준",
                    `같은 시즌(${season})·같은 카테고리(${category}) 상품과 비교`,
                    "구매전환율, 장바구니 전환율, 찜 관심도, 반품 안정성, ROAS를 종합해 점수화",
                    "이전 기간 데이터가 있는 경우 추세 비교 가능",
                    "이전 기간 데이터가 없는 경우 현재 분석 데이터 기준으로만 판단",
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