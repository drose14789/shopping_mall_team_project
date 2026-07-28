import { useEffect, useRef, useState } from "react";
import "./App.css";

const BASE_API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const CHAT_API_URL = `${BASE_API_URL}/chat`;
const SCORE_API_URL =
  `${BASE_API_URL}/score/evaluate-multiple`;

const MAX_HISTORY_MESSAGES = 10;
const MAX_HISTORY_CONTENT_LENGTH = 2000;
const STORAGE_KEY =
  "online-shopping-legal-chat-messages";
const MAX_STORED_MESSAGES = 30;
const MAX_STORED_SOURCE_CONTENT_LENGTH = 2500;

const METRIC_LABELS = {
  click_rate: "상품 클릭률",
  wish_conv_rate: "찜 전환율",
  cart_conv_rate: "장바구니 전환율",
  conv_rate: "구매 전환율",
  return_stability: "반품 안정성",
  roas: "ROAS",
};

function truncateText(value, maxLength) {
  if (typeof value !== "string") {
    return "";
  }

  return value.slice(0, maxLength);
}

function prepareMessagesForStorage(messages) {
  return messages
    .filter(
      (message) =>
        (message.role === "user" ||
          message.role === "assistant") &&
        typeof message.content === "string" &&
        message.content.trim()
    )
    .slice(-MAX_STORED_MESSAGES)
    .map((message) => ({
      id:
        typeof message.id === "string"
          ? message.id
          : `${Date.now()}-${Math.random()
              .toString(36)
              .slice(2)}`,
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
            child_content: truncateText(
              source.child_content,
              MAX_STORED_SOURCE_CONTENT_LENGTH
            ),
            parent_content: truncateText(
              source.parent_content,
              MAX_STORED_SOURCE_CONTENT_LENGTH
            ),
            content: truncateText(
              source.content,
              MAX_STORED_SOURCE_CONTENT_LENGTH
            ),
            text: truncateText(
              source.text,
              MAX_STORED_SOURCE_CONTENT_LENGTH
            ),
            excerpt: truncateText(
              source.excerpt,
              MAX_STORED_SOURCE_CONTENT_LENGTH
            ),
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

function loadStoredMessages() {
  try {
    const storedValue =
      window.localStorage.getItem(STORAGE_KEY);

    if (!storedValue) {
      return [];
    }

    const parsedMessages = JSON.parse(storedValue);

    if (!Array.isArray(parsedMessages)) {
      return [];
    }

    return prepareMessagesForStorage(parsedMessages);
  } catch (storageError) {
    console.error(
      "저장된 대화를 불러오지 못했습니다.",
      storageError
    );

    return [];
  }
}

function getSourceScore(source) {
  const score =
    source.rerank_score ??
    source.score ??
    source.dense_score ??
    source.similarity_score;

  return typeof score === "number"
    ? score.toFixed(4)
    : null;
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
    id: `${Date.now()}-${Math.random()
      .toString(36)
      .slice(2)}`,
    role,
    content,
    sources,
  };
}

function buildRequestHistory(messages) {
  return messages
    .filter(
      (message) =>
        (message.role === "user" ||
          message.role === "assistant") &&
        typeof message.content === "string" &&
        message.content.trim()
    )
    .slice(-MAX_HISTORY_MESSAGES)
    .map((message) => ({
      role: message.role,
      content: message.content
        .trim()
        .slice(0, MAX_HISTORY_CONTENT_LENGTH),
    }));
}

function formatNumber(value, digits = 2) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "-";
  }

  return number.toFixed(digits);
}

function getMetricLabel(key) {
  return METRIC_LABELS[key] || key;
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

function AnalysisResultCard({ result, index }) {
  const calculatedMetrics =
    result.calculated_metrics || {};
  const percentileScores =
    result.percentile_scores || {};
  const coachingFeedback =
    result.coaching_feedback || {};

  return (
    <article className="analysis-result-card">
      <div className="analysis-result-header">
        <div>
          <span className="result-number">
            분석 결과 {index + 1}
          </span>

          <h3>
            {result.product_name || "상품명 없음"}
          </h3>
        </div>

        <strong className="total-score">
          {formatNumber(result.total_score)}점
        </strong>
      </div>

      <dl className="result-summary">
        <div>
          <dt>카테고리</dt>
          <dd>{result.category || "-"}</dd>
        </div>

        <div>
          <dt>시즌</dt>
          <dd>{result.season || "-"}</dd>
        </div>

        <div>
          <dt>상품 유형</dt>
          <dd>{result.product_type || "-"}</dd>
        </div>
      </dl>

      <div className="metric-section">
        <h4>계산 지표</h4>

        <div className="metric-grid">
          {Object.entries(calculatedMetrics).map(
            ([key, value]) => (
              <div className="metric-item" key={key}>
                <span>{getMetricLabel(key)}</span>
                <strong>
                  {formatNumber(value)}
                  {key === "roas" ? "" : "%"}
                </strong>
              </div>
            )
          )}
        </div>
      </div>

      <div className="metric-section">
        <h4>백분위 점수</h4>

        <div className="metric-grid">
          {Object.entries(percentileScores).map(
            ([key, value]) => (
              <div className="metric-item" key={key}>
                <span>{getMetricLabel(key)}</span>
                <strong>
                  {formatNumber(value)}점
                </strong>
              </div>
            )
          )}
        </div>
      </div>

      {Object.keys(coachingFeedback).length > 0 && (
        <div className="feedback-section">
          <h4>분석 피드백</h4>

          <ul>
            {Object.entries(coachingFeedback).map(
              ([key, value]) => (
                <li key={key}>
                  <strong>{key}</strong>
                  <span>{value}</span>
                </li>
              )
            )}
          </ul>
        </div>
      )}
    </article>
  );
}

function App() {
  const [selectedFiles, setSelectedFiles] =
    useState([]);
  const [analysisResults, setAnalysisResults] =
    useState([]);
  const [analysisMessage, setAnalysisMessage] =
    useState("");
  const [analysisError, setAnalysisError] =
    useState("");
  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState(
    loadStoredMessages
  );
  const [isLoading, setIsLoading] =
    useState(false);
  const [chatError, setChatError] = useState("");

  const messageEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isLoading]);

  useEffect(() => {
    try {
      if (messages.length === 0) {
        window.localStorage.removeItem(STORAGE_KEY);
        return;
      }

      const storedMessages =
        prepareMessagesForStorage(messages);

      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(storedMessages)
      );
    } catch (storageError) {
      console.error(
        "대화를 저장하지 못했습니다.",
        storageError
      );
    }
  }, [messages]);

  const handleFileChange = (event) => {
    const files = Array.from(
      event.target.files || []
    );

    const invalidFile = files.find(
      (file) =>
        !file.name.toLowerCase().endsWith(".xlsx")
    );

    if (invalidFile) {
      setSelectedFiles([]);
      setAnalysisError(
        ".xlsx 형식의 엑셀 파일만 선택할 수 있습니다."
      );
      event.target.value = "";
      return;
    }

    setSelectedFiles(files);
    setAnalysisResults([]);
    setAnalysisMessage("");
    setAnalysisError("");
  };

  const handleAnalysisSubmit = async (event) => {
    event.preventDefault();

    if (selectedFiles.length === 0) {
      setAnalysisError(
        "분석할 엑셀 파일을 선택해주세요."
      );
      fileInputRef.current?.focus();
      return;
    }

    if (isAnalyzing) {
      return;
    }

    const formData = new FormData();

    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    setIsAnalyzing(true);
    setAnalysisError("");
    setAnalysisMessage("");
    setAnalysisResults([]);

    try {
      const response = await fetch(SCORE_API_URL, {
        method: "POST",
        body: formData,
      });

      const responseText = await response.text();

      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error(
          "서버에서 올바른 분석 결과를 받지 못했습니다."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "상품 데이터 분석 중 오류가 발생했습니다."
        );
      }

      setAnalysisMessage(
        data.message || "분석이 완료되었습니다."
      );

      setAnalysisResults(
        Array.isArray(data.results)
          ? data.results
          : []
      );
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "알 수 없는 오류가 발생했습니다.";

      setAnalysisError(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalysisReset = () => {
    setSelectedFiles([]);
    setAnalysisResults([]);
    setAnalysisMessage("");
    setAnalysisError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleChatSubmit = async (event) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setChatError("질문을 입력해주세요.");
      textareaRef.current?.focus();
      return;
    }

    if (isLoading) {
      return;
    }

    const requestHistory =
      buildRequestHistory(messages);

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
    setChatError("");

    try {
      const response = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          history: requestHistory,
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

      setChatError(message);

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
      handleChatSubmit(event);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setQuestion("");
    setChatError("");
    textareaRef.current?.focus();
  };

  return (
    <main className="app">
      <section className="integrated-container">
        <header className="app-header">
          <h1>온라인 쇼핑몰 상품 분석 서비스</h1>

          <p>
            상품 성과 데이터분석과 온라인 쇼핑 법률
            챗봇을 한 화면에서 이용할 수 있습니다.
          </p>
        </header>

        <div className="workspace-grid">
          <section className="analysis-container">
            <header className="section-header">
              <div>
                <span className="section-label">
                  DATA ANALYSIS
                </span>

                <h2>상품 성과 분석</h2>

                <p>
                  상품 데이터가 포함된 엑셀 파일을
                  업로드하여 점수와 개선 항목을
                  확인하세요.
                </p>
              </div>
            </header>

            <form
              className="analysis-form"
              onSubmit={handleAnalysisSubmit}
            >
              <label
                className="file-upload-box"
                htmlFor="analysis-files"
              >
                <strong>엑셀 파일 선택</strong>

                <span>
                  .xlsx 파일을 한 개 이상 선택할 수
                  있습니다.
                </span>

                <input
                  ref={fileInputRef}
                  id="analysis-files"
                  type="file"
                  accept=".xlsx"
                  multiple
                  onChange={handleFileChange}
                  disabled={isAnalyzing}
                />
              </label>

              {selectedFiles.length > 0 && (
                <div className="selected-file-list">
                  <strong>
                    선택된 파일 {selectedFiles.length}개
                  </strong>

                  <ul>
                    {selectedFiles.map((file) => (
                      <li
                        key={`${file.name}-${file.size}`}
                      >
                        {file.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="analysis-button-group">
                <button
                  type="submit"
                  className="analysis-submit-button"
                  disabled={
                    isAnalyzing ||
                    selectedFiles.length === 0
                  }
                >
                  {isAnalyzing
                    ? "분석 중..."
                    : "상품 분석 시작"}
                </button>

                <button
                  type="button"
                  className="analysis-reset-button"
                  onClick={handleAnalysisReset}
                  disabled={isAnalyzing}
                >
                  초기화
                </button>
              </div>
            </form>

            {analysisError && (
              <div className="error-message">
                {analysisError}
              </div>
            )}

            {analysisMessage && (
              <div className="analysis-success-message">
                {analysisMessage}
              </div>
            )}

            <div className="analysis-result-list">
              {analysisResults.map(
                (result, index) => (
                  <AnalysisResultCard
                    key={
                      `${result.product_name}-${result.row_index}-${index}`
                    }
                    result={result}
                    index={index}
                  />
                )
              )}
            </div>

            {!isAnalyzing &&
              analysisResults.length === 0 && (
                <div className="analysis-empty-state">
                  <h3>분석 결과가 없습니다.</h3>

                  <p>
                    엑셀 파일을 선택한 뒤 상품 분석
                    시작 버튼을 눌러주세요.
                  </p>
                </div>
              )}
          </section>

          <section className="chat-container">
            <header className="chat-header">
              <div>
                <span className="section-label">
                  LEGAL CHATBOT
                </span>

                <h2>온라인 쇼핑 법률 챗봇</h2>

                <p>
                  반품, 환불, 판매자 정보 등 온라인
                  쇼핑 관련 질문을 입력해주세요.
                </p>
              </div>

              <button
                type="button"
                className="new-chat-button"
                onClick={handleNewChat}
                disabled={
                  isLoading ||
                  messages.length === 0
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

                    <h3>무엇이 궁금한가요?</h3>

                    <p>
                      아래 입력창에 온라인 쇼핑 관련
                      질문을 입력해주세요.
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
                    className={
                      `message-row ${message.role}`
                    }
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

                      {message.role ===
                        "assistant" && (
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

              {chatError && (
                <div className="error-message">
                  {chatError}
                </div>
              )}

              <form
                className="question-form"
                onSubmit={handleChatSubmit}
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
              제공되는 답변은 일반적인 법률
              정보이며, 구체적인 분쟁은 관련
              기관이나 전문가의 확인이 필요할 수
              있습니다.
            </p>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;