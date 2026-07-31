import { getDiagnosisType, getRecommendedAction } from './helpers';

export function getDetailData(row) {
    const diagnosisType = getDiagnosisType(row);
    const recommendedAction = getRecommendedAction(row);
    const isExpand = row.action === "예산 확대";
    const isMaintain = row.action === "예산 유지";
    const isImprove = row.action === "개선 후 재집행";
    const isReduce = row.action === "광고 축소";
    const score = isExpand
        ? 84
        : isMaintain
            ? 65
            : isImprove
                ? 58
                : isReduce
                    ? 38
                    : 52.6;
    const penalty = isExpand
        ? 0
        : isMaintain
            ? -5
            : isImprove
                ? -12
                : isReduce
                    ? -25
                    : -25;
    return {
        diagnosisType,
        recommendedAction,
        score,
        penalty,
        recommendedAdBudget: isExpand
            ? "42,700원"
            : isMaintain
                ? "25,000원"
                : isImprove
                    ? "18,500원"
                    : "10,200원",
        actionSummary: isExpand
            ? "성과 지표가 안정적이므로 광고 예산을 소폭 확대해 테스트할 수 있습니다."
            : isMaintain
                ? "성과가 안정적인 편이므로 현재 예산을 유지하며 반품과 전환 흐름을 관찰합니다."
                : isImprove
                    ? "상세페이지와 구매 전환 요소를 개선한 뒤 광고 재집행을 검토합니다."
                    : "광고 효율이 낮아 광고비 확대는 보류하고, 소재와 전환 구조를 먼저 개선합니다.",
        scoreBars: [
            {
                label: "클릭률 점수",
                score: isExpand ? 89 : isMaintain ? 62 : isImprove ? 74 : 34,
            },
            {
                label: "찜 전환율 점수",
                score: isExpand ? 82 : isMaintain ? 68 : isImprove ? 59 : 41,
            },
            {
                label: "장바구니 전환율 점수",
                score: isExpand ? 85 : isMaintain ? 64 : isImprove ? 42 : 28,
            },
            {
                label: "구매전환율 점수",
                score: isExpand ? 88 : isMaintain ? 61 : isImprove ? 39 : 22,
            },
            {
                label: "반품 안정성 점수",
                score: isExpand ? 91 : isMaintain ? 57 : isImprove ? 63 : 40,
            },
            {
                label: "ROAS 점수",
                score: isExpand ? 86 : isMaintain ? 72 : isImprove ? 48 : 12,
            },
        ],
        adEfficiencyScore: isExpand
            ? 86
            : isMaintain
                ? 67
                : isImprove
                    ? 49
                    : 23,
        basicRawData: [
            { label: "상품ID", value: "125448201" },
            { label: "상품명", value: row.name },
            { label: "카테고리", value: row.cat },
            { label: "판매 사이트", value: "에이블리" },
        ],
        performanceRawData: [
            {
                label: "노출수",
                value: isExpand
                    ? "45,678"
                    : isMaintain
                        ? "31,420"
                        : isImprove
                            ? "28,500"
                            : "15,600",
            },
            {
                label: "클릭수",
                value: isExpand
                    ? "2,501"
                    : isMaintain
                        ? "879"
                        : isImprove
                            ? "1,560"
                            : "187",
            },
            {
                label: "광고비",
                value: isExpand
                    ? "12,000원"
                    : isMaintain
                        ? "8,500원"
                        : isImprove
                            ? "7,100원"
                            : "6,800원",
            },
            {
                label: "주문금액",
                value: isExpand
                    ? "45,000원"
                    : isMaintain
                        ? "28,000원"
                        : isImprove
                            ? "23,000원"
                            : "5,400원",
            },
            {
                label: "상품금액",
                value: isExpand
                    ? "39,000원"
                    : isMaintain
                        ? "28,000원"
                        : isImprove
                            ? "23,000원"
                            : "10,200원",
            },
            {
                label: "상품 상세 방문수",
                value: isExpand
                    ? "1,841"
                    : isMaintain
                        ? "796"
                        : isImprove
                            ? "631"
                            : "162",
            },
            {
                label: "장바구니 유저수",
                value: isExpand
                    ? "171명"
                    : isMaintain
                        ? "54명"
                        : isImprove
                            ? "52명"
                            : "5명",
            },
            {
                label: "찜 유저수",
                value: isExpand
                    ? "134명"
                    : isMaintain
                        ? "120명"
                        : isImprove
                            ? "60명"
                            : "25명",
            },
            {
                label: "상품주문수",
                value: isExpand
                    ? "38건"
                    : isMaintain
                        ? "22건"
                        : isImprove
                            ? "19건"
                            : "3건",
            },
            {
                label: "반품건수",
                value: isExpand
                    ? "2건"
                    : isMaintain
                        ? "1건"
                        : isImprove
                            ? "3건"
                            : "3건",
            },
        ],
        coachingFeedback: isExpand
            ? [
                {
                    label: "상품클릭률",
                    status: "veryGood",
                    text: "상위 10% 그룹 평균 대비 166.9% 수준으로 매우 우수합니다.",
                },
                {
                    label: "찜전환율",
                    status: "good",
                    text: "상위 10% 그룹 평균의 72.8% 수준으로 양호합니다.",
                },
                {
                    label: "장바구니전환율",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 36.1% 수준으로 개선이 필요합니다.",
                },
                {
                    label: "구매전환율",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 22.0% 수준으로 개선이 필요합니다.",
                },
                {
                    label: "반품안정성",
                    status: "veryGood",
                    text: "상위 10% 그룹 평균 대비 105.6% 수준으로 매우 우수합니다.",
                },
                {
                    label: "ROAS",
                    status: "weak",
                    text: "상위 10% 그룹 평균의 0.0% 수준으로 개선이 필요합니다.",
                },
            ]
            : isMaintain
                ? [
                    {
                        label: "상품클릭률",
                        status: "good",
                        text: "같은 카테고리 평균 수준으로 안정적인 클릭 반응을 보입니다.",
                    },
                    {
                        label: "찜전환율",
                        status: "good",
                        text: "관심 유입은 안정적이며 급격한 조정은 필요하지 않습니다.",
                    },
                    {
                        label: "장바구니전환율",
                        status: "good",
                        text: "장바구니 전환 흐름이 평균권으로 유지되고 있습니다.",
                    },
                    {
                        label: "구매전환율",
                        status: "normal",
                        text: "구매전환율은 평균권이나 추가 개선 여지가 있습니다.",
                    },
                    {
                        label: "반품안정성",
                        status: "normal",
                        text: "반품 안정성은 보통 수준으로 지속 관찰이 필요합니다.",
                    },
                    {
                        label: "ROAS",
                        status: "good",
                        text: "ROAS가 안정적으로 유지되어 현재 예산 유지가 적절합니다.",
                    },
                ]
                : isImprove
                    ? [
                        {
                            label: "상품클릭률",
                            status: "good",
                            text: "클릭 반응은 양호하지만 이후 전환 흐름이 약합니다.",
                        },
                        {
                            label: "찜전환율",
                            status: "normal",
                            text: "찜 전환은 보통 수준으로 상품 관심은 일부 확인됩니다.",
                        },
                        {
                            label: "장바구니전환율",
                            status: "weak",
                            text: "상세 방문 대비 장바구니 전환이 낮아 상세페이지 설득력 개선이 필요합니다.",
                        },
                        {
                            label: "구매전환율",
                            status: "weak",
                            text: "구매전환율이 낮아 가격, 혜택, 상세 정보 보강이 필요합니다.",
                        },
                        {
                            label: "반품안정성",
                            status: "normal",
                            text: "반품 안정성은 보통 수준이나 개선 후 함께 확인해야 합니다.",
                        },
                        {
                            label: "ROAS",
                            status: "weak",
                            text: "광고비 대비 주문금액이 낮아 ROAS 개선이 필요합니다.",
                        },
                    ]
                    : [
                        {
                            label: "상품클릭률",
                            status: "weak",
                            text: "클릭률이 낮아 광고 소재와 대표 이미지 개선이 필요합니다.",
                        },
                        {
                            label: "찜전환율",
                            status: "weak",
                            text: "상품 관심 유입이 낮아 상품명과 썸네일 점검이 필요합니다.",
                        },
                        {
                            label: "장바구니전환율",
                            status: "weak",
                            text: "상세 방문 이후 장바구니 전환이 약합니다.",
                        },
                        {
                            label: "구매전환율",
                            status: "weak",
                            text: "구매전환율이 낮아 광고 확대보다 전환 개선이 우선입니다.",
                        },
                        {
                            label: "반품안정성",
                            status: "normal",
                            text: "주문 수가 적어 반품 안정성은 보수적으로 판단합니다.",
                        },
                        {
                            label: "ROAS",
                            status: "weak",
                            text: "ROAS가 기준 미달로 광고비 회수 효율이 낮습니다.",
                        },
                    ],
        funnelStages: [
            {
                label: "노출",
                value: isExpand ? "45,678" : isMaintain ? "31,420" : isImprove ? "28,500" : "15,600",
                rate: "",
                bottleneck: false,
            },
            {
                label: "클릭",
                value: isExpand ? "2,501" : isMaintain ? "879" : isImprove ? "1,560" : "187",
                rate: isExpand ? "CTR 5.48%" : isMaintain ? "CTR 2.80%" : isImprove ? "CTR 5.47%" : "CTR 1.20%",
                bottleneck: isReduce,
            },
            {
                label: "상세 방문",
                value: isExpand ? "1,841" : isMaintain ? "796" : isImprove ? "631" : "162",
                rate: isExpand ? "73.6%" : isMaintain ? "90.6%" : isImprove ? "40.4%" : "86.6%",
                bottleneck: isImprove,
            },
            {
                label: "장바구니",
                value: isExpand ? "171" : isMaintain ? "54" : isImprove ? "52" : "5",
                rate: isExpand ? "9.3%" : isMaintain ? "6.8%" : isImprove ? "8.2%" : "3.1%",
                bottleneck: isImprove,
            },
            {
                label: "구매",
                value: isExpand ? "38" : isMaintain ? "22" : isImprove ? "19" : "3",
                rate: isExpand ? "2.1%" : isMaintain ? "2.8%" : isImprove ? "3.0%" : "1.9%",
                bottleneck: isImprove || isReduce,
            },
        ],
        bottleneckMessage: isExpand
            ? "현재 주요 병목은 크지 않으며, 노출부터 구매까지 전환 흐름이 비교적 안정적입니다."
            : isMaintain
                ? "전반적인 퍼널 흐름은 안정적이며, 특정 단계의 급격한 이탈은 크지 않습니다."
                : isImprove
                    ? "상세 방문 이후 장바구니와 구매 전환 구간에서 병목이 감지됩니다."
                    : "노출 이후 클릭과 구매 전환으로 이어지는 흐름이 약해 퍼널 전반의 개선이 필요합니다.",
        bottleneckCauses: isExpand
            ? [
                "클릭률이 상위 그룹 대비 높아 광고 소재 반응이 우수합니다.",
                "반품 안정성이 높아 광고 확대 시 리스크가 낮은 편입니다.",
                "장바구니·구매 전환 구간은 개선 여지가 있으므로 확대 후 전환율 변화를 함께 확인해야 합니다.",
            ]
            : isMaintain
                ? [
                    "전반적인 퍼널 흐름은 안정적이지만 일부 전환 지표는 추가 개선 여지가 있습니다.",
                    "현재 예산은 유지하되 찜, 장바구니, 구매 전환 흐름을 주기적으로 확인해야 합니다.",
                    "시즌 변화나 반품률 상승이 발생하면 광고 운영 방향을 재검토해야 합니다.",
                ]
                : isImprove
                    ? [
                        "상세페이지 방문 이후 장바구니와 구매 전환으로 이어지는 비율이 낮습니다.",
                        "상품 상세페이지의 착용컷, 소재 설명, 사이즈 정보가 부족할 가능성이 있습니다.",
                        "구매 전 혜택, 배송, 교환·반품 안내가 충분히 설득되지 않았을 가능성이 있습니다.",
                    ]
                    : [
                        "노출 이후 클릭으로 이어지는 반응이 낮아 광고 소재 매력이 부족할 가능성이 있습니다.",
                        "클릭 이후 상세페이지와 구매 전환으로 이어지는 흐름이 약합니다.",
                        "광고비 대비 주문금액이 낮아 현재 광고 효율을 먼저 점검해야 합니다.",
                    ],
        actionItems: isExpand
            ? [
                {
                    tag: "예산 테스트",
                    text: "현재 예산을 한 번에 크게 늘리기보다, 3~5일 동안 소폭 증액해 클릭률과 구매전환율이 유지되는지 확인합니다.",
                },
                {
                    tag: "전환 보강",
                    text: "광고를 늘리기 전에 상세 상단의 구매 혜택, 배송 안내, 사이즈 불안 요소를 먼저 정리해 구매 전환 손실을 줄입니다.",
                },
                {
                    tag: "중단 기준",
                    text: "증액 후 ROAS가 떨어지거나 반품률이 상승하면 확대를 멈추고 상세 정보와 기대 불일치 요소를 먼저 점검합니다.",
                },
            ]
            : isMaintain
                ? [
                    {
                        tag: "유지 운영",
                        text: "현재 예산은 유지하되, 클릭률과 구매전환율이 함께 떨어지는지 주기적으로 확인합니다.",
                    },
                    {
                        tag: "소폭 개선",
                        text: "성과를 크게 바꾸기보다 상세 상단 문구, 대표 이미지, 혜택 안내처럼 전환에 가까운 요소부터 가볍게 보완합니다.",
                    },
                    {
                        tag: "재검토 기준",
                        text: "반품률이 오르거나 ROAS가 낮아지면 유지 전략을 멈추고 개선형 상품으로 재분류해 점검합니다.",
                    },
                ]
                : isImprove
                    ? [
                        {
                            tag: "전환 점검",
                            text: "클릭 이후 이탈이 발생하는 구간을 기준으로 상세페이지 상단, 착용컷, 소재·사이즈 설명을 먼저 보강합니다.",
                        },
                        {
                            tag: "구매 설득",
                            text: "장바구니 이후 구매가 약하다면 쿠폰, 배송비, 교환·반품 안내처럼 결제 직전 불안 요소를 정리합니다.",
                        },
                        {
                            tag: "재집행",
                            text: "상세페이지 수정 후 바로 큰 예산을 투입하지 말고, 소액 광고로 전환율 변화부터 다시 확인합니다.",
                        },
                    ]
                    : [
                        {
                            tag: "확대 보류",
                            text: "현재는 광고를 더 늘리기보다 예산 소진을 줄이고, 클릭률과 구매전환율이 낮은 원인을 먼저 확인합니다.",
                        },
                        {
                            tag: "소재 점검",
                            text: "노출 대비 클릭 반응이 낮다면 대표 이미지, 첫 문구, 상품명 키워드가 충분히 매력적인지 먼저 수정합니다.",
                        },
                        {
                            tag: "재판단",
                            text: "소재와 상세페이지를 수정한 뒤에도 클릭률과 ROAS가 회복되지 않으면 광고 축소 또는 보류 상태를 유지합니다.",
                        },
                    ],
    };
}
