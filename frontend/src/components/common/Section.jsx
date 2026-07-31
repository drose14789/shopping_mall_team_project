import React, { useState } from "react";
import {BasisCardHeader} from "./header";

export function BasisSection({
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