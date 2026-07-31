import { 
    MAX_STORED_MESSAGES, 
    MAX_STORED_SOURCE_CONTENT_LENGTH, 
    CHAT_STORAGE_KEY, 
    CHAT_INTRO_MESSAGE, 
    MAX_HISTORY_MESSAGES, 
    MAX_HISTORY_CONTENT_LENGTH 
} from '../constants/data';

export function getMockResponse(q) {
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

export function truncateChatText(value, maxLength) {
    if (typeof value !== "string") {
        return "";
    }

    return value.slice(0, maxLength);
}

export function prepareChatMessagesForStorage(messages) {
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

export function loadStoredChatMessages() {
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

export function createChatMessage(role, content, sources = []) {
    return {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        role,
        content,
        sources,
    };
}

export function buildChatRequestHistory(messages) {
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

export function getChatSourceScore(source) {
    const score = source.rerank_score ??
        source.score ??
        source.dense_score ??
        source.similarity_score;

    return typeof score === "number" ? score.toFixed(4) : null;
}

export function getChatSourceHeading(source) {
    if (Array.isArray(source.heading_path)) {
        return source.heading_path.join(" > ");
    }

    return source.heading_path ||
        source.heading ||
        source.title ||
        "제목 없음";
}

export function getChatSourceContent(source) {
    return source.parent_content ||
        source.content ||
        source.text ||
        source.excerpt ||
        source.child_content ||
        "";
}