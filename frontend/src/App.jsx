import { useEffect, useRef, useState } from "react";
/* ══════════════════════════════════════
   Icons
══════════════════════════════════════ */
function HomeIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>);
}
function ChartIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>);
}
function DiagIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>);
}
function ChatIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
    </svg>);
}
function BasisIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>);
}
/* ══════════════════════════════════════
   Sidebar
══════════════════════════════════════ */
const NAV_ITEMS = [
    { id: "main", label: "메인", Icon: HomeIcon },
    { id: "upload", label: "상품 액션 추천", Icon: ChartIcon },
    { id: "diag", label: "판매 전 진단", Icon: DiagIcon },
    { id: "chat", label: "법 규제 챗봇", Icon: ChatIcon },
    { id: "basis", label: "진단 기준", Icon: BasisIcon },
];
function Sidebar({ screen, setScreen, }) {
    const activeId = screen === "main"
        ? "main"
        : screen === "diag"
            ? "diag"
            : screen === "chat"
                ? "chat"
                : screen === "basis"
                    ? "basis"
                    : "upload";
    return (<aside className="w-56 min-h-screen bg-white border-r border-slate-100 flex flex-col flex-shrink-0">
      <div className="px-5 py-5 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
          </div>
          <span className="font-bold text-slate-800 text-[15px] tracking-tight">
            ActionFit AI
          </span>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-3 mb-2">
          메뉴
        </p>
        {NAV_ITEMS.map(({ id, label, Icon }) => {
            const isActive = activeId === id;
            const clickable = id === "main" ||
                id === "upload" ||
                id === "diag" ||
                id === "chat" ||
                id === "basis";
            return (<button key={id} onClick={() => clickable && setScreen(id)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-sm font-medium transition-colors relative ${isActive ? "text-blue-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"}`} style={isActive ? { backgroundColor: "#EFF6FF" } : {}}>
              {isActive && (<span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full" style={{ backgroundColor: "#3B82F6" }}/>)}
              <Icon active={isActive}/>
              {label}
            </button>);
        })}
      </nav>
      <div className="px-4 py-4 border-t border-slate-100">
        <p className="text-[10px] text-slate-400">
          © 2026 ActionFit AI
        </p>
      </div>
    </aside>);
}
/* ══════════════════════════════════════
   Topbar
══════════════════════════════════════ */
function Topbar({ subtitle }) {
    return (<header className="h-14 bg-white border-b border-slate-100 flex items-center px-6 gap-4 flex-shrink-0">
      <div className="flex items-center gap-3 flex-1">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="상품명, 카테고리, 키워드 검색" className="w-72 pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition"/>
        </div>
        {subtitle && (<>
            <span className="text-slate-200 text-sm">|</span>
            <span className="text-sm font-semibold text-slate-500">
              {subtitle}
            </span>
          </>)}
      </div>
    </header>);
}
/* ══════════════════════════════════════
   Illustrations
══════════════════════════════════════ */
function DashboardIllustration() {
    return (<svg width="260" height="160" viewBox="0 0 260 160" fill="none">
      <circle cx="200" cy="80" r="60" fill="rgba(255,255,255,0.07)"/>
      <circle cx="200" cy="80" r="40" fill="rgba(255,255,255,0.07)"/>
      <rect x="40" y="90" width="20" height="50" rx="4" fill="rgba(255,255,255,0.35)"/>
      <rect x="68" y="70" width="20" height="70" rx="4" fill="rgba(255,255,255,0.5)"/>
      <rect x="96" y="48" width="20" height="92" rx="4" fill="rgba(255,255,255,0.7)"/>
      <rect x="124" y="62" width="20" height="78" rx="4" fill="rgba(255,255,255,0.55)"/>
      <rect x="152" y="32" width="20" height="108" rx="4" fill="white"/>
      <polyline points="50,90 78,70 106,48 134,62 162,32" stroke="rgba(255,255,255,0.9)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      <circle cx="50" cy="90" r="4" fill="white"/>
      <circle cx="78" cy="70" r="4" fill="white"/>
      <circle cx="106" cy="48" r="4" fill="white"/>
      <circle cx="134" cy="62" r="4" fill="white"/>
      <circle cx="162" cy="32" r="5.5" fill="white"/>
      <rect x="170" y="18" width="76" height="40" rx="9" fill="white" fillOpacity="0.96"/>
      <rect x="180" y="26" width="24" height="4" rx="2" fill="#2563eb"/>
      <rect x="180" y="34" width="36" height="3" rx="1.5" fill="#e2e8f0"/>
      <rect x="180" y="40" width="28" height="3" rx="1.5" fill="#e2e8f0"/>
      <circle cx="228" cy="30" r="8" fill="#eff6ff"/>
      <path d="M225 30l2 2 4-4" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="182" y="98" width="60" height="26" rx="7" fill="white" fillOpacity="0.96"/>
      <circle cx="196" cy="111" r="5" fill="#eff6ff"/>
      <rect x="206" y="108" width="28" height="3" rx="1.5" fill="#2563eb"/>
      <rect x="206" y="114" width="20" height="2.5" rx="1.25" fill="#e2e8f0"/>
    </svg>);
}
function UploadIllustration() {
    return (<svg width="200" height="130" viewBox="0 0 200 130" fill="none">
      <rect x="20" y="20" width="90" height="90" rx="10" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.45)" strokeWidth="1.5"/>
      <line x1="20" y1="42" x2="110" y2="42" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <line x1="20" y1="60" x2="110" y2="60" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <line x1="20" y1="78" x2="110" y2="78" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <line x1="20" y1="96" x2="110" y2="96" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <line x1="65" y1="20" x2="65" y2="110" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <circle cx="158" cy="65" r="32" fill="rgba(255,255,255,0.14)"/>
      <circle cx="158" cy="65" r="20" fill="rgba(255,255,255,0.18)"/>
      <path d="M150 67l8-8 8 8M158 59v15" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M147 77h22" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <rect x="28" y="27" width="26" height="9" rx="2" fill="rgba(255,255,255,0.7)"/>
      <rect x="28" y="48" width="26" height="4" rx="1" fill="rgba(255,255,255,0.4)"/>
      <rect x="28" y="66" width="20" height="4" rx="1" fill="rgba(255,255,255,0.4)"/>
      <rect x="28" y="84" width="24" height="4" rx="1" fill="rgba(255,255,255,0.4)"/>
    </svg>);
}
const TABLE_DATA = [
    {
        date: "2026.05.20",
        file: "상품성과_20260520.xlsx",
        period: "2026.03~2026.05",
        season: "봄",
    },
    {
        date: "2026.04.20",
        file: "상품성과_20260420.xlsx",
        period: "2026.01~2026.03",
        season: "겨울",
    },
    {
        date: "2026.03.15",
        file: "상품성과_20260315.xlsx",
        period: "2025.12~2026.02",
        season: "겨울",
    },
    {
        date: "2026.02.10",
        file: "상품성과_20260210.xlsx",
        period: "2025.10~2025.12",
        season: "가을",
    },
];
function seasonBadgeStyle(season) {
    if (season.includes("겨울")) {
        return {
            emoji: "❄️",
            className: "bg-emerald-50 text-emerald-700 border-emerald-200",
        };
    }
    if (season.includes("봄")) {
        return {
            emoji: "🌸",
            className: "bg-pink-50 text-pink-700 border-pink-200",
        };
    }
    if (season.includes("여름")) {
        return {
            emoji: "☀️",
            className: "bg-blue-50 text-blue-700 border-blue-200",
        };
    }
    if (season.includes("가을")) {
        return {
            emoji: "🍂",
            className: "bg-amber-50 text-amber-800 border-amber-200",
        };
    }
    return {
        emoji: "📌",
        className: "bg-slate-50 text-slate-600 border-slate-200",
    };
}
const actionBadge = (a) => ({
    "예산 확대": "bg-blue-50 text-blue-700 border-blue-200",
    "예산 유지": "bg-emerald-50 text-emerald-700 border-emerald-200",
    "개선 후 재집행": "bg-amber-50 text-amber-700 border-amber-200",
    "광고 축소": "bg-rose-50 text-rose-700 border-rose-200",
    "핵심 확대형": "bg-blue-50 text-blue-700 border-blue-200",
    "상세페이지 개선형": "bg-amber-50 text-amber-700 border-amber-200",
    "구매 직전 이탈형": "bg-orange-50 text-orange-700 border-orange-200",
    "반품 리스크형": "bg-red-50 text-red-700 border-red-200",
    "광고 축소형": "bg-rose-50 text-rose-700 border-rose-200",
})[a] ?? "bg-slate-50 text-slate-600 border-slate-200";
const priorityCls = (p) => ({
    높음: "text-rose-600 font-semibold",
    보통: "text-amber-600 font-semibold",
    낮음: "text-slate-400",
})[p] ?? "";
const statusBadge = (s) => ({
    완료: "bg-emerald-50 text-emerald-700",
    진행중: "bg-blue-50 text-blue-700",
    대기: "bg-slate-100 text-slate-500",
})[s] ?? "";
/* ══════════════════════════════════════
   화면 1 — 메인 화면
══════════════════════════════════════ */
function MainScreen({ setScreen, }) {
    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-5">
      {/* Hero */}
      <div className="rounded-2xl p-7 flex items-center justify-between overflow-hidden relative" style={{
            background: "linear-gradient(135deg, #60A5FA 0%, #93C5FD 50%, #C4B5FD 100%)",
        }}>
        {/* Subtle dark overlay for text legibility */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-black/5 pointer-events-none"/>
        {/* Soft highlight ring top-right */}
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/10 pointer-events-none"/>
        <div className="absolute top-6 right-40 w-32 h-32 rounded-full bg-white/8 pointer-events-none"/>

        <div className="relative z-10 max-w-md">
          <p className="text-[11px] font-semibold uppercase tracking-widest mb-3" style={{
            color: "rgba(255,255,255,0.85)",
            textShadow: "0 1px 4px rgba(30,58,138,0.25)",
        }}>
            ActionFit AI
          </p>
          <h1 className="text-[22px] font-bold leading-snug mb-1" style={{
            color: "#fff",
            textShadow: "0 1px 6px rgba(30,58,138,0.3)",
        }}>
            여성 패션 셀러를 위한
          </h1>
          <h1 className="text-[22px] font-bold leading-snug mb-4" style={{
            color: "#fff",
            textShadow: "0 1px 6px rgba(30,58,138,0.3)",
        }}>
            상품별 마케팅 액션 추천 서비스
          </h1>
          <p className="text-sm leading-relaxed mb-6" style={{
            color: "rgba(255,255,255,0.9)",
            textShadow: "0 1px 4px rgba(30,58,138,0.2)",
        }}>
            상품 성과 데이터를 분석해 광고 확대, 유지, 개선, 축소 등 16가지 유형 액션을 제안하고
            <br />
            쇼핑몰 운영에 필요한 법 규제 리스크까지 함께
            확인합니다.
          </p>
          <button onClick={() => setScreen("upload")} className="bg-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-md hover:bg-blue-50 transition flex items-center gap-2" style={{ color: "#2563EB" }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            상품 성과 파일 업로드하기
          </button>
        </div>
        <div className="relative z-10 hidden lg:block">
          <DashboardIllustration />
        </div>
      </div>

      {/* Analysis flow summary */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-start justify-between gap-4 mb-5">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#2563EB"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>

              <h3 className="font-semibold text-slate-800 text-sm">
                ActionFit AI 분석 흐름
              </h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              상품 성과 파일을 업로드하면 아래 흐름에 따라 오늘 실행할 추천 액션을 생성합니다.
            </p>
          </div>

          <button
            onClick={() => setScreen("basis")}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition"
          >
            진단 기준 보기
            <svg
              width="11"
              height="11"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>

        <div className="flex items-start gap-1.5 overflow-x-auto pb-2">
          {[
            {
              step: "1",
              title: "파일 업로드",
              desc: "상품 성과 파일 등록",
              icon: "📤",
            },
            {
              step: "2",
              title: "데이터 정제",
              desc: "필수 컬럼 확인",
              icon: "🧾",
            },
            {
              step: "3",
              title: "지표 계산",
              desc: "CTR·ROAS 등 계산",
              icon: "🧮",
            },
            {
              step: "4",
              title: "시즌·카테고리 비교",
              desc: "동일 맥락 비교",
              icon: "📊",
            },
            {
              step: "5",
              title: "16가지 유형 분류",
              desc: "상품 상태 진단",
              icon: "🏷️",
            },
            {
              step: "6",
              title: "리뷰 원인 검증",
              desc: "키워드 보조 분석",
              icon: "💬",
            },
            {
              step: "7",
              title: "오늘의 액션",
              desc: "우선순위 추천",
              icon: "🎯",
            },
            {
              step: "8",
              title: "성과 리포트",
              desc: "변화 비교",
              icon: "📈",
            },
          ].map((item, i, arr) => (
            <div key={item.step} className="flex items-start gap-1.5 flex-shrink-0">
              <div className="flex flex-col items-center" style={{ width: 98 }}>
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center mb-2 text-lg">
                  {item.icon}
                </div>

                <div className="text-[9px] font-bold px-2 py-0.5 rounded-md mb-1.5 whitespace-nowrap bg-blue-100 text-blue-600">
                  STEP {item.step}
                </div>

                <p className="text-[11px] font-bold text-slate-700 text-center leading-snug">
                  {item.title}
                </p>

                <p className="text-[10px] text-slate-400 text-center leading-snug mt-0.5">
                  {item.desc}
                </p>
              </div>

              {i < arr.length - 1 && (
                <div className="flex-shrink-0 mt-5 pt-0.5">
                  <svg
                    width="11"
                    height="11"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#CBD5E1"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 rounded-lg border border-blue-100 bg-blue-50">
          <p className="text-[11px] leading-relaxed text-blue-700">
            ActionFit AI는 단순히 점수 하나만 보고 판단하지 않고, 광고 효율·구매 퍼널·반품 리스크·시즌/카테고리 맥락·리뷰 키워드·이전 분석 대비 변화를 함께 고려합니다.
          </p>
        </div>
      </div>

      {/* Summary + Table */}
      <div className="flex gap-4">
        <div className="w-60 flex-shrink-0 bg-white rounded-xl border border-slate-100 p-5">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800 text-sm">
              최근 분석 요약
            </h3>
            <span className="text-[10px] text-slate-400">
              2026.05.20 기준
            </span>
          </div>

          <p className="text-[10px] text-slate-600 font-medium leading-relaxed mt-2 bg-slate-50 border border-slate-100 rounded-lg px-2.5 py-2">
            최근 분석 결과에서 가장 많이 나온 추천 유형 4개를 요약했어요.
          </p>
        </div>
          <div className="space-y-3">
          {[
            {
                label: "상세페이지 개선형",
                count: "42개",
                pct: "상세 정보 보강",
                dot: "bg-amber-500",
            },
            {
                label: "핵심 확대형",
                count: "32개",
                pct: "광고 예산 확대",
                dot: "bg-blue-500",
            },
            {
                label: "광고 축소형",
                count: "21개",
                pct: "광고비 축소·보류",
                dot: "bg-rose-400",
            },
            {
                label: "반품 리스크형",
                count: "18개",
                pct: "반품 원인 점검",
                dot: "bg-red-500",
            }
        ].map((item) => (<div key={item.label} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${item.dot} flex-shrink-0`}/>
                <p className="flex-1 text-xs text-slate-500 truncate">
                  {item.label}
                </p>
                <div className="text-right">
                  <p className="text-sm font-bold text-slate-800">
                    {item.count}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {item.pct}
                  </p>
                </div>
              </div>))}
          </div>
        </div>
        <div className="flex-1 bg-white rounded-xl border border-slate-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-semibold text-slate-800 text-sm">
              최근 분석 미리보기
            </h3>
            <button onClick={() => setScreen("history")} className="text-blue-600 text-xs font-semibold hover:underline">
              전체 보기
            </button>
          </div>
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                {[
            "분석일",
            "파일명",
            "데이터 기간",
            "분석 시즌",
        ].map((h) => (<th key={h} className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wide px-5 py-3">
                    {h}
                  </th>))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
            {TABLE_DATA.map((row) => {
            const seasonStyle = seasonBadgeStyle(row.season);
            return (<tr key={row.file} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-3 text-xs font-medium text-slate-700 whitespace-nowrap">
                      {row.date}
                    </td>

                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-emerald-100 flex items-center justify-center flex-shrink-0">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                          </svg>
                        </div>
                        <span className="text-xs text-slate-600 font-medium whitespace-nowrap">
                          {row.file}
                        </span>
                      </div>
                    </td>

                    <td className="px-5 py-3 text-xs text-slate-500 whitespace-nowrap">
                      {row.period}
                    </td>

                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border font-semibold whitespace-nowrap ${seasonStyle.className}`}>
                        <span>{seasonStyle.emoji}</span>
                        {row.season}
                      </span>
                    </td>
                  </tr>);
        })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action CTA bar */}
      <div className="rounded-xl p-5 flex items-center gap-5 border border-blue-100" style={{
            background: "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 45%, #EDE9FE 100%)",
        }}>
        <div className="w-10 h-10 rounded-xl bg-white/70 flex items-center justify-center flex-shrink-0 text-xl shadow-sm">
          🎯
        </div>
        <div className="flex-1">
          <p className="font-semibold text-sm mb-0.5" style={{ color: "#1E3A8A" }}>
            오늘의 추천 액션
          </p>
          <p className="text-xs leading-relaxed" style={{ color: "#475569" }}>
            최근 분석 기준,{" "}
            <strong className="font-bold text-slate-700">
              상세페이지 개선형
            </strong>
            과{" "}
            <strong className="font-bold text-slate-700">
              핵심 확대형
            </strong>{" "}
            상품이 우선 확인 대상으로 분류됐어요.
            <br />
            오늘 먼저 확인할 상품과 개선 액션을 확인해보세요.
          </p>
        </div>
        <button onClick={() => setScreen("today")} className="flex-shrink-0 bg-white font-semibold text-xs px-4 py-2.5 rounded-lg hover:bg-blue-50 transition whitespace-nowrap flex items-center gap-1.5 border border-blue-200 shadow-sm" style={{ color: "#2563EB" }}>
          오늘의 액션 보기
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
    </div>);
}
/* ══════════════════════════════════════
   검수 결과 모달
══════════════════════════════════════ */
const STATUS_META = {
    clean: {
        label: "자동 정제됨",
        bg: "bg-blue-50",
        text: "text-blue-700",
        border: "border-blue-200",
        cellBg: "#eff6ff",
        chipBorder: "#bfdbfe",
    },
    optional: {
        label: "참고",
        bg: "bg-slate-100",
        text: "text-slate-600",
        border: "border-slate-300",
        cellBg: "#f1f5f9",
        chipBorder: "#cbd5e1",
    },
    warn: {
        label: "확인 필요",
        bg: "bg-amber-50",
        text: "text-amber-700",
        border: "border-amber-200",
        cellBg: "#fffbeb",
        chipBorder: "#fde68a",
    },
    error: {
        label: "필수 오류",
        bg: "bg-rose-50",
        text: "text-rose-700",
        border: "border-rose-200",
        cellBg: "#fff1f2",
        chipBorder: "#fecdd3",
    },
};
const MOCK_ISSUES = [
    { row: 12, col: "광고비", raw: "12,000원", cleaned: "12000", status: "clean", note: "원화 기호와 쉼표를 제거해 숫자형 데이터로 변환했습니다.", reflect: "반영 가능" },
    { row: 15, col: "노출수", raw: "45,678", cleaned: "45678", status: "clean", note: "쉼표를 제거해 정수형으로 변환했습니다.", reflect: "반영 가능" },
    { row: 18, col: "클릭수", raw: "1,234", cleaned: "1234", status: "clean", note: "쉼표를 제거해 정수형으로 변환했습니다.", reflect: "반영 가능" },
    { row: 23, col: "주문금액", raw: "₩45,000", cleaned: "45000", status: "clean", note: "통화 기호와 쉼표를 제거해 숫자형 데이터로 변환했습니다.", reflect: "반영 가능" },
    { row: 25, col: "ROAS", raw: "3.5%", cleaned: "참고용", status: "optional", note: "원본 수치로 ROAS를 재계산하므로 참고용으로만 활용합니다.", reflect: "참고용" },
    { row: 41, col: "반품건수", raw: "없음", status: "warn", note: "반품이 없으면 0, 데이터가 없으면 빈 값으로 입력해주세요.", reason: "텍스트 값 '없음'은 숫자형 필드에 사용할 수 없습니다. 원본 파일을 확인 후 값을 수정해주세요.", reflect: "확인 후 반영 가능" },
    { row: 55, col: "노출수", raw: "28.500", status: "warn", note: "소수점인지 천 단위 구분자인지 의미 판단이 필요합니다. 원본 파일 확인 후 값을 수정해주세요.", reason: "소수점인지 천 단위 구분자인지 의미 판단이 필요합니다.", reflect: "확인 후 반영 가능" },
    { row: 56, col: "반품건수", raw: "3건", cleaned: "3", status: "clean", note: "'건' 단위를 제거해 숫자형으로 변환했습니다.", reflect: "반영 가능" },
];
const TABLE_ROWS = [
    { r: 12, cells: ["링이 앵글 프릴 블라우스", "블라우스", "45678", "1,234", "12,000원", "₩45,000", "38", "2", "3.5%"] },
    { r: 15, cells: ["데일리 셔링 리본 원피스", "원피스", "45,678", "987", "8500원", "₩28,000", "22", "1", "3.3%"] },
    { r: 18, cells: ["오버핏 린넨 롱 원피스", "원피스", "21000", "1,234", "5000원", "₩18,000", "14", "0", "3.6%"] },
    { r: 23, cells: ["베이직 크롭 티셔츠", "티셔츠", "18400", "520", "4200원", "₩45,000", "11", "0", "2.9%"] },
    { r: 25, cells: ["플로럴 시폰 원피스", "원피스", "31200", "890", "7800원", "₩26,000", "20", "2", "3.5%"] },
    { r: 41, cells: ["바쉐 베이직 티셔츠", "티셔츠", "9800", "450", "3200원", "₩11,000", "9", "없음", "3.4%"] },
    { r: 55, cells: ["플리츠 미디 스커트", "스커트", "28.500", "820", "7100원", "₩23,000", "19", "3", "2.8%"] },
    { r: 56, cells: ["크롭 린넨 재킷", "재킷", "15200", "411", "6800원", "₩22,000", "16", "3건", "3.2%"] },
];
const TABLE_COLS = ["상품명", "카테고리", "노출수", "클릭수", "광고비", "주문금액", "상품주문수", "반품건수", "ROAS"];
const REFERENCE_ONLY_COLS = ["ROAS"];
const PAGE_SIZE = 20;
function InspectionModal({ onClose, setScreen }) {
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
/* ══════════════════════════════════════
   화면 2 — 상품 성과 파일 업로드 화면
══════════════════════════════════════ */
const SEASON_BY_MONTH = {
    1: "겨울",
    2: "겨울",
    3: "겨울",
    4: "봄",
    5: "봄",
    6: "봄",
    7: "여름",
    8: "여름",
    9: "여름",
    10: "가을",
    11: "가을",
    12: "가을",
};
function getMonthsBetween(start, end) {
    const [startYear, startMonth] = start.split("-").map(Number);
    const [endYear, endMonth] = end.split("-").map(Number);
    const months = [];
    let year = startYear;
    let month = startMonth;
    while (year < endYear || (year === endYear && month <= endMonth)) {
        months.push(month);
        month += 1;
        if (month > 12) {
            month = 1;
            year += 1;
        }
    }
    return months;
}
function getSeasonFromPeriod(start, end) {
    const months = getMonthsBetween(start, end);
    const counts = {
        겨울: 0,
        봄: 0,
        여름: 0,
        가을: 0,
    };
    months.forEach((month) => {
        const season = SEASON_BY_MONTH[month];
        counts[season] += 1;
    });
    const seasons = Object.entries(counts);
    seasons.sort((a, b) => b[1] - a[1]);
    return seasons[0][0];
}
;
function addMonthsToYearMonth(yearMonth, monthsToAdd) {
    const [year, month] = yearMonth.split("-").map(Number);
    const date = new Date(year, month - 1 + monthsToAdd, 1);
    const nextYear = date.getFullYear();
    const nextMonth = String(date.getMonth() + 1).padStart(2, "0");
    return `${nextYear}-${nextMonth}`;
}
const SEASON_EMOJI = {
    봄: "🌸",
    여름: "☀️",
    가을: "🍂",
    겨울: "❄️",
};
const REQUIRED_COLS = [
    "상품ID",
    "상품명",
    "노출수",
    "클릭수",
    "광고비",
    "주문금액",
    "상품금액",
    "상품 상세 방문수",
    "장바구니 유저수",
    "찜 유저수",
    "상품주문수",
    "반품건수",
    "판매 사이트"
];
// const OPTIONAL_COLS = [
//   "클릭률",
//   "ROAS",
//   "구매전환율",
//   "장바구니 전환율",
//   "반품률",
//   "광고비 비중",
//   "상품URL",
//   "이미지URL",
// ];
function UploadScreen({ setScreen, }) {
    const [dragging, setDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
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
        setValidationStarted(false);
        setValidationReady(false);
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
    const [cleanseOpen, setCleanseOpen] = useState(false);
    const [examplesOpen, setExamplesOpen] = useState(false);
    function handleValidationStart() {
        if (!selectedFile || !startMonth || !endMonth)
            return;
        setValidationStarted(true);
        setValidationReady(false);
        setTimeout(() => {
            setValidationReady(true);
        }, 800);
    }
    function handleStartMonthChange(value) {
        setStartMonth(value);
        setEndMonth(addMonthsToYearMonth(value, 2));
        setValidationStarted(false);
        setValidationReady(false);
    }
    const season = startMonth && endMonth ? getSeasonFromPeriod(startMonth, endMonth) : "";
    const canStartValidation = !!selectedFile && !!startMonth && !!endMonth && !(validationStarted && !validationReady);
    const fmt = (v) => v.replace("-", ".");
    const hasWarn = true;
    const hasError = false;
    const SUMMARY_VALIDATION = [
        {
            label: "필수 컬럼 확인",
            status: "정상",
            desc: "모든 필수 컬럼이 확인되었습니다.",
            ok: true,
        },
        {
            label: "숫자형 데이터 자동 정제",
            status: "완료",
            desc: "18건이 자동으로 정제되었습니다. (쉼표·통화기호·단위 제거)",
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
            status: "경고",
            desc: "2건의 값은 의미 판단이 필요합니다. 검수 결과를 확인해주세요.",
            ok: false,
        },
    ];
    return (<>
      {showModal && (<InspectionModal onClose={() => setShowModal(false)} setScreen={setScreen}/>)}

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
                    {selectedFile.name.split('.').pop()?.toLowerCase()}
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
                setValidationStarted(false);
                setValidationReady(false);
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
              {REQUIRED_COLS.map((c) => (<span key={c} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium">
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
                시작월 선택
              </label>
              <input type="month" value={startMonth} onChange={(e) => handleStartMonthChange(e.target.value)} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition"/>
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
              <button onClick={() => setShowModal(true)} className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border transition" style={{
                color: "#2563EB",
                backgroundColor: "#EFF6FF",
                borderColor: "#BFDBFE",
            }} onMouseEnter={(e) => (e.currentTarget.style.backgroundColor =
                "#DBEAFE")} onMouseLeave={(e) => (e.currentTarget.style.backgroundColor =
                "#EFF6FF")}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
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
                    value: "18건",
                    sub: "형식 오류 자동 변환",
                    color: "border-blue-200 bg-blue-50",
                    textColor: "text-blue-700",
                    subColor: "text-blue-500",
                },
                {
                    label: "확인 필요 항목",
                    value: "2건",
                    sub: "의미 판단 필요",
                    color: "border-amber-200",
                    textColor: "text-amber-700",
                    subColor: "text-amber-500",
                    bgStyle: { backgroundColor: "#FFFBEB" },
                },
                {
                    label: "필수 오류",
                    value: "0건",
                    sub: "분석 불가 오류 없음",
                    color: "border-emerald-200 bg-emerald-50",
                    textColor: "text-emerald-700",
                    subColor: "text-emerald-500",
                },
                {
                    label: "분석 가능 여부",
                    value: "가능",
                    sub: "검수 확인 후 시작 권장",
                    color: "border-slate-200 bg-slate-50",
                    textColor: "text-slate-700",
                    subColor: "text-slate-400",
                },
            ].map((s) => (<div key={s.label} className={`rounded-xl border p-4 ${s.color}`} style={"bgStyle" in s ? s.bgStyle : undefined}>
                  <p className="text-[11px] text-slate-500 font-semibold mb-1">
                    {s.label}
                  </p>
                  <p className={`text-xl font-bold ${s.textColor} mb-0.5`}>
                    {s.value}
                  </p>
                  <p className={`text-[10px] ${s.subColor}`}>
                    {s.sub}
                  </p>
                </div>))}
            </div>

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
                ? "필수 컬럼 누락 또는 숫자 변환이 불가능한 값이 있어 분석을 시작할 수 없습니다."
                : hasWarn
                    ? "일부 값은 확인이 필요합니다. 검수 결과를 확인한 뒤 분석을 진행할 수 있습니다."
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
/* ══════════════════════════════════════
   화면 3 — 판매 전 카테고리 진단
══════════════════════════════════════ */
const DIAG_CATEGORIES = [
    "블라우스",
    "원피스",
    "티셔츠",
    "스커트",
    "팬츠",
    "니트",
    "아우터",
];
const DIAG_SEASONS = ["봄", "여름", "가을", "겨울"];
const MOCK_DIAG_RESULT = {
    score: 82,
    verdict: "판매 추천",
    summary: "여름 시즌의 블라우스 카테고리는 구매전환율과 장바구니 전환율이 평균보다 높고, 반품률이 안정적인 편입니다. 판매를 진행해볼 만한 카테고리로 판단됩니다.",
    metrics: [
        {
            label: "구매전환율",
            catAvg: "4.8%",
            allAvg: "3.2%",
            verdict: "평균보다 높음",
            good: true,
        },
        {
            label: "장바구니 전환율",
            catAvg: "8.1%",
            allAvg: "6.4%",
            verdict: "평균보다 높음",
            good: true,
        },
        {
            label: "찜 관심도",
            catAvg: "5.7%",
            allAvg: "4.9%",
            verdict: "보통 이상",
            good: true,
        },
        {
            label: "반품률",
            catAvg: "6.2%",
            allAvg: "7.5%",
            verdict: "안정적",
            good: true,
        },
        {
            label: "ROAS",
            catAvg: "420%",
            allAvg: "310%",
            verdict: "우수",
            good: true,
        },
    ],
    strengths: ["구매전환율 높음", "장바구니 반응 양호"],
    cautions: ["반품 리스크 보통", "상세페이지 정보 보강 필요"],
};
function DiagIllustration() {
    return (<svg width="180" height="120" viewBox="0 0 180 120" fill="none">
      <circle cx="140" cy="60" r="50" fill="rgba(255,255,255,0.08)"/>
      <circle cx="140" cy="60" r="32" fill="rgba(255,255,255,0.08)"/>
      {/* Category boxes */}
      <rect x="16" y="20" width="56" height="28" rx="7" fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.4)" strokeWidth="1"/>
      <rect x="20" y="28" width="20" height="3" rx="1.5" fill="white" fillOpacity="0.8"/>
      <rect x="20" y="34" width="32" height="2.5" rx="1.25" fill="white" fillOpacity="0.5"/>
      <rect x="16" y="56" width="56" height="28" rx="7" fill="rgba(255,255,255,0.28)" stroke="rgba(255,255,255,0.5)" strokeWidth="1"/>
      <rect x="20" y="64" width="24" height="3" rx="1.5" fill="white" fillOpacity="0.9"/>
      <rect x="20" y="70" width="36" height="2.5" rx="1.25" fill="white" fillOpacity="0.6"/>
      <rect x="16" y="92" width="56" height="18" rx="7" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
      <rect x="20" y="99" width="28" height="2.5" rx="1.25" fill="white" fillOpacity="0.5"/>
      {/* Score ring */}
      <circle cx="136" cy="58" r="26" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="4"/>
      <circle cx="136" cy="58" r="26" fill="none" stroke="white" strokeWidth="4" strokeDasharray="118 47" strokeLinecap="round" style={{
            transform: "rotate(-90deg)",
            transformOrigin: "136px 58px",
        }}/>
      <text x="136" y="54" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">
        82
      </text>
      <text x="136" y="66" textAnchor="middle" fill="rgba(255,255,255,0.75)" fontSize="8">
        점수
      </text>
      {/* Arrow */}
      <line x1="74" y1="68" x2="106" y2="62" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeDasharray="3 2"/>
      <polygon points="106,58 112,62 106,66" fill="rgba(255,255,255,0.5)"/>
    </svg>);
}
function DiagScreen({ setScreen, }) {
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
const RISK_META = {
    낮음: {
        label: "낮음",
        bg: "bg-emerald-50",
        text: "text-emerald-700",
        border: "border-emerald-200",
        dot: "#059669",
    },
    "주의 필요": {
        label: "주의 필요",
        bg: "bg-amber-50",
        text: "text-amber-700",
        border: "border-amber-200",
        dot: "#D97706",
    },
    높음: {
        label: "높음",
        bg: "bg-rose-50",
        text: "text-rose-700",
        border: "border-rose-200",
        dot: "#E11D48",
    },
    "확인 불가": {
        label: "확인 불가",
        bg: "bg-slate-50",
        text: "text-slate-600",
        border: "border-slate-200",
        dot: "#64748B",
    },
};
const REFERENCE_DOCS = [
    {
        name: "표시·광고의 공정화에 관한 법률",
        badge: "검색 가능",
        badgeCls: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        name: "전자상거래 등에서의 소비자보호 지침",
        badge: "검색 가능",
        badgeCls: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        name: "전자상거래 등에서의 상품 등의 정보제공에 관한 고시",
        badge: "기준 문서",
        badgeCls: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
        name: "소비자분쟁해결기준",
        badge: "검색 가능",
        badgeCls: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        name: "개인정보 보호법",
        badge: "검색 가능",
        badgeCls: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        name: "전자상거래 표준약관",
        badge: "업데이트 필요",
        badgeCls: "bg-amber-50 text-amber-700 border-amber-200",
    },
    {
        name: "지그재그 규제 데이터",
        badge: "기준 문서",
        badgeCls: "bg-blue-50 text-blue-700 border-blue-200",
    },
];
const FAQ_QUESTIONS = [
    "이 광고 문구 과장광고로 문제될 수 있어?",
    "의류 상세페이지에 꼭 적어야 하는 정보가 뭐야?",
    "반품 불가라고 적어도 돼?",
    "리뷰 데이터를 분석해도 개인정보 문제가 없을까?",
    "배송 지연 시 어떤 안내가 필요해?",
    "지그재그에서 제한되는 표현이 있을까?",
    '"무조건 날씬해 보임" 같은 문구를 써도 될까?',
    "고객 리뷰를 광고 문구에 활용해도 될까?",
];

const FAQ_API_QUESTIONS = {
    "이 광고 문구 과장광고로 문제될 수 있어?":
        "온라인 쇼핑몰 광고 문구가 표시·광고법상 거짓 또는 과장 광고에 해당하는 판단 기준과 금지되는 표현은 무엇인가요?",
    "의류 상세페이지에 꼭 적어야 하는 정보가 뭐야?":
        "의류 상품을 온라인으로 판매할 때 상품 상세페이지에 전자상거래 상품정보제공고시에 따라 반드시 표시해야 하는 항목은 무엇인가요?",
    "반품 불가라고 적어도 돼?":
        "온라인 쇼핑몰이 상품 상세페이지에 반품 불가라고 표시할 수 있나요? 전자상거래법상 청약철회 제한이 가능한 요건과 예외는 무엇인가요?",
    "리뷰 데이터를 분석해도 개인정보 문제가 없을까?":
        "온라인 쇼핑몰이 고객 리뷰 데이터를 통계 분석이나 마케팅 분석에 활용할 때 개인정보 보호법상 주의해야 할 사항은 무엇인가요?",
    "배송 지연 시 어떤 안내가 필요해?":
        "온라인 쇼핑몰에서 상품 배송이 지연될 때 소비자에게 안내해야 하는 내용과 환불 또는 계약 해제 관련 기준은 무엇인가요?",
    "지그재그에서 제한되는 표현이 있을까?":
        "지그재그 상품 등록과 광고 문구에서 제한되는 표현 및 플랫폼 운영 규정은 무엇인가요?",
    '"무조건 날씬해 보임" 같은 문구를 써도 될까?':
        '"무조건 날씬해 보임"처럼 효과를 단정하는 의류 광고 문구가 표시·광고법상 과장 광고가 될 수 있는지 알려주세요.',
    "고객 리뷰를 광고 문구에 활용해도 될까?":
        "고객 리뷰를 온라인 쇼핑몰 광고 문구나 상세페이지에 활용할 때 작성자 동의, 실제 구매 후기 표시, 편집 및 과장과 관련해 주의할 법적 기준은 무엇인가요?",
};
const CHECKABLE_ITEMS = [
    "광고 문구 리스크",
    "상품 상세페이지 필수 정보",
    "반품·환불 안내 기준",
    "개인정보 수집·활용 주의사항",
    "배송 지연 안내 기준",
    "쇼핑몰 약관 참고",
    "지그재그 상품 등록 및 표현 제한",
    "플랫폼 운영 규정",
];
function getMockResponse(q) {
    const lower = q.toLowerCase();
    if (lower.includes("날씬") ||
        lower.includes("무조건") ||
        lower.includes("과장")) {
        return {
            risk: "주의 필요",
            explanation: '"무조건"처럼 결과를 단정하는 표현은 소비자가 효과를 확정적으로 오해할 가능성이 있어 주의가 필요합니다. 체형 보정 효과를 객관적 근거 없이 단정하면 과장 표현으로 해석될 수 있습니다.',
            suggestions: [
                "슬림한 실루엣을 연출하는 원피스",
                "허리 라인을 자연스럽게 잡아주는 원피스",
                "체형을 편안하게 커버하는 데일리 원피스",
            ],
            sources: [
                "표시·광고의 공정화에 관한 법률",
                "전자상거래 등에서의 상품 등의 정보제공에 관한 고시",
            ],
        };
    }
    if (lower.includes("반품 불가") ||
        lower.includes("반품불가")) {
        return {
            risk: "높음",
            explanation: '전자상거래법상 소비자는 수령일로부터 7일 이내 청약철회(단순변심 반품)가 가능합니다. "반품 불가"라고 일방적으로 고지하는 것은 소비자 권리를 침해하는 표현으로 법적 분쟁의 원인이 될 수 있습니다.',
            suggestions: [
                "단순변심 반품: 수령 후 7일 이내 가능 (배송비 고객 부담)",
                "상품 하자 시: 수령 후 3개월 이내 반품·교환 가능",
                "맞춤 제작 상품 등 청약철회 예외 사유가 있다면 해당 내용을 구체적으로 명시하세요.",
            ],
            sources: [
                "전자상거래 등에서의 소비자보호 지침",
                "소비자분쟁해결기준",
                "전자상거래 표준약관",
            ],
        };
    }
    if (lower.includes("개인정보") ||
        lower.includes("리뷰 데이터")) {
        return {
            risk: "주의 필요",
            explanation: "리뷰 데이터는 작성자의 개인정보가 포함될 수 있습니다. 마케팅·분석 목적으로 활용하려면 수집 당시 동의 목적 범위 내에서만 사용해야 하며, 별도 분석 활용 동의가 없다면 원칙적으로 제한됩니다.",
            suggestions: [
                '리뷰 수집 시 "마케팅 활용 동의" 항목을 별도로 받으세요.',
                "익명 처리된 통계 형태로만 분석하는 방식을 검토하세요.",
                "개인을 식별할 수 없는 형태로 가공한 경우에는 활용 가능합니다.",
            ],
            sources: ["개인정보 보호법"],
        };
    }
    if (lower.includes("의류") ||
        lower.includes("상세페이지") ||
        lower.includes("꼭 적어야")) {
        return {
            risk: "낮음",
            explanation: "전자상거래 상품 정보제공 고시에 따라 의류 상품 상세페이지에는 아래 항목을 필수로 제공해야 합니다. 이미 포함하고 있다면 리스크가 낮습니다.",
            suggestions: [
                "소재(혼용률)",
                "치수 또는 사이즈 (실측 기준)",
                "세탁방법 및 취급주의 사항",
                "제조국 / 제조연월",
                "제조자 또는 수입자 정보",
                "색상 (실제 색상과 차이 안내 포함 권장)",
            ],
            sources: [
                "전자상거래 등에서의 상품 등의 정보제공에 관한 고시",
            ],
        };
    }
    if (lower.includes("배송 지연") || lower.includes("배송")) {
        return {
            risk: "낮음",
            explanation: "배송 지연 시 소비자에게 사전 안내 의무가 있습니다. 지연 사실과 사유, 예상 배송일을 고지하면 리스크를 낮출 수 있습니다.",
            suggestions: [
                "지연 사유와 예상 배송일을 고객에게 문자 또는 이메일로 안내하세요.",
                "7일 이상 지연 시 소비자는 계약을 취소하고 환불을 요청할 수 있습니다.",
                "배송 지연 안내 문구를 상품 상세페이지에 미리 안내하면 분쟁을 예방할 수 있습니다.",
            ],
            sources: [
                "전자상거래 등에서의 소비자보호 지침",
                "소비자분쟁해결기준",
            ],
        };
    }
    if (lower.includes("지그재그") ||
        lower.includes("플랫폼") ||
        lower.includes("제한")) {
        return {
            risk: "주의 필요",
            explanation: "지그재그 플랫폼은 상품 등록 시 과장·허위 표현, 타 브랜드 비교 문구, 최저가 보장 등의 표현을 제한하고 있습니다. 규정 위반 시 상품 노출 제한 또는 계정 제재를 받을 수 있습니다.",
            suggestions: [
                '"업계 최저가", "타사 대비 최고" 등 비교 표현은 피하세요.',
                '"100% 천연 소재"처럼 검증이 어려운 단정 표현은 사용을 자제하세요.',
                "브랜드명·상표 무단 사용 문구도 제한 대상입니다.",
            ],
            sources: [
                "지그재그 규제 데이터",
                "표시·광고의 공정화에 관한 법률",
            ],
        };
    }
    if (lower.includes("리뷰") && lower.includes("광고")) {
        return {
            risk: "주의 필요",
            explanation: "고객 리뷰를 광고 문구에 활용할 경우, 리뷰 작성자의 동의가 필요하며, 실제 구매자의 의견임을 명확히 표시해야 합니다. 리뷰 선택적 게재나 과장 편집은 기만 광고로 해석될 수 있습니다.",
            suggestions: [
                "광고 활용 동의를 리뷰 작성 시 사전에 받으세요.",
                '"실제 구매자 후기" 또는 "실사용 리뷰"임을 명시하세요.',
                "내용을 임의로 편집하거나 부분 발췌해 의미를 왜곡하지 마세요.",
            ],
            sources: [
                "표시·광고의 공정화에 관한 법률",
                "전자상거래 등에서의 소비자보호 지침",
            ],
        };
    }
    // Default: no result
    return { noResult: true };
}
const INIT_MESSAGES = [
    {
        id: 0,
        role: "ai",
        text: "안녕하세요! 쇼핑몰 법 규제 챗봇입니다.\n광고 문구, 상세페이지, 반품·환불, 개인정보, 플랫폼 규정 관련 리스크를 질문해보세요.\n왼쪽의 자주 묻는 질문을 클릭하면 바로 질문할 수 있습니다.",
    },
    {
        id: 1,
        role: "user",
        text: '"무조건 날씬해 보이는 인생 원피스"라는 문구를 광고에 써도 될까?',
    },
    {
        id: 2,
        role: "ai",
        ...getMockResponse("무조건 날씬"),
    },
];

const CHAT_API_BASE_URL = (
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const CHAT_API_URL = `${CHAT_API_BASE_URL}/chat`;
const CHAT_STREAM_API_URL = `${CHAT_API_BASE_URL}/chat/stream`;
const CHAT_STORAGE_KEY = "online-shopping-legal-chat-messages";
const MAX_HISTORY_MESSAGES = 10;
const MAX_HISTORY_CONTENT_LENGTH = 2000;
const MAX_STORED_MESSAGES = 30;
const MAX_STORED_SOURCE_CONTENT_LENGTH = 2500;

const CHAT_INTRO_MESSAGE = {
    id: "chat-intro",
    role: "assistant",
    content: "안녕하세요! 쇼핑몰 법 규제 챗봇입니다.\n반품·환불, 판매자 정보, 개인정보 등 온라인 쇼핑 관련 질문을 입력해주세요.",
    sources: [],
    isIntro: true,
};

function truncateChatText(value, maxLength) {
    if (typeof value !== "string") {
        return "";
    }

    return value.slice(0, maxLength);
}

function prepareChatMessagesForStorage(messages) {
    return messages
        .filter((message) => !message.isIntro &&
            (message.role === "user" || message.role === "assistant") &&
            typeof message.content === "string" &&
            message.content.trim())
        .slice(-MAX_STORED_MESSAGES)
        .map((message) => ({
        id: typeof message.id === "string"
            ? message.id
            : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        role: message.role,
        content: message.content,
        sources: Array.isArray(message.sources)
            ? message.sources.slice(0, 3).map((source) => ({
                rank: source.rank,
                heading: source.heading,
                heading_path: source.heading_path,
                source_file: source.source_file,
                file_name: source.file_name,
                parent_id: source.parent_id,
                child_content: truncateChatText(source.child_content, MAX_STORED_SOURCE_CONTENT_LENGTH),
                parent_content: truncateChatText(source.parent_content, MAX_STORED_SOURCE_CONTENT_LENGTH),
                content: truncateChatText(source.content, MAX_STORED_SOURCE_CONTENT_LENGTH),
                text: truncateChatText(source.text, MAX_STORED_SOURCE_CONTENT_LENGTH),
                excerpt: truncateChatText(source.excerpt, MAX_STORED_SOURCE_CONTENT_LENGTH),
                dense_score: source.dense_score,
                rerank_score: source.rerank_score,
                score: source.score,
                similarity_score: source.similarity_score,
                rank_group: source.rank_group,
                retrieved_by: source.retrieved_by,
            }))
            : [],
    }));
}

function loadStoredChatMessages() {
    try {
        const storedValue = window.localStorage.getItem(CHAT_STORAGE_KEY);

        if (!storedValue) {
            return [CHAT_INTRO_MESSAGE];
        }

        const parsedMessages = JSON.parse(storedValue);

        if (!Array.isArray(parsedMessages)) {
            return [CHAT_INTRO_MESSAGE];
        }

        const storedMessages = prepareChatMessagesForStorage(parsedMessages);
        return storedMessages.length > 0
            ? [CHAT_INTRO_MESSAGE, ...storedMessages]
            : [CHAT_INTRO_MESSAGE];
    }
    catch (storageError) {
        console.error("저장된 대화를 불러오지 못했습니다.", storageError);
        return [CHAT_INTRO_MESSAGE];
    }
}

function createChatMessage(role, content, sources = []) {
    return {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        role,
        content,
        sources,
    };
}

function buildChatRequestHistory(messages) {
    return messages
        .filter((message) => !message.isIntro &&
            (message.role === "user" || message.role === "assistant") &&
            typeof message.content === "string" &&
            message.content.trim())
        .slice(-MAX_HISTORY_MESSAGES)
        .map((message) => ({
        role: message.role,
        content: message.content
            .trim()
            .slice(0, MAX_HISTORY_CONTENT_LENGTH),
    }));
}

function getChatSourceScore(source) {
    const score = source.rerank_score ??
        source.score ??
        source.dense_score ??
        source.similarity_score;

    return typeof score === "number" ? score.toFixed(4) : null;
}

function getChatSourceHeading(source) {
    if (Array.isArray(source.heading_path)) {
        return source.heading_path.join(" > ");
    }

    return source.heading_path ||
        source.heading ||
        source.title ||
        "제목 없음";
}

function getChatSourceContent(source) {
    return source.parent_content ||
        source.content ||
        source.text ||
        source.excerpt ||
        source.child_content ||
        "";
}

function ChatScreen({ setScreen, }) {
    const [messages, setMessages] = useState(loadStoredChatMessages);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [streamingStarted, setStreamingStarted] = useState(false);
    const [error, setError] = useState("");
    const chatEndRef = useRef(null);
    const textareaRef = useRef(null);
    const requestInFlightRef = useRef(false);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [messages, isLoading]);

    useEffect(() => {
        try {
            const storedMessages = prepareChatMessagesForStorage(messages);

            if (storedMessages.length === 0) {
                window.localStorage.removeItem(CHAT_STORAGE_KEY);
                return;
            }

            window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(storedMessages));
        }
        catch (storageError) {
            console.error("대화를 저장하지 못했습니다.", storageError);
        }
    }, [messages]);

    async function send(text) {
        const displayedQuestion = text.trim();

        if (!displayedQuestion || requestInFlightRef.current) {
            return;
        }

        requestInFlightRef.current = true;

        const apiQuestion =
            FAQ_API_QUESTIONS[displayedQuestion] ??
            displayedQuestion;

        const isFaqQuestion =
            Object.prototype.hasOwnProperty.call(
                FAQ_API_QUESTIONS,
                displayedQuestion,
            );

        // 왼쪽 FAQ는 각각 독립된 질문이므로 이전 대화 문맥을 보내지 않습니다.
        const requestHistory = isFaqQuestion
            ? []
            : buildChatRequestHistory(messages);

        const userMessage = createChatMessage(
            "user",
            displayedQuestion,
        );

        const assistantMessageId =
            `assistant-${Date.now()}-${Math.random()
                .toString(36)
                .slice(2)}`;

        let assistantAdded = false;
        let finalData = null;

        function appendAssistantToken(token) {
            if (!token) {
                return;
            }

            setStreamingStarted(true);

            setMessages((currentMessages) => {
                if (!assistantAdded) {
                    assistantAdded = true;

                    return [
                        ...currentMessages,
                        {
                            id: assistantMessageId,
                            role: "assistant",
                            content: token,
                            sources: [],
                            isStreaming: true,
                        },
                    ];
                }

                return currentMessages.map((message) =>
                    message.id === assistantMessageId
                        ? {
                            ...message,
                            content:
                                `${message.content}${token}`,
                        }
                        : message
                );
            });
        }

        function finishAssistantMessage(data) {
            const answer =
                typeof data?.answer === "string" &&
                data.answer.trim()
                    ? data.answer
                    : "답변이 없습니다.";

            const sources = Array.isArray(data?.sources)
                ? data.sources
                : [];

            setMessages((currentMessages) => {
                const exists = currentMessages.some(
                    (message) =>
                        message.id === assistantMessageId,
                );

                if (!exists) {
                    assistantAdded = true;

                    return [
                        ...currentMessages,
                        {
                            id: assistantMessageId,
                            role: "assistant",
                            content: answer,
                            sources,
                            isStreaming: false,
                        },
                    ];
                }

                return currentMessages.map((message) =>
                    message.id === assistantMessageId
                        ? {
                            ...message,
                            content: answer,
                            sources,
                            isStreaming: false,
                        }
                        : message
                );
            });
        }

        function processStreamEvent(eventData) {
            if (!eventData || typeof eventData !== "object") {
                return;
            }

            if (eventData.type === "token") {
                appendAssistantToken(
                    typeof eventData.content === "string"
                        ? eventData.content
                        : "",
                );
                return;
            }

            if (eventData.type === "final") {
                finalData = eventData.data ?? null;
                finishAssistantMessage(finalData);
                return;
            }

            if (eventData.type === "error") {
                throw new Error(
                    eventData.detail ||
                    "챗봇 요청 중 오류가 발생했습니다.",
                );
            }
        }

        setMessages((currentMessages) => [
            ...currentMessages,
            userMessage,
        ]);
        setInput("");
        setError("");
        setIsLoading(true);
        setStreamingStarted(false);

        try {
            const response = await fetch(
                CHAT_STREAM_API_URL,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        question: apiQuestion,
                        history: requestHistory,
                    }),
                },
            );

            if (!response.ok) {
                let detail =
                    "챗봇 요청 중 오류가 발생했습니다.";

                try {
                    const errorData = await response.json();
                    detail = errorData.detail || detail;
                }
                catch {
                    // JSON 오류 응답이 아니면 기본 문구를 사용합니다.
                }

                throw new Error(detail);
            }

            if (!response.body) {
                throw new Error(
                    "서버의 스트리밍 응답을 읽을 수 없습니다.",
                );
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, {
                    stream: true,
                });

                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    const trimmedLine = line.trim();

                    if (!trimmedLine) {
                        continue;
                    }

                    let eventData;

                    try {
                        eventData = JSON.parse(trimmedLine);
                    }
                    catch {
                        throw new Error(
                            "서버의 스트리밍 응답을 해석하지 못했습니다.",
                        );
                    }

                    processStreamEvent(eventData);
                }
            }

            buffer += decoder.decode();

            if (buffer.trim()) {
                let eventData;

                try {
                    eventData = JSON.parse(buffer.trim());
                }
                catch {
                    throw new Error(
                        "서버의 마지막 스트리밍 응답을 해석하지 못했습니다.",
                    );
                }

                processStreamEvent(eventData);
            }

            if (!finalData && !assistantAdded) {
                throw new Error(
                    "서버에서 최종 답변을 받지 못했습니다.",
                );
            }
        }
        catch (requestError) {
            const message = requestError instanceof Error
                ? requestError.message
                : "알 수 없는 오류가 발생했습니다.";

            setError(message);

            setMessages((currentMessages) => {
                const hasAssistantMessage =
                    currentMessages.some(
                        (currentMessage) =>
                            currentMessage.id ===
                            assistantMessageId,
                    );

                if (hasAssistantMessage) {
                    return currentMessages.map(
                        (currentMessage) =>
                            currentMessage.id ===
                            assistantMessageId
                                ? {
                                    ...currentMessage,
                                    isStreaming: false,
                                }
                                : currentMessage,
                    );
                }

                return [
                    ...currentMessages,
                    createChatMessage(
                        "assistant",
                        `요청을 처리하지 못했습니다.\n${message}`,
                    ),
                ];
            });
        }
        finally {
            requestInFlightRef.current = false;
            setStreamingStarted(false);
            setIsLoading(false);

            window.setTimeout(() => {
                textareaRef.current?.focus();
            }, 0);
        }
    }

    function handleKeyDown(event) {
        if (event.key === "Enter" &&
            !event.shiftKey &&
            !event.nativeEvent.isComposing) {
            event.preventDefault();
            send(input);
        }
    }

    function handleNewChat() {
        setMessages([CHAT_INTRO_MESSAGE]);
        setInput("");
        setError("");
        window.localStorage.removeItem(CHAT_STORAGE_KEY);
        textareaRef.current?.focus();
    }

    const BotAvatar = () => (<div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{
            backgroundColor: "#EFF6FF",
            border: "1px solid #BFDBFE",
        }}>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="9" y1="13" x2="15" y2="13"/>
        <line x1="9" y1="17" x2="12" y2="17"/>
      </svg>
    </div>);

    function renderSources(sources) {
        if (!Array.isArray(sources) || sources.length === 0) {
            return null;
        }

        return (<details className="border-t border-slate-100 pt-3">
          <summary className="text-[11px] font-bold text-blue-600 cursor-pointer select-none">
            참고 근거 {sources.length}개
          </summary>

          <div className="mt-3 space-y-2.5">
            {sources.map((source, index) => {
                const score = getChatSourceScore(source);
                const content = getChatSourceContent(source);
                const sourceFile = source.source_file ||
                    source.file_name ||
                    "문서명 없음";

                return (<article key={source.parent_id ||
                        source.id ||
                        `${sourceFile}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <span className="text-[10px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-1 rounded-lg">
                      근거 {index + 1}
                    </span>
                    {score && (<span className="text-[10px] text-slate-400">
                        검색 점수 {score}
                      </span>)}
                  </div>

                  <p className="text-xs font-bold text-slate-700 leading-relaxed">
                    {getChatSourceHeading(source)}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    문서: {sourceFile}
                  </p>

                  {content && (<p className="text-[11px] text-slate-600 leading-relaxed mt-2 whitespace-pre-line max-h-40 overflow-y-auto">
                      {content}
                    </p>)}
                </article>);
            })}
          </div>
        </details>);
    }

    function renderMessage(message) {
        if (message.role === "user") {
            return (<div className="flex justify-end">
          <div className="max-w-[70%] px-4 py-3 rounded-2xl rounded-tr-sm text-sm text-white leading-relaxed whitespace-pre-line" style={{ backgroundColor: "#2563EB" }}>
            {message.content}
          </div>
        </div>);
        }

        return (<div className="flex justify-start">
        <div className="max-w-[90%] space-y-1.5">
          <div className="flex items-center gap-2">
            <BotAvatar />
            <span className="text-[11px] font-semibold text-slate-400">
              ActionFit 법 규제 챗봇
            </span>
          </div>

          <div className={`rounded-2xl rounded-tl-sm border p-4 space-y-3 shadow-sm ${message.isIntro
                ? "bg-blue-50/50 border-blue-100"
                : "bg-white border-slate-100"}`}>
            <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
              {message.content}
            </p>

            {!message.isIntro && renderSources(message.sources)}

            {!message.isIntro && (<div className="border-t border-slate-100 pt-2">
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  본 답변은 업로드된 법령 및 플랫폼 규제 문서를
                  기반으로 한 쇼핑몰 운영 참고용 안내이며, 법률
                  자문이나 최종 법적 판단을 대신하지 않습니다.
                </p>
              </div>)}
          </div>
        </div>
      </div>);
    }

    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-5 space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-800">
          쇼핑몰 법 규제 챗봇
        </h2>
        <p className="text-sm text-slate-400 mt-0.5">
          광고 문구, 상세페이지, 반품·환불, 개인정보, 플랫폼
          규정 관련 리스크를 문서 근거와 함께 확인해요.
        </p>
      </div>

      <div className="rounded-2xl px-7 py-5 overflow-hidden relative" style={{
            background: "linear-gradient(135deg, #3B82F6 0%, #93C5FD 55%, #C4B5FD 100%)",
        }}>
        <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-black/5 pointer-events-none"/>
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full pointer-events-none" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}/>
        <div className="absolute -bottom-12 right-40 w-40 h-40 rounded-full pointer-events-none" style={{ backgroundColor: "rgba(255,255,255,0.05)" }}/>
        <div className="relative z-10 max-w-2xl">
          <p className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.72)" }}>
            법 규제 리스크 확인
          </p>
          <p className="text-base font-semibold mb-1" style={{ color: "#fff" }}>
            온라인 쇼핑몰 운영과 관련된 법률 기준이 궁금한가요?
          </p>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.88)" }}>
            저장된 법령과 정책 문서를 검색해 근거와 함께 답변합니다.
          </p>
        </div>
      </div>

      <div className="flex gap-4 items-start">
        <div className="flex-shrink-0" style={{ width: "31%" }}>
          <div className="bg-white rounded-xl border border-slate-100 p-5" style={{ minHeight: 700 }}>
            <div className="flex items-center gap-2 mb-5">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: "#EFF6FF" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <p className="text-sm font-bold text-slate-700">
                자주 묻는 질문
              </p>
            </div>

            <div className="flex flex-col gap-2.5">
              {FAQ_QUESTIONS.map((question, index) => (<button key={index} type="button" disabled={isLoading} onClick={() => send(question)} className="w-full text-left text-xs text-slate-600 px-4 py-3 rounded-xl border border-slate-100 hover:border-blue-300 hover:bg-blue-50/60 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all leading-snug">
                  {question}
                </button>))}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="bg-white rounded-xl border border-slate-100 px-5 py-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#EFF6FF" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 11 12 14 22 4"/>
                  <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-slate-700">
                  확인 가능한 항목
                </p>
                <p className="text-[11px] text-slate-400">
                  이 챗봇으로 아래 주제를 질문할 수 있어요.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {CHECKABLE_ITEMS.map((item) => (<span key={item} className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {item}
                </span>))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 flex flex-col" style={{ height: 640 }}>
            <div className="flex-shrink-0 px-5 py-3.5 border-b border-slate-50 flex items-center gap-2.5">
              <BotAvatar />
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-700">
                  ActionFit 법 규제 챗봇
                </p>
                <p className={`text-[10px] font-medium ${isLoading ? "text-blue-500" : "text-emerald-500"}`}>
                  ● {isLoading ? "답변 생성 중" : "응답 준비됨"}
                </p>
              </div>

              <button type="button" onClick={handleNewChat} disabled={isLoading || messages.every((message) => message.isIntro)} className="text-[11px] font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
                새 대화
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
              {messages.map((message) => (<div key={message.id}>
                  {renderMessage(message)}
                </div>))}

              {isLoading && !streamingStarted && (<div className="flex justify-start">
                  <div className="max-w-[90%] space-y-1.5">
                    <div className="flex items-center gap-2">
                      <BotAvatar />
                      <span className="text-[11px] font-semibold text-slate-400">
                        ActionFit 법 규제 챗봇
                      </span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-sm border border-slate-100 px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce"/>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "120ms" }}/>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "240ms" }}/>
                      </div>
                    </div>
                  </div>
                </div>)}

              <div ref={chatEndRef}/>
            </div>

            {error && (<div className="mx-5 mb-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
                {error}
              </div>)}

            <div className="flex-shrink-0 border-t border-slate-100 px-5 pt-3 pb-4 space-y-2.5">
              <div className="flex gap-2 flex-wrap">
                {[
                    "광고 문구 붙여넣기",
                    "상세페이지 문구 붙여넣기",
                    "반품·환불 문구 붙여넣기",
                ].map((label) => (<button key={label} type="button" disabled={isLoading} onClick={() => {
                        setInput(label.replace(" 붙여넣기", ": "));
                        textareaRef.current?.focus();
                    }} className="text-[11px] font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-50 transition">
                    + {label}
                  </button>))}
              </div>

              <div className="flex gap-2 items-end">
                <textarea ref={textareaRef} rows={2} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} disabled={isLoading} placeholder={'온라인 쇼핑 관련 질문을 입력해주세요.\n예: "단순 변심으로도 반품할 수 있나요?"'} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-700 bg-slate-50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 disabled:bg-slate-100 disabled:cursor-not-allowed transition resize-none leading-relaxed"/>

                <button type="button" onClick={() => send(input)} disabled={isLoading || !input.trim()} className="flex-shrink-0 w-11 h-11 rounded-xl text-white flex items-center justify-center transition-all" style={!isLoading && input.trim()
                    ? {
                        backgroundColor: "#2563EB",
                        boxShadow: "0 4px 14px rgba(37,99,235,0.25)",
                    }
                    : {
                        backgroundColor: "#E2E8F0",
                        cursor: "not-allowed",
                    }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 px-6 py-5">
        <div className="flex items-baseline gap-2 mb-4">
          <p className="text-sm font-bold text-slate-700">
            참고 문서
          </p>
          <p className="text-xs text-slate-400">
            아래 문서를 검색해 답변 근거로 활용합니다.
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {REFERENCE_DOCS.map((doc) => (<div key={doc.name} className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-100 bg-slate-50">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span className="text-xs text-slate-600 whitespace-nowrap">
                {doc.name}
              </span>
              <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${doc.badgeCls} whitespace-nowrap`}>
                {doc.badge}
              </span>
            </div>))}
        </div>
      </div>

      <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-white border border-slate-100">
        <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p className="text-[10px] text-slate-400 leading-relaxed">
          본 기능은 업로드된 법령 및 플랫폼 규제 문서를 기반으로
          한 쇼핑몰 운영 참고용 안내입니다. 법률 자문이나 최종
          법적 판단을 대신하지 않으며, 실제 분쟁이나 법적 검토가
          필요한 경우 전문가 상담이 필요합니다.
        </p>
      </div>
    </div>);
}
/* ══════════════════════════════════════
   화면 5 — 진단 기준
══════════════════════════════════════ */
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

function BasisSection({
  title,
  desc,
  icon,
  defaultOpen = false,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full px-6 py-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition"
      >
        <div className="text-left">
          <BasisCardHeader icon={icon} title={title} />
          {desc && (
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              {desc}
            </p>
          )}
        </div>

        <div
          className={`w-8 h-8 rounded-lg border border-slate-100 flex items-center justify-center text-slate-400 transition ${
            open ? "bg-blue-50 text-blue-600 rotate-180" : "bg-white"
          }`}
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-50">{children}</div>
      )}
    </div>
  );
}

function BasisScreen({ setScreen }) {
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
              "광고비",
              "주문금액",
              "상품금액",
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
/* ══════════════════════════════════════
   화면 6 — 분석 이력
══════════════════════════════════════ */
const HISTORY_DATA = [
    {
        date: "2026.05.20",
        file: "상품성과_20260520.xlsx",
        period: "2026.03~2026.05",
        season: "봄",
        count: "177개",
    },
    {
        date: "2026.04.20",
        file: "상품성과_20260420.xlsx",
        period: "2026.01~2026.03",
        season: "겨울",
        count: "162개",
    },
    {
        date: "2026.03.15",
        file: "상품성과_20260315.xlsx",
        period: "2025.12~2026.02",
        season: "겨울",
        count: "148개",
    },
    {
        date: "2026.02.10",
        file: "상품성과_20260210.xlsx",
        period: "2025.10~2025.12",
        season: "가을",
        count: "135개",
    },
];
const HISTORY_PAGE_SIZE = 5;
function getSeasonStyle(season) {
    if (season.includes("겨울")) {
        return {
            emoji: "❄️",
            bg: "#ECFDF5",
            text: "#047857",
            border: "#A7F3D0",
        };
    }
    if (season.includes("봄")) {
        return {
            emoji: "🌸",
            bg: "#FDF2F8",
            text: "#DB2777",
            border: "#FBCFE8",
        };
    }
    if (season.includes("여름")) {
        return {
            emoji: "☀️",
            bg: "#EFF6FF",
            text: "#2563EB",
            border: "#BFDBFE",
        };
    }
    if (season.includes("가을")) {
        return {
            emoji: "🍂",
            bg: "#FEF3C7",
            text: "#92400E",
            border: "#FCD34D",
        };
    }
    return {
        emoji: "📌",
        bg: "#F8FAFC",
        text: "#475569",
        border: "#E2E8F0",
    };
}
function HistoryScreen({ setScreen, }) {
    const [historyPage, setHistoryPage] = useState(0);
    const historyPageCount = Math.max(1, Math.ceil(HISTORY_DATA.length / HISTORY_PAGE_SIZE));
    const historyPageStart = historyPage * HISTORY_PAGE_SIZE;
    const historyPageEnd = Math.min(historyPageStart + HISTORY_PAGE_SIZE, HISTORY_DATA.length);
    const pagedHistory = HISTORY_DATA.slice(historyPageStart, historyPageEnd);
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
            {pagedHistory.map((row) => (<tr key={row.file} className="hover:bg-slate-50/70 transition-colors">
                <td className="px-5 py-3.5 text-xs font-medium text-slate-700 whitespace-nowrap">
                  {row.date}
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
                      {row.file}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-xs text-slate-500">
                  {row.period}
                </td>
                <td className="px-5 py-3.5">
                  {(() => {
                const seasonStyle = getSeasonStyle(row.season);
                return (<span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border font-semibold whitespace-nowrap" style={{
                        backgroundColor: seasonStyle.bg,
                        color: seasonStyle.text,
                        borderColor: seasonStyle.border,
                    }}>
                        <span>{seasonStyle.emoji}</span>
                        {row.season}
                      </span>);
            })()}
                </td>
                <td className="px-5 py-3.5 text-xs font-semibold text-slate-700 whitespace-nowrap">
                  {row.count}
                </td>
                <td className="px-5 py-3.5">
                  <button onClick={() => setScreen("results")} className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline transition flex items-center gap-1 whitespace-nowrap">
                    결과 보기
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </button>
                </td>
              </tr>))}
          </tbody>
          </table>

          {HISTORY_DATA.length > HISTORY_PAGE_SIZE && (<div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/50">
              <p className="text-[11px] text-slate-400">
                {historyPageStart + 1}–{historyPageEnd} /{" "}
                <strong className="text-slate-600">
                  {HISTORY_DATA.length}
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
/* ══════════════════════════════════════
   화면 4 — 오늘의 추천 액션
══════════════════════════════════════ */
const TODAY_DATA = [
  {
      rank: 1,
      name: "링이 앵글 프릴 블라우스",
      cat: "블라우스",
      actionGroup: "예산 확대",
      action: "예산 확대",
      diagnosisType: "핵심 확대형",
      reason: "클릭률·ROAS 높고 반품률 낮음",
      effect: "광고 효율 확대 가능",
  },
  {
      rank: 2,
      name: "오버핏 린넨 롱 원피스",
      cat: "원피스",
      actionGroup: "개선 필요",
      action: "개선 후 재집행",
      diagnosisType: "상세페이지 개선형",
      reason: "장바구니 대비 구매전환 낮음",
      effect: "상세페이지 개선 필요",
  },
  {
      rank: 3,
      name: "바쉐 베이직 티셔츠",
      cat: "티셔츠",
      actionGroup: "광고 축소",
      action: "광고 축소",
      diagnosisType: "광고 축소형",
      reason: "광고비 대비 매출 낮음",
      effect: "광고비 누수 방지",
  },
  {
      rank: 4,
      name: "크롭 린넨 재킷",
      cat: "재킷",
      actionGroup: "예산 확대",
      action: "예산 확대",
      diagnosisType: "숨은 효율형",
      reason: "ROAS 3.8, 찜 유저수 증가 추세",
      effect: "시즌 수요 선점 가능",
  },
  {
      rank: 5,
      name: "플리츠 미디 스커트",
      cat: "스커트",
      actionGroup: "반품 리스크",
      action: "개선 후 재집행",
      diagnosisType: "반품 리스크 확대 보류형",
      reason: "반품률 9.1%로 업종 평균 초과",
      effect: "반품 원인 분석 후 재집행",
  },
];

const TODAY_ACTION_GROUPS = [
  "전체",
  "예산 확대",
  "예산 유지",
  "개선 필요",
  "광고 축소",
  "반품 리스크",
];

const TODAY_DIAGNOSIS_TYPES = [
  "전체 진단 유형",
  "핵심 확대형",
  "반품 리스크 확대 보류형",
  "구매 직전 이탈형",
  "구매·반품 복합 리스크형",
  "전환 효율형",
  "반품 주의 유지형",
  "상세페이지 개선형",
  "상세·반품 복합 개선형",
  "숨은 효율형",
  "소재 개선+반품 주의형",
  "소재·구매 전환 개선형",
  "소재·구매·반품 복합 리스크형",
  "소수 전환형",
  "소수 전환+반품 리스크형",
  "광고 반응 부족형",
  "광고 축소형",
];

function TodayScreen({ setScreen, }) {
  const [activeGroup, setActiveGroup] = useState("전체");
  const [selectedDiagnosis, setSelectedDiagnosis] = useState("전체 진단 유형");
  const hasData = true;

  const firstAction = TODAY_DATA[0];
  const topActions = TODAY_DATA.slice(1, 4);

  const filtered = TODAY_DATA.filter((row) => {
      const groupMatched =
          activeGroup === "전체" || row.actionGroup === activeGroup;

      const diagnosisMatched =
          selectedDiagnosis === "전체 진단 유형" ||
          row.diagnosisType === selectedDiagnosis;

      return groupMatched && diagnosisMatched;
  });

  const actionMeta = (action) => {
      if (action === "예산 확대") {
          return {
              label: "바로 예산 조정",
              icon: "📈",
              bg: "bg-blue-50",
              border: "border-blue-200",
              text: "text-blue-700",
              todo: "광고 예산을 10~20% 소폭 증액한 뒤 3일간 ROAS와 반품률 변화를 확인하세요.",
          };
      }

      if (action === "개선 후 재집행") {
          return {
              label: "상세페이지 개선",
              icon: "🛠️",
              bg: "bg-amber-50",
              border: "border-amber-200",
              text: "text-amber-700",
              todo: "착용컷, 사이즈 정보, 혜택 문구를 보강한 뒤 광고 재집행을 준비하세요.",
          };
      }

      if (action === "광고 축소") {
          return {
              label: "광고비 누수 방지",
              icon: "📉",
              bg: "bg-rose-50",
              border: "border-rose-200",
              text: "text-rose-700",
              todo: "광고비를 축소하거나 일시 보류하고 상품명, 대표 이미지, 상세페이지를 재점검하세요.",
          };
      }

      return {
          label: "상태 유지 점검",
          icon: "✅",
          bg: "bg-slate-50",
          border: "border-slate-200",
          text: "text-slate-600",
          todo: "현재 예산을 유지하면서 지표 변화를 관찰하세요.",
      };
  };

  const actionGroupBadge = (group) =>
      ({
          "예산 확대": "bg-blue-50 text-blue-700 border-blue-200",
          "예산 유지": "bg-emerald-50 text-emerald-700 border-emerald-200",
          "개선 필요": "bg-amber-50 text-amber-700 border-amber-200",
          "광고 축소": "bg-rose-50 text-rose-700 border-rose-200",
          "반품 리스크": "bg-red-50 text-red-700 border-red-200",
      })[group] ?? "bg-slate-50 text-slate-600 border-slate-200";

  const diagnosisBadge = (type) => {
      if (type.includes("확대") || type.includes("효율") || type.includes("소수 전환")) {
          return "bg-blue-50 text-blue-700 border-blue-200";
      }

      if (type.includes("개선") || type.includes("이탈") || type.includes("구매")) {
          return "bg-amber-50 text-amber-700 border-amber-200";
      }

      if (type.includes("반품") || type.includes("리스크")) {
          return "bg-red-50 text-red-700 border-red-200";
      }

      if (type.includes("축소") || type.includes("반응 부족")) {
          return "bg-rose-50 text-rose-700 border-rose-200";
      }

      if (type.includes("유지")) {
          return "bg-emerald-50 text-emerald-700 border-emerald-200";
      }

      return "bg-slate-50 text-slate-600 border-slate-200";
  };

  if (!hasData) {
      return (
          <div className="flex-1 overflow-y-auto bg-slate-50 p-6">
              <div>
                  <h2 className="text-xl font-bold text-slate-800">
                      오늘의 추천 액션
                  </h2>
                  <p className="text-sm text-slate-400 mt-1">
                      가장 최근 분석 결과를 기준으로 우선 확인해야 할 상품을 정리해드려요.
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
                  <button
                      onClick={() => setScreen("upload")}
                      className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white rounded-xl transition"
                      style={{
                          backgroundColor: "#2563EB",
                          boxShadow: "0 4px 14px rgba(37,99,235,0.25)",
                      }}
                  >
                      상품 성과 파일 업로드하기
                  </button>
              </div>
          </div>
      );
  }

  const firstMeta = actionMeta(firstAction.action);

  return (
      <div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-5">
          {/* 상단 설명 영역 */}
          <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-6">
              <div className="flex items-start justify-between gap-6">
                  <div>
                      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-blue-100 text-[11px] font-bold text-blue-600 mb-3">
                          🎯 최근 분석 파일 기준
                      </div>

                      <h2 className="text-2xl font-bold text-slate-800">
                          오늘의 추천 액션
                      </h2>
                      <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                          최근 분석 파일에서 지금 가장 먼저 조치가 필요한 상품을 우선순위로 정리했어요.
                          <br />
                          전체 상품 결과가 아니라, 오늘 바로 확인해야 할 확대·개선·축소 액션만 추려서 보여줍니다.
                      </p>
                  </div>

                  <div className="bg-white border border-slate-100 rounded-xl px-4 py-3 min-w-[220px] shadow-sm">
                      <p className="text-[11px] font-semibold text-slate-400 mb-1">
                          기준 파일
                      </p>
                      <p className="text-sm font-bold text-slate-700">
                          상품성과_20260520.xlsx
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1">
                          분석 이력의 가장 최근 파일 기준
                      </p>
                  </div>
              </div>
          </div>

          {/* 오늘 1순위 액션 + 체크리스트 */}
          <div className="grid grid-cols-[minmax(0,1.55fr)_minmax(310px,0.45fr)] gap-4">
              <div
                  className={`rounded-2xl border ${firstMeta.border} ${firstMeta.bg} p-6 shadow-sm`}
              >
                  <div className="flex items-start justify-between gap-4 mb-5">
                      <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center text-xl shadow-sm">
                              {firstMeta.icon}
                          </div>

                          <div>
                              <p className="text-[11px] font-bold text-slate-400 mb-1">
                                  오늘 가장 먼저 할 일
                              </p>
                              <h3 className="text-xl font-bold text-slate-800">
                                  {firstAction.name}
                              </h3>
                          </div>
                      </div>

                      <span className="px-2.5 py-1 rounded-lg bg-white/80 border border-white text-[11px] font-bold text-slate-500">
                          {firstAction.cat}
                      </span>
                  </div>

                  <div className="rounded-2xl bg-white/75 border border-white p-4 mb-3">
                      <div className="grid grid-cols-[82px_1fr] gap-3 items-center mb-3">
                          <p className="text-[11px] font-bold text-slate-400">
                              추천 액션
                          </p>
                          <div className="flex items-center gap-2 flex-wrap">
                              <span
                                  className={`text-xs px-2 py-1 rounded-md border font-semibold ${actionGroupBadge(
                                      firstAction.actionGroup
                                  )}`}
                              >
                                  {firstAction.actionGroup}
                              </span>
                              <span
                                  className={`text-xs px-2 py-1 rounded-md border font-semibold ${diagnosisBadge(
                                      firstAction.diagnosisType
                                  )}`}
                              >
                                  {firstAction.diagnosisType}
                              </span>
                              <span className={`text-xs font-bold ${firstMeta.text}`}>
                                  {firstMeta.label}
                              </span>
                          </div>
                      </div>

                      <div className="grid grid-cols-[82px_1fr] gap-3 items-start">
                          <p className="text-[11px] font-bold text-slate-400">
                              선정 근거
                          </p>
                          <p className="text-xs text-slate-600 leading-relaxed">
                              {firstAction.reason}
                          </p>
                      </div>
                  </div>

                  <div className="rounded-2xl bg-white/85 border border-white p-4">
                      <p className="text-[11px] font-bold text-slate-400 mb-1.5">
                          오늘 실행할 액션
                      </p>
                      <p className="text-xs text-slate-600 leading-relaxed">
                          {firstMeta.todo}
                      </p>
                  </div>

                  <button
                      onClick={() => setScreen("detail")}
                      className="mt-4 bg-white text-blue-600 border border-blue-100 rounded-xl px-4 py-2 text-xs font-bold hover:bg-blue-50 transition flex items-center gap-1"
                  >
                      상세 진단 보기
                      <svg
                          width="11"
                          height="11"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                      >
                          <polyline points="9 18 15 12 9 6" />
                      </svg>
                  </button>
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-4">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                          ✅
                      </div>
                      <div>
                          <h3 className="text-sm font-bold text-slate-800">
                              오늘 전체 액션 체크리스트
                          </h3>
                          <p className="text-[11px] text-slate-400">
                              우선 조치 상품 전체를 기준으로 자동 생성했어요.
                          </p>
                      </div>
                  </div>

                  <div className="space-y-3">
                      {[
                          "광고 확대 후보의 ROAS·반품률 확인",
                          "상세페이지 개선 상품의 착용컷·사이즈 정보 점검",
                          "광고 축소 후보의 광고비 누수 여부 확인",
                          "반품 리스크 상품의 리뷰 키워드 확인",
                      ].map((item) => (
                          <label
                              key={item}
                              className="flex items-start gap-2 text-xs text-slate-600 leading-relaxed"
                          >
                              <input
                                  type="checkbox"
                                  className="mt-0.5 rounded border-slate-300"
                              />
                              <span>{item}</span>
                          </label>
                      ))}
                  </div>
              </div>
          </div>

          {/* 다음 우선순위 카드 */}
          <div className="grid grid-cols-3 gap-4">
              {topActions.map((row) => {
                  const meta = actionMeta(row.action);

                  return (
                      <div
                          key={row.rank}
                          className={`rounded-2xl border ${meta.border} ${meta.bg} p-5 shadow-sm`}
                      >
                          <div className="flex items-start justify-between mb-4">
                              <div className="flex items-center gap-2">
                                  <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-lg shadow-sm">
                                      {meta.icon}
                                  </div>
                                  <div>
                                      <p className="text-[11px] font-bold text-slate-400">
                                          오늘의 {row.rank}순위
                                      </p>
                                      <p className={`text-xs font-bold ${meta.text}`}>
                                          {meta.label}
                                      </p>
                                  </div>
                              </div>

                              <span className="px-2 py-1 rounded-lg bg-white/80 border border-white text-[11px] font-bold text-slate-500">
                                  {row.cat}
                              </span>
                          </div>

                          <h3 className="text-base font-bold text-slate-800 mb-2">
                              {row.name}
                          </h3>

                          <div className="space-y-3">
                              <div>
                                  <p className="text-[11px] font-bold text-slate-400 mb-1">
                                      추천 액션
                                  </p>
                                  <div className="flex items-center gap-1.5 flex-wrap">
                                      <span
                                          className={`text-xs px-2 py-1 rounded-md border font-semibold ${actionGroupBadge(
                                              row.actionGroup
                                          )}`}
                                      >
                                          {row.actionGroup}
                                      </span>
                                      <span
                                          className={`text-xs px-2 py-1 rounded-md border font-semibold ${diagnosisBadge(
                                              row.diagnosisType
                                          )}`}
                                      >
                                          {row.diagnosisType}
                                      </span>
                                  </div>
                              </div>

                              <div>
                                  <p className="text-[11px] font-bold text-slate-400 mb-1">
                                      우선 확인 이유
                                  </p>
                                  <p className="text-xs text-slate-600 leading-relaxed">
                                      {row.reason}
                                  </p>
                              </div>

                              <div className="rounded-xl bg-white/70 border border-white px-3 py-3">
                                  <p className="text-[11px] font-bold text-slate-400 mb-1">
                                      오늘 할 일
                                  </p>
                                  <p className="text-xs text-slate-600 leading-relaxed">
                                      {meta.todo}
                                  </p>
                              </div>
                          </div>

                          <button
                              onClick={() => setScreen("detail")}
                              className="mt-4 w-full bg-white text-blue-600 border border-blue-100 rounded-xl py-2 text-xs font-bold hover:bg-blue-50 transition flex items-center justify-center gap-1"
                          >
                              상세 진단 보기
                              <svg
                                  width="11"
                                  height="11"
                                  viewBox="0 0 24 24"
                                  fill="none"
                                  stroke="currentColor"
                                  strokeWidth="2.5"
                              >
                                  <polyline points="9 18 15 12 9 6" />
                              </svg>
                          </button>
                      </div>
                  );
              })}
          </div>

          {/* 액션별 확인 목록 */}
          <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
              <div className="flex items-center gap-1 px-4 pt-4 pb-2 border-b border-slate-100 overflow-x-auto">
                  {TODAY_ACTION_GROUPS.map((tab) => (
                      <button
                          key={tab}
                          onClick={() => setActiveGroup(tab)}
                          className={`flex-shrink-0 px-3 py-2 text-xs font-semibold rounded-lg transition-all border ${
                              activeGroup === tab
                                  ? "border-blue-200 text-blue-700 bg-blue-50"
                                  : "border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                          }`}
                      >
                          {tab}
                      </button>
                  ))}

                  <div className="flex-1" />

                  <select
                      value={selectedDiagnosis}
                      onChange={(e) => setSelectedDiagnosis(e.target.value)}
                      className="flex-shrink-0 h-8 px-3 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  >
                      {TODAY_DIAGNOSIS_TYPES.map((type) => (
                          <option key={type} value={type}>
                              {type}
                          </option>
                      ))}
                  </select>

                  <button
                      onClick={() => setScreen("results")}
                      className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-500 hover:text-blue-600 transition rounded-lg hover:bg-blue-50"
                  >
                      전체 결과 보기
                      <svg
                          width="11"
                          height="11"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                      >
                          <polyline points="9 18 15 12 9 6" />
                      </svg>
                  </button>
              </div>

              {filtered.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-2xl">
                          📋
                      </div>
                      <p className="text-sm font-semibold text-slate-500 mb-1">
                          해당 조건의 상품이 없습니다
                      </p>
                      <p className="text-xs text-slate-400">
                          다른 액션 그룹이나 진단 유형을 선택해보세요.
                      </p>
                  </div>
              ) : (
                  <div>
                      <div className="grid grid-cols-[52px_minmax(0,1.35fr)_110px_150px_minmax(0,1fr)_82px] gap-4 px-5 py-3 bg-slate-50 border-b border-slate-100">
                          <p className="text-[11px] font-bold text-slate-400">순위</p>
                          <p className="text-[11px] font-bold text-slate-400">상품명</p>
                          <p className="text-[11px] font-bold text-slate-400">액션 그룹</p>
                          <p className="text-[11px] font-bold text-slate-400">진단 유형</p>
                          <p className="text-[11px] font-bold text-slate-400">추천 이유</p>
                          <p className="text-[11px] font-bold text-slate-400 text-right">
                              상세
                          </p>
                      </div>

                      <div className="divide-y divide-slate-50">
                          {filtered.map((row) => (
                              <div
                                  key={row.rank}
                                  className="grid grid-cols-[52px_minmax(0,1.35fr)_110px_150px_minmax(0,1fr)_82px] gap-4 px-5 py-4 hover:bg-slate-50/70 transition-colors items-center"
                              >
                                  <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-xs font-bold text-slate-500">
                                      {row.rank}
                                  </div>

                                  <div className="min-w-0">
                                      <div className="flex items-center gap-2 mb-1">
                                          <p className="text-sm font-bold text-slate-700 truncate">
                                              {row.name}
                                          </p>
                                          <span className="text-[11px] text-slate-400">
                                              {row.cat}
                                          </span>
                                      </div>
                                      <p className="text-[11px] text-slate-400 truncate">
                                          {row.effect}
                                      </p>
                                  </div>

                                  <span
                                      className={`w-fit text-xs px-2 py-1 rounded-md border font-semibold ${actionGroupBadge(
                                          row.actionGroup
                                      )}`}
                                  >
                                      {row.actionGroup}
                                  </span>

                                  <span
                                      className={`w-fit text-xs px-2 py-1 rounded-md border font-semibold ${diagnosisBadge(
                                          row.diagnosisType
                                      )}`}
                                  >
                                      {row.diagnosisType}
                                  </span>

                                  <p className="text-xs text-slate-500 truncate">
                                      {row.reason}
                                  </p>

                                  <button
                                      onClick={() => setScreen("detail")}
                                      className="justify-self-end text-xs font-semibold text-blue-600 hover:text-blue-800 transition flex items-center gap-1"
                                  >
                                      상세 보기
                                      <svg
                                          width="11"
                                          height="11"
                                          viewBox="0 0 24 24"
                                          fill="none"
                                          stroke="currentColor"
                                          strokeWidth="2.5"
                                      >
                                          <polyline points="9 18 15 12 9 6" />
                                      </svg>
                                  </button>
                              </div>
                          ))}
                      </div>
                  </div>
              )}
          </div>

          <div className="flex items-center pb-2">
              <button
                  onClick={() => setScreen("main")}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600 transition"
              >
                  <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                  >
                      <polyline points="15 18 9 12 15 6" />
                  </svg>
                  메인으로 돌아가기
              </button>
          </div>
      </div>
  );
}
/* ══════════════════════════════════════
   화면 5 — 상품 액션 추천 결과
══════════════════════════════════════ */
const RESULTS_DATA = [
    { name: "링이 앵글 프릴 블라우스", cat: "블라우스", action: "예산 확대", priority: "높음", rank: 1, reason: "ROAS 4.2, CTR 상위 15%, 반품률 낮음", status: "완료" },
    { name: "데일리 셔링 리본 원피스", cat: "원피스", action: "예산 유지", priority: "낮음", rank: 8, reason: "지표 안정적, 시즌 변동 없음", status: "완료" },
    { name: "오버핏 린넨 롱 원피스", cat: "원피스", action: "개선 후 재집행", priority: "보통", rank: 4, reason: "장바구니 전환율 낮음, 상세페이지 이탈 높음", status: "진행중" },
    { name: "바쉐 베이직 티셔츠", cat: "티셔츠", action: "광고 축소", priority: "높음", rank: 2, reason: "ROAS 0.8, 광고비 대비 매출 부족", status: "대기" },
    { name: "플리츠 미디 스커트", cat: "스커트", action: "예산 유지", priority: "보통", rank: 5, reason: "구매전환율 보통, 찜 유저수 증가 추세", status: "완료" },
    { name: "크롭 린넨 재킷", cat: "재킷", action: "예산 확대", priority: "높음", rank: 1, reason: "CTR 3.1%, ROAS 3.8, 시즌 적합도 높음", status: "완료" },
    { name: "베이직 스트라이프 티셔츠", cat: "티셔츠", action: "예산 유지", priority: "낮음", rank: 9, reason: "지표 안정, 클릭률 평균 수준", status: "완료" },
    { name: "플로럴 미디 원피스", cat: "원피스", action: "예산 확대", priority: "높음", rank: 2, reason: "ROAS 5.1, 장바구니 전환율 상위 20%", status: "완료" },
    { name: "와이드 슬랙스", cat: "바지", action: "개선 후 재집행", priority: "보통", rank: 6, reason: "클릭 대비 구매전환율 낮음, 사이즈 이슈 의심", status: "진행중" },
    { name: "솔리드 카디건", cat: "니트", action: "예산 유지", priority: "낮음", rank: 7, reason: "반품률 안정, ROAS 2.9 유지 중", status: "완료" },
    { name: "리넨 셔링 블라우스", cat: "블라우스", action: "광고 축소", priority: "높음", rank: 3, reason: "ROAS 1.1, 노출 대비 클릭 저조", status: "대기" },
    { name: "오간자 프릴 블라우스", cat: "블라우스", action: "예산 확대", priority: "보통", rank: 4, reason: "CTR 2.8%, 찜 유저 증가 추세", status: "완료" },
    { name: "숏 데님 재킷", cat: "재킷", action: "광고 축소", priority: "높음", rank: 1, reason: "광고비 비중 38%, ROAS 0.6 기준 미달", status: "대기" },
    { name: "체크 미니 스커트", cat: "스커트", action: "예산 유지", priority: "낮음", rank: 8, reason: "계절 전환기 안정 유지, 재고 소진 중", status: "완료" },
    { name: "루즈핏 니트 가디건", cat: "니트", action: "개선 후 재집행", priority: "보통", rank: 5, reason: "상세페이지 이탈 높음, 리뷰 부족", status: "진행중" },
    { name: "머메이드 롱 스커트", cat: "스커트", action: "예산 확대", priority: "높음", rank: 2, reason: "ROAS 4.7, 구매전환율 상위 10%", status: "완료" },
    { name: "슬림 컷 슬랙스", cat: "바지", action: "예산 유지", priority: "보통", rank: 6, reason: "전월 대비 지표 유지, 시즌 적합", status: "완료" },
    { name: "레이스 크롭 탑", cat: "탑", action: "광고 축소", priority: "보통", rank: 7, reason: "클릭률 0.9%, 업종 평균 대비 저조", status: "대기" },
    { name: "컬러 블록 원피스", cat: "원피스", action: "예산 확대", priority: "높음", rank: 3, reason: "신규 상품 ROAS 3.6, 빠른 성장세", status: "완료" },
    { name: "롤업 데님 팬츠", cat: "바지", action: "개선 후 재집행", priority: "보통", rank: 4, reason: "반품률 8.2%, 사이즈 안내 보완 필요", status: "진행중" },
    { name: "실크 터치 블라우스", cat: "블라우스", action: "예산 유지", priority: "낮음", rank: 9, reason: "ROAS 2.4 안정, 큰 변동 없음", status: "완료" },
    { name: "네온 컬러 탑", cat: "탑", action: "광고 축소", priority: "높음", rank: 2, reason: "ROAS 0.5, 재고 부담 증가", status: "대기" },
    { name: "트위드 미니 재킷", cat: "재킷", action: "예산 확대", priority: "보통", rank: 5, reason: "CTR 2.5%, 가을 시즌 적합도 높음", status: "완료" },
    { name: "에코 퍼 베스트", cat: "베스트", action: "예산 유지", priority: "낮음", rank: 7, reason: "겨울 시즌 안정적 성과", status: "완료" },
    { name: "플리스 집업 후드", cat: "아우터", action: "개선 후 재집행", priority: "높음", rank: 3, reason: "노출 대비 구매전환율 1.2%, 상세 개선 필요", status: "진행중" },
];
function getDiagnosisType(row) {
    if (row.action === "예산 확대")
        return "핵심 확대형";
    if (row.action === "예산 유지")
        return "반품 주의 유지형";
    if (row.action === "개선 후 재집행")
        return "상세페이지 개선형";
    if (row.action === "광고 축소")
        return "광고 축소형";
    return "진단 필요";
}
function getRecommendedAction(row) {
    if (row.action === "예산 확대")
        return "광고 예산 확대";
    if (row.action === "예산 유지")
        return "현재 예산 유지";
    if (row.action === "개선 후 재집행")
        return "상세 정보 보강";
    if (row.action === "광고 축소")
        return "광고비 축소·보류";
    return "확인 필요";
}
function getDetailData(row) {
    const diagnosisType = getDiagnosisType(row);
    const recommendedAction = getRecommendedAction(row);
    const isExpand = row.action === "예산 확대";
    const isMaintain = row.action === "예산 유지";
    const isImprove = row.action === "개선 후 재집행";
    const isReduce = row.action === "광고 축소";
    const score = isExpand
        ? 84
        : isMaintain
            ? 65
            : isImprove
                ? 58
                : isReduce
                    ? 38
                    : 52.6;
    const penalty = isExpand
        ? 0
        : isMaintain
            ? -5
            : isImprove
                ? -12
                : isReduce
                    ? -25
                    : -25;
    return {
        diagnosisType,
        recommendedAction,
        score,
        penalty,
        recommendedAdBudget: isExpand
            ? "42,700원"
            : isMaintain
                ? "25,000원"
                : isImprove
                    ? "18,500원"
                    : "10,200원",
        actionSummary: isExpand
            ? "성과 지표가 안정적이므로 광고 예산을 소폭 확대해 테스트할 수 있습니다."
            : isMaintain
                ? "성과가 안정적인 편이므로 현재 예산을 유지하며 반품과 전환 흐름을 관찰합니다."
                : isImprove
                    ? "상세페이지와 구매 전환 요소를 개선한 뒤 광고 재집행을 검토합니다."
                    : "광고 효율이 낮아 광고비 확대는 보류하고, 소재와 전환 구조를 먼저 개선합니다.",
        scoreBars: [
            {
                label: "클릭률 점수",
                score: isExpand ? 89 : isMaintain ? 62 : isImprove ? 74 : 34,
            },
            {
                label: "찜 전환율 점수",
                score: isExpand ? 82 : isMaintain ? 68 : isImprove ? 59 : 41,
            },
            {
                label: "장바구니 전환율 점수",
                score: isExpand ? 85 : isMaintain ? 64 : isImprove ? 42 : 28,
            },
            {
                label: "구매전환율 점수",
                score: isExpand ? 88 : isMaintain ? 61 : isImprove ? 39 : 22,
            },
            {
                label: "반품 안정성 점수",
                score: isExpand ? 91 : isMaintain ? 57 : isImprove ? 63 : 40,
            },
            {
                label: "ROAS 점수",
                score: isExpand ? 86 : isMaintain ? 72 : isImprove ? 48 : 12,
            },
        ],
        adEfficiencyScore: isExpand
            ? 86
            : isMaintain
                ? 67
                : isImprove
                    ? 49
                    : 23,
        basicRawData: [
            { label: "상품ID", value: "125448201" },
            { label: "상품명", value: row.name },
            { label: "카테고리", value: row.cat },
            { label: "판매 사이트", value: "에이블리" },
        ],
        performanceRawData: [
            {
                label: "노출수",
                value: isExpand
                    ? "45,678"
                    : isMaintain
                        ? "31,420"
                        : isImprove
                            ? "28,500"
                            : "15,600",
            },
            {
                label: "클릭수",
                value: isExpand
                    ? "2,501"
                    : isMaintain
                        ? "879"
                        : isImprove
                            ? "1,560"
                            : "187",
            },
            {
                label: "광고비",
                value: isExpand
                    ? "12,000원"
                    : isMaintain
                        ? "8,500원"
                        : isImprove
                            ? "7,100원"
                            : "6,800원",
            },
            {
                label: "주문금액",
                value: isExpand
                    ? "45,000원"
                    : isMaintain
                        ? "28,000원"
                        : isImprove
                            ? "23,000원"
                            : "5,400원",
            },
            {
                label: "상품금액",
                value: isExpand
                    ? "39,000원"
                    : isMaintain
                        ? "28,000원"
                        : isImprove
                            ? "23,000원"
                            : "10,200원",
            },
            {
                label: "상품 상세 방문수",
                value: isExpand
                    ? "1,841"
                    : isMaintain
                        ? "796"
                        : isImprove
                            ? "631"
                            : "162",
            },
            {
                label: "장바구니 유저수",
                value: isExpand
                    ? "171명"
                    : isMaintain
                        ? "54명"
                        : isImprove
                            ? "52명"
                            : "5명",
            },
            {
                label: "찜 유저수",
                value: isExpand
                    ? "134명"
                    : isMaintain
                        ? "120명"
                        : isImprove
                            ? "60명"
                            : "25명",
            },
            {
                label: "상품주문수",
                value: isExpand
                    ? "38건"
                    : isMaintain
                        ? "22건"
                        : isImprove
                            ? "19건"
                            : "3건",
            },
            {
                label: "반품건수",
                value: isExpand
                    ? "2건"
                    : isMaintain
                        ? "1건"
                        : isImprove
                            ? "3건"
                            : "3건",
            },
        ],
        coachingFeedback: isExpand
            ? [
                {
                    label: "상품클릭률",
                    status: "veryGood",
                    text: "상위 10% 그룹 평균 대비 166.9% 수준으로 매우 우수합니다.",
                },
                {
                    label: "찜전환율",
                    status: "good",
                    text: "상위 10% 그룹 평균의 72.8% 수준으로 양호합니다.",
                },
                {
                    label: "장바구니전환율",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 36.1% 수준으로 개선이 필요합니다.",
                },
                {
                    label: "구매전환율",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 22.0% 수준으로 개선이 필요합니다.",
                },
                {
                    label: "반품안정성",
                    status: "veryGood",
                    text: "상위 10% 그룹 평균 대비 105.6% 수준으로 매우 우수합니다.",
                },
                {
                    label: "ROAS",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 0.0% 수준으로 개선이 필요합니다.",
                },
            ]
            : isMaintain
                ? [
                    {
                        label: "상품클릭률",
                        status: "good",
                        text: "같은 카테고리 평균 수준으로 안정적인 클릭 반응을 보입니다.",
                    },
                    {
                        label: "찜전환율",
                        status: "good",
                        text: "관심 유입은 안정적이며 급격한 조정은 필요하지 않습니다.",
                    },
                    {
                        label: "장바구니전환율",
                        status: "good",
                        text: "장바구니 전환 흐름이 평균권으로 유지되고 있습니다.",
                    },
                    {
                        label: "구매전환율",
                        status: "normal",
                        text: "구매전환율은 평균권이나 추가 개선 여지가 있습니다.",
                    },
                    {
                        label: "반품안정성",
                        status: "normal",
                        text: "반품 안정성은 보통 수준으로 지속 관찰이 필요합니다.",
                    },
                    {
                        label: "ROAS",
                        status: "good",
                        text: "ROAS가 안정적으로 유지되어 현재 예산 유지가 적절합니다.",
                    },
                ]
                : isImprove
                    ? [
                        {
                            label: "상품클릭률",
                            status: "good",
                            text: "클릭 반응은 양호하지만 이후 전환 흐름이 약합니다.",
                        },
                        {
                            label: "찜전환율",
                            status: "normal",
                            text: "찜 전환은 보통 수준으로 상품 관심은 일부 확인됩니다.",
                        },
                        {
                            label: "장바구니전환율",
                            status: "weak",
                            text: "상세 방문 대비 장바구니 전환이 낮아 상세페이지 설득력 개선이 필요합니다.",
                        },
                        {
                            label: "구매전환율",
                            status: "weak",
                            text: "구매전환율이 낮아 가격, 혜택, 상세 정보 보강이 필요합니다.",
                        },
                        {
                            label: "반품안정성",
                            status: "normal",
                            text: "반품 안정성은 보통 수준이나 개선 후 함께 확인해야 합니다.",
                        },
                        {
                            label: "ROAS",
                            status: "weak",
                            text: "광고비 대비 주문금액이 낮아 ROAS 개선이 필요합니다.",
                        },
                    ]
                    : [
                        {
                            label: "상품클릭률",
                            status: "weak",
                            text: "클릭률이 낮아 광고 소재와 대표 이미지 개선이 필요합니다.",
                        },
                        {
                            label: "찜전환율",
                            status: "weak",
                            text: "상품 관심 유입이 낮아 상품명과 썸네일 점검이 필요합니다.",
                        },
                        {
                            label: "장바구니전환율",
                            status: "weak",
                            text: "상세 방문 이후 장바구니 전환이 약합니다.",
                        },
                        {
                            label: "구매전환율",
                            status: "weak",
                            text: "구매전환율이 낮아 광고 확대보다 전환 개선이 우선입니다.",
                        },
                        {
                            label: "반품안정성",
                            status: "normal",
                            text: "주문 수가 적어 반품 안정성은 보수적으로 판단합니다.",
                        },
                        {
                            label: "ROAS",
                            status: "weak",
                            text: "ROAS가 기준 미달로 광고비 회수 효율이 낮습니다.",
                        },
                    ],
        funnelStages: [
            {
                label: "노출",
                value: isExpand ? "45,678" : isMaintain ? "31,420" : isImprove ? "28,500" : "15,600",
                rate: "",
                bottleneck: false,
            },
            {
                label: "클릭",
                value: isExpand ? "2,501" : isMaintain ? "879" : isImprove ? "1,560" : "187",
                rate: isExpand ? "CTR 5.48%" : isMaintain ? "CTR 2.80%" : isImprove ? "CTR 5.47%" : "CTR 1.20%",
                bottleneck: isReduce,
            },
            {
                label: "상세 방문",
                value: isExpand ? "1,841" : isMaintain ? "796" : isImprove ? "631" : "162",
                rate: isExpand ? "73.6%" : isMaintain ? "90.6%" : isImprove ? "40.4%" : "86.6%",
                bottleneck: isImprove,
            },
            {
                label: "장바구니",
                value: isExpand ? "171" : isMaintain ? "54" : isImprove ? "52" : "5",
                rate: isExpand ? "9.3%" : isMaintain ? "6.8%" : isImprove ? "8.2%" : "3.1%",
                bottleneck: isImprove,
            },
            {
                label: "구매",
                value: isExpand ? "38" : isMaintain ? "22" : isImprove ? "19" : "3",
                rate: isExpand ? "2.1%" : isMaintain ? "2.8%" : isImprove ? "3.0%" : "1.9%",
                bottleneck: isImprove || isReduce,
            },
        ],
        bottleneckMessage: isExpand
            ? "현재 주요 병목은 크지 않으며, 노출부터 구매까지 전환 흐름이 비교적 안정적입니다."
            : isMaintain
                ? "전반적인 퍼널 흐름은 안정적이며, 특정 단계의 급격한 이탈은 크지 않습니다."
                : isImprove
                    ? "상세 방문 이후 장바구니와 구매 전환 구간에서 병목이 감지됩니다."
                    : "노출 이후 클릭과 구매 전환으로 이어지는 흐름이 약해 퍼널 전반의 개선이 필요합니다.",
        bottleneckCauses: isExpand
            ? [
                "클릭률이 상위 그룹 대비 높아 광고 소재 반응이 우수합니다.",
                "반품 안정성이 높아 광고 확대 시 리스크가 낮은 편입니다.",
                "장바구니·구매 전환 구간은 개선 여지가 있으므로 확대 후 전환율 변화를 함께 확인해야 합니다.",
            ]
            : isMaintain
                ? [
                    "전반적인 퍼널 흐름은 안정적이지만 일부 전환 지표는 추가 개선 여지가 있습니다.",
                    "현재 예산은 유지하되 찜, 장바구니, 구매 전환 흐름을 주기적으로 확인해야 합니다.",
                    "시즌 변화나 반품률 상승이 발생하면 광고 운영 방향을 재검토해야 합니다.",
                ]
                : isImprove
                    ? [
                        "상세페이지 방문 이후 장바구니와 구매 전환으로 이어지는 비율이 낮습니다.",
                        "상품 상세페이지의 착용컷, 소재 설명, 사이즈 정보가 부족할 가능성이 있습니다.",
                        "구매 전 혜택, 배송, 교환·반품 안내가 충분히 설득되지 않았을 가능성이 있습니다.",
                    ]
                    : [
                        "노출 이후 클릭으로 이어지는 반응이 낮아 광고 소재 매력이 부족할 가능성이 있습니다.",
                        "클릭 이후 상세페이지와 구매 전환으로 이어지는 흐름이 약합니다.",
                        "광고비 대비 주문금액이 낮아 현재 광고 효율을 먼저 점검해야 합니다.",
                    ],
        actionItems: isExpand
            ? [
                {
                    tag: "예산 테스트",
                    text: "현재 예산을 한 번에 크게 늘리기보다, 3~5일 동안 소폭 증액해 클릭률과 구매전환율이 유지되는지 확인합니다.",
                },
                {
                    tag: "전환 보강",
                    text: "광고를 늘리기 전에 상세 상단의 구매 혜택, 배송 안내, 사이즈 불안 요소를 먼저 정리해 구매 전환 손실을 줄입니다.",
                },
                {
                    tag: "중단 기준",
                    text: "증액 후 ROAS가 떨어지거나 반품률이 상승하면 확대를 멈추고 상세 정보와 기대 불일치 요소를 먼저 점검합니다.",
                },
            ]
            : isMaintain
                ? [
                    {
                        tag: "유지 운영",
                        text: "현재 예산은 유지하되, 클릭률과 구매전환율이 함께 떨어지는지 주기적으로 확인합니다.",
                    },
                    {
                        tag: "소폭 개선",
                        text: "성과를 크게 바꾸기보다 상세 상단 문구, 대표 이미지, 혜택 안내처럼 전환에 가까운 요소부터 가볍게 보완합니다.",
                    },
                    {
                        tag: "재검토 기준",
                        text: "반품률이 오르거나 ROAS가 낮아지면 유지 전략을 멈추고 개선형 상품으로 재분류해 점검합니다.",
                    },
                ]
                : isImprove
                    ? [
                        {
                            tag: "전환 점검",
                            text: "클릭 이후 이탈이 발생하는 구간을 기준으로 상세페이지 상단, 착용컷, 소재·사이즈 설명을 먼저 보강합니다.",
                        },
                        {
                            tag: "구매 설득",
                            text: "장바구니 이후 구매가 약하다면 쿠폰, 배송비, 교환·반품 안내처럼 결제 직전 불안 요소를 정리합니다.",
                        },
                        {
                            tag: "재집행",
                            text: "상세페이지 수정 후 바로 큰 예산을 투입하지 말고, 소액 광고로 전환율 변화부터 다시 확인합니다.",
                        },
                    ]
                    : [
                        {
                            tag: "확대 보류",
                            text: "현재는 광고를 더 늘리기보다 예산 소진을 줄이고, 클릭률과 구매전환율이 낮은 원인을 먼저 확인합니다.",
                        },
                        {
                            tag: "소재 점검",
                            text: "노출 대비 클릭 반응이 낮다면 대표 이미지, 첫 문구, 상품명 키워드가 충분히 매력적인지 먼저 수정합니다.",
                        },
                        {
                            tag: "재판단",
                            text: "소재와 상세페이지를 수정한 뒤에도 클릭률과 ROAS가 회복되지 않으면 광고 축소 또는 보류 상태를 유지합니다.",
                        },
                    ],
    };
}
function ProductDetailModal({ product, onClose, setScreen, }) {
    const d = getDetailData(product);
    const bottleneckCauses = d.bottleneckCauses;
    const actionItems = d.actionItems;
    const scoreColor = d.score >= 80
        ? "#2563EB"
        : d.score >= 60
            ? "#059669"
            : d.score >= 40
                ? "#D97706"
                : "#E11D48";
    return (<div className="fixed inset-0 z-50 flex items-center justify-center p-6" style={{
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
              {/* 왼쪽: 원형 점수 */}
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

              {/* 가운데: 지표별 점수 */}
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
                  {d.scoreBars.map((s) => (<div key={s.label} className="grid grid-cols-[140px_1fr_44px] items-center gap-3">
                      <span className="text-xs text-slate-500">
                        {s.label}
                      </span>

                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all bg-blue-600" style={{
                width: `${s.score}%`,
            }}/>
                      </div>

                      <span className="text-xs font-bold text-slate-700 text-right">
                        {s.score}점
                      </span>
                    </div>))}
                </div>
              </div>

              {/* 오른쪽: 권장 광고 운영 금액 */}
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

              <p className="text-[10px] text-slate-400">
                업로드 파일 기준
              </p>
            </div>

            {/* 상품 기본 정보 */}
            <div className="mb-4">
              <p className="text-[11px] font-bold text-slate-400 mb-2">
                상품 기본 정보
              </p>

              <div className="grid grid-cols-4 gap-3">
                {d.basicRawData.map((m) => (<div key={m.label} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                    <p className="text-[10px] text-slate-400 font-semibold mb-0.5">
                      {m.label}
                    </p>
                    <p className="text-sm font-bold text-slate-800 truncate">
                      {m.value}
                    </p>
                  </div>))}
              </div>
            </div>

            {/* 성과 원본 데이터 */}
            <div>
              <p className="text-[11px] font-bold text-slate-400 mb-2">
                성과 원본 데이터
              </p>

              <div className="grid grid-cols-5 gap-3">
                {d.performanceRawData.map((m) => (<div key={m.label} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                    <p className="text-[10px] text-slate-400 font-semibold mb-0.5">
                      {m.label}
                    </p>
                    <p className="text-sm font-bold text-slate-800 truncate">
                      {m.value}
                    </p>
                  </div>))}
              </div>
            </div>
          </div>

          {/* 퍼널·성과 지표 해석 */}
          <div className="bg-white rounded-xl border border-slate-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  퍼널·성과 지표 해석
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  퍼널 전환 지표와 광고·리스크 보조 지표를 구분해 해석합니다.
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
                        {weakSteps.length > 0 ? (<>
                            병목 감지:{" "}
                            <strong>
                              {weakSteps.map((item) => item.step).join(", ")}
                            </strong>{" "}
                            단계에서 상위 그룹 대비 낮은 전환 흐름이 확인됩니다.
                          </>) : (<>
                            현재 퍼널 흐름은 전반적으로 안정적이며, 급격한 이탈 구간은 크지 않습니다.
                          </>)}
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
                {bottleneckCauses.map((cause, i) => (<div key={i} className="flex items-start gap-2.5 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2.5">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white border border-slate-200 text-[10px] font-bold text-slate-400 flex items-center justify-center">
                      {i + 1}
                    </span>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {cause}
                    </p>
                  </div>))}
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
                {actionItems.map((action) => (<div key={action.tag} className="flex items-start gap-3 bg-white rounded-lg border border-blue-100 px-3 py-2.5">
                    <span className={`flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-md ${action.tag === "예산 테스트" || action.tag === "유지 운영" || action.tag === "전환 점검" || action.tag === "확대 보류"
                ? "bg-blue-600 text-white"
                : action.tag === "전환 보강" || action.tag === "소폭 개선" || action.tag === "구매 설득" || action.tag === "소재 점검"
                    ? "bg-amber-100 text-amber-700"
                    : action.tag === "중단 기준" || action.tag === "재검토 기준" || action.tag === "재집행" || action.tag === "재판단"
                        ? "bg-slate-100 text-slate-600"
                        : "bg-slate-100 text-slate-600"}`}>
                      {action.tag}
                    </span>

                    <p className="text-xs text-slate-700 leading-relaxed">
                      {action.text}
                    </p>
                  </div>))}
              </div>
            </div>
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
    </div>);
}
const RESULTS_PAGE_SIZE = 10;
function ResultsScreen({ setScreen, }) {
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
/* ══════════════════════════════════════
   화면 4 — 상품 상세 진단
══════════════════════════════════════ */
function DetailScreen({ setScreen, }) {
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
/* ══════════════════════════════════════
   Root
══════════════════════════════════════ */
export default function App() {
    const [screen, setScreen] = useState("main");
    return (<div className="flex h-screen w-screen bg-slate-50 overflow-hidden" style={{
            fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif",
        }}>
      <Sidebar screen={screen} setScreen={setScreen}/>
      <div className="flex flex-col flex-1 min-w-0">
        <Topbar subtitle={screen === "upload"
            ? "상품 성과 파일 업로드"
            : screen === "results"
                ? "상품 액션 추천 결과"
                : screen === "detail"
                    ? "상품 상세 진단"
                    : screen === "history"
                        ? "분석 이력"
                        : screen === "today"
                            ? "오늘의 추천 액션"
                            : screen === "diag"
                                ? "판매 전 카테고리 진단"
                                : screen === "chat"
                                    ? "쇼핑몰 법 규제 챗봇"
                                    : screen === "basis"
                                        ? "진단 기준"
                                        : undefined}/>
        {screen === "main" ? (<MainScreen setScreen={setScreen}/>) : screen === "upload" ? (<UploadScreen setScreen={setScreen}/>) : screen === "results" ? (<ResultsScreen setScreen={setScreen}/>) : screen === "detail" ? (<DetailScreen setScreen={setScreen}/>) : screen === "history" ? (<HistoryScreen setScreen={setScreen}/>) : screen === "today" ? (<TodayScreen setScreen={setScreen}/>) : screen === "diag" ? (<DiagScreen setScreen={setScreen}/>) : screen === "chat" ? (<ChatScreen setScreen={setScreen}/>) : (<BasisScreen setScreen={setScreen}/>)}
      </div>
    </div>);
}