import React, { useState, useEffect, useRef } from "react";
import {
    loadStoredChatMessages,
    prepareChatMessagesForStorage,
    buildChatRequestHistory,
    createChatMessage,
    getChatSourceScore,
    getChatSourceContent,
    getChatSourceHeading,} from "../utils/chatHelpers";
import {
    CHAT_STORAGE_KEY,
    CHAT_STREAM_API_URL,
    CHAT_INTRO_MESSAGE,
    FAQ_API_QUESTIONS,
    FAQ_QUESTIONS,CHECKABLE_ITEMS,
    REFERENCE_DOCS} from "../constants/data";


export default function ChatScreen({ setScreen, }) {
    const [messages, setMessages] = useState(loadStoredChatMessages);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [streamingStarted, setStreamingStarted] = useState(false);
    const [error, setError] = useState("");
    const chatEndRef = useRef(null);
    const textareaRef = useRef(null);
    const requestInFlightRef = useRef(false);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [messages, isLoading]);

    useEffect(() => {
        try {
            const storedMessages = prepareChatMessagesForStorage(messages);

            if (storedMessages.length === 0) {
                window.localStorage.removeItem(CHAT_STORAGE_KEY);
                return;
            }

            window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(storedMessages));
        }
        catch (storageError) {
            console.error("대화를 저장하지 못했습니다.", storageError);
        }
    }, [messages]);

    async function send(text) {
        const displayedQuestion = text.trim();

        if (!displayedQuestion || requestInFlightRef.current) {
            return;
        }

        requestInFlightRef.current = true;

        const apiQuestion =
            FAQ_API_QUESTIONS[displayedQuestion] ??
            displayedQuestion;

        const isFaqQuestion =
            Object.prototype.hasOwnProperty.call(
                FAQ_API_QUESTIONS,
                displayedQuestion,
            );

        // 왼쪽 FAQ는 각각 독립된 질문이므로 이전 대화 문맥을 보내지 않습니다.
        const requestHistory = isFaqQuestion
            ? []
            : buildChatRequestHistory(messages);

        const userMessage = createChatMessage(
            "user",
            displayedQuestion,
        );

        const assistantMessageId =
            `assistant-${Date.now()}-${Math.random()
                .toString(36)
                .slice(2)}`;

        let assistantAdded = false;
        let finalData = null;

        function appendAssistantToken(token) {
            if (!token) {
                return;
            }

            setStreamingStarted(true);

            setMessages((currentMessages) => {
                if (!assistantAdded) {
                    assistantAdded = true;

                    return [
                        ...currentMessages,
                        {
                            id: assistantMessageId,
                            role: "assistant",
                            content: token,
                            sources: [],
                            isStreaming: true,
                        },
                    ];
                }

                return currentMessages.map((message) =>
                    message.id === assistantMessageId
                        ? {
                            ...message,
                            content:
                                `${message.content}${token}`,
                        }
                        : message
                );
            });
        }

        function finishAssistantMessage(data) {
            const answer =
                typeof data?.answer === "string" &&
                data.answer.trim()
                    ? data.answer
                    : "답변이 없습니다.";

            const sources = Array.isArray(data?.sources)
                ? data.sources
                : [];

            setMessages((currentMessages) => {
                const exists = currentMessages.some(
                    (message) =>
                        message.id === assistantMessageId,
                );

                if (!exists) {
                    assistantAdded = true;

                    return [
                        ...currentMessages,
                        {
                            id: assistantMessageId,
                            role: "assistant",
                            content: answer,
                            sources,
                            isStreaming: false,
                        },
                    ];
                }

                return currentMessages.map((message) =>
                    message.id === assistantMessageId
                        ? {
                            ...message,
                            content: answer,
                            sources,
                            isStreaming: false,
                        }
                        : message
                );
            });
        }

        function processStreamEvent(eventData) {
            if (!eventData || typeof eventData !== "object") {
                return;
            }

            if (eventData.type === "token") {
                appendAssistantToken(
                    typeof eventData.content === "string"
                        ? eventData.content
                        : "",
                );
                return;
            }

            if (eventData.type === "final") {
                finalData = eventData.data ?? null;
                finishAssistantMessage(finalData);
                return;
            }

            if (eventData.type === "error") {
                throw new Error(
                    eventData.detail ||
                    "챗봇 요청 중 오류가 발생했습니다.",
                );
            }
        }

        setMessages((currentMessages) => [
            ...currentMessages,
            userMessage,
        ]);
        setInput("");
        setError("");
        setIsLoading(true);
        setStreamingStarted(false);

        try {
            const response = await fetch(
                CHAT_STREAM_API_URL,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        question: apiQuestion,
                        history: requestHistory,
                    }),
                },
            );

            if (!response.ok) {
                let detail =
                    "챗봇 요청 중 오류가 발생했습니다.";

                try {
                    const errorData = await response.json();
                    detail = errorData.detail || detail;
                }
                catch {
                    // JSON 오류 응답이 아니면 기본 문구를 사용합니다.
                }

                throw new Error(detail);
            }

            if (!response.body) {
                throw new Error(
                    "서버의 스트리밍 응답을 읽을 수 없습니다.",
                );
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, {
                    stream: true,
                });

                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    const trimmedLine = line.trim();

                    if (!trimmedLine) {
                        continue;
                    }

                    let eventData;

                    try {
                        eventData = JSON.parse(trimmedLine);
                    }
                    catch {
                        throw new Error(
                            "서버의 스트리밍 응답을 해석하지 못했습니다.",
                        );
                    }

                    processStreamEvent(eventData);
                }
            }

            buffer += decoder.decode();

            if (buffer.trim()) {
                let eventData;

                try {
                    eventData = JSON.parse(buffer.trim());
                }
                catch {
                    throw new Error(
                        "서버의 마지막 스트리밍 응답을 해석하지 못했습니다.",
                    );
                }

                processStreamEvent(eventData);
            }

            if (!finalData && !assistantAdded) {
                throw new Error(
                    "서버에서 최종 답변을 받지 못했습니다.",
                );
            }
        }
        catch (requestError) {
            const message = requestError instanceof Error
                ? requestError.message
                : "알 수 없는 오류가 발생했습니다.";

            setError(message);

            setMessages((currentMessages) => {
                const hasAssistantMessage =
                    currentMessages.some(
                        (currentMessage) =>
                            currentMessage.id ===
                            assistantMessageId,
                    );

                if (hasAssistantMessage) {
                    return currentMessages.map(
                        (currentMessage) =>
                            currentMessage.id ===
                            assistantMessageId
                                ? {
                                    ...currentMessage,
                                    isStreaming: false,
                                }
                                : currentMessage,
                    );
                }

                return [
                    ...currentMessages,
                    createChatMessage(
                        "assistant",
                        `요청을 처리하지 못했습니다.\n${message}`,
                    ),
                ];
            });
        }
        finally {
            requestInFlightRef.current = false;
            setStreamingStarted(false);
            setIsLoading(false);

            window.setTimeout(() => {
                textareaRef.current?.focus();
            }, 0);
        }
    }

    function handleKeyDown(event) {
        if (event.key === "Enter" &&
            !event.shiftKey &&
            !event.nativeEvent.isComposing) {
            event.preventDefault();
            send(input);
        }
    }

    function handleNewChat() {
        setMessages([CHAT_INTRO_MESSAGE]);
        setInput("");
        setError("");
        window.localStorage.removeItem(CHAT_STORAGE_KEY);
        textareaRef.current?.focus();
    }

    const BotAvatar = () => (<div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{
            backgroundColor: "#EFF6FF",
            border: "1px solid #BFDBFE",
        }}>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="9" y1="13" x2="15" y2="13"/>
        <line x1="9" y1="17" x2="12" y2="17"/>
      </svg>
    </div>);

    function renderSources(sources) {
        if (!Array.isArray(sources) || sources.length === 0) {
            return null;
        }

        return (<details className="border-t border-slate-100 pt-3">
          <summary className="text-[11px] font-bold text-blue-600 cursor-pointer select-none">
            참고 근거 {sources.length}개
          </summary>

          <div className="mt-3 space-y-2.5">
            {sources.map((source, index) => {
                const score = getChatSourceScore(source);
                const content = getChatSourceContent(source);
                const sourceFile = source.source_file ||
                    source.file_name ||
                    "문서명 없음";

                return (<article key={source.parent_id ||
                        source.id ||
                        `${sourceFile}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <span className="text-[10px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-1 rounded-lg">
                      근거 {index + 1}
                    </span>
                    {score && (<span className="text-[10px] text-slate-400">
                        검색 점수 {score}
                      </span>)}
                  </div>

                  <p className="text-xs font-bold text-slate-700 leading-relaxed">
                    {getChatSourceHeading(source)}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    문서: {sourceFile}
                  </p>

                  {content && (<p className="text-[11px] text-slate-600 leading-relaxed mt-2 whitespace-pre-line max-h-40 overflow-y-auto">
                      {content}
                    </p>)}
                </article>);
            })}
          </div>
        </details>);
    }

    function renderMessage(message) {
        if (message.role === "user") {
            return (<div className="flex justify-end">
          <div className="max-w-[70%] px-4 py-3 rounded-2xl rounded-tr-sm text-sm text-white leading-relaxed whitespace-pre-line" style={{ backgroundColor: "#2563EB" }}>
            {message.content}
          </div>
        </div>);
        }

        return (<div className="flex justify-start">
        <div className="max-w-[90%] space-y-1.5">
          <div className="flex items-center gap-2">
            <BotAvatar />
            <span className="text-[11px] font-semibold text-slate-400">
              ActionFit 법 규제 챗봇
            </span>
          </div>

          <div className={`rounded-2xl rounded-tl-sm border p-4 space-y-3 shadow-sm ${message.isIntro
                ? "bg-blue-50/50 border-blue-100"
                : "bg-white border-slate-100"}`}>
            <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
              {message.content}
            </p>

            {!message.isIntro && renderSources(message.sources)}

            {!message.isIntro && (<div className="border-t border-slate-100 pt-2">
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  본 답변은 업로드된 법령 및 플랫폼 규제 문서를
                  기반으로 한 쇼핑몰 운영 참고용 안내이며, 법률
                  자문이나 최종 법적 판단을 대신하지 않습니다.
                </p>
              </div>)}
          </div>
        </div>
      </div>);
    }

    return (<div className="flex-1 overflow-y-auto bg-slate-50 p-5 space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-800">
          쇼핑몰 법 규제 챗봇
        </h2>
        <p className="text-sm text-slate-400 mt-0.5">
          광고 문구, 상세페이지, 반품·환불, 개인정보, 플랫폼
          규정 관련 리스크를 문서 근거와 함께 확인해요.
        </p>
      </div>

      <div className="rounded-2xl px-7 py-5 overflow-hidden relative" style={{
            background: "linear-gradient(135deg, #3B82F6 0%, #93C5FD 55%, #C4B5FD 100%)",
        }}>
        <div className="absolute inset-0 bg-gradient-to-br from-black/10 via-transparent to-black/5 pointer-events-none"/>
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full pointer-events-none" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}/>
        <div className="absolute -bottom-12 right-40 w-40 h-40 rounded-full pointer-events-none" style={{ backgroundColor: "rgba(255,255,255,0.05)" }}/>
        <div className="relative z-10 max-w-2xl">
          <p className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.72)" }}>
            법 규제 리스크 확인
          </p>
          <p className="text-base font-semibold mb-1" style={{ color: "#fff" }}>
            온라인 쇼핑몰 운영과 관련된 법률 기준이 궁금한가요?
          </p>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.88)" }}>
            저장된 법령과 정책 문서를 검색해 근거와 함께 답변합니다.
          </p>
        </div>
      </div>

      <div className="flex gap-4 items-start">
        <div className="flex-shrink-0" style={{ width: "31%" }}>
          <div className="bg-white rounded-xl border border-slate-100 p-5" style={{ minHeight: 700 }}>
            <div className="flex items-center gap-2 mb-5">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: "#EFF6FF" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <p className="text-sm font-bold text-slate-700">
                자주 묻는 질문
              </p>
            </div>

            <div className="flex flex-col gap-2.5">
              {FAQ_QUESTIONS.map((question, index) => (<button key={index} type="button" disabled={isLoading} onClick={() => send(question)} className="w-full text-left text-xs text-slate-600 px-4 py-3 rounded-xl border border-slate-100 hover:border-blue-300 hover:bg-blue-50/60 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all leading-snug">
                  {question}
                </button>))}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="bg-white rounded-xl border border-slate-100 px-5 py-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#EFF6FF" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 11 12 14 22 4"/>
                  <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-slate-700">
                  확인 가능한 항목
                </p>
                <p className="text-[11px] text-slate-400">
                  이 챗봇으로 아래 주제를 질문할 수 있어요.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {CHECKABLE_ITEMS.map((item) => (<span key={item} className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {item}
                </span>))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 flex flex-col" style={{ height: 640 }}>
            <div className="flex-shrink-0 px-5 py-3.5 border-b border-slate-50 flex items-center gap-2.5">
              <BotAvatar />
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-700">
                  ActionFit 법 규제 챗봇
                </p>
                <p className={`text-[10px] font-medium ${isLoading ? "text-blue-500" : "text-emerald-500"}`}>
                  ● {isLoading ? "답변 생성 중" : "응답 준비됨"}
                </p>
              </div>

              <button type="button" onClick={handleNewChat} disabled={isLoading || messages.every((message) => message.isIntro)} className="text-[11px] font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
                새 대화
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
              {messages.map((message) => (<div key={message.id}>
                  {renderMessage(message)}
                </div>))}

              {isLoading && !streamingStarted && (<div className="flex justify-start">
                  <div className="max-w-[90%] space-y-1.5">
                    <div className="flex items-center gap-2">
                      <BotAvatar />
                      <span className="text-[11px] font-semibold text-slate-400">
                        ActionFit 법 규제 챗봇
                      </span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-sm border border-slate-100 px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce"/>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "120ms" }}/>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "240ms" }}/>
                      </div>
                    </div>
                  </div>
                </div>)}

              <div ref={chatEndRef}/>
            </div>

            {error && (<div className="mx-5 mb-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
                {error}
              </div>)}

            <div className="flex-shrink-0 border-t border-slate-100 px-5 pt-3 pb-4 space-y-2.5">
              <div className="flex gap-2 flex-wrap">
                {[
                    "광고 문구 붙여넣기",
                    "상세페이지 문구 붙여넣기",
                    "반품·환불 문구 붙여넣기",
                ].map((label) => (<button key={label} type="button" disabled={isLoading} onClick={() => {
                        setInput(label.replace(" 붙여넣기", ": "));
                        textareaRef.current?.focus();
                    }} className="text-[11px] font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-50 transition">
                    + {label}
                  </button>))}
              </div>

              <div className="flex gap-2 items-end">
                <textarea ref={textareaRef} rows={2} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} disabled={isLoading} placeholder={'온라인 쇼핑 관련 질문을 입력해주세요.\n예: "단순 변심으로도 반품할 수 있나요?"'} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-700 bg-slate-50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 disabled:bg-slate-100 disabled:cursor-not-allowed transition resize-none leading-relaxed"/>

                <button type="button" onClick={() => send(input)} disabled={isLoading || !input.trim()} className="flex-shrink-0 w-11 h-11 rounded-xl text-white flex items-center justify-center transition-all" style={!isLoading && input.trim()
                    ? {
                        backgroundColor: "#2563EB",
                        boxShadow: "0 4px 14px rgba(37,99,235,0.25)",
                    }
                    : {
                        backgroundColor: "#E2E8F0",
                        cursor: "not-allowed",
                    }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 px-6 py-5">
        <div className="flex items-baseline gap-2 mb-4">
          <p className="text-sm font-bold text-slate-700">
            참고 문서
          </p>
          <p className="text-xs text-slate-400">
            아래 문서를 검색해 답변 근거로 활용합니다.
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {REFERENCE_DOCS.map((doc) => (<div key={doc.name} className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-100 bg-slate-50">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span className="text-xs text-slate-600 whitespace-nowrap">
                {doc.name}
              </span>
              <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${doc.badgeCls} whitespace-nowrap`}>
                {doc.badge}
              </span>
            </div>))}
        </div>
      </div>

      <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-white border border-slate-100">
        <svg className="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p className="text-[10px] text-slate-400 leading-relaxed">
          본 기능은 업로드된 법령 및 플랫폼 규제 문서를 기반으로
          한 쇼핑몰 운영 참고용 안내입니다. 법률 자문이나 최종
          법적 판단을 대신하지 않으며, 실제 분쟁이나 법적 검토가
          필요한 경우 전문가 상담이 필요합니다.
        </p>
      </div>
    </div>);
}