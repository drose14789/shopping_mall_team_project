import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/chat";

function getSourceScore(source) {
  const score =
    source.rerank_score ??
    source.score ??
    source.dense_score ??
    source.similarity_score;

  return typeof score === "number" ? score.toFixed(4) : null;
}

function getSourceHeading(source) {
  if (Array.isArray(source.heading_path)) {
    return source.heading_path.join(" > ");
  }

  return (
    source.heading_path ||
    source.heading ||
    source.title ||
    "제목 없음"
  );
}

function getSourceContent(source) {
  return (
    source.parent_content ||
    source.content ||
    source.text ||
    source.excerpt ||
    ""
  );
}

function createMessage(role, content, sources = []) {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    role,
    content,
    sources,
  };
}

function SourceList({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  return (
    <details className="message-sources">
      <summary>
        참고 근거 {sources.length}개
      </summary>

      <div className="source-list">
        {sources.map((source, index) => {
          const score = getSourceScore(source);
          const content = getSourceContent(source);
          const sourceFile =
            source.source_file ||
            source.file_name ||
            "문서명 없음";

          return (
            <article
              className="source-card"
              key={
                source.parent_id ||
                source.id ||
                `${sourceFile}-${index}`
              }
            >
              <div className="source-card-header">
                <span className="source-rank">
                  근거 {index + 1}
                </span>

                {score && (
                  <span className="source-score">
                    검색 점수 {score}
                  </span>
                )}
              </div>

              <h3>{getSourceHeading(source)}</h3>

              <p className="source-file">
                문서: {sourceFile}
              </p>

              {content && (
                <p className="source-content">
                  {content}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </details>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const messageEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isLoading]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError("질문을 입력해주세요.");
      textareaRef.current?.focus();
      return;
    }

    if (isLoading) {
      return;
    }

    const userMessage = createMessage(
      "user",
      trimmedQuestion
    );

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setQuestion("");
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const responseText = await response.text();

      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error(
          "서버에서 올바른 JSON 응답을 받지 못했습니다."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "챗봇 요청 중 오류가 발생했습니다."
        );
      }

      const assistantMessage = createMessage(
        "assistant",
        data.answer || "답변이 없습니다.",
        Array.isArray(data.sources)
          ? data.sources
          : []
      );

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "알 수 없는 오류가 발생했습니다.";

      setError(message);

      setMessages((currentMessages) => [
        ...currentMessages,
        createMessage(
          "assistant",
          `요청을 처리하지 못했습니다.\n${message}`
        ),
      ]);
    } finally {
      setIsLoading(false);

      window.setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
  };

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setQuestion("");
    setError("");
    textareaRef.current?.focus();
  };

  return (
    <main className="app">
      <section className="chat-container">
        <header className="chat-header">
          <div>
            <h1>온라인 쇼핑몰 법률 안내 챗봇</h1>
            <p>
              반품, 환불, 판매자 정보 등 온라인 쇼핑과
              관련된 질문을 입력해주세요.
            </p>
          </div>

          <button
            type="button"
            className="new-chat-button"
            onClick={handleNewChat}
            disabled={
              isLoading || messages.length === 0
            }
          >
            새 대화
          </button>
        </header>

        <section className="chat-panel">
          <div className="message-list">
            {messages.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-icon">
                  법률
                </div>

                <h2>무엇이 궁금한가요?</h2>

                <p>
                  아래 입력창에 온라인 쇼핑 관련 질문을
                  입력해주세요.
                </p>

                <div className="example-list">
                  <button
                    type="button"
                    onClick={() =>
                      setQuestion(
                        "단순 변심으로도 반품할 수 있나요?"
                      )
                    }
                  >
                    단순 변심 반품
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setQuestion(
                        "품절이면 언제 환불받을 수 있나요?"
                      )
                    }
                  >
                    품절 환불
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setQuestion(
                        "판매자 정보는 언제 확인할 수 있나요?"
                      )
                    }
                  >
                    판매자 정보
                  </button>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <article
                key={message.id}
                className={`message-row ${message.role}`}
              >
                <div className="message-avatar">
                  {message.role === "user"
                    ? "나"
                    : "AI"}
                </div>

                <div className="message-body">
                  <div className="message-label">
                    {message.role === "user"
                      ? "사용자"
                      : "법률 안내 챗봇"}
                  </div>

                  <div className="message-bubble">
                    <p>{message.content}</p>
                  </div>

                  {message.role === "assistant" && (
                    <SourceList
                      sources={message.sources}
                    />
                  )}
                </div>
              </article>
            ))}

            {isLoading && (
              <article className="message-row assistant">
                <div className="message-avatar">
                  AI
                </div>

                <div className="message-body">
                  <div className="message-label">
                    법률 안내 챗봇
                  </div>

                  <div className="message-bubble loading-bubble">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </article>
            )}

            <div ref={messageEndRef} />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form
            className="question-form"
            onSubmit={handleSubmit}
          >
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="질문을 입력하세요. Enter로 전송, Shift + Enter로 줄바꿈"
              rows={3}
              disabled={isLoading}
              aria-label="질문 입력"
            />

            <button
              type="submit"
              disabled={
                isLoading || !question.trim()
              }
            >
              {isLoading
                ? "답변 생성 중..."
                : "전송"}
            </button>
          </form>
        </section>

        <p className="notice">
          제공되는 답변은 일반적인 법률 정보이며,
          구체적인 분쟁은 관련 기관이나 전문가의 확인이
          필요할 수 있습니다.
        </p>
      </section>
    </main>
  );
}

export default App;