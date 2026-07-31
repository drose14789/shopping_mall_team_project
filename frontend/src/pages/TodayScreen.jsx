import { TODAY_DATA, TODAY_FILTERS } from "../constants/data"; 
import { actionBadge } from "../utils/helpers"; 

export default function TodayScreen({ setScreen, }) {
    const [activeTab, setActiveTab] = useState("전체");
    const hasData = true;
    const filtered = TODAY_DATA.filter((r) => {
        if (activeTab === "전체")
            return true;
        if (activeTab === "예산 확대 우선")
            return r.action === "예산 확대";
        if (activeTab === "개선 후 재집행 우선")
            return r.action === "개선 후 재집행";
        if (activeTab === "광고 축소 검토")
            return r.action === "광고 축소";
        if (activeTab === "반품 리스크")
            return r.reason.includes("반품");
        if (activeTab === "우선순위 높음")
            return r.rank <= 3;
        return true;
    });
    if (!hasData) {
        return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            오늘의 추천 액션
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            가장 최근 분석 결과를 기준으로 우선 확인해야 할
            상품을 정리해드려요.
          </p>
        </div>
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-5 text-3xl">
            🎯
          </div>
          <p className="text-base font-semibold text-slate-700 mb-2">
            아직 생성된 추천 액션이 없습니다.
          </p>
          <p className="text-sm text-slate-400 leading-relaxed mb-6">
            상품 성과 파일을 업로드하면 광고 확대, 유지,
            <br />
            개선, 축소 후보를 확인할 수 있어요.
          </p>
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
        </div>
      </div>);
    }
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            오늘의 추천 액션
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            최근 분석 결과를 기준으로 우선 확인해야 할 상품을
            정리했어요.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          상품성과_20260520.xlsx 기준
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
            {
                label: "우선 확인 상품",
                value: "12개",
                icon: "🎯",
                border: "border-blue-200",
                bg: "#EFF6FF",
                text: "#1D4ED8",
                sub: "전체 분석 결과 기준",
            },
            {
                label: "예산 확대 우선",
                value: "5개",
                icon: "📈",
                border: "border-emerald-200",
                bg: "#ECFDF5",
                text: "#065F46",
                sub: "ROAS · CTR 상위 기준",
            },
            {
                label: "개선 필요 우선",
                value: "4개",
                icon: "🔧",
                border: "border-amber-200",
                bg: "#FFFBEB",
                text: "#92400E",
                sub: "퍼널 병목 감지 기준",
            },
            {
                label: "광고 축소 검토",
                value: "3개",
                icon: "📉",
                border: "border-rose-200",
                bg: "#FFF1F2",
                text: "#9F1239",
                sub: "ROAS 기준 미달",
            },
        ].map((s) => (<div key={s.label} className={`rounded-xl border p-4 ${s.border}`} style={{ backgroundColor: s.bg }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{s.icon}</span>
              <p className="text-xs font-semibold text-slate-500">
                {s.label}
              </p>
            </div>
            <p className="text-2xl font-bold mb-0.5" style={{ color: s.text }}>
              {s.value}
            </p>
            <p className="text-[11px] text-slate-400">
              {s.sub}
            </p>
          </div>))}
      </div>

      {/* Filter tabs + table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="flex items-center gap-1 px-4 pt-4 pb-0 border-b border-slate-100 overflow-x-auto">
          {TODAY_FILTERS.map((tab) => (<button key={tab} onClick={() => setActiveTab(tab)} className={`flex-shrink-0 px-3 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${activeTab === tab ? "border-blue-500 text-blue-700 bg-blue-50/60" : "border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-50"}`}>
              {tab}
            </button>))}
          <div className="flex-1"/>
          <button onClick={() => setScreen("results")} className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 mb-1 text-xs font-semibold text-slate-500 hover:text-blue-600 transition rounded-lg hover:bg-blue-50">
            전체 결과 보기
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>

        {filtered.length === 0 ? (<div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-2xl">
              📋
            </div>
            <p className="text-sm font-semibold text-slate-500 mb-1">
              해당 조건의 상품이 없습니다
            </p>
            <p className="text-xs text-slate-400">
              다른 필터를 선택해보세요.
            </p>
          </div>) : (<table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                {[
                "우선순위",
                "상품명",
                "카테고리",
                "추천 액션",
                "추천 이유",
                "기대 효과",
                "상세 보기",
            ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3">
                    {h}
                  </th>))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filtered.map((row) => (<tr key={row.rank} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs" style={row.rank === 1
                    ? {
                        backgroundColor: "#EFF6FF",
                        color: "#2563EB",
                    }
                    : row.rank === 2
                        ? {
                            backgroundColor: "#FFF7ED",
                            color: "#C2410C",
                        }
                        : row.rank === 3
                            ? {
                                backgroundColor: "#FFF1F2",
                                color: "#BE123C",
                            }
                            : {
                                backgroundColor: "#F8FAFC",
                                color: "#64748B",
                            }}>
                      {row.rank}
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-xs font-medium text-slate-700 whitespace-nowrap">
                    {row.name}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500">
                    {row.cat}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`text-xs px-2 py-1 rounded-md border font-medium ${actionBadge(row.action)}`}>
                      {row.action}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500 max-w-[180px]">
                    {row.reason}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-600 font-medium max-w-[160px]">
                    {row.effect}
                  </td>
                  <td className="px-5 py-3.5">
                    <button onClick={() => setScreen("detail")} className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline transition flex items-center gap-1">
                      상세 보기
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </button>
                  </td>
                </tr>))}
            </tbody>
          </table>)}
      </div>

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