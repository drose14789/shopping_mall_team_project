import React, { useState } from 'react';
import { REQUIRED_COLS, TABLE_DATA } from '../constants/data';
import { seasonBadgeStyle, actionBadge} from '../utils/helpers'; 
import { DashboardIllustration } from '../components/common/Icons'; 
import { InspectionModal } from '../components/InspectionModal'; 

export default function MainScreen({ setScreen, }) {
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






