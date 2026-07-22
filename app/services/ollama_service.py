from __future__ import annotations

import os
from typing import Any

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
)

# 법률 RAG 답변에 사용하는 모델
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma3:4b",
)

# 일반 대화에 사용하는 빠른 모델
GENERAL_CHAT_MODEL = os.getenv(
    "OLLAMA_GENERAL_MODEL",
    "gemma3:1b",
)

REQUEST_TIMEOUT = 180


GENERAL_CHAT_SYSTEM_PROMPT = """
당신은 온라인 쇼핑몰 법률 안내 서비스의 친절한 챗봇입니다.

현재 요청은 법률 검색이 필요한 질문이 아니라 일반적인 대화입니다.

다음 지침을 지켜주세요.

1. 자연스럽고 친절한 한국어로 답변합니다.
2. 인사와 감사 같은 간단한 대화에는 짧게 답변합니다.
3. 사용자의 말을 불필요하게 반복하지 않습니다.
4. 확실하지 않은 내용을 사실처럼 만들어내지 않습니다.
5. 답변은 특별한 이유가 없다면 1~3문장으로 작성합니다.
""".strip()


def generate_answer(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    model: str | None = None,
    num_predict: int | None = None,
) -> str:
    """
    Ollama에 프롬프트를 보내고 생성된 답변을 반환합니다.
    """
    prompt = prompt.strip()

    if not prompt:
        raise ValueError(
            "Ollama에 전달할 프롬프트가 비어 있습니다."
        )

    selected_model = model or OLLAMA_MODEL

    options: dict[str, Any] = {
        "temperature": temperature,
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    payload: dict[str, Any] = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }

    if system_prompt:
        payload["system"] = system_prompt.strip()

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.ConnectionError as error:
        raise RuntimeError(
            "Ollama 서버에 연결할 수 없습니다. "
            "Ollama가 실행 중인지 확인해주세요."
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "Ollama 응답 시간이 초과되었습니다."
        ) from error

    except requests.HTTPError as error:
        raise RuntimeError(
            f"Ollama 요청에 실패했습니다: {response.text}"
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"Ollama 통신 중 오류가 발생했습니다: {error}"
        ) from error

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError(
            "Ollama에서 올바른 JSON 응답을 받지 못했습니다."
        ) from error

    answer = data.get("response")

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(
            "Ollama가 정상적인 답변을 반환하지 않았습니다."
        )

    return answer.strip()


def generate_general_answer(question: str) -> str:
    """
    일반적인 대화에 대한 답변을 gemma3:1b로 생성합니다.
    """
    question = question.strip()

    if not question:
        raise ValueError(
            "일반 대화 질문이 비어 있습니다."
        )

    return generate_answer(
        prompt=question,
        system_prompt=GENERAL_CHAT_SYSTEM_PROMPT,
        temperature=0.7,
        model=GENERAL_CHAT_MODEL,
        num_predict=120,
    )