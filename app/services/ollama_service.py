from __future__ import annotations

import json
import os
from collections.abc import Callable
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


def _build_payload(
    prompt: str,
    system_prompt: str | None,
    temperature: float,
    model: str | None,
    num_predict: int | None,
    stream: bool,
) -> dict[str, Any]:
    selected_model = model or OLLAMA_MODEL

    options: dict[str, Any] = {
        "temperature": temperature,
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    payload: dict[str, Any] = {
        "model": selected_model,
        "prompt": prompt,
        "stream": stream,
        "options": options,
    }

    if system_prompt:
        payload["system"] = system_prompt.strip()

    return payload


def _raise_request_error(error: requests.RequestException) -> None:
    if isinstance(error, requests.ConnectionError):
        raise RuntimeError(
            "Ollama 서버에 연결할 수 없습니다. "
            "Ollama가 실행 중인지 확인해주세요."
        ) from error

    if isinstance(error, requests.Timeout):
        raise RuntimeError(
            "Ollama 응답 시간이 초과되었습니다."
        ) from error

    if isinstance(error, requests.HTTPError):
        response = error.response
        detail = (
            response.text
            if response is not None
            else str(error)
        )

        raise RuntimeError(
            f"Ollama 요청에 실패했습니다: {detail}"
        ) from error

    raise RuntimeError(
        f"Ollama 통신 중 오류가 발생했습니다: {error}"
    ) from error


def _generate_non_streaming(
    payload: dict[str, Any],
) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        _raise_request_error(error)

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


def _generate_streaming(
    payload: dict[str, Any],
    on_token: Callable[[str], None],
) -> str:
    answer_parts: list[str] = []

    try:
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            response.raise_for_status()

            # requests의 기본 chunk_size는 여러 Ollama 토큰을
            # 모아서 전달할 수 있으므로 1바이트 단위로 즉시 읽습니다.
            for raw_line in response.iter_lines(
                chunk_size=1,
                decode_unicode=True,
            ):
                if not raw_line:
                    continue

                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError as error:
                    raise RuntimeError(
                        "Ollama 스트리밍 응답을 해석하지 "
                        "못했습니다."
                    ) from error

                error_message = data.get("error")

                if error_message:
                    raise RuntimeError(
                        f"Ollama 생성 오류: {error_message}"
                    )

                token = data.get("response", "")

                if isinstance(token, str) and token:
                    answer_parts.append(token)
                    on_token(token)

                if data.get("done") is True:
                    break

    except requests.RequestException as error:
        _raise_request_error(error)

    answer = "".join(answer_parts).strip()

    if not answer:
        raise RuntimeError(
            "Ollama가 정상적인 답변을 반환하지 않았습니다."
        )

    return answer


def generate_answer(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    model: str | None = None,
    num_predict: int | None = None,
    on_token: Callable[[str], None] | None = None,
) -> str:
    """
    Ollama에 프롬프트를 보내고 생성된 답변을 반환합니다.

    on_token이 전달되면 Ollama의 생성 내용을 조각 단위로
    전달하면서 최종 전체 답변도 반환합니다.
    """
    prompt = prompt.strip()

    if not prompt:
        raise ValueError(
            "Ollama에 전달할 프롬프트가 비어 있습니다."
        )

    use_stream = on_token is not None

    payload = _build_payload(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        model=model,
        num_predict=num_predict,
        stream=use_stream,
    )

    if on_token is None:
        return _generate_non_streaming(payload)

    return _generate_streaming(
        payload=payload,
        on_token=on_token,
    )


def generate_general_answer(
    question: str,
    on_token: Callable[[str], None] | None = None,
) -> str:
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
        on_token=on_token,
    )