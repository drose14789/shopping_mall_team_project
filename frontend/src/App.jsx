import React, { useState } from 'react';

// 공통 부품 및 네비게이션
import { Sidebar } from './components/common/Sidebar';
import { Topbar } from './components/common/Sidebar';

// 화면(Page) 컴포넌트들
import MainScreen from './pages/MainScreen';
import UploadScreen from './pages/UploadScreen';
import ResultsScreen from './pages/ResultsScreen';
import DetailScreen from './pages/DetailScreen';
import HistoryScreen from './pages/HistoryScreen';
import TodayScreen from './pages/TodayScreen';
import DiagScreen from './pages/DiagScreen';
import ChatScreen from './pages/ChatScreen';
import BasisScreen from './pages/BasisScreen';

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
        {screen === "main" ? (<MainScreen setScreen={setScreen}/>) : screen === "upload" ? (<UploadScreen setScreen={setScreen}/>) : screen === "results" ? (<ResultsScreen setScreen={setScreen}/>) : screen === "detail" ? (<DetailScreen setScreen={setScreen}/>) : screen === "history" ? (<HistoryScreen setScreen={setScreen}/>) : screen === "today" ? (<TodayScreen setScreen={setScreen}/>) : screen === "diag" ? (<DiagScreen setScreen={setScreen}/>) : screen === "chat" ? (<ChatScreen setScreen={setScreen}/>) : screen === "basis" ? (<BasisScreen setScreen={setScreen}/>) : null}
      </div>
    </div>);
}