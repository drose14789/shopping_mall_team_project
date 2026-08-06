import json
import math
import os
import re
from typing import Any

import requests
from fastapi import APIRouter, Body

router = APIRouter(prefix="/analysis", tags=["Analysis"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = (
    os.getenv("OLLAMA_GENERAL_MODEL")
    or os.getenv("OLLAMA_MODEL")
    or "gemma3:1b"
)
OLLAMA_TIMEOUT_SECONDS = int(
    os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")
)


def _safe_number(value: Any, default: float = 0.0) -> float:
    """None, 문자열, NaN 값을 안전한 숫자로 변환합니다."""
    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number
    except (TypeError, ValueError):
        return default


def _round_number(value: Any, digits: int = 1) -> float:
    return round(_safe_number(value), digits)


def _clean_product(product: dict[str, Any]) -> dict[str, Any]:
    """
    LLM에 전달할 상품 분석 데이터만 정리합니다.
    상품별 분석값이 다르기 때문에 생성 문장도 상품별로 달라집니다.
    """
    return {
        "result_id": product.get("id"),
        "product_id": product.get("product_id"),
        "product_name": product.get("product_name"),
        "category": product.get("category"),
        "quarter": product.get("quarter"),
        "diagnosis_type": product.get("product_type"),
        "total_score": _round_number(product.get("total_score"), 2),

        "raw_metrics": {
            "exposure_count": int(
                _safe_number(product.get("exposure_count"))
            ),
            "click_count": int(
                _safe_number(product.get("click_count"))
            ),
            "visit_count": int(
                _safe_number(product.get("visit_count"))
            ),
            "wish_user_count": int(
                _safe_number(product.get("wish_user_count"))
            ),
            "cart_user_count": int(
                _safe_number(product.get("cart_user_count"))
            ),
            "order_count": int(
                _safe_number(product.get("order_count"))
            ),
            "return_count": int(
                _safe_number(product.get("return_count"))
            ),
            "ad_spend": _round_number(product.get("ad_spend"), 0),
            "order_amount": _round_number(
                product.get("order_amount"), 0
            ),
            "unit_price": _round_number(
                product.get("unit_price"), 0
            ),
        },

        "calculated_metrics": {
            "click_rate": _round_number(
                product.get("calc_click_rate")
            ),
            "wish_conversion_rate": _round_number(
                product.get("calc_wish_conv")
            ),
            "cart_conversion_rate": _round_number(
                product.get("calc_cart_conv")
            ),
            "purchase_conversion_rate": _round_number(
                product.get("calc_conv_rate")
            ),
            "return_stability": _round_number(
                product.get("calc_return_stability")
            ),
            "roas": _round_number(product.get("calc_roas")),
        },

        "metric_scores": {
            "click_rate_score": _round_number(
                product.get("score_click_rate")
            ),
            "wish_conversion_score": _round_number(
                product.get("score_wish_conv")
            ),
            "cart_conversion_score": _round_number(
                product.get("score_cart_conv")
            ),
            "purchase_conversion_score": _round_number(
                product.get("score_conv_rate")
            ),
            "return_stability_score": _round_number(
                product.get("score_return_stability")
            ),
            "roas_score": _round_number(
                product.get("score_roas")
            ),
        },

        "recommended_ad_spend": _round_number(
            product.get("recommended_ad_spend"), 0
        ),
    }


def _extract_json(content: str) -> dict[str, Any]:
    """Ollama 응답에서 JSON 객체를 안전하게 추출합니다."""
    content = content.strip()

    try:
        parsed = json.loads(content)

        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("LLM 응답에서 JSON 객체를 찾지 못했습니다.")

    parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("LLM 응답이 JSON 객체가 아닙니다.")

    return parsed


def _validate_result(result: dict[str, Any]) -> dict[str, Any]:
    diagnosis = result.get("diagnosis_summary")
    actions = result.get("recommended_actions")

    if not isinstance(diagnosis, list) or len(diagnosis) < 2:
        raise ValueError("진단 근거가 2개 이상 생성되지 않았습니다.")

    if not isinstance(actions, list) or len(actions) < 2:
        raise ValueError("추천 액션이 2개 이상 생성되지 않았습니다.")

    cleaned_diagnosis: list[str] = []

    for item in diagnosis[:2]:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            text = f"{title}: {content}" if title else content
        else:
            text = ""

        if not text:
            raise ValueError("비어 있는 진단 근거가 있습니다.")

        cleaned_diagnosis.append(text)

    cleaned_actions: list[dict[str, str]] = []

    for item in actions[:2]:
        if not isinstance(item, dict):
            raise ValueError("추천 액션 형식이 올바르지 않습니다.")

        tag = str(
            item.get("tag")
            or item.get("label")
            or "운영 점검"
        ).strip()

        text = str(
            item.get("text")
            or item.get("content")
            or ""
        ).strip()

        if not text:
            raise ValueError("비어 있는 추천 액션이 있습니다.")

        cleaned_actions.append({
            "tag": tag[:20],
            "text": text,
        })

    return {
        "diagnosis_summary": cleaned_diagnosis,
        "recommended_actions": cleaned_actions,
        "generated_by": "llm",
    }


def _metric_rows(
    product: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "label": "상품클릭률",
            "score": _safe_number(
                product.get("score_click_rate")
            ),
            "value": _safe_number(
                product.get("calc_click_rate")
            ),
            "unit": "%",
        },
        {
            "label": "찜전환율",
            "score": _safe_number(
                product.get("score_wish_conv")
            ),
            "value": _safe_number(
                product.get("calc_wish_conv")
            ),
            "unit": "%",
        },
        {
            "label": "장바구니전환율",
            "score": _safe_number(
                product.get("score_cart_conv")
            ),
            "value": _safe_number(
                product.get("calc_cart_conv")
            ),
            "unit": "%",
        },
        {
            "label": "구매전환율",
            "score": _safe_number(
                product.get("score_conv_rate")
            ),
            "value": _safe_number(
                product.get("calc_conv_rate")
            ),
            "unit": "%",
        },
        {
            "label": "반품 안정성",
            "score": _safe_number(
                product.get("score_return_stability")
            ),
            "value": _safe_number(
                product.get("calc_return_stability")
            ),
            "unit": "%",
        },
        {
            "label": "ROAS",
            "score": _safe_number(
                product.get("score_roas")
            ),
            "value": _safe_number(product.get("calc_roas")),
            "unit": "%",
        },
    ]


def _action_for_weak_metric(
    metric: dict[str, Any],
) -> dict[str, str]:
    label = metric["label"]

    actions = {
        "상품클릭률": {
            "tag": "소재 점검",
            "text": (
                "대표 이미지, 상품명, 광고 문구를 나누어 테스트하고 "
                "상품클릭률 변화를 확인합니다."
            ),
        },
        "찜전환율": {
            "tag": "관심 유도",
            "text": (
                "상품의 핵심 장점과 혜택 정보를 상세페이지 상단에 "
                "배치해 관심 저장 행동을 강화합니다."
            ),
        },
        "장바구니전환율": {
            "tag": "구매 설득",
            "text": (
                "가격 혜택, 배송 조건, 옵션 정보를 명확하게 제시해 "
                "장바구니 진입 장벽을 줄입니다."
            ),
        },
        "구매전환율": {
            "tag": "전환 점검",
            "text": (
                "장바구니 이후 결제 단계의 가격, 배송비, 재고 및 "
                "옵션 선택 과정에서 이탈 원인을 확인합니다."
            ),
        },
        "반품 안정성": {
            "tag": "반품 점검",
            "text": (
                "상품 설명과 실제 품질의 차이, 사이즈 정보 및 "
                "반품 사유를 확인해 구매 후 불일치를 줄입니다."
            ),
        },
        "ROAS": {
            "tag": "효율 점검",
            "text": (
                "광고비 확대를 보류하고 광고비 대비 주문금액과 "
                "구매전환 추이를 먼저 점검합니다."
            ),
        },
    }

    return actions.get(
        label,
        {
            "tag": "운영 점검",
            "text": "낮은 지표를 중심으로 상품 운영 데이터를 점검합니다.",
        },
    )


def _build_fallback(
    product: dict[str, Any],
) -> dict[str, Any]:
    """
    Ollama가 일시적으로 응답하지 않아도 화면에는 항상
    상품별 분석값을 사용한 결과가 표시되도록 합니다.
    """
    metrics = _metric_rows(product)
    strongest = max(metrics, key=lambda item: item["score"])
    weakest = min(metrics, key=lambda item: item["score"])

    total_score = _round_number(product.get("total_score"), 2)
    product_type = (
        product.get("product_type")
        or "분석 대상"
    )

    diagnosis_summary = [
        (
            f"{strongest['label']}은 실제 값 "
            f"{strongest['value']:.1f}{strongest['unit']}, "
            f"점수 {strongest['score']:.1f}점으로 "
            f"현재 상품에서 가장 강한 지표로 확인됩니다."
        ),
        (
            f"{weakest['label']}은 실제 값 "
            f"{weakest['value']:.1f}{weakest['unit']}, "
            f"점수 {weakest['score']:.1f}점으로 상대적으로 낮습니다. "
            f"총점 {total_score}점과 {product_type} 진단을 함께 고려해 "
            f"이 지표를 우선 점검해야 합니다."
        ),
    ]

    first_action = _action_for_weak_metric(weakest)

    roas = _safe_number(product.get("calc_roas"))
    order_count = int(
        _safe_number(product.get("order_count"))
    )

    if roas >= 300 and order_count > 0:
        second_action = {
            "tag": "예산 테스트",
            "text": (
                f"현재 ROAS {roas:.1f}%와 주문수 "
                f"{order_count:,}건을 기준으로 광고비를 한 번에 크게 "
                "늘리지 말고 단계적으로 확대해 성과 유지 여부를 확인합니다."
            ),
        }
    else:
        second_action = {
            "tag": "성과 점검",
            "text": (
                f"현재 ROAS {roas:.1f}%와 주문수 "
                f"{order_count:,}건을 기준으로 전환 흐름을 점검한 뒤 "
                "광고 운영 금액을 조정합니다."
            ),
        }

    return {
        "diagnosis_summary": diagnosis_summary,
        "recommended_actions": [
            first_action,
            second_action,
        ],
        "generated_by": "fallback",
    }


def _call_ollama(
    cleaned_product: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""
당신은 온라인 쇼핑몰 상품 성과 분석 전문가입니다.

아래 상품 한 개의 실제 데이터 분석 결과만 근거로
'진단 근거 요약' 2개와 '추천 액션' 2개를 작성하세요.

작성 규칙:
1. 제공되지 않은 원인이나 사실은 추측하지 마세요.
2. 상품별 실제 수치와 지표 점수를 사용하세요.
3. 두 진단 문장은 서로 다른 근거를 사용하세요.
4. 강한 지표뿐 아니라 상대적으로 약한 지표도 확인하세요.
5. 광고 예산 확대를 무조건 권장하지 마세요.
6. 주문이 없거나 ROAS가 낮다면 전환 점검을 우선하세요.
7. 각 문장은 한국어로 간결하고 구체적으로 작성하세요.
8. JSON 이외의 내용은 출력하지 마세요.

반드시 다음 형식으로 출력하세요:
{{
  "diagnosis_summary": [
    "상품별 실제 수치가 포함된 첫 번째 진단 근거",
    "상품별 실제 수치가 포함된 두 번째 진단 근거"
  ],
  "recommended_actions": [
    {{
      "tag": "짧은 액션 이름",
      "text": "구체적인 실행 방법"
    }},
    {{
      "tag": "짧은 액션 이름",
      "text": "구체적인 실행 방법"
    }}
  ]
}}

상품 분석 데이터:
{json.dumps(cleaned_product, ensure_ascii=False, indent=2)}
""".strip()

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "제공된 데이터만 근거로 상품별 진단과 "
                        "실행 가능한 액션을 작성하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "options": {
                "temperature": 0.2,
                "num_predict": 700,
            },
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    response_data = response.json()
    content = (
        response_data.get("message", {}).get("content", "")
    )

    if not content:
        raise ValueError("Ollama 응답 내용이 비어 있습니다.")

    parsed = _extract_json(content)
    return _validate_result(parsed)


@router.post("/summary")
def generate_analysis_summary(
    product: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """
    상세 보기를 연 상품 한 개에 대해서만 LLM 분석을 생성합니다.

    LLM 호출이 일시적으로 실패하더라도 상품 분석값을 기반으로
    자동 문장을 생성하여 사용자 화면에는 결과가 항상 표시됩니다.
    """
    cleaned_product = _clean_product(product)

    try:
        return _call_ollama(cleaned_product)
    except Exception as exc:
        print(
            "[analysis/summary] Ollama 생성 실패, "
            f"데이터 기반 결과 사용: {exc}"
        )

        return _build_fallback(product)