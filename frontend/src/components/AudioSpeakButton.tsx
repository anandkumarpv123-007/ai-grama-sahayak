"use client";

import { useState, useRef, useEffect } from "react";
import { synthesizeSpeech } from "../services/api";

interface AudioSpeakButtonProps {
  text: string;
  language: string; // "Telugu" | "English"
}

export default function AudioSpeakButton({ text, language }: AudioSpeakButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const isTe = language === "Telugu";
  const langCode: "te" | "en" = isTe ? "te" : "en";

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
    setIsLoading(false);
  };

  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, []);

  const handleToggleSpeak = async () => {
    if (isPlaying || isLoading) {
      stopAudio();
      return;
    }

    setIsLoading(true);
    setStatusMessage(null);

    try {
      // 1. Try backend voice synthesis endpoint
      const res = await synthesizeSpeech(text, langCode);
      if (res?.audio_base64) {
        const audioSrc = `data:${res.mime_type || "audio/wav"};base64,${res.audio_base64}`;
        const audio = new Audio(audioSrc);
        audioRef.current = audio;

        audio.onplay = () => {
          setIsLoading(false);
          setIsPlaying(true);
        };

        audio.onended = () => {
          setIsPlaying(false);
          audioRef.current = null;
        };

        audio.onerror = () => {
          fallbackBrowserSpeech();
        };

        await audio.play();
        return;
      } else {
        fallbackBrowserSpeech();
      }
    } catch {
      // Backend TTS unavailable (e.g. 503 or offline) — fallback to browser speech synthesis
      fallbackBrowserSpeech();
    }
  };

  const fallbackBrowserSpeech = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setIsLoading(false);
      setIsPlaying(false);
      setStatusMessage(
        isTe
          ? "ఈ బ్రౌజర్‌లో వాయిస్ ప్లేబ్యాక్ అందుబాటులో లేదు."
          : "Voice synthesis is not supported in this browser."
      );
      return;
    }

    window.speechSynthesis.cancel();

    // Check available voices
    const voices = window.speechSynthesis.getVoices();
    const targetLang = isTe ? "te-IN" : "en-IN";
    const voice = voices.find((v) => v.lang.startsWith(isTe ? "te" : "en"));

    if (isTe && voices.length > 0 && !voice) {
      // Browser has voices but no Telugu voice pack installed
      setIsLoading(false);
      setIsPlaying(false);
      setStatusMessage(
        "ఈ బ్రౌజర్ లేదా పరికరంలో తెలుగు వాయిస్ ప్యాక్ అందుబాటులో లేదు."
      );
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = targetLang;
    if (voice) utterance.voice = voice;
    utterance.rate = 0.95;

    utterance.onstart = () => {
      setIsLoading(false);
      setIsPlaying(true);
    };

    utterance.onend = () => {
      setIsPlaying(false);
    };

    utterance.onerror = () => {
      setIsLoading(false);
      setIsPlaying(false);
      setStatusMessage(
        isTe
          ? "ఆడియో ప్లేబ్యాక్ విఫలమైంది."
          : "Audio playback encountered an error."
      );
    };

    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="audio-speak-container">
      <button
        className={`audio-speak-btn ${isPlaying ? "playing" : ""}`}
        onClick={handleToggleSpeak}
        disabled={isLoading}
        aria-label={isPlaying ? "Stop speech" : "Listen to response"}
        title={isPlaying ? "Stop audio" : "Listen to audio response"}
      >
        {isLoading ? (
          <span>⏳ {isTe ? "సిద్ధమవుతోంది..." : "Loading..."}</span>
        ) : isPlaying ? (
          <span>⏹️ {isTe ? "ఆపండి" : "Stop"}</span>
        ) : (
          <span>🔊 {isTe ? "వినండి" : "Listen"}</span>
        )}
      </button>
      {statusMessage && (
        <span className="audio-status-msg" role="status">
          {statusMessage}
        </span>
      )}
    </div>
  );
}
