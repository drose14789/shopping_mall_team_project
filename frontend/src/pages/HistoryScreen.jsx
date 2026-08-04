import { useState, useEffect  } from "react";
import { HISTORY_PAGE_SIZE } from "../constants/data"; // 경로에 맞게 수정
import { getSeasonStyle, getClientUuid  } from "../utils/helpers";


export default function HistoryScreen({setScreen,setSelectedFile}) {
    const [historyData, setHistoryData] = useState([]);
    const [historyPage, setHistoryPage] = useState(0);
    const historyPageCount = Math.max(1, Math.ceil(historyData.length / HISTORY_PAGE_SIZE));
    const historyPageStart = historyPage * HISTORY_PAGE_SIZE;
    const historyPageEnd = Math.min(historyPageStart + HISTORY_PAGE_SIZE, historyData.length);
    const pagedHistory = historyData.slice(historyPageStart, historyPageEnd);
    useEffect(() => {

    const client_uuid = getClientUuid();

    fetch(
        `http://localhost:8000/score/history/${client_uuid}`
    )
    .then(res => res.json())
    .then(data => {

        console.log("History 데이터:", data);

        setHistoryData(
            Array.isArray(data)
            ? data
            : []
        );

    })
    .catch(err => {
        console.error(
            "History 조회 실패",
            err
        );
    });

}, []);
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-800">
          분석 이력
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          업로드한 파일과 분석 회차별 결과를 확인할 수 있습니다.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
      {[
            {
                label: "총 분석 회차",
                value: "4회",
                sub: "최근 3개월 기준",
            },
            {
                label: "저장된 분석 기간",
                value: "최근 3개월",
                sub: "동일 브라우저 기준",
            },
            {
                label: "최근 분석일",
                value: "2026.05.20",
                sub: "상품성과_20260520.xlsx",
            },
        ].map((s) => (<div key={s.label} className="bg-white rounded-xl border border-slate-100 p-4">
            <p className="text-xs text-slate-400 font-semibold mb-1">
              {s.label}
            </p>
            <p className="text-xl font-bold text-slate-800 mb-0.5">
              {s.value}
            </p>
            <p className="text-[11px] text-slate-400">
              {s.sub}
            </p>
          </div>))}
      </div>

      {/* History table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800 text-sm">
            분석 목록
          </h3>
          <button onClick={() => setScreen("upload")} className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border transition" style={{
            color: "#2563EB",
            backgroundColor: "#EFF6FF",
            borderColor: "#BFDBFE",
        }} onMouseEnter={(e) => (e.currentTarget.style.backgroundColor =
            "#DBEAFE")} onMouseLeave={(e) => (e.currentTarget.style.backgroundColor =
            "#EFF6FF")}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            새 파일 업로드
          </button>
        </div>
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50">
              {[
            "분석일",
            "파일명",
            "분석 기간",
            "분석 시즌",
            "상품 수",
            "결과 보기",
        ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3 whitespace-nowrap">
                  {h}
                </th>))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {pagedHistory.map((row) => (<tr key={row.file_name} className="hover:bg-slate-50/70 transition-colors">
                <td className="px-5 py-3.5 text-xs font-medium text-slate-700 whitespace-nowrap">
                  {row.created_at?.slice(0,10)}
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-emerald-100 flex items-center justify-center flex-shrink-0">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                    </div>
                    <span className="text-xs text-slate-600 font-medium">
                      {row.file_name}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-xs text-slate-500">
                  {row.analysis_start_time}
                  ~
                  {row.analysis_end_time}
                </td>
                <td className="px-5 py-3.5">
                  {(() => {
                const seasonStyle = getSeasonStyle(row.quarter);
                return (<span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border font-semibold whitespace-nowrap" style={{
                        backgroundColor: seasonStyle.bg,
                        color: seasonStyle.text,
                        borderColor: seasonStyle.border,
                    }}>
                        <span>{seasonStyle.emoji}</span>
                        {row.quarter}
                      </span>);
            })()}
                </td>
                <td className="px-5 py-3.5 text-xs font-semibold text-slate-700 whitespace-nowrap">
                  {row.product_count}
                </td>
                <td className="px-5 py-3.5">
                 <button onClick={() => {setSelectedFile(row.file_name);setScreen("results");}} className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline transition flex items-center gap-1 whitespace-nowrap">
                    결과 보기
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </button>
                </td>
              </tr>))}
          </tbody>
          </table>

          {historyData.length > HISTORY_PAGE_SIZE && (<div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/50">
              <p className="text-[11px] text-slate-400">
                {historyPageStart + 1}–{historyPageEnd} /{" "}
                <strong className="text-slate-600">
                  {historyData.length}
                </strong>
                건
              </p>

              <div className="flex items-center gap-1">
                <button type="button" onClick={() => setHistoryPage((p) => Math.max(0, p - 1))} disabled={historyPage === 0} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${historyPage === 0
                ? "text-slate-300 border-slate-150 cursor-not-allowed"
                : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                  이전
                </button>

                {Array.from({ length: historyPageCount }, (_, i) => (<button key={i} type="button" onClick={() => setHistoryPage(i)} className={`w-7 h-7 rounded-lg text-[11px] font-semibold transition ${historyPage === i
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-100 border border-slate-200"}`}>
                      {i + 1}
                    </button>))}

                <button type="button" onClick={() => setHistoryPage((p) => Math.min(historyPageCount - 1, p + 1))} disabled={historyPage >= historyPageCount - 1} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition ${historyPage >= historyPageCount - 1
                ? "text-slate-300 border-slate-150 cursor-not-allowed"
                : "text-slate-600 border-slate-200 hover:bg-slate-100"}`}>
                  다음
                </button>
              </div>
            </div>)}
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