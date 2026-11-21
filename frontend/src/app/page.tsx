

"use client";

import { useState, useRef } from "react";

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

const categories = [
  {
    title: "Agriculture",
    description: "Farming, crops, pests & weather guidance",
    icon: "🌾",
    color: "agriculture",
  },
  {
    title: "Healthcare",
    description: "Health information & healthcare guidance",
    icon: "🩺",
    color: "healthcare",
  },
  {
    title: "Education",
    description: "Scholarships, learning & educational support",
    icon: "📚",
    color: "education",
  },
  {
    title: "Government Schemes",
    description: "Benefits, eligibility & application guidance",
    icon: "🏛️",
    color: "schemes",
  },
];

export default function Home() {
  const [language, setLanguage] = useState("Telugu");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [question, setQuestion] = useState("");
  const [voiceMessage, setVoiceMessage] = useState("");
  const [isListening, setIsListening] = useState(false);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

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

    recognition.lang =
      language === "Telugu"
        ? "te-IN"
        : language === "Hindi"
          ? "hi-IN"
          : "en-IN";

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
          <option value="Telugu">తెలుగు</option>
          <option value="English">English</option>
          <option value="Hindi">हिन्दी</option>
        </select>
      </header>

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
            className="voice-button"
            onClick={startVoiceInput}
            aria-label={isListening ? "Stop listening" : "Speak your question"}
          >
            <span className="mic-icon">
              {isListening ? "🔴" : "🎙️"}
            </span>
            <span>
              <strong>
                {isListening ? "Listening..." : "Speak your question"}
              </strong>
              <small>
                {isListening
                  ? "Tap to stop recording"
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
              onClick={() => setSelectedCategory(category.title)}
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
            <button onClick={() => setSelectedCategory("")}>Change</button>
          </div>
        )}
      </section>

      {/* Question input */}
      <section className="question-section">
        <div className="question-box">
          <div className="question-icon">💬</div>

          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question here..."
            aria-label="Type your question"
          />

          <button
            className="send-button"
            disabled={!question.trim()}
            onClick={() => {
              if (question.trim()) {
                alert(
                  "Your question is ready for backend integration. We will connect the AI next!"
                );
              }
            }}
          >
            Send <span>➤</span>
          </button>
        </div>

        <p className="question-hint">
          You can type in Telugu, Hindi, or English
        </p>
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <span>🌿 AI Grama Sahayak</span>
        <span>Simple • Trusted • Accessible</span>
      </footer>
    </main>
  );
}
