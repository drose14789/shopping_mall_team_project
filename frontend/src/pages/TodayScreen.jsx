import { API_BASE_URL } from "../constants/api";
import { useState, useEffect } from "react";
import { TODAY_ACTION_GROUPS, TODAY_DIAGNOSIS_TYPES } from "../constants/data"; 
import { actionBadge, getClientUuid } from "../utils/helpers"; 
import { ProductDetailModal } from "../components/InspectionModal";

export default function TodayScreen({ setScreen }) {
    const [data, setData] = useState([]);
    const [activeGroup, setActiveGroup] = useState("예산 확대");
    const [selectedDiagnosis, setSelectedDiagnosis] = useState("전체 진단 유형");
    const [showProductModal, setShowProductModal] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const clientUuid = getClientUuid();
    const hasData = data.length > 0;

    useEffect(() => {

    fetch(`${API_BASE_URL}/today/recommend/${clientUuid}`)
        .then((res)=>res.json())
        .then((result)=>{

            const merged = [
                ...(result.expand || []).map((item, index)=>({
                    ...item,
                    rank:index + 1,
                    actionGroup:"예산 확대",
                    action:"예산 확대",
                    name:item.product_name,
                    cat:item.category,
                    diagnosisType:item.product_type
                })),

                ...(result.improve || []).map((item, index)=>({
                    ...item,
                    rank:index + 1,
                    actionGroup:"개선 필요",
                    action:"개선 후 재집행",
                    name:item.product_name,
                    cat:item.category,
                    diagnosisType:item.product_type
                })),

                ...(result.reduce || []).map((item, index)=>({
                    ...item,
                    rank:index + 1,
                    actionGroup:"광고 축소",
                    action:"광고 축소",
                    name:item.product_name,
                    cat:item.category,
                    diagnosisType:item.product_type
                })),

                ...(result.returnRisk || []).map((item, index)=>({
                    ...item,
                    rank:index + 1,
                    actionGroup:"반품 리스크",
                    action:"반품 리스크",
                    name:item.product_name,
                    cat:item.category,
                    diagnosisType:item.product_type
                }))
            ];

            setData(merged);

        })
        .catch((err)=>{
            console.error(
                "오늘의 추천 데이터 조회 실패",
                err
            );
        });

},[clientUuid]);

    

    const firstAction = data.find(
    item => item.actionGroup === "예산 확대"
);
    const topActions = [
    data.find(item => item.actionGroup === "개선 필요"),
    data.find(item => item.actionGroup === "광고 축소"),
    data.find(item => item.actionGroup === "반품 리스크"),
].filter(Boolean);

    const filtered = data.filter((row) => {
    const groupMatched =
        row.actionGroup === activeGroup;

    const diagnosisMatched =
          selectedDiagnosis === "전체 진단 유형" ||
          row.diagnosisType === selectedDiagnosis;

      return groupMatched && diagnosisMatched;
  });

    const actionMeta = (action) => {
    if (action === "예산 확대") {
        return {
            label: "예산 확대 추천",
            icon: "📈",
            bg: "bg-blue-50",
            border: "border-blue-200",
            text: "text-blue-700",
            todo: "성과가 좋은 상품의 광고 노출을 확대하고 예산 증가 후 ROAS와 주문 변화를 확인하세요.",
        };
    }

    if (action === "개선 후 재집행") {
        return {
            label: "개선 후 재집행",
            icon: "🛠️",
            bg: "bg-amber-50",
            border: "border-amber-200",
            text: "text-amber-700",
            todo: "상품 상세페이지와 구매 방해 요소를 개선한 뒤 광고를 다시 집행해 성과 변화를 확인하세요.",
        };
    }

    if (action === "광고 축소") {
        return {
            label: "광고 축소 추천",
            icon: "📉",
            bg: "bg-rose-50",
            border: "border-rose-200",
            text: "text-rose-700",
            todo: "효율이 낮은 광고 상품의 예산을 줄이고 광고비 대비 성과를 재점검하세요.",
        };
    }

    if (action === "반품 리스크") {
        return {
            label: "반품 리스크 주의",
            icon: "⚠️",
            bg: "bg-red-50",
            border: "border-red-200",
            text: "text-red-700",
            todo: "반품 발생 원인을 분석하고 상품 정보와 고객 불만 요소를 개선해 추가 반품을 예방하세요.",
        };
    }
};
  const actionGroupBadge = (group) =>
      ({
          "예산 확대": "bg-blue-50 text-blue-700 border-blue-200",
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
                          {data[0]?.fileName}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1">
                          분석 이력의 가장 최근 파일 기준
                      </p>
                  </div>
              </div>
          </div>

          <div className="grid grid-cols-[minmax(0,1.55fr)_minmax(310px,0.45fr)] gap-4">
            <div
                className={`rounded-2xl border ${firstMeta.border} ${firstMeta.bg} p-6 shadow-sm`}
            >
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center text-xl shadow-sm">
                            {firstMeta.icon}
                        </div>

                        <div>
                            <p className="text-[11px] font-bold text-slate-400">
                                오늘 가장 먼저 할 일
                            </p>
                            <p className={`text-xs font-bold ${firstMeta.text}`}>
                                {firstAction.label}
                            </p>
                            <h3 className="text-xl font-bold text-slate-800">
                                {firstAction.name}
                            </h3>
                        </div>
                    </div>

                       <span className="px-2 py-1 rounded-lg bg-white/80 border border-white text-[11px] font-bold text-slate-500">
                {firstAction.cat}
            </span>
        </div>


        <div className="space-y-3">

            <div>
                <p className="text-[11px] font-bold text-slate-400 mb-1">
                    추천 액션
                </p>

                <div className="flex items-center gap-1.5 flex-wrap">
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
                </div>
            </div>

                      <div>
                <p className="text-[11px] font-bold text-slate-400 mb-1">
                    선정 이유
                </p>

                <p className="text-xs text-slate-600 leading-relaxed">
                    {firstAction.reason}
                </p>
            </div>


            <div className="rounded-xl bg-white/70 border border-white px-3 py-3">
                <p className="text-[11px] font-bold text-slate-400 mb-1">
                    오늘 할 일
                </p>

                <p className="text-xs text-slate-600 leading-relaxed">
                    {firstMeta.todo}
                </p>
            </div>

        </div>

                  <button
                    onClick={() => {
                        setSelectedProduct(firstAction);
                        setShowProductModal(true);
                    }}
                    className="mt-4 w-40 bg-white text-blue-600 border border-blue-100 rounded-xl py-2 text-xs font-bold hover:bg-blue-50 transition flex items-center justify-center gap-1">
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
                          key={`${row.actionGroup}-${row.rank}`}
                          className={`rounded-2xl border ${meta.border} ${meta.bg} p-5 shadow-sm`}
                      >
                          <div className="flex items-start justify-between mb-4">
                              <div className="flex items-center gap-2">
                                  <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-lg shadow-sm">
                                      {meta.icon}
                                  </div>
                                  <div>
                                      <p className="text-[11px] font-bold text-slate-400">
                                          오늘의 추천 확인 상품
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
                              onClick={() => {
                                        setSelectedProduct(row);
                                        setShowProductModal(true);
                                    }}
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
                                  key={`${row.actionGroup}-${row.rank}`}
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
                                        onClick={() => {
                                            setSelectedProduct(row);
                                            setShowProductModal(true);
                                        }}
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
          {showProductModal && selectedProduct && (
            <ProductDetailModal
                product={selectedProduct}
                onClose={() => {
                    setShowProductModal(false);
                    setSelectedProduct(null);
                }}
            />
        )}
      </div>
  );
}