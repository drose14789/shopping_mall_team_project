import React, { useState, useRef } from "react";
import {UploadIllustration} from '../components/common/Icons'; 
import * as AllData from '../constants/data';



export default function UploadScreen({ setScreen, }) {
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
              {AllData.REQUIRED_COLS.map((c) => (<span key={c} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-lg font-medium">
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
