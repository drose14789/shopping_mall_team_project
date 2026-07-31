import React from 'react';

export function HomeIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>);
}
export function ChartIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>);
}
export function DiagIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>);
}
export function ChatIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
    </svg>);
}
export function BasisIcon({ active }) {
    return (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={active ? "#2563eb" : "#94a3b8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>);
}

export function DashboardIllustration() {
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

export function UploadIllustration() {
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

export function DiagIllustration() {
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