

"use client";

import { useState, useRef, useEffect } from "react";

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

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  // Reference to the bottom of the chat
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Reference to the pending mock AI response timer
  const responseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Automatically scroll to the latest chat content
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isThinking]);

  // Clear any pending response timer when the component unmounts
  useEffect(() => {
    return () => {
      if (responseTimerRef.current !== null) {
        clearTimeout(responseTimerRef.current);
      }
    };
  }, []);

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

  // Temporary mock AI responses until backend integration
  const getMockResponse = () => {
    if (language === "Telugu") {
      return `మీ ప్రశ్న అందింది! 🙏

${
  selectedCategory
    ? `${selectedCategory} విభాగానికి సంబంధించిన మీ ప్రశ్నను మేము గుర్తించాము.`
    : "మీ ప్రశ్నను మేము గుర్తించాము."
}

ఇది ప్రస్తుతం డెమో సమాధానం మాత్రమే. నిజమైన AI సహాయకుడిని త్వరలో అనుసంధానిస్తాము. మరింత ఖచ్చితమైన సమాచారం కోసం మీ ప్రశ్నకు సంబంధించిన వివరాలను తెలియజేయండి.`;
    }

    if (language === "Hindi") {
      return `आपका प्रश्न प्राप्त हुआ! 🙏

${
  selectedCategory
    ? `हमने आपके ${selectedCategory} से संबंधित प्रश्न को पहचाना है।`
    : "हमने आपका प्रश्न समझ लिया है।"
}

यह अभी एक डेमो उत्तर है। वास्तविक AI सहायक जल्द ही जोड़ा जाएगा। अधिक सटीक जानकारी के लिए कृपया अपने प्रश्न के बारे में कुछ और विवरण दें।`;
    }

    return `Your question has been received! 🙏

${
  selectedCategory
    ? `We have identified your question under ${selectedCategory}.`
    : "We have received your question."
}

This is currently a demo response. The real AI assistant will be connected soon. Please provide a little more detail about your question for more specific guidance.`;
  };

  const handleSendMessage = () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isThinking) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
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

    // Simulate AI response delay and store the timer
    responseTimerRef.current = setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: "assistant",
        text: getMockResponse(),
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

      setIsThinking(false);

      // Timer has completed
      responseTimerRef.current = null;
    }, 1500);
  };

  // Start a fresh conversation and cancel any pending response
  const handleNewChat = () => {
    if (responseTimerRef.current !== null) {
      clearTimeout(responseTimerRef.current);
      responseTimerRef.current = null;
    }

    setMessages([]);
    setIsThinking(false);
    setQuestion("");
    setVoiceMessage("");
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

          <p className="demo-notice">
            Demo mode — responses are mock responses, not verified guidance.
          </p>
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
            placeholder="Type your question here..."
            aria-label="Type your question"
          />

          <button
            className="send-button"
            disabled={!question.trim() || isThinking}
            onClick={handleSendMessage}
          >
            {isThinking ? "..." : "Send"} <span>➤</span>
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
