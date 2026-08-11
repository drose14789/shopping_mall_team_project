import { SEASON_BY_MONTH } from '../constants/data'; 


export function getClientUuid(){

    let uuid = localStorage.getItem("client_uuid");

    if(!uuid){
        uuid =
            typeof crypto !== "undefined" &&
            typeof crypto.randomUUID === "function"
                ? crypto.randomUUID()
                : `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        localStorage.setItem("client_uuid", uuid);
    }

    return uuid;
}

export function getSeasonFromPeriod(start, end) {
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
export function addMonthsToYearMonth(yearMonth, monthsToAdd) {
    const [year, month] = yearMonth.split("-").map(Number);
    const date = new Date(year, month - 1 + monthsToAdd, 1);
    const nextYear = date.getFullYear();
    const nextMonth = String(date.getMonth() + 1).padStart(2, "0");
    return `${nextYear}-${nextMonth}`;
}

export function getMonthsBetween(start, end) {
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

export function seasonBadgeStyle(season) {
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

export const actionBadge = (a) => ({
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

export const priorityCls = (p) => ({
    높음: "text-rose-600 font-semibold",
    보통: "text-amber-600 font-semibold",
    낮음: "text-slate-400",
})[p] ?? "";

export const statusBadge = (s) => ({
    완료: "bg-emerald-50 text-emerald-700",
    진행중: "bg-blue-50 text-blue-700",
    대기: "bg-slate-100 text-slate-500",
})[s] ?? "";

export function getSeasonStyle(season) {
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

export function getDiagnosisType(row) {
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
export function getRecommendedAction(row) {
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
