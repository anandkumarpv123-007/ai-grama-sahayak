"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { synthesizeSpeech, ApiException } from "../services/api";
import {
  prepareSpeechText,
  splitIntoSentenceChunks,
  selectBrowserVoice,
} from "../services/voiceUtils";

interface AudioSpeakButtonProps {
  text: string;
  language: string; // "Telugu" | "English"
}

export default function AudioSpeakButton({ text, language }: AudioSpeakButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isCancelledRef = useRef<boolean>(false);
  const loadingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isPlayingRef = useRef<boolean>(false);
  const activeUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const isTe = language === "Telugu";
  const langCode: "te" | "en" = isTe ? "te" : "en";

  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  const clearLoadingTimer = () => {
    if (loadingTimerRef.current) {
      clearTimeout(loadingTimerRef.current);
      loadingTimerRef.current = null;
    }
  };

  const stopAudio = useCallback(() => {
    isCancelledRef.current = true;
    clearLoadingTimer();

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current.src = "";
      } catch {
        // ignore
      }
      audioRef.current = null;
    }

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // ignore
      }
    }

    activeUtteranceRef.current = null;
    isPlayingRef.current = false;
    setIsPlaying(false);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [stopAudio]);

  const playBrowserSpeechFallback = useCallback(
    (textToSpeak: string, noticePrefix?: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        clearLoadingTimer();
        setIsLoading(false);
        isPlayingRef.current = false;
        setIsPlaying(false);
        setStatusMessage(
          isTe
            ? "ఈ బ్రౌజర్‌లో వాయిస్ ప్లేబ్యాక్ అందుబాటులో లేదు."
            : "Voice synthesis is not supported in this browser."
        );
        return;
      }

      const getVoicesAndSpeak = () => {
        if (isCancelledRef.current) {
          clearLoadingTimer();
          setIsLoading(false);
          isPlayingRef.current = false;
          setIsPlaying(false);
          return;
        }

        const voices = window.speechSynthesis.getVoices();
        const selection = selectBrowserVoice(voices, isTe);

        // If browser lacks a suitable speech voice (especially for Telugu),
        // show a clear user-facing error instead of pretending playback succeeded
        if (isTe && !selection.hasGenuineVoice) {
          clearLoadingTimer();
          setIsLoading(false);
          isPlayingRef.current = false;
          setIsPlaying(false);
          setStatusMessage(
            "ఈ పరికరంలో తెలుగు వాయిస్ ప్యాక్ లేదు. (డివైజ్ సెట్టింగ్స్‌లో ఇన్స్టాల్ చేయండి)"
          );
          return;
        }

        const chunks = splitIntoSentenceChunks(textToSpeak, 200);
        if (chunks.length === 0) {
          clearLoadingTimer();
          setIsLoading(false);
          isPlayingRef.current = false;
          setIsPlaying(false);
          return;
        }

        // Transition button state to Playing immediately so UI reflects active playback and provides Stop option
        clearLoadingTimer();
        setIsLoading(false);
        isPlayingRef.current = true;
        setIsPlaying(true);
        if (noticePrefix) {
          setStatusMessage(noticePrefix);
        }

        let chunkIndex = 0;

        const speakNextChunk = () => {
          if (isCancelledRef.current) {
            isPlayingRef.current = false;
            setIsPlaying(false);
            activeUtteranceRef.current = null;
            return;
          }

          if (chunkIndex >= chunks.length) {
            isPlayingRef.current = false;
            setIsPlaying(false);
            activeUtteranceRef.current = null;
            return;
          }

          const utterance = new SpeechSynthesisUtterance(chunks[chunkIndex]);
          // Persistent reference prevents Chromium V8 garbage-collecting the utterance mid-speech
          activeUtteranceRef.current = utterance;

          utterance.lang = selection.targetLang;
          if (selection.voice) {
            utterance.voice = selection.voice;
          }
          utterance.rate = 0.95;

          utterance.onstart = () => {
            if (!isCancelledRef.current) {
              clearLoadingTimer();
              setIsLoading(false);
              isPlayingRef.current = true;
              setIsPlaying(true);
              if (noticePrefix) {
                setStatusMessage(noticePrefix);
              }
            }
          };

          utterance.onend = () => {
            if (isCancelledRef.current) {
              isPlayingRef.current = false;
              setIsPlaying(false);
              activeUtteranceRef.current = null;
              return;
            }
            chunkIndex++;
            if (chunkIndex < chunks.length) {
              speakNextChunk();
            } else {
              isPlayingRef.current = false;
              setIsPlaying(false);
              activeUtteranceRef.current = null;
            }
          };

          utterance.onerror = (e) => {
            if (isCancelledRef.current || e.error === "interrupted" || e.error === "canceled") {
              isPlayingRef.current = false;
              setIsPlaying(false);
              activeUtteranceRef.current = null;
              return;
            }
            isPlayingRef.current = false;
            setIsPlaying(false);
            activeUtteranceRef.current = null;
            setStatusMessage(
              isTe
                ? "బ్రౌజర్ ఆడియో ప్లేబ్యాక్ విఫలమైంది."
                : "Device speech playback failed."
            );
          };

          try {
            window.speechSynthesis.speak(utterance);
            // Chromium async user-activation workaround: resume if speech engine paused
            if (window.speechSynthesis.paused) {
              window.speechSynthesis.resume();
            }
          } catch {
            isPlayingRef.current = false;
            setIsPlaying(false);
            activeUtteranceRef.current = null;
            setStatusMessage(
              isTe
                ? "ఆడియో ప్లేబ్యాక్ ప్రారంభం కాలేదు."
                : "Unable to start audio playback."
            );
          }
        };

        speakNextChunk();
      };

      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        getVoicesAndSpeak();
      } else {
        let voicesLoaded = false;
        const onVoices = () => {
          if (!voicesLoaded) {
            voicesLoaded = true;
            window.speechSynthesis.removeEventListener("voiceschanged", onVoices);
            getVoicesAndSpeak();
          }
        };
        window.speechSynthesis.addEventListener("voiceschanged", onVoices);
        setTimeout(() => {
          if (!voicesLoaded) {
            voicesLoaded = true;
            window.speechSynthesis.removeEventListener("voiceschanged", onVoices);
            getVoicesAndSpeak();
          }
        }, 250);
      }
    },
    [isTe]
  );

  const handleToggleSpeak = async () => {
    if (isPlaying || isLoading) {
      stopAudio();
      return;
    }

    isCancelledRef.current = false;
    setIsLoading(true);
    setStatusMessage(null);

    clearLoadingTimer();
    // 5-second watchdog timer: resets loading state if server never responds
    // Guarded to never interrupt or stop audio if playback has already begun
    loadingTimerRef.current = setTimeout(() => {
      if (isPlayingRef.current) {
        return;
      }
      setIsLoading(false);
      setStatusMessage(
        isTe ? "ఆడియో లోడింగ్ సమయం ముగిసింది." : "Audio request timed out."
      );
    }, 5000);

    const prepared = prepareSpeechText(text, 3800, isTe);
    if (!prepared.textToSpeak.trim()) {
      clearLoadingTimer();
      setIsLoading(false);
      setStatusMessage(
        isTe ? "చదవడానికి పాఠ్యం లేదు." : "No text available to read."
      );
      return;
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await synthesizeSpeech(
        prepared.textToSpeak,
        langCode,
        controller.signal
      );

      if (isCancelledRef.current) {
        clearLoadingTimer();
        setIsLoading(false);
        return;
      }

      if (res?.audio_base64 && res.audio_base64.trim()) {
        const audioSrc = `data:${res.mime_type || "audio/wav"};base64,${res.audio_base64}`;
        const audio = new Audio(audioSrc);
        audioRef.current = audio;

        audio.onplay = () => {
          clearLoadingTimer();
          isPlayingRef.current = true;
          setIsLoading(false);
          setIsPlaying(true);
          if (prepared.wasTruncated) {
            setStatusMessage(
              isTe ? "పూర్తి వివరాలు స్క్రీన్‌పై ఉన్నాయి" : "Full details on screen"
            );
          }
        };

        audio.onended = () => {
          isPlayingRef.current = false;
          setIsPlaying(false);
          audioRef.current = null;
        };

        audio.onerror = () => {
          clearLoadingTimer();
          if (!isCancelledRef.current) {
            playBrowserSpeechFallback(
              prepared.textToSpeak,
              isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
            );
          }
        };

        try {
          await audio.play();
          return;
        } catch {
          if (!isCancelledRef.current) {
            playBrowserSpeechFallback(
              prepared.textToSpeak,
              isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
            );
          }
          return;
        }
      } else {
        if (!isCancelledRef.current) {
          playBrowserSpeechFallback(
            prepared.textToSpeak,
            isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
          );
        }
      }
    } catch (err: unknown) {
      clearLoadingTimer();
      if (isCancelledRef.current) {
        setIsLoading(false);
        return;
      }

      let notice = isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio";
      if (err instanceof ApiException) {
        if (err.status === 503) {
          notice = isTe ? "సర్వర్ ఆఫ్‌లైన్ — పరికర ఆడియో ద్వారా" : "Online voice unavailable (503) — using device audio";
        } else if (err.status === 400) {
          notice = isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio";
        }
      }

      playBrowserSpeechFallback(prepared.textToSpeak, notice);
    }
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
