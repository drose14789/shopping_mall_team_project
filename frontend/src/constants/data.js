
import { HomeIcon, ChartIcon, DiagIcon, ChatIcon, BasisIcon } from '../components/common/Icons';

export const NAV_ITEMS = [
    { id: "main", label: "메인", Icon: HomeIcon },
    { id: "upload", label: "상품 액션 추천", Icon: ChartIcon },
    { id: "diag", label: "판매 전 진단", Icon: DiagIcon },
    { id: "chat", label: "법 규제 챗봇", Icon: ChatIcon },
    { id: "basis", label: "진단 기준", Icon: BasisIcon },
];

export const TABLE_DATA = [
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

export const STATUS_META = {
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

export const MOCK_ISSUES = [
    { row: 12, col: "광고비", raw: "12,000원", cleaned: "12000", status: "clean", note: "원화 기호와 쉼표를 제거해 숫자형 데이터로 변환했습니다.", reflect: "반영 가능" },
    { row: 15, col: "노출수", raw: "45,678", cleaned: "45678", status: "clean", note: "쉼표를 제거해 정수형으로 변환했습니다.", reflect: "반영 가능" },
    { row: 18, col: "클릭수", raw: "1,234", cleaned: "1234", status: "clean", note: "쉼표를 제거해 정수형으로 변환했습니다.", reflect: "반영 가능" },
    { row: 23, col: "주문금액", raw: "₩45,000", cleaned: "45000", status: "clean", note: "통화 기호와 쉼표를 제거해 숫자형 데이터로 변환했습니다.", reflect: "반영 가능" },
    { row: 25, col: "ROAS", raw: "3.5%", cleaned: "참고용", status: "optional", note: "원본 수치로 ROAS를 재계산하므로 참고용으로만 활용합니다.", reflect: "참고용" },
    { row: 41, col: "반품건수", raw: "없음", status: "warn", note: "반품이 없으면 0, 데이터가 없으면 빈 값으로 입력해주세요.", reason: "텍스트 값 '없음'은 숫자형 필드에 사용할 수 없습니다. 원본 파일을 확인 후 값을 수정해주세요.", reflect: "확인 후 반영 가능" },
    { row: 55, col: "노출수", raw: "28.500", status: "warn", note: "소수점인지 천 단위 구분자인지 의미 판단이 필요합니다. 원본 파일 확인 후 값을 수정해주세요.", reason: "소수점인지 천 단위 구분자인지 의미 판단이 필요합니다.", reflect: "확인 후 반영 가능" },
    { row: 56, col: "반품건수", raw: "3건", cleaned: "3", status: "clean", note: "'건' 단위를 제거해 숫자형으로 변환했습니다.", reflect: "반영 가능" },
];

export const TABLE_ROWS = [
    { r: 12, cells: ["링이 앵글 프릴 블라우스", "블라우스", "45678", "1,234", "12,000원", "₩45,000", "38", "2", "3.5%"] },
    { r: 15, cells: ["데일리 셔링 리본 원피스", "원피스", "45,678", "987", "8500원", "₩28,000", "22", "1", "3.3%"] },
    { r: 18, cells: ["오버핏 린넨 롱 원피스", "원피스", "21000", "1,234", "5000원", "₩18,000", "14", "0", "3.6%"] },
    { r: 23, cells: ["베이직 크롭 티셔츠", "티셔츠", "18400", "520", "4200원", "₩45,000", "11", "0", "2.9%"] },
    { r: 25, cells: ["플로럴 시폰 원피스", "원피스", "31200", "890", "7800원", "₩26,000", "20", "2", "3.5%"] },
    { r: 41, cells: ["바쉐 베이직 티셔츠", "티셔츠", "9800", "450", "3200원", "₩11,000", "9", "없음", "3.4%"] },
    { r: 55, cells: ["플리츠 미디 스커트", "스커트", "28.500", "820", "7100원", "₩23,000", "19", "3", "2.8%"] },
    { r: 56, cells: ["크롭 린넨 재킷", "재킷", "15200", "411", "6800원", "₩22,000", "16", "3건", "3.2%"] },
];

export const TABLE_COLS = ["상품명", "카테고리", "노출수", "클릭수", "광고과금액", "주문금액", "상품주문수", "반품건수", "ROAS"];
export const REFERENCE_ONLY_COLS = ["ROAS"];
export const REQUIRED_COLS = ["상품ID", "상품명", "노출수", "클릭수", "광고과금액", "주문금액", "상품금액", "상품 상세 방문수", "장바구니 유저수", "찜 유저수", "상품주문수", "반품건수", "판매 사이트"];
export const SEASON_BY_MONTH = {
    1: "겨울", 2: "겨울", 3: "겨울",
    4: "봄", 5: "봄", 6: "봄",
    7: "여름", 8: "여름", 9: "여름",
    10: "가을", 11: "가을", 12: "가을",
};
export const recommendationMap = {
        "핵심 확대형": "광고 예산 확대를 검토하세요. 단, 3~5일간 소폭 증액하며 ROAS와 반품율 변화를 함께 확인합니다.",
        "반품 리스크 확대 보류형": "성과는 좋지만 반품 리스크가 있으므로 사이즈, 소재, 색감, 배송, 상세 설명을 보강한 뒤 확대를 검토하세요.",
        "구매 직전 이탈형": "장바구니까지는 유입되지만 구매 전환이 부족합니다. 가격, 쿠폰, 무료배송, 구매 혜택, 결제 유도 문구를 점검하세요.",
        "구매·반품 복합 리스크형": "구매전환과 반품 안정성이 모두 약합니다. 혜택 보강과 함께 상품 정보, 사이즈, 소재 설명을 우선 개선하세요.",
        "전환 효율형": "구매전환은 좋지만 장바구니 진입이 약합니다. 상세 상단 구성과 핵심 혜택을 보강한 뒤 예산 유지 또는 소액 확대를 검토하세요.",
        "반품 주의 유지형": "구매는 발생하지만 반품 리스크가 있습니다. 광고 확대는 보류하고 반품 원인 점검 후 예산 유지를 권장합니다.",
        "상세페이지 개선형": "클릭은 발생하지만 상세페이지 이후 전환이 약합니다. 착용컷, 소재감, 사이즈, 혜택 정보 보강이 필요합니다.",
        "상세·반품 복합 개선형": "관심은 있으나 전환과 반품 안정성이 모두 약합니다. 상세페이지 보강과 반품 개선을 함께 진행하세요.",
        "숨은 효율형": "유입은 적지만 들어온 고객의 전환 효율은 좋습니다. 썸네일, 상품명, 대표 이미지 개선 후 소액 확대 테스트를 권장합니다.",
        "소재 개선+반품 주의형": "전환은 좋지만 유입과 반품 안정성이 약합니다. 이미지와 상품 정보, 사이즈, 소재 설명을 함께 보강하세요.",        
        "소재·구매 전환 개선형": "장바구니 관심은 있으나 구매 전환이 낮습니다. 썸네일 개선과 함께 가격, 쿠폰, 구매 혜택을 점검하세요.",
        "소재·구매·반품 복합 리스크형": "유입, 구매전환, 반품 안정성 모두 점검이 필요합니다. 광고확대는 보류하고 상품 정보와 구매 혜택을 전반적으로 개선하세요.",
        "소수 전환형": "유입과 관심은 낮지만 구매한 고객의 전환은 양호합니다. 데이터를 추가 확보한 뒤 소액 테스트를 진행하세요.",
        "소수 전환+반품 리스크형": "일부 구매는 발생하지만 반품 리스크가 있습니다. 확대는 보류하고 반품 원인과 상품 정보를 먼저 점검하세요.",
        "광고 반응 부족형": "광고 반응과 전환흐름이 모두 약합니다. 소재, 상품명, 대표 이미지, 상세페이지를 개선한 뒤 재집행하세요.",
        "광고 축소형": "전반적인 성과와 안정성이 모두 낮습니다. 광고비를 축소하거나 보류하고 상품경쟁력 개선을 우선하세요.",
        
        "default": "데이터를 바탕으로 상세 페이지와 상품 정보를 점검해 주세요."
};
export const SEASON_EMOJI = {봄: "🌸", 여름: "☀️", 가을: "🍂", 겨울: "❄️"};

export const PAGE_SIZE = 20;
export const RESULTS_PAGE_SIZE = 10;

export const DIAG_CATEGORIES = [
    "블라우스",
    "원피스",
    "티셔츠",
    "스커트",
    "팬츠",
    "니트",
    "아우터",
];
export const DIAG_SEASONS = ["봄", "여름", "가을", "겨울"];

export const MOCK_DIAG_RESULT = {
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

export const RISK_META = {
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
export const REFERENCE_DOCS = [
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
export const FAQ_QUESTIONS = [
    "이 광고 문구 과장광고로 문제될 수 있어?",
    "의류 상세페이지에 꼭 적어야 하는 정보가 뭐야?",
    "반품 불가라고 적어도 돼?",
    "리뷰 데이터를 분석해도 개인정보 문제가 없을까?",
    "배송 지연 시 어떤 안내가 필요해?",
    "지그재그에서 제한되는 표현이 있을까?",
    '"무조건 날씬해 보임" 같은 문구를 써도 될까?',
    "고객 리뷰를 광고 문구에 활용해도 될까?",
];

export const FAQ_API_QUESTIONS = {
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
export const CHECKABLE_ITEMS = [
    "광고 문구 리스크",
    "상품 상세페이지 필수 정보",
    "반품·환불 안내 기준",
    "개인정보 수집·활용 주의사항",
    "배송 지연 안내 기준",
    "쇼핑몰 약관 참고",
    "지그재그 상품 등록 및 표현 제한",
    "플랫폼 운영 규정",
];

export const INIT_MESSAGES = [
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
        text: '"무조건 날씬해 보이는" 같은 단정적인 표현은 표시·광고법상 부당한 표시·광고(거짓·과장 광고)에 해당할 소지가 높습니다.',
        sources: ["표시·광고의 공정화에 관한 법률"],
    },
];

export const CHAT_API_BASE_URL = (
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
export const CHAT_API_URL = `${CHAT_API_BASE_URL}/chat`;
export const CHAT_STREAM_API_URL = `${CHAT_API_BASE_URL}/chat/stream`;
export const CHAT_STORAGE_KEY = "online-shopping-legal-chat-messages";
export const MAX_HISTORY_MESSAGES = 10;
export const MAX_HISTORY_CONTENT_LENGTH = 2000;
export const MAX_STORED_MESSAGES = 30;
export const MAX_STORED_SOURCE_CONTENT_LENGTH = 2500;

export const CHAT_INTRO_MESSAGE = {
    id: "chat-intro",
    role: "assistant",
    content: "안녕하세요! 쇼핑몰 법 규제 챗봇입니다.\n반품·환불, 판매자 정보, 개인정보 등 온라인 쇼핑 관련 질문을 입력해주세요.",
    sources: [],
    isIntro: true,
};

export const HISTORY_DATA = [
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

export const HISTORY_PAGE_SIZE = 5;

export const TODAY_DATA = [
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

export const TODAY_ACTION_GROUPS = [
  "전체",
  "예산 확대",
  "예산 유지",
  "개선 필요",
  "광고 축소",
  "반품 리스크",
];

export const TODAY_DIAGNOSIS_TYPES = [
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

export const RESULTS_DATA = [
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