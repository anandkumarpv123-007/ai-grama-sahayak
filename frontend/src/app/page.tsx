"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  sendChatMessage,
  transcribeAudio,
  Source,
  ApiException,
} from "../services/api";
import { getSupportedMimeType, formatDuration } from "../services/voiceUtils";
import {
  ConnectivityState,
  subscribeConnectivity,
  probeBackendHealth,
} from "../services/connectivity";
import { findOfflinePublicInfo } from "../services/offlineKnowledge";
import {
  SavedQuestion,
  getSavedQuestions,
  saveQuestionForLater,
} from "../services/savedQuestions";
import DocumentAnalysis from "../components/DocumentAnalysis";
import NearbyServices from "../components/NearbyServices";
import GrievanceDrafting from "../components/GrievanceDrafting";
import AudioSpeakButton from "../components/AudioSpeakButton";
import SchemeEligibility from "../components/SchemeEligibility";
import SafeMarkdown from "../components/SafeMarkdown";
import LowNetworkBanner from "../components/LowNetworkBanner";

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
  isCached?: boolean;
};

interface SpecialistAssistant {
  id: "agriculture" | "healthcare" | "education" | "schemes";
  title: string;
  titleEn: string;
  titleTe: string;
  descriptionEn: string;
  descriptionTe: string;
  icon: string;
  color: string;
  badgeEn: string;
  badgeTe: string;
  suggestedQuestionsEn: string[];
  suggestedQuestionsTe: string[];
}

const SPECIALIST_ASSISTANTS: SpecialistAssistant[] = [
  {
    id: "schemes",
    title: "Government Schemes",
    titleEn: "Government Welfare Schemes",
    titleTe: "ప్రభుత్వ సంక్షేమ పథకాలు",
    descriptionEn: "Old-age pensions, farmer income support, healthcare coverage & welfare eligibility",
    descriptionTe: "వృద్ధాప్య పింఛన్లు, రైతు భరోసా, ఆరోగ్యశ్రీ & సంక్షేమ పథకాల అర్హత పరిశీలన",
    icon: "🏛️",
    color: "schemes",
    badgeEn: "Direct Benefit Transfers",
    badgeTe: "ప్రత్యక్ష నగదు బదిలీ",
    suggestedQuestionsEn: [
      "Who is eligible for NTR Bharosa Old Age Pension?",
      "How to complete PM-KISAN e-KYC?",
      "What are the benefits of Dr. NTR Vaidya Seva?",
    ],
    suggestedQuestionsTe: [
      "ఎన్టీఆర్ భరోసా వృద్ధాప్య పింఛనుకు ఎవరు అర్హులు?",
      "పీఎం-కిసాన్ ఈ-కేవైసీ ఎలా పూర్తి చేయాలి?",
      "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ ప్రయోజనాలు ఏమిటి?",
    ],
  },
  {
    id: "agriculture",
    title: "Agriculture",
    titleEn: "Agriculture & Farming Support",
    titleTe: "వ్యవసాయం & సాగుబడి సమాచారం",
    descriptionEn: "Crop protection, pest management, weather updates & Rythu Bharosa Kendrams",
    descriptionTe: "పంటల రక్షణ, తెగుళ్ళ నివారణ, వాతావరణ సమాచారం & రైతు భరోసా కేంద్రాలు (RBK)",
    icon: "🌾",
    color: "agriculture",
    badgeEn: "Farmer Advisories",
    badgeTe: "రైతు సలహాలు",
    suggestedQuestionsEn: [
      "How to prevent blast disease in paddy crop?",
      "What services are offered at Rythu Bharosa Kendram (RBK)?",
      "What are the seasonal MSP procurement guidelines?",
    ],
    suggestedQuestionsTe: [
      "వరి పంటలో అగ్గితెగులు మరియు కాండం తొలుచు పురుగు నివారణ ఎలా?",
      "రైతు భరోసా కేంద్రం (RBK) ద్వారా ఎలాంటి సేవలు అందుతాయి?",
      "ప్రభుత్వ కనీస మద్దతు ధర (MSP) వివరాలు ఏమిటి?",
    ],
  },
  {
    id: "healthcare",
    title: "Healthcare",
    titleEn: "Healthcare & Aarogyasri Guidance",
    titleTe: "ఆరోగ్యం & ఆరోగ్యశ్రీ సహాయం",
    descriptionEn: "Cashless hospital treatments, PHC locator, maternal care & health cards",
    descriptionTe: "ఆసుపత్రుల్లో ఉచిత నగదు రహిత చికిత్స, పీహెచ్‌సీలు & ఆరోగ్యశ్రీ కార్డు సమాచారం",
    icon: "🩺",
    color: "healthcare",
    badgeEn: "Health Services",
    badgeTe: "ఆరోగ్య సేవలు",
    suggestedQuestionsEn: [
      "Which treatments are covered under Dr. NTR Vaidya Seva?",
      "Where is the nearest Government Hospital or PHC?",
      "How to avail maternal health benefits under government schemes?",
    ],
    suggestedQuestionsTe: [
      "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద ఏయే చికిత్సలు ఉచితంగా లభిస్తాయి?",
      "సమీప ప్రభుత్వ ఆసుపత్రి లేదా ప్రాథమిక ఆరోగ్య కేంద్రం ఎక్కడ ఉంది?",
      "తల్లి మరియు బిడ్డ సంక్షేమ పథకాల వివరాలు ఏమిటి?",
    ],
  },
  {
    id: "education",
    title: "Education",
    titleEn: "Education & Skilling Support",
    titleTe: "విద్య & నైపుణ్యాభివృద్ధి",
    descriptionEn: "Student scholarships, school admissions, fee reimbursement & skilling courses",
    descriptionTe: "విద్యార్థి వేతనాలు, పాఠశాల ప్రవేశాలు, ఫీజు రీయింబర్స్‌మెంట్ & నైపుణ్య శిక్షణ",
    icon: "📚",
    color: "education",
    badgeEn: "Scholarships & Schools",
    badgeTe: "స్కాలర్‌షిప్‌లు & విద్య",
    suggestedQuestionsEn: [
      "What are the guidelines for Thalliki Vandanam / Amma Vodi?",
      "How to apply for post-matric student scholarships in AP?",
      "What free technical skill training programs are offered by APSSDC?",
    ],
    suggestedQuestionsTe: [
      "తల్లికి వందనం / జగనన్న అమ్మ ఒడి మార్గదర్శకాలు ఏమిటి?",
      "పోస్ట్ మెట్రిక్ స్కాలర్‌షిప్ కొరకు ఎలా దరఖాస్తు చేసుకోవాలి?",
      "APSSDC ద్వారా అందుబాటులో ఉన్న ఉచిత నైపుణ్య కోర్సులు ఏమిటి?",
    ],
  },
];

type ActiveTab = "chat" | "documents" | "services" | "grievances";

export type VoiceRecordingState =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "transcribing"
  | "transcribed"
  | "cancelled"
  | "error";

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat");
  const [language, setLanguage] = useState("Telugu");
  const isTe = language === "Telugu";

  const [selectedCategory, setSelectedCategory] = useState<string>("schemes");
  const [showEligibility, setShowEligibility] = useState(false);
  const [question, setQuestion] = useState("");
  const [voiceMessage, setVoiceMessage] = useState("");
  const [recordingState, setRecordingState] = useState<VoiceRecordingState>("idle");
  const [recordingDuration, setRecordingDuration] = useState(0);

  const isListening = recordingState === "recording" || recordingState === "requesting_permission";

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [backendNotice, setBackendNotice] = useState<string | null>(null);

  // Connectivity and Saved Questions State (Tasks 1, 2, 3)
  const [connectivity, setConnectivity] = useState<ConnectivityState>({
    status: "online",
    isBrowserOnline: true,
    isBackendReachable: true,
    lastChecked: new Date().toISOString(),
  });
  const [savedQuestions, setSavedQuestions] = useState<SavedQuestion[]>(() => {
    return getSavedQuestions();
  });
  const [savedActionToast, setSavedActionToast] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const maxDurationTimerRef = useRef<NodeJS.Timeout | null>(null);
  const voiceAbortControllerRef = useRef<AbortController | null>(null);
  const voiceRequestSeqRef = useRef<number>(0);
  const isVoiceCancelledRef = useRef<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const lastFailedMessageRef = useRef<string | null>(null);
  const messageIdCounterRef = useRef(1);

  const refreshSavedQuestions = useCallback(() => {
    setSavedQuestions(getSavedQuestions());
  }, []);

  // Initialize Connectivity subscription, health probe, and Service Worker
  useEffect(() => {
    const unsubscribe = subscribeConnectivity((state) => {
      setConnectivity(state);
    });

    // Initial probe and periodic 25s probe
    probeBackendHealth();
    const interval = setInterval(() => {
      probeBackendHealth();
    }, 25000);

    // Register Service Worker for offline shell caching (Task 2)
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Ignored if service worker is unsupported or restricted
      });
    }

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [refreshSavedQuestions]);

  // Automatically scroll to the latest chat content
  useEffect(() => {
    if (activeTab === "chat" && messages.length > 0) {
      chatEndRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, isThinking, activeTab]);

  // Clean up media tracks to turn off hardware microphone indicator
  const cleanupMediaStream = useCallback(() => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore
        }
      });
      mediaStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
  }, []);

  const clearRecordingTimers = useCallback(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (maxDurationTimerRef.current) {
      clearTimeout(maxDurationTimerRef.current);
      maxDurationTimerRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupMediaStream();
      clearRecordingTimers();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // ignore
        }
      }
      if (voiceAbortControllerRef.current) {
        voiceAbortControllerRef.current.abort();
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [cleanupMediaStream, clearRecordingTimers]);

  // Fallback: Browser Web Speech API
  const startBrowserSpeechRecognitionFallback = () => {
    const windowWithSpeech = window as WindowWithSpeechRecognition;
    const SpeechRecognition =
      windowWithSpeech.SpeechRecognition ||
      windowWithSpeech.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setRecordingState("error");
      setVoiceMessage(
        isTe
          ? "మీ బ్రౌజర్‌లో వాయిస్ రికార్డింగ్ సదుపాయం అందుబాటులో లేదు. దయచేసి టైప్ చేయండి."
          : "Voice recognition is not supported in this browser. Please type your query."
      );
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = isTe ? "te-IN" : "en-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setRecordingState("recording");
        setRecordingDuration(0);
        setVoiceMessage(
          isTe
            ? "బ్రౌజర్ వాయిస్ రికార్డింగ్ ప్రారంభమైంది... మాట్లాడండి."
            : "Listening via device microphone... Please speak now."
        );

        recordingTimerRef.current = setInterval(() => {
          setRecordingDuration((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event: SpeechRecognitionEventLike) => {
        clearRecordingTimers();
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setQuestion(transcript);
          setRecordingState("transcribed");
          setVoiceMessage(
            isTe
              ? `గుర్తించబడిన ప్రశ్న: "${transcript}"`
              : `Captured query: "${transcript}"`
          );
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorLike) => {
        clearRecordingTimers();
        setRecordingState("error");
        if (event.error === "not-allowed") {
          setVoiceMessage(
            isTe
              ? "మైక్రోఫోన్ అనుమతి నిరాకరించబడింది. దయచేసి బ్రౌజర్ అనుమతులు ఇవ్వండి."
              : "Microphone permission denied. Please allow microphone access in your browser."
          );
        } else if (event.error === "no-speech") {
          setVoiceMessage(
            isTe
              ? "ఎలాంటి శబ్దం గుర్తించబడలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి."
              : "No speech detected. Please speak closer to your microphone."
          );
        } else {
          setVoiceMessage(
            isTe
              ? `వాయిస్ గుర్తింపు లోపం: ${event.error}`
              : `Voice error: ${event.error}`
          );
        }
      };

      recognition.onend = () => {
        clearRecordingTimers();
        setRecordingState((prev) => (prev === "recording" ? "idle" : prev));
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setRecordingState("error");
      setVoiceMessage(
        isTe
          ? "మైక్రోఫోన్ ప్రారంభించడంలో సమస్య ఏర్పడింది."
          : "Could not initialize microphone."
      );
    }
  };

  const cancelVoiceInput = () => {
    isVoiceCancelledRef.current = true;
    voiceRequestSeqRef.current += 1;

    if (voiceAbortControllerRef.current) {
      voiceAbortControllerRef.current.abort();
      voiceAbortControllerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
    }

    cleanupMediaStream();
    clearRecordingTimers();
    audioChunksRef.current = [];
    setRecordingState("cancelled");
    setRecordingDuration(0);
    setVoiceMessage(isTe ? "వాయిస్ రికార్డింగ్ రద్దు చేయబడింది." : "Voice recording cancelled.");
  };

  // Main voice input handler (Task 4: Graceful Degradation)
  const startVoiceInput = async () => {
    if (connectivity.status === "offline") {
      setRecordingState("error");
      setVoiceMessage(
        isTe
          ? "లైవ్ వాయిస్ రికార్డింగ్ మరియు ట్రాన్స్‌క్రిప్షన్ కొరకు ఇంటర్నెట్ అవసరం. దయచేసి టైప్ చేయండి లేదా తర్వాత అడగడానికి సేవ్ చేయండి."
          : "Voice transcription requires an active internet connection. Please type your query or save it for later."
      );
      return;
    }

    if (recordingState === "recording") {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
        return;
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        return;
      }
      return;
    }

    isVoiceCancelledRef.current = false;
    setVoiceMessage("");
    setRecordingDuration(0);
    setRecordingState("requesting_permission");

    if (navigator.mediaDevices && typeof MediaRecorder !== "undefined") {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });

        if (isVoiceCancelledRef.current) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        mediaStreamRef.current = stream;
        const mimeType = getSupportedMimeType();
        const options: MediaRecorderOptions = mimeType ? { mimeType } : {};
        const recorder = new MediaRecorder(stream, options);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        recorder.onstart = () => {
          setRecordingState("recording");
          setRecordingDuration(0);
          setVoiceMessage(
            isTe
              ? "రికార్డింగ్ అవుతోంది... మీ ప్రశ్నను స్పష్టంగా మాట్లాడండి (గరిష్టంగా 30 సెకన్లు)."
              : "Recording... Speak your question clearly (max 30s)."
          );

          recordingTimerRef.current = setInterval(() => {
            setRecordingDuration((prev) => prev + 1);
          }, 1000);

          maxDurationTimerRef.current = setTimeout(() => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
              mediaRecorderRef.current.stop();
            }
          }, 30000);
        };

        recorder.onstop = async () => {
          clearRecordingTimers();
          cleanupMediaStream();

          if (isVoiceCancelledRef.current) {
            audioChunksRef.current = [];
            return;
          }

          const currentChunks = [...audioChunksRef.current];
          audioChunksRef.current = [];

          if (currentChunks.length === 0) {
            setRecordingState("error");
            setVoiceMessage(
              isTe
                ? "శబ్దం రికార్డు కాలేదు. దయచేసి మళ్ళీ మాట్లాడండి."
                : "No audio captured. Please try speaking again."
            );
            return;
          }

          const actualMime = recorder.mimeType || mimeType || "audio/webm";
          const audioBlob = new Blob(currentChunks, { type: actualMime });

          if (audioBlob.size < 100) {
            setRecordingState("error");
            setVoiceMessage(
              isTe
                ? "ఆడియో చాలా చిన్నదిగా ఉంది. దయచేసి పూర్తి ప్రశ్నను మాట్లాడండి."
                : "Audio was too short. Please speak your full question."
            );
            return;
          }

          setRecordingState("transcribing");
          setVoiceMessage(
            isTe
              ? "వాయిస్ ప్రాసెస్ అవుతోంది... దయచేసి వేచి ఉండండి."
              : "Transcribing your question with Sarvam AI..."
          );

          const seq = ++voiceRequestSeqRef.current;
          const controller = new AbortController();
          voiceAbortControllerRef.current = controller;

          try {
            const resp = await transcribeAudio(
              audioBlob,
              isTe ? "te" : "en",
              controller.signal
            );

            if (seq !== voiceRequestSeqRef.current || isVoiceCancelledRef.current) return;

            const text = resp ? resp.transcribed_text : "";
            if (text && text.trim()) {
              const cleanText = text.trim();
              setQuestion(cleanText);
              setRecordingState("transcribed");
              setVoiceMessage(
                isTe
                  ? `గుర్తించబడిన ప్రశ్న: "${cleanText}"`
                  : `Transcribed: "${cleanText}"`
              );
            } else {
              setRecordingState("error");
              setVoiceMessage(
                isTe
                  ? "వాయిస్ స్పష్టంగా గుర్తించబడలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి."
                  : "Could not transcribe audio clearly. Please try again."
              );
            }
          } catch (err: unknown) {
            if (seq !== voiceRequestSeqRef.current || isVoiceCancelledRef.current) return;
            setRecordingState("error");
            if (err instanceof ApiException && err.status === 503) {
              setVoiceMessage(
                isTe
                  ? "వాయిస్ సర్వర్ ప్రస్తుతం అందుబాటులో లేదు (503). మీరు టైప్ చేయవచ్చు."
                  : "Voice server temporarily offline (503). You can type below."
              );
            } else {
              setVoiceMessage(
                isTe
                  ? "ట్రాన్స్‌క్రిప్షన్ విఫలమైంది. దయచేసి మళ్ళీ ప్రయత్నించండి."
                  : "Transcription failed. Please try again or type your question."
              );
            }
          }
        };

        recorder.start(250);
        return;
      } catch (err: unknown) {
        cleanupMediaStream();
        clearRecordingTimers();
        const errName = err instanceof Error ? err.name : "";
        if (errName === "NotAllowedError" || errName === "PermissionDeniedError") {
          setRecordingState("error");
          setVoiceMessage(
            isTe
              ? "మైక్రోఫోన్ అనుమతి నిరాకరించబడింది. దయచేసి బ్రౌజర్ సెట్టింగ్స్‌లో అనుమతించండి."
              : "Microphone permission denied. Please allow microphone access in your browser."
          );
        } else if (errName === "NotFoundError" || errName === "DevicesNotFoundError") {
          setRecordingState("error");
          setVoiceMessage(
            isTe
              ? "మీ పరికరంలో మైక్రోఫోన్ కనుగొనబడలేదు."
              : "No microphone detected on your device."
          );
        } else {
          startBrowserSpeechRecognitionFallback();
        }
        return;
      }
    }

    startBrowserSpeechRecognitionFallback();
  };

  const getAssistantId = (): "agriculture" | "healthcare" | "education" | "schemes" => {
    const match = SPECIALIST_ASSISTANTS.find(
      (c) => c.id === selectedCategory || c.title === selectedCategory
    );
    return match ? match.id : "schemes";
  };

  const currentAssistant =
    SPECIALIST_ASSISTANTS.find((a) => a.id === selectedCategory || a.title === selectedCategory) ||
    SPECIALIST_ASSISTANTS[0];

  // Chat Submission Handler (Task 2 & Task 4: Offline Public Knowledge Match & Saved Queue)
  const handleSendMessage = async (textToSend?: string) => {
    const rawQuestion = textToSend || question;
    const trimmedQuestion = rawQuestion.trim();

    if (!trimmedQuestion || isThinking) return;

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

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setVoiceMessage("");
    setBackendNotice(null);
    lastFailedMessageRef.current = null;

    // Check low-network or offline state
    const isNetworkUnavailable =
      connectivity.status === "offline" || connectivity.status === "backend_unreachable";

    if (isNetworkUnavailable) {
      setIsThinking(true);
      setTimeout(() => {
        setIsThinking(false);

        // Check if question matches verified cached public knowledge
        const offlineMatch = findOfflinePublicInfo(trimmedQuestion);

        if (offlineMatch) {
          const cachedMarkdown = isTe
            ? `📦 **ఆఫ్‌లైన్ నిల్వ సమాచారం (${offlineMatch.titleTe})**\n\n**ప్రయోజనం:** ${offlineMatch.benefitTe}\n\n**అర్హత నిబంధనలు:**\n${offlineMatch.eligibilityTe.map((e) => `* ${e}`).join("\n")}\n\n**మినహాయింపులు:**\n${offlineMatch.exclusionsTe.map((x) => `* ${x}`).join("\n")}\n\n**దరఖాస్తు విధానం:** ${offlineMatch.procedureTe}\n\n*🕒 అధికారిక ధృవీకరణ: ${offlineMatch.verifiedDate} | స్థానిక నిల్వ: ${offlineMatch.cachedAt} | ఆధారం: ${offlineMatch.verifiedSource}*\n\n*(గమనిక: ప్రభుత్వ మార్గదర్శకాలు మారవచ్చు. నెట్‌వర్క్ పునరుద్ధరించబడిన తర్వాత గ్రామ సచివాలయంలో ప్రస్తుత అర్హతను ధృవీకరించుకోండి).*`
            : `📦 **Cached Public Information (${offlineMatch.titleEn})**\n\n**Benefit:** ${offlineMatch.benefitEn}\n\n**Eligibility Criteria:**\n${offlineMatch.eligibilityEn.map((e) => `* ${e}`).join("\n")}\n\n**Exclusions:**\n${offlineMatch.exclusionsEn.map((x) => `* ${x}`).join("\n")}\n\n**Application Channel:** ${offlineMatch.procedureEn}\n\n*🕒 Source Verified: ${offlineMatch.verifiedDate} | Local Cache: ${offlineMatch.cachedAt} | Source: ${offlineMatch.verifiedSource}*\n\n*(Caution: Government rules may change. Confirm live eligibility once connection is restored).*`;

          const cachedAssistantMsg: ChatMessage = {
            id: messageIdCounterRef.current++,
            sender: "assistant",
            text: cachedMarkdown,
            isCached: true,
            safetyNotice: isTe
              ? "ఇది ఆఫ్‌లైన్ నిల్వ నుండి అందించబడిన ప్రాథమిక సమాచారం మాత్రమే."
              : "This preliminary advice was served safely from your local offline cache.",
          };
          setMessages((prev) => [...prev, cachedAssistantMsg]);
        } else {
          lastFailedMessageRef.current = trimmedQuestion;
          const offlineFallbackText = isTe
            ? `📡 **నెట్‌వర్క్ అందుబాటులో లేదు (Offline Mode)**\n\nక్షమించండి, మీ ప్రశ్నకు ప్రత్యక్ష సమాధానం ఇవ్వడానికి లైవ్ సర్వరుతో అనుసంధానం అవసరం. మీరు ఈ ప్రశ్నను సేవ్ చేసుకోవచ్చు; ఇంటర్నెట్ పునరుద్ధరించబడినప్పుడు ఒక్క క్లిక్‌తో సమర్పించవచ్చు.\n\n*అత్యవసర ఆరోగ్య సలహాల కొరకు 104 లేదా 108 కు నేరుగా కాల్ చేయవచ్చు.*`
            : `📡 **Network Connection Unavailable**\n\nLive answers require an active server connection. You can save this question to submit manually once connectivity is restored.\n\n*For immediate emergency medical advice, dial 104 or 108 toll-free without internet.*`;

          const fallbackMsg: ChatMessage = {
            id: messageIdCounterRef.current++,
            sender: "assistant",
            text: offlineFallbackText,
            isError: true,
          };
          setMessages((prev) => [...prev, fallbackMsg]);
        }
      }, 250);
      return;
    }

    setIsThinking(true);

    try {
      const response = await sendChatMessage(
        {
          message: trimmedQuestion,
          assistant: getAssistantId(),
          language: isTe ? "te" : "en",
          state: "Andhra Pradesh",
          conversation_id: conversationIdRef.current,
        },
        controller.signal
      );

      if (controller.signal.aborted) return;

      if (response.conversation_id) {
        conversationIdRef.current = response.conversation_id;
      }

      // Check if backend returned empty sources or fallback answer, and if offline public cache has verified info
      const isFallbackAnswer =
        (!response.sources || response.sources.length === 0) &&
        (response.answer.includes("ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం అందుబాటులో లేదు") ||
          response.answer.includes("No verified official information") ||
          response.answer.includes("అందుబాటులో లేదు"));

      const offlineMatch = findOfflinePublicInfo(trimmedQuestion);

      if (isFallbackAnswer && offlineMatch) {
        const cachedMarkdown = isTe
          ? `📦 **ఆఫ్‌లైన్ నిల్వ సమాచారం (${offlineMatch.titleTe})**\n\nలైవ్ సర్వర్‌లో నిర్దిష్ట వివరాలు లేనందున, ధృవీకరించబడిన ప్రజా సమాచార నిల్వ నుండి వివరాలు అందించబడుతున్నాయి:\n\n**ప్రయోజనం:** ${offlineMatch.benefitTe}\n\n**అర్హత నిబంధనలు:**\n${offlineMatch.eligibilityTe.map((e) => `* ${e}`).join("\n")}\n\n**మినహాయింపులు:**\n${offlineMatch.exclusionsTe.map((x) => `* ${x}`).join("\n")}\n\n**దరఖాస్తు విధానం:** ${offlineMatch.procedureTe}\n\n*🕒 అధికారిక ధృవీకరణ: ${offlineMatch.verifiedDate} | స్థానిక నిల్వ: ${offlineMatch.cachedAt} | ఆధారం: ${offlineMatch.verifiedSource}*\n\n*(గమనిక: ప్రభుత్వ సంక్షేమ మార్గదర్శకాలు మారవచ్చు. స్థానిక గ్రామ సచివాలయంలో ప్రస్తుత అర్హతను ధృవీకరించుకోండి).*`
          : `📦 **Cached Public Information (${offlineMatch.titleEn})**\n\nServing from verified public cache as live search returned no direct match:\n\n**Benefit:** ${offlineMatch.benefitEn}\n\n**Eligibility Criteria:**\n${offlineMatch.eligibilityEn.map((e) => `* ${e}`).join("\n")}\n\n**Exclusions:**\n${offlineMatch.exclusionsEn.map((x) => `* ${x}`).join("\n")}\n\n**Application Channel:** ${offlineMatch.procedureEn}\n\n*🕒 Source Verified: ${offlineMatch.verifiedDate} | Local Cache: ${offlineMatch.cachedAt} | Source: ${offlineMatch.verifiedSource}*\n\n*(Caution: Government guidelines may vary. Confirm with local Grama Sachivalayam).*`;

        const cachedAssistantMsg: ChatMessage = {
          id: messageIdCounterRef.current++,
          sender: "assistant",
          text: cachedMarkdown,
          isCached: true,
          safetyNotice: isTe
            ? "ఇది ధృవీకరించబడిన ప్రజా నిల్వ నుండి అందించబడిన ప్రాథమిక సమాచారం."
            : "Served safely from verified public cache as fallback.",
        };
        setMessages((prev) => [...prev, cachedAssistantMsg]);
        return;
      }

      const assistantMessage: ChatMessage = {
        id: messageIdCounterRef.current++,
        sender: "assistant",
        text: response.answer,
        sources: response.sources || [],
        safetyNotice: response.safety_notice || null,
        followUps: response.follow_up_questions || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      if (controller.signal.aborted) return;

      lastFailedMessageRef.current = trimmedQuestion;
      let errorNotice = "";

      if (err instanceof ApiException) {
        errorNotice = `API Error [${err.code}]: ${err.message}`;
      } else {
        errorNotice = isTe
          ? "బ్యాకెండ్ చాట్ సర్వరు అందుబాటులో లేదు (/api/chat). దయచేసి సర్వరు నడుస్తుందో లేదో తనిఖీ చేయండి."
          : "Backend chat service is unreachable at /api/chat. Please check backend connection.";
      }

      setBackendNotice(errorNotice);

      const offlineMatch = findOfflinePublicInfo(trimmedQuestion);
      if (offlineMatch) {
        const cachedMarkdown = isTe
          ? `📦 **ఆఫ్‌లైన్ నిల్వ సమాచారం (${offlineMatch.titleTe})**\n\nసర్వర్ అనుసంధాన లోపం ఏర్పడినందున, స్థానిక ధృవీకరించబడిన ప్రజా నిల్వ నుండి సమాచారం అందించబడుతోంది:\n\n**ప్రయోజనం:** ${offlineMatch.benefitTe}\n\n**అర్హత నిబంధనలు:**\n${offlineMatch.eligibilityTe.map((e) => `* ${e}`).join("\n")}\n\n**మినహాయింపులు:**\n${offlineMatch.exclusionsTe.map((x) => `* ${x}`).join("\n")}\n\n**దరఖాస్తు విధానం:** ${offlineMatch.procedureTe}\n\n*🕒 అధికారిక ధృవీకరణ: ${offlineMatch.verifiedDate} | స్థానిక నిల్వ: ${offlineMatch.cachedAt} | ఆధారం: ${offlineMatch.verifiedSource}*\n\n*(గమనిక: ప్రభుత్వ మార్గదర్శకాలు మారవచ్చు. స్థానిక గ్రామ సచివాలయంలో ప్రస్తుత అర్హతను ధృవీకరించుకోండి).*`
          : `📦 **Cached Public Information (${offlineMatch.titleEn})**\n\nServer temporarily unreachable; served safely from verified offline public cache:\n\n**Benefit:** ${offlineMatch.benefitEn}\n\n**Eligibility Criteria:**\n${offlineMatch.eligibilityEn.map((e) => `* ${e}`).join("\n")}\n\n**Exclusions:**\n${offlineMatch.exclusionsEn.map((x) => `* ${x}`).join("\n")}\n\n**Application Channel:** ${offlineMatch.procedureEn}\n\n*🕒 Source Verified: ${offlineMatch.verifiedDate} | Local Cache: ${offlineMatch.cachedAt} | Source: ${offlineMatch.verifiedSource}*\n\n*(Caution: Government guidelines may vary. Confirm with local Grama Sachivalayam).*`;

        const cachedAssistantMsg: ChatMessage = {
          id: messageIdCounterRef.current++,
          sender: "assistant",
          text: cachedMarkdown,
          isCached: true,
          safetyNotice: isTe
            ? "ఇది ధృవీకరించబడిన ప్రజా నిల్వ నుండి అందించబడిన ప్రాథమిక సమాచారం."
            : "Served safely from verified offline public cache.",
        };
        setMessages((prev) => [...prev, cachedAssistantMsg]);
        return;
      }

      const unavailableMessage: ChatMessage = {
        id: messageIdCounterRef.current++,
        sender: "assistant",
        text: isTe
          ? "క్షమించండి, గ్రామ సహాయక్ చాట్ సర్వీస్ ప్రస్తుతం అందుబాటులో లేదు. దయచేసి కాసేపటి తర్వాత 'మళ్ళీ ప్రయత్నించండి' బటన్ నొక్కండి, లేదా ఈ ప్రశ్నను తర్వాత కోసం సేవ్ చేయండి."
          : "The Grama Sahayak chat service is currently unavailable. Please try again in a moment using the Retry button, or save this question for later.",
        isError: true,
      };

      setMessages((prev) => [...prev, unavailableMessage]);
    } finally {
      setIsThinking(false);
      abortControllerRef.current = null;
    }
  };

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
      handleSendMessage(lastFailedMessageRef.current);
    }
  };

  const handleSaveCurrentQuestion = (textToSave?: string) => {
    const target = textToSave || question || lastFailedMessageRef.current;
    if (!target || !target.trim()) return;

    // Save with explicit citizen consent and strict privacy validation
    const res = saveQuestionForLater(target, getAssistantId(), language, true);
    if (res.success) {
      setSavedActionToast(isTe ? "ప్రశ్న సేవ్ చేయబడింది! ✓" : "Question saved for later! ✓");
      refreshSavedQuestions();
      setQuestion("");
      setTimeout(() => setSavedActionToast(null), 3000);
    } else {
      setSavedActionToast(res.message || (isTe ? "ప్రశ్నను సేవ్ చేయడం సాధ్యం కాలేదు." : "Could not save question."));
      setTimeout(() => setSavedActionToast(null), 5000);
    }
  };

  return (
    <main className="home-container">
      {/* Credible Civic Platform Header */}
      <header className="site-header">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">
            <span>🏛️</span>
          </div>
          <div className="brand-text">
            <div className="brand-title-row">
              <h1>AI Grama Sahayak</h1>
              <span className="platform-tag">
                {isTe ? "ఆంధ్రప్రదేశ్ పౌర సహాయక్" : "AP Civic Technology"}
              </span>
            </div>
            <p className="brand-subtitle">
              {isTe
                ? "గ్రామీణ పౌరుల కోసం అధికారిక సమాచారం & సంక్షేమ మార్గదర్శక వేదిక"
                : "Multimodal digital guidance for rural citizens of Andhra Pradesh"}
            </p>
          </div>
        </div>

        <div className="header-actions">
          {/* Low-Network Assistance Pill & Drawer (Tasks 1, 2, 3, 5) */}
          <LowNetworkBanner
            language={language}
            connectivity={connectivity}
            savedQuestions={savedQuestions}
            onRefreshSavedQuestions={refreshSavedQuestions}
            onSubmitSavedQuestion={(text, cat) => {
              setSelectedCategory(cat);
              handleSendMessage(text);
            }}
          />

          <label htmlFor="language-selector" className="sr-only">
            {isTe ? "భాష ఎంచుకోండి" : "Select language"}
          </label>
          <div className="language-selector-wrapper">
            <span className="lang-icon" aria-hidden="true">🌐</span>
            <select
              id="language-selector"
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
          </div>
        </div>
      </header>

      {/* Navigation Tabs for Core Services */}
      <nav className="portal-nav" aria-label="Portal Services">
        <button
          className={`nav-tab ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          <span className="nav-tab-icon">💬</span>
          <span>{isTe ? "సహాయక్ చాట్" : "Sahayak Chat"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "documents" ? "active" : ""}`}
          onClick={() => setActiveTab("documents")}
        >
          <span className="nav-tab-icon">📄</span>
          <span>{isTe ? "పత్రాల విశ్లేషణ" : "Document Analysis"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "services" ? "active" : ""}`}
          onClick={() => setActiveTab("services")}
        >
          <span className="nav-tab-icon">📍</span>
          <span>{isTe ? "సమీప ప్రభుత్వ సేవలు" : "Nearby Services"}</span>
        </button>

        <button
          className={`nav-tab ${activeTab === "grievances" ? "active" : ""}`}
          onClick={() => setActiveTab("grievances")}
        >
          <span className="nav-tab-icon">📝</span>
          <span>{isTe ? "ఫిర్యాదు ముసాయిదా" : "Draft Grievance"}</span>
        </button>
      </nav>

      {/* View: Document Analysis */}
      {activeTab === "documents" && (
        <DocumentAnalysis language={language} isOffline={connectivity.status !== "online"} />
      )}

      {/* View: Nearby Services */}
      {activeTab === "services" && (
        <NearbyServices language={language} isOffline={connectivity.status !== "online"} />
      )}

      {/* View: Grievances */}
      {activeTab === "grievances" && (
        <GrievanceDrafting language={language} isOffline={connectivity.status !== "online"} />
      )}

      {/* View: Chat (Default Citizen Experience) */}
      {activeTab === "chat" && (
        <>
          {/* Civic Tech Hero Banner */}
          <section className="hero">
            <div className="hero-content">
              <span className="welcome-tag">
                {isTe ? "🌿 గ్రామీణ పౌర డిజిటల్ వేదిక" : "🌿 CIVIC DIGITAL ASSISTANCE PLATFORM"}
              </span>

              <h2>
                {isTe ? (
                  <>
                    మీకు నేడు ఎలా <br />
                    <span>సహాయపడగలం?</span>
                  </>
                ) : (
                  <>
                    How can we assist <br />
                    <span>your family today?</span>
                  </>
                )}
              </h2>

              <p>
                {isTe
                  ? "ప్రభుత్వ సంక్షేమ పథకాలు, సాగుబడి సలహాలు, ఆరోగ్యశ్రీ చికిత్సలు మరియు విద్యార్థి స్కాలర్‌షిప్‌లపై ధృవీకరించబడిన సమాచారం పొందండి. స్పష్టంగా తెలుగులో మాట్లాడండి లేదా టైప్ చేయండి."
                  : "Get verified public guidance on government welfare schemes, farming crop advisories, cashless healthcare & student scholarships. Speak in Telugu or English."}
              </p>

              {/* Prominent Microphone & Recording Controls */}
              <div className="voice-control-wrapper">
                <button
                  type="button"
                  className={`voice-button ${isListening ? "listening" : ""} ${recordingState === "transcribing" ? "transcribing" : ""}`}
                  onClick={startVoiceInput}
                  disabled={recordingState === "requesting_permission" || recordingState === "transcribing"}
                  aria-label={
                    recordingState === "recording"
                      ? isTe ? "రికార్డింగ్ ఆపి పంపండి" : "Stop and transcribe"
                      : recordingState === "transcribing"
                      ? isTe ? "వాయిస్ ప్రాసెస్ అవుతోంది" : "Processing speech"
                      : isTe ? "మీ ప్రశ్నను మాట్లాడండి" : "Speak your question"
                  }
                >
                  <span className="mic-icon">
                    {recordingState === "recording" ? (
                      <span className="recording-indicator" aria-hidden="true">
                        <span className="recording-wave-bar"></span>
                        <span className="recording-wave-bar"></span>
                        <span className="recording-wave-bar"></span>
                      </span>
                    ) : recordingState === "transcribing" ? (
                      "⏳"
                    ) : (
                      "🎙️"
                    )}
                  </span>
                  <span>
                    <strong>
                      {recordingState === "recording"
                        ? `${isTe ? "రికార్డింగ్ ఆపి పంపండి" : "Stop & Transcribe"} (${formatDuration(recordingDuration)} / 00:30)`
                        : recordingState === "transcribing"
                        ? isTe
                          ? "వాయిస్ ప్రాసెస్ అవుతోంది..."
                          : "Transcribing with Sarvam AI..."
                        : recordingState === "requesting_permission"
                        ? isTe
                          ? "మైక్రోఫోన్ అనుమతించండి..."
                          : "Allow microphone..."
                        : isTe
                        ? "మీ ప్రశ్నను మాట్లాడండి"
                        : "Speak your question"}
                    </strong>
                    <small>
                      {recordingState === "recording"
                        ? isTe
                          ? "టెక్స్ట్‌గా మార్చడానికి ఇక్కడ తాకండి"
                          : "Tap to finish and transcribe"
                        : recordingState === "transcribing"
                        ? isTe
                          ? "AI ద్వారా గుర్తిస్తున్నాము"
                          : "Converting voice to text"
                        : isTe
                        ? "వాయిస్ ఉపయోగించి నేరుగా అడగండి"
                        : "Tap to ask using your voice"}
                    </small>
                  </span>
                </button>

                {(recordingState === "recording" || recordingState === "transcribing" || recordingState === "requesting_permission") && (
                  <button
                    type="button"
                    className="voice-cancel-button"
                    onClick={cancelVoiceInput}
                    aria-label={isTe ? "రికార్డింగ్ రద్దు చేయండి" : "Cancel voice input"}
                    title={isTe ? "రద్దు చేయండి" : "Cancel"}
                  >
                    ✕ {isTe ? "రద్దు చేయండి" : "Cancel"}
                  </button>
                )}
              </div>

              {voiceMessage && (
                <p className="voice-notice" role="status">
                  {voiceMessage}
                </p>
              )}
            </div>

            <div className="hero-decoration" aria-hidden="true">
              <span className="deco-icon-1">🌾</span>
              <span className="deco-icon-2">🏛️</span>
              <span className="deco-icon-3">🩺</span>
            </div>
          </section>

          {/* 4 Specialist Assistant Cards */}
          <section className="assistance-section">
            <div className="section-heading">
              <div>
                <span className="section-label">
                  {isTe ? "ప్రత్యేక సహాయకులు" : "SPECIALIST ASSISTANTS"}
                </span>
                <h2>
                  {isTe ? "మీకు ఏ విభాగంలో సహాయం కావాలి?" : "Select your area of assistance"}
                </h2>
              </div>
              <p>
                {isTe
                  ? "అధికారిక సమాచార మార్గదర్శకత్వం కోసం విభాగాన్ని ఎంచుకోండి"
                  : "Choose a specialist domain to receive focused and verified answers"}
              </p>
            </div>

            <div className="category-grid">
              {SPECIALIST_ASSISTANTS.map((assistant) => {
                const isSelected = selectedCategory === assistant.id || selectedCategory === assistant.title;
                return (
                  <button
                    key={assistant.id}
                    type="button"
                    className={`category-card ${assistant.color} ${isSelected ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedCategory(assistant.id);
                      if (assistant.id === "schemes") {
                        setShowEligibility(true);
                      } else {
                        setShowEligibility(false);
                      }
                    }}
                  >
                    <div className="category-card-top">
                      <div className="category-icon">{assistant.icon}</div>
                      <span className="category-badge">
                        {isTe ? assistant.badgeTe : assistant.badgeEn}
                      </span>
                    </div>

                    <div className="category-text">
                      <h3>{isTe ? assistant.titleTe : assistant.titleEn}</h3>
                      <p>{isTe ? assistant.descriptionTe : assistant.descriptionEn}</p>
                    </div>

                    <div className="category-card-footer">
                      <span className="select-action-text">
                        {isSelected
                          ? isTe ? "ఎంచుకోబడింది ✓" : "Active Assistant ✓"
                          : isTe ? "ఎంచుకోండి →" : "Select Domain →"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Quick Action: Check Scheme Eligibility Button */}
            <div className="quick-action-row">
              <button
                type="button"
                className={`quick-eligibility-btn ${
                  (selectedCategory === "schemes" || selectedCategory === "Government Schemes") && showEligibility
                    ? "active"
                    : ""
                }`}
                onClick={() => {
                  if ((selectedCategory === "schemes" || selectedCategory === "Government Schemes") && showEligibility) {
                    setShowEligibility(false);
                  } else {
                    setSelectedCategory("schemes");
                    setShowEligibility(true);
                  }
                }}
              >
                <span>📋</span>
                <span>
                  {isTe
                    ? "సంక్షేమ పథకాల అర్హత పరిశీలన సాధనం (Check Eligibility Form)"
                    : "Interactive Scheme Eligibility Calculator"}
                </span>
                <span className="toggle-chevron">
                  {(selectedCategory === "schemes" || selectedCategory === "Government Schemes") && showEligibility
                    ? "▲"
                    : "▼"}
                </span>
              </button>
            </div>

            {/* Dedicated Eligibility Evaluation View within Government Schemes */}
            {((selectedCategory === "schemes" || selectedCategory === "Government Schemes") && showEligibility) && (
              <div className="embedded-eligibility-section">
                <SchemeEligibility language={language} />
              </div>
            )}

            {/* Suggested Citizen Questions */}
            <div className="suggested-questions-panel">
              <div className="suggested-title-row">
                <span className="sparkle-icon">💡</span>
                <strong>
                  {isTe
                    ? `సూచించిన ప్రశ్నలు (${isTe ? currentAssistant.titleTe : currentAssistant.titleEn}):`
                    : `Suggested Questions (${currentAssistant.titleEn}):`}
                </strong>
              </div>
              <div className="suggested-chips-grid">
                {(isTe ? currentAssistant.suggestedQuestionsTe : currentAssistant.suggestedQuestionsEn).map(
                  (sq, qIdx) => (
                    <button
                      key={qIdx}
                      type="button"
                      className="suggested-chip-btn"
                      onClick={() => handleSendMessage(sq)}
                    >
                      <span>💬</span>
                      <span className="chip-query-text">{sq}</span>
                      <span className="chip-arrow">→</span>
                    </button>
                  )
                )}
              </div>
            </div>
          </section>

          {/* Chat conversation area */}
          {messages.length > 0 && (
            <section className="chat-section">
              <div className="chat-heading">
                <div>
                  <span className="section-label">
                    {isTe ? "మీ సంభాషణ" : "CITIZEN CONSULTATION"}
                  </span>
                  <h2>{isTe ? "సహాయక్ చాట్ వివరాలు" : "Chat with Grama Sahayak"}</h2>
                </div>

                <button
                  type="button"
                  className="new-chat-button"
                  onClick={handleNewChat}
                  title={isTe ? "కొత్త సంభాషణ ప్రారంభించండి" : "Start a new conversation"}
                >
                  <span>+</span>
                  <span>{isTe ? "కొత్త చాట్" : "New Chat"}</span>
                </button>
              </div>

              <div className="chat-messages">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`chat-message ${
                      message.sender === "user" ? "user-message" : "assistant-message"
                    }`}
                  >
                    <div className="message-avatar">
                      {message.sender === "user" ? "👤" : "🌿"}
                    </div>

                    <div className="message-content">
                      <span className="message-sender">
                        {message.sender === "user"
                          ? isTe ? "మీరు" : "You"
                          : isTe ? "గ్రామ సహాయక్" : "Grama Sahayak"}
                      </span>

                      {/* Safe Markdown formatting */}
                      {message.sender === "assistant" ? (
                        <SafeMarkdown content={message.text} />
                      ) : (
                        <p className="user-text">{message.text}</p>
                      )}

                      {/* Safety / Contextual Advisory Box */}
                      {message.safetyNotice && (
                        <div className="safety-notice-box" role="alert">
                          <span className="notice-icon">⚠️</span>
                          <div className="notice-body">
                            <strong>{isTe ? "ముఖ్య గమనిక: " : "Advisory: "}</strong>
                            <span>{message.safetyNotice}</span>
                          </div>
                        </div>
                      )}

                      {/* Official Sources Citation Cards */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="sources-container">
                          <span className="sources-title">
                            🏛️ {isTe ? "ధృవీకరించబడిన అధికారిక ఆధారాలు:" : "Verified Official Sources:"}
                          </span>
                          <div className="sources-list">
                            {message.sources.map((src, sIdx) => (
                              <div key={sIdx} className="source-item">
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="source-link"
                                >
                                  {src.title} ↗
                                </a>
                                {src.publisher && (
                                  <span className="source-meta"> — {src.publisher}</span>
                                )}
                                {src.verified_at && (
                                  <span className="source-meta">
                                    {" "}• {isTe ? `ధృవీకరించబడింది: ${src.verified_at}` : `Verified: ${src.verified_at}`}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-up Questions Chips */}
                      {message.followUps && message.followUps.length > 0 && (
                        <div className="follow-up-container">
                          <span className="follow-up-title">
                            💡 {isTe ? "సంబంధిత తదుపరి ప్రశ్నలు:" : "Related Follow-up Questions:"}
                          </span>
                          <div className="follow-up-chips">
                            {message.followUps.map((fq, fIdx) => (
                              <button
                                key={fIdx}
                                type="button"
                                className="follow-up-chip"
                                onClick={() => handleSendMessage(fq)}
                              >
                                {fq} →
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Voice Audio Listen Button */}
                      {message.sender === "assistant" && !message.isError && (
                        <div className="message-audio-row">
                          <AudioSpeakButton text={message.text} language={language} />
                        </div>
                      )}

                      {/* Error or Offline Actions: Retry & Save for Later */}
                      {message.isError && (
                        <div className="msg-action-row">
                          <button type="button" className="retry-button" onClick={handleRetry}>
                            ↻ {isTe ? "మళ్లీ ప్రయత్నించండి" : "Retry Live"}
                          </button>
                          <button
                            type="button"
                            className="save-question-chip-btn"
                            onClick={() => handleSaveCurrentQuestion()}
                          >
                            💾 {isTe ? "ప్రశ్నను సేవ్ చేయండి" : "Save for Later"}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isThinking && (
                  <div className="chat-message assistant-message thinking-message">
                    <div className="message-avatar">🌿</div>
                    <div className="message-content">
                      <span className="message-sender">
                        {isTe ? "గ్రామ సహాయక్" : "Grama Sahayak"}
                      </span>
                      <p className="thinking-text">
                        <span>{isTe ? "సమాధానం సిద్ధం చేస్తోంది" : "Consulting verified knowledge"}</span>
                        <span className="thinking-dots">...</span>
                      </p>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {backendNotice ? (
                <p className="demo-notice error-notice-text">
                  ℹ️ {backendNotice}
                </p>
              ) : (
                <p className="demo-notice">
                  ⚖️ {isTe
                    ? "గ్రామ సహాయక్ • ఆంధ్రప్రదేశ్ ప్రభుత్వ ధృవీకరించబడిన సంక్షేమ నిబంధనలు మరియు మార్గదర్శకాలపై ఆధారపడి పనిచేస్తుంది."
                    : "AI Grama Sahayak • Integrated with verified public information, gazettes and AP government guidelines."}
                </p>
              )}
            </section>
          )}

          {/* Bottom Question Input Bar */}
          <section className="question-section">
            {savedActionToast && (
              <div className="saved-toast-notification" role="status">
                <span>✓</span>
                <span>{savedActionToast}</span>
              </div>
            )}

            <div className="question-box">
              <div className="question-icon" aria-hidden="true">💬</div>

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
                  connectivity.status !== "online"
                    ? isTe
                      ? "నెట్‌వర్క్ లేదు — ప్రశ్నను టైప్ చేసి సేవ్ చేయండి లేదా శోధించండి..."
                      : "Offline — Type question to search cached info or save..."
                    : isTe
                    ? `మీ ప్రశ్నను ఇక్కడ అడగండి (${currentAssistant.titleTe})...`
                    : `Ask your question here (${currentAssistant.titleEn})...`
                }
                aria-label={isTe ? "మీ ప్రశ్నను నమోదు చేయండి" : "Type your question"}
              />

              {/* Allow saving question for later anytime (offline or planning ahead) */}
              {question.trim() && (
                <button
                  type="button"
                  className="save-input-btn"
                  onClick={() => handleSaveCurrentQuestion()}
                  title={isTe ? "ఈ ప్రశ్నను తర్వాత అడగడానికి సేవ్ చేయండి" : "Save this question for later"}
                >
                  💾 {isTe ? "సేవ్" : "Save"}
                </button>
              )}

              <button
                type="button"
                className="send-button"
                disabled={!question.trim() || isThinking}
                onClick={() => handleSendMessage()}
                aria-label={isTe ? "పంపండి" : "Send question"}
              >
                <span>{isThinking ? "⏳" : isTe ? "పంపండి" : "Send"}</span>
                <span className="send-arrow">➤</span>
              </button>
            </div>

            <div className="question-hint-row">
              <span className="hint-tag">
                {isTe ? "చిట్కా" : "Tip"}
              </span>
              <p className="question-hint">
                {isTe
                  ? "మీరు తెలుగు లేదా ఇంగ్లీషులో టైప్ చేయవచ్చు. ఆధార్, బ్యాంక్ లేదా రహస్య వివరాలను సేవ్ చేయవద్దు; సాధారణ ప్రజా ప్రశ్నలను మాత్రమే తర్వాత కోసం సేవ్ చేసుకోండి."
                  : "You can type in Telugu or English. Do NOT save Aadhaar, bank, or personal IDs; only non-sensitive public inquiries can be saved."}
              </p>
            </div>
          </section>
        </>
      )}

      {/* Trust & Transparency Footer */}
      <footer className="site-footer">
        <div className="footer-left">
          <span className="footer-brand">🌿 AI Grama Sahayak</span>
          <span className="footer-pipe">•</span>
          <span className="footer-tagline">
            {isTe
              ? "గ్రామీణ పౌరులకు పారదర్శక, ప్రాప్యమైన డిజిటల్ సహాయం"
              : "Transparent, Accessible Civic Intelligence for Rural Citizens"}
          </span>
        </div>
        <div className="footer-right">
          <small>
            {isTe
              ? "నిరాకరణ: ఇది పౌర సహాయ సాధనం మాత్రమే. అధికారిక అనుమతులు లేదా ధృవీకరణలకు స్థానిక సచివాలయాన్ని సంప్రదించండి."
              : "Disclaimer: Autonomous informational guidance. Consult Grama Sachivalayam for formal statutory filings."}
          </small>
        </div>
      </footer>
    </main>
  );
}
