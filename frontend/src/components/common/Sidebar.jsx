import React from 'react';
import { NAV_ITEMS } from '../../constants/data';

export function Sidebar({ screen, setScreen, }) {
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

export function Topbar({ subtitle, icon: Icon }) {
    return (<header className="h-14 bg-white border-b border-slate-100 flex items-center px-6 gap-4 flex-shrink-0">
      <div className="flex items-center gap-3 flex-1">
        {Icon && (
          <Icon
            size={18}
            className="text-blue-500"
          />
        )}
        {subtitle && (<>
            <span className="text-slate-200 text-sm">|</span>
            <span className="text-sm font-semibold text-slate-500">
              {subtitle}
            </span>
          </>)}
      </div>
    </header>);
}