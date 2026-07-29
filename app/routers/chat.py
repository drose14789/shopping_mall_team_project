from __future__ import annotations

import json
import time
import traceback
from collections import OrderedDict
from collections.abc import Iterator
from copy import deepcopy
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services import rag_service
from app.services.chat_service import (
    BOT_INFO_ANSWER,
    answer_chat,
    get_fixed_general_answer,
    is_bot_info_question,
    is_ollama_general_chat,
    resolve_followup_question,
    resolve_initial_legal_statement,
)
from app.services.ollama_service import (
    generate_general_answer,
)


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# 실제 RAG 답변과 근거 문서를 함께 보관하는 메모리 캐시입니다.
# FastAPI가 재시작되면 자동으로 초기화됩니다.
RAG_CACHE_TTL_SECONDS = 60 * 60
RAG_CACHE_MAX_ENTRIES = 100

RAG_RESPONSE_CACHE: OrderedDict[
    str,
    tuple[float, dict[str, Any]],
] = OrderedDict()

RAG_CACHE_LOCK = Lock()


def _build_rag_cache_key(
    request: ChatRequest,
) -> str | None:
    """
    이전 대화 문맥이 없는 독립 질문만 캐시합니다.

    후속 질문은 같은 문장이라도 이전 대화에 따라 답변이 달라질
    수 있으므로 캐시하지 않습니다.
    """
    if request.history:
        return None

    question = " ".join(request.question.split()).casefold()

    if not question:
        return None

    return question


def _get_cached_rag_response(
    request: ChatRequest,
) -> dict[str, Any] | None:
    cache_key = _build_rag_cache_key(request)

    if cache_key is None:
        return None

    current_time = time.monotonic()

    with RAG_CACHE_LOCK:
        cached_item = RAG_RESPONSE_CACHE.get(cache_key)

        if cached_item is None:
            return None

        created_at, cached_response = cached_item

        if (
            current_time - created_at
            > RAG_CACHE_TTL_SECONDS
        ):
            del RAG_RESPONSE_CACHE[cache_key]
            return None

        # 최근 사용된 항목을 뒤로 이동합니다.
        RAG_RESPONSE_CACHE.move_to_end(cache_key)

        return deepcopy(cached_response)


def _store_rag_response(
    request: ChatRequest,
    response: dict[str, Any],
) -> None:
    """
    실제 검색 근거가 포함된 응답만 캐시합니다.
    """
    cache_key = _build_rag_cache_key(request)

    if cache_key is None:
        return

    answer = response.get("answer")
    sources = response.get("sources")

    if (
        not isinstance(answer, str)
        or not answer.strip()
        or not isinstance(sources, list)
        or not sources
    ):
        return

    with RAG_CACHE_LOCK:
        RAG_RESPONSE_CACHE[cache_key] = (
            time.monotonic(),
            deepcopy(response),
        )
        RAG_RESPONSE_CACHE.move_to_end(cache_key)

        while (
            len(RAG_RESPONSE_CACHE)
            > RAG_CACHE_MAX_ENTRIES
        ):
            RAG_RESPONSE_CACHE.popitem(last=False)


def _model_to_dict(model: Any) -> dict[str, Any]:
    """
    Pydantic v1과 v2에서 모두 동작하도록 모델을 dict로 변환한다.
    """
    model_dump = getattr(model, "model_dump", None)

    if callable(model_dump):
        return model_dump()

    legacy_dict = getattr(model, "dict", None)

    if callable(legacy_dict):
        return legacy_dict()

    raise TypeError(
        "Pydantic 모델을 dict로 변환할 수 없습니다."
    )


def _get_controlled_intent_detectors() -> list[Callable[[str], bool]]:
    """
    rag_service.py에 정의된 고정 intent 판별 함수를 자동으로 가져온다.

    함수 이름이 is_로 시작하고 _question으로 끝나는 함수만
    판별기로 사용한다. 이후 rag_service.py에 새로운 intent를
    추가해도 chat.py를 다시 수정할 필요가 없다.
    """
    detectors: list[Callable[[str], bool]] = []

    for name, value in vars(rag_service).items():
        if (
            name.startswith("is_")
            and name.endswith("_question")
            and callable(value)
        ):
            detectors.append(value)

    return detectors


CONTROLLED_INTENT_DETECTORS = _get_controlled_intent_detectors()


def _matches_controlled_rag_intent(question: str) -> bool:
    """
    질문이 rag_service의 고정 intent 중 하나에 해당하는지 확인한다.
    """
    cleaned_question = " ".join(str(question).split())

    if not cleaned_question:
        return False

    for detector in CONTROLLED_INTENT_DETECTORS:
        try:
            if detector(cleaned_question):
                return True
        except (TypeError, ValueError):
            continue

    return False


def _history_to_dicts(
    request: ChatRequest,
) -> list[dict[str, str]]:
    return [
        _model_to_dict(message)
        for message in request.history
    ]


def _answer_request(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    기존 비스트리밍 응답 처리.
    """
    question = " ".join(request.question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    if _matches_controlled_rag_intent(question):
        return rag_service.answer_question(question)

    return answer_chat(
        question=question,
        history=_history_to_dicts(request),
    )


def _answer_request_streaming(
    request: ChatRequest,
    on_token: Callable[[str], None],
) -> dict[str, Any]:
    """
    질문 유형별 기존 처리 규칙을 유지하면서,
    Ollama가 생성하는 답변 조각을 on_token으로 전달한다.
    """
    question = " ".join(request.question.split())

    if not question:
        raise ValueError("질문을 입력해주세요.")

    cached_response = _get_cached_rag_response(request)

    if cached_response is not None:
        cached_answer = str(
            cached_response.get("answer", "")
        ).strip()

        if cached_answer:
            on_token(cached_answer)

        return cached_response

    if _matches_controlled_rag_intent(question):
        result = rag_service.answer_question(
            question,
            on_token=on_token,
        )
        _store_rag_response(request, result)
        return result

    history = _history_to_dicts(request)

    if is_bot_info_question(question):
        on_token(BOT_INFO_ANSWER)

        return {
            "question": question,
            "answer": BOT_INFO_ANSWER,
            "intent": "bot_info",
            "sources": [],
        }

    fixed_answer = get_fixed_general_answer(question)

    if fixed_answer is not None:
        on_token(fixed_answer)

        return {
            "question": question,
            "answer": fixed_answer,
            "intent": "general_chat",
            "sources": [],
        }

    if is_ollama_general_chat(question):
        answer = generate_general_answer(
            question,
            on_token=on_token,
        )

        return {
            "question": question,
            "answer": answer,
            "intent": "general_chat",
            "sources": [],
        }

    resolved_question = resolve_followup_question(
        question=question,
        history=history,
    )

    if resolved_question == question:
        resolved_question = resolve_initial_legal_statement(
            question
        )

    result = rag_service.answer_question(
        resolved_question,
        on_token=on_token,
    )

    # 화면에는 사용자가 입력한 질문을 유지한다.
    result["question"] = question

    _store_rag_response(request, result)

    return result


def _encode_event(
    event_type: str,
    **payload: Any,
) -> str:
    """
    프론트에서 한 줄씩 읽을 수 있는 NDJSON 이벤트를 만든다.
    """
    event = {
        "type": event_type,
        **payload,
    }

    return (
        json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )


def _stream_chat_events(
    request: ChatRequest,
) -> Iterator[str]:
    """
    동기식 RAG/Ollama 작업은 별도 스레드에서 실행하고,
    생성되는 토큰을 Queue를 통해 즉시 프론트로 전달한다.
    """
    event_queue: Queue[tuple[str, Any]] = Queue()

    def on_token(token: str) -> None:
        if token:
            event_queue.put(("token", token))

    def worker() -> None:
        try:
            result = _answer_request_streaming(
                request=request,
                on_token=on_token,
            )

            # 기존 ChatResponse 형식과 동일한지 검증한다.
            response = ChatResponse(**result)

            event_queue.put(
                (
                    "final",
                    _model_to_dict(response),
                )
            )

        except ValueError as error:
            event_queue.put(
                (
                    "error",
                    {
                        "status_code": 400,
                        "detail": str(error),
                    },
                )
            )

        except RuntimeError as error:
            event_queue.put(
                (
                    "error",
                    {
                        "status_code": 503,
                        "detail": str(error),
                    },
                )
            )

        except Exception:
            traceback.print_exc()

            event_queue.put(
                (
                    "error",
                    {
                        "status_code": 500,
                        "detail": (
                            "챗봇 답변 생성 중 오류가 "
                            "발생했습니다."
                        ),
                    },
                )
            )

        finally:
            event_queue.put(("done", None))

    thread = Thread(
        target=worker,
        name="chat-stream-worker",
        daemon=True,
    )
    thread.start()

    yield _encode_event(
        "start",
        question=request.question,
    )

    while True:
        event_type, payload = event_queue.get()

        if event_type == "token":
            yield _encode_event(
                "token",
                content=str(payload),
            )
            continue

        if event_type == "final":
            yield _encode_event(
                "final",
                data=payload,
            )
            continue

        if event_type == "error":
            yield _encode_event(
                "error",
                **payload,
            )
            continue

        if event_type == "done":
            yield _encode_event("done")
            break


@router.post(
    "",
    response_model=ChatResponse,
    summary="온라인 쇼핑몰 법률 챗봇 질문",
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    기존 JSON 방식의 챗봇 API.

    기존 프론트나 테스트 코드와의 호환성을 위해 그대로 유지한다.
    """
    try:
        result = _answer_request(request)
        return ChatResponse(**result)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="챗봇 답변 생성 중 오류가 발생했습니다.",
        ) from error


@router.post(
    "/stream",
    summary="온라인 쇼핑몰 법률 챗봇 스트리밍 질문",
)
def chat_stream(
    request: ChatRequest,
) -> StreamingResponse:
    """
    NDJSON 형식으로 답변 생성 조각을 즉시 전송한다.

    이벤트 종류:
    - start: 요청 처리 시작
    - token: 생성된 답변 조각
    - final: 최종 답변과 근거 문서
    - error: 처리 오류
    - done: 스트림 종료
    """
    return StreamingResponse(
        _stream_chat_events(request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            # GZipMiddleware가 스트리밍 응답을 모아서 압축하지
            # 않도록 명시적으로 identity 인코딩을 사용합니다.
            "Content-Encoding": "identity",
        },
    )