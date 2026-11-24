"use client";

import { useState, useRef, useEffect } from "react";
import {
  sendChatMessage,
  Source,
  ApiException,
} from "../services/api";
import DocumentAnalysis from "../components/DocumentAnalysis";
import NearbyServices from "../components/NearbyServices";
import GrievanceDrafting from "../components/GrievanceDrafting";
import AudioSpeakButton from "../components/AudioSpeakButton";
import SchemeEligibility from "../components/SchemeEligibility";

type SpeechRecognitionAlternativeLike = {
  transcript: string;
};

type SpeechRecognitionResultLike = {
  0: SpeechRecognitionAlternativeLike;
};

type SpeechRecognitionEventLike = {
  results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionErrorLike = {
  error: string;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

type WindowWithSpeechRecognition = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

type ChatMessage = {
  id: number;
  sender: "user" | "assistant";
  text: string;
  sources?: Source[];
  safetyNotice?: string | null;
  followUps?: string[];
  isError?: boolean;
};

const categories = [
  {
    title: "Agriculture",
    assistantId: "agriculture" as const,
    description: "Farming, crops, pests & weather guidance",
    icon: "🌾",
    color: "agriculture",
  },
  {
    title: "Healthcare",
    assistantId: "healthcare" as const,
    description: "Health information & healthcare guidance",
    icon: "🩺",
    color: "healthcare",
  },
  {
    title: "Education",
    assistantId: "education" as const,
    description: "Scholarships, learning & educational support",
    icon: "📚",
    color: "education",
  },
  {
    title: "Government Schemes",
    assistantId: "schemes" as const,
    description: "Benefits, eligibility & application guidance",
    icon: "🏛️",
    color: "schemes",
  },
];

type ActiveTab = "chat" | "documents" | "services" | "grievances";

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat");
  const [language, setLanguage] = useState("Telugu");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [showEligibility, setShowEligibility] = useState(false);
  const [question, setQuestion] = useState("");
  const [voiceMessage, setVoiceMessage] = useState("");
  const [isListening, setIsListening] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [backendNotice, setBackendNotice] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const lastFailedMessageRef = useRef<string | null>(null);
  const messageIdCounterRef = useRef(1);

  // Automatically scroll to the latest chat content
  useEffect(() => {
    if (activeTab === "chat") {
      chatEndRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, isThinking, activeTab]);

  // Clean up any in-flight requests when the component unmounts
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Browser Speech Recognition (Web Speech API).
   * Note: Browser SpeechRecognition may use browser/vendor network services
   * (e.g. Google speech servers in Chrome) and is not guaranteed to operate offline.
   */
  const startVoiceInput = () => {
    const browserWindow = window as WindowWithSpeechRecognition;

    const SpeechRecognitionAPI =
      browserWindow.SpeechRecognition ||
      browserWindow.webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      setVoiceMessage(
        "Speech recognition is not supported in this browser. Please try Google Chrome."
      );
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognitionAPI();

    recognition.lang = language === "Telugu" ? "te-IN" : "en-IN";

    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceMessage("Listening... Speak your question now 🎤");
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;

      setQuestion(transcript);
      setVoiceMessage("Your speech was converted to text successfully! ✓");
    };

    recognition.onerror = (event) => {
      setIsListening(false);

      if (event.error === "not-allowed") {
        setVoiceMessage(
          "Microphone permission denied. Please allow microphone access in your browser."
        );
      } else if (event.error === "no-speech") {
        setVoiceMessage(
          "No speech detected. Please tap the microphone and try again."
        );
      } else if (event.error === "network") {
        setVoiceMessage(
          "Network error occurred during speech recognition. Please try again."
        );
      } else {
        setVoiceMessage(
          "Something went wrong with voice recognition. Please try again."
        );
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch {
      setIsListening(false);
      setVoiceMessage("Unable to start microphone. Please try again.");
    }
  };

  // Map category title to backend assistant identifier
  const getAssistantId = (): "agriculture" | "healthcare" | "education" | "schemes" => {
    const match = categories.find((c) => c.title === selectedCategory);
    return match ? match.assistantId : "schemes";
  };

  // Map language to backend contract code ('te' or 'en')
  const getLanguageCode = (): "te" | "en" => {
    return language === "Telugu" ? "te" : "en";
  };

  const handleSendMessage = async (textToSend?: string) => {
    const rawQuestion = textToSend || question;
    const trimmedQuestion = rawQuestion.trim();

    if (!trimmedQuestion || isThinking) return;

    // Abort previous in-flight request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const userMessage: ChatMessage = {
      id: messageIdCounterRef.current++,
      sender: "user",
      text: trimmedQuestion,
    };

    setMessages((previousMessages) => [
      ...previousMessages,
      userMessage,
    ]);

    setQuestion("");
    setVoiceMessage("");
    setIsThinking(true);
    setBackendNotice(null);
    lastFailedMessageRef.current = null;

    try {
      const response = await sendChatMessage(
        {
          message: trimmedQuestion,
          assistant: getAssistantId(),
          language: getLanguageCode(),
          state: "Andhra Pradesh",
          conversation_id: conversationIdRef.current,
        },
        controller.signal
      );

      // Verify request wasn't cancelled by New Chat
      if (controller.signal.aborted) return;

      // Update multi-turn conversation ID
      if (response.conversation_id) {
        conversationIdRef.current = response.conversation_id;
      }

      const assistantMessage: ChatMessage = {
        id: messageIdCounterRef.current++,
        sender: "assistant",
        text: response.answer,
        sources: response.sources || [],
        safetyNotice: response.safety_notice || null,
        followUps: response.follow_up_questions || [],
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);
    } catch (err: unknown) {
      if (controller.signal.aborted) {
        // Request was intentionally cancelled (e.g., New Chat)
        return;
      }

      lastFailedMessageRef.current = trimmedQuestion;

      let errorNotice = "";
      if (err instanceof ApiException) {
        errorNotice = `API Error [${err.code}]: ${err.message}`;
      } else {
        errorNotice =
          language === "Telugu"
            ? "బ్యాకెండ్ చాట్ సర్వరు అందుబాటులో లేదు (/api/chat). (Member 1 చాట్ ఆర్కెస్ట్రేషన్ అభివృద్ధి చేస్తున్నారు)."
            : "Backend chat service is unreachable at /api/chat. (Member 1 develops this endpoint).";
      }

      setBackendNotice(errorNotice);

      // Honest service-unavailable message — no fake answers or fabricated advice!
      const unavailableMessage: ChatMessage = {
        id: messageIdCounterRef.current++,
        sender: "assistant",
        text:
          language === "Telugu"
            ? "క్షమించండి, గ్రామ సహాయక్ చాట్ సర్వీస్ ప్రస్తుతం అందుబాటులో లేదు (/api/chat). దయచేసి కాసేపటి తర్వాత 'మళ్లీ ప్రయత్నించండి' బటన్ నొక్కండి."
            : "The Grama Sahayak chat service is currently unavailable (/api/chat). Please try again in a few moments using the Retry button.",
        isError: true,
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        unavailableMessage,
      ]);
    } finally {
      setIsThinking(false);
      abortControllerRef.current = null;
    }
  };

  // Start a fresh conversation and cancel any pending response
  const handleNewChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    conversationIdRef.current = null;
    lastFailedMessageRef.current = null;
    setMessages([]);
    setIsThinking(false);
    setQuestion("");
    setVoiceMessage("");
    setBackendNotice(null);
  };

  const handleRetry = () => {
    if (lastFailedMessageRef.current) {
      const retryText = lastFailedMessageRef.current;
      handleSendMessage(retryText);
    }
  };

  return (
    <main className="home-container">
      {/* Header */}
      <header className="site-header">
        <div className="brand">
          <div className="brand-icon">🌿</div>
          <div>
            <h1>AI Grama Sahayak</h1>
            <p>Your trusted digital assistant</p>
          </div>
        </div>

        <select
          className="language-select"
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setVoiceMessage("");
          }}
          aria-label="Select language"
        >
          <option value="Telugu">తెలుగు (Telugu)</option>
          <option value="English">English</option>
        </select>
      </header>

      {/* Navigation Tabs for Services */}
      <nav className="portal-nav" aria-label="Portal Services">
        <button
          className={`nav-tab ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          <span className="nav-tab-icon">💬</span>
          <span>{language === "Telugu" ? "సహాయక్ చాట్" : "Sahayak Chat"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "documents" ? "active" : ""}`}
          onClick={() => setActiveTab("documents")}
        >
          <span className="nav-tab-icon">📄</span>
          <span>{language === "Telugu" ? "పత్రాల విశ్లేషణ" : "Document Analysis"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "services" ? "active" : ""}`}
          onClick={() => setActiveTab("services")}
        >
          <span className="nav-tab-icon">📍</span>
          <span>{language === "Telugu" ? "సమీప ప్రభుత్వ సేవలు" : "Nearby Services"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "grievances" ? "active" : ""}`}
          onClick={() => setActiveTab("grievances")}
        >
          <span className="nav-tab-icon">📝</span>
          <span>{language === "Telugu" ? "ఫిర్యాదు ముసాయిదా" : "Draft Grievance"}</span>
        </button>
      </nav>

      {/* View: Document Analysis */}
      {activeTab === "documents" && <DocumentAnalysis language={language} />}

      {/* View: Nearby Services */}
      {activeTab === "services" && <NearbyServices language={language} />}

      {/* View: Grievances */}
      {activeTab === "grievances" && <GrievanceDrafting language={language} />}

      {/* View: Chat (Default Homepage Experience) */}
      {activeTab === "chat" && (
        <>
          {/* Hero */}
          <section className="hero">
            <div className="hero-content">
              <span className="welcome-tag">YOUR DIGITAL VILLAGE ASSISTANT</span>

              <h2>
                How can we help
                <br />
                <span>you today?</span>
              </h2>

              <p>
                Ask anything. Get trusted guidance in your own language.
                Simple, accessible help for everyone.
              </p>

              <button
                className={`voice-button ${isListening ? "listening" : ""}`}
                onClick={startVoiceInput}
                aria-label={isListening ? "Stop listening" : "Speak your question"}
              >
                <span className="mic-icon">
                  {isListening ? (
                    <span className="recording-indicator" aria-hidden="true">
                      <span className="recording-wave-bar"></span>
                      <span className="recording-wave-bar"></span>
                      <span className="recording-wave-bar"></span>
                    </span>
                  ) : (
                    "🎙️"
                  )}
                </span>
                <span>
                  <strong>
                    {isListening
                      ? language === "Telugu"
                        ? "రికార్డింగ్ అవుతోంది... మాట్లాడండి"
                        : "Listening... Speak now"
                      : language === "Telugu"
                        ? "మీ ప్రశ్నను మాట్లాడండి"
                        : "Speak your question"}
                  </strong>
                  <small>
                    {isListening
                      ? language === "Telugu"
                        ? "రికార్డింగ్ ఆపడానికి తాకండి"
                        : "Tap to stop recording"
                      : language === "Telugu"
                        ? "వాయిస్ ఉపయోగించి అడగడానికి తాకండి"
                        : "Tap to ask using your voice"}
                  </small>
                </span>
              </button>

              {voiceMessage && (
                <p className="voice-notice" role="status">
                  {voiceMessage}
                </p>
              )}
            </div>

            <div className="hero-decoration" aria-hidden="true">
              <span>🌱</span>
              <span>🌾</span>
              <span>🍃</span>
            </div>
          </section>

          {/* Categories */}
          <section className="assistance-section">
            <div className="section-heading">
              <div>
                <span className="section-label">HERE TO HELP</span>
                <h2>What do you need help with?</h2>
              </div>
              <p>Choose a category to get started</p>
            </div>

            <div className="category-grid">
              {categories.map((category) => (
                <button
                  key={category.title}
                  className={`category-card ${category.color} ${
                    selectedCategory === category.title ? "selected" : ""
                  }`}
                  onClick={() => {
                    setSelectedCategory(category.title);
                    if (category.title === "Government Schemes") {
                      setShowEligibility(true);
                    } else {
                      setShowEligibility(false);
                    }
                  }}
                >
                  <div className="category-icon">{category.icon}</div>

                  <div className="category-text">
                    <h3>{category.title}</h3>
                    <p>{category.description}</p>
                  </div>

                  <span className="card-arrow">→</span>
                </button>
              ))}
            </div>

            {selectedCategory && (
              <div className="selected-category-message">
                <span>✓</span>
                <p>
                  <strong>{selectedCategory}</strong> selected. You can now ask your
                  question below.
                </p>
                <button
                  onClick={() => {
                    setSelectedCategory("");
                    setShowEligibility(false);
                  }}
                >
                  Change
                </button>
              </div>
            )}

            {/* Quick Action: Check Scheme Eligibility */}
            <div className="quick-action-row">
              <button
                type="button"
                className={`quick-eligibility-btn ${selectedCategory === "Government Schemes" && showEligibility ? "active" : ""}`}
                onClick={() => {
                  if (selectedCategory === "Government Schemes" && showEligibility) {
                    setShowEligibility(false);
                  } else {
                    setSelectedCategory("Government Schemes");
                    setShowEligibility(true);
                  }
                }}
              >
                <span>📋</span>
                <span>
                  {language === "Telugu"
                    ? "పథకం అర్హతను తనిఖీ చేయండి (Check Eligibility)"
                    : "Check Scheme Eligibility"}
                </span>
                <span>{selectedCategory === "Government Schemes" && showEligibility ? "▲" : "▼"}</span>
              </button>
            </div>

            {/* Dedicated Eligibility Evaluation View within Government Schemes */}
            {(selectedCategory === "Government Schemes" && showEligibility) && (
              <div className="embedded-eligibility-section">
                <SchemeEligibility language={language} />
              </div>
            )}
          </section>

          {/* Chat conversation */}
          {messages.length > 0 && (
            <section className="chat-section">
              <div className="chat-heading">
                <div>
                  <span className="section-label">YOUR CONVERSATION</span>
                  <h2>Chat with Grama Sahayak</h2>
                </div>

                <button
                  className="new-chat-button"
                  onClick={handleNewChat}
                >
                  + New Chat
                </button>
              </div>

              <div className="chat-messages">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`chat-message ${
                      message.sender === "user"
                        ? "user-message"
                        : "assistant-message"
                    }`}
                  >
                    <div className="message-avatar">
                      {message.sender === "user" ? "👤" : "🌿"}
                    </div>

                    <div className="message-content">
                      <span className="message-sender">
                        {message.sender === "user"
                          ? "You"
                          : "Grama Sahayak"}
                      </span>

                      <p>{message.text}</p>

                      {/* Safety Notice */}
                      {message.safetyNotice && (
                        <div className="safety-notice-box" role="alert">
                          <span>⚠️</span>
                          <div>
                            <strong>Advisory: </strong>
                            <span>{message.safetyNotice}</span>
                          </div>
                        </div>
                      )}

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="sources-container">
                          <span className="sources-title">
                            {language === "Telugu" ? "అధికారిక ఆధారాలు:" : "Official Sources:"}
                          </span>
                          <div className="sources-list">
                            {message.sources.map((src, sIdx) => (
                              <div key={sIdx} className="source-item">
                                <span>🏛️</span>
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="source-link"
                                >
                                  {src.title}
                                </a>
                                {src.publisher && (
                                  <span className="source-meta">({src.publisher})</span>
                                )}
                                {src.verified_at && (
                                  <span className="source-meta">
                                    {" "}• {language === "Telugu" ? `ధృవీకరించబడింది: ${src.verified_at}` : `Verified: ${src.verified_at}`}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-up Questions */}
                      {message.followUps && message.followUps.length > 0 && (
                        <div className="follow-up-container">
                          <span className="follow-up-title">
                            {language === "Telugu" ? "సూచించిన ప్రశ్నలు:" : "Suggested Questions:"}
                          </span>
                          <div className="follow-up-chips">
                            {message.followUps.map((fq, fIdx) => (
                              <button
                                key={fIdx}
                                className="follow-up-chip"
                                onClick={() => handleSendMessage(fq)}
                              >
                                {fq} →
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Voice Audio Listen Button (Member 3) */}
                      {message.sender === "assistant" && !message.isError && (
                        <AudioSpeakButton text={message.text} language={language} />
                      )}

                      {/* Retry Button on Error */}
                      {message.isError && (
                        <button className="retry-button" onClick={handleRetry}>
                          ↻ {language === "Telugu" ? "మళ్లీ ప్రయత్నించండి" : "Retry"}
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                {isThinking && (
                  <div className="chat-message assistant-message thinking-message">
                    <div className="message-avatar">🌿</div>

                    <div className="message-content">
                      <span className="message-sender">Grama Sahayak</span>
                      <p className="thinking-text">
                        Thinking<span className="thinking-dots">...</span>
                      </p>
                    </div>
                  </div>
                )}

                {/* Automatic scroll target */}
                <div ref={chatEndRef} />
              </div>

              {backendNotice ? (
                <p className="demo-notice" style={{ color: "#b94a48" }}>
                  ℹ️ {backendNotice}
                </p>
              ) : (
                <p className="demo-notice">
                  AI Grama Sahayak • Integrated with verified public information and government schemes.
                </p>
              )}
            </section>
          )}

          {/* Question input */}
          <section className="question-section">
            <div className="question-box">
              <div className="question-icon">💬</div>

              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSendMessage();
                  }
                }}
                placeholder={
                  language === "Telugu"
                    ? "మీ ప్రశ్నను ఇక్కడ నమోదు చేయండి..."
                    : "Type your question here..."
                }
                aria-label="Type your question"
              />

              <button
                className="send-button"
                disabled={!question.trim() || isThinking}
                onClick={() => handleSendMessage()}
              >
                {isThinking ? "..." : "Send"} <span>➤</span>
              </button>
            </div>

            <p className="question-hint">
              {language === "Telugu"
                ? "మీరు తెలుగు లేదా ఇంగ్లీషులో టైప్ చేయవచ్చు"
                : "You can type in Telugu or English"}
            </p>
          </section>
        </>
      )}

      {/* Footer */}
      <footer className="site-footer">
        <span>🌿 AI Grama Sahayak</span>
        <span>Simple • Trusted • Accessible</span>
      </footer>
    </main>
  );
}
