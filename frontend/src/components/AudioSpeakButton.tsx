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
  const requestSeqRef = useRef<number>(0);

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
    requestSeqRef.current++;
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

  // Stop audio on cleanup when language changes or component unmounts
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [language, stopAudio]);

  const playBrowserSpeechFallback = useCallback(
    (textToSpeak: string, noticePrefix?: string, isServerError: boolean = false) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        clearLoadingTimer();
        setIsLoading(false);
        isPlayingRef.current = false;
        setIsPlaying(false);
        if (isServerError) {
          setStatusMessage(
            isTe ? "వాయిస్ సర్వర్ అందుబాటులో లేదు." : "Voice server is unavailable."
          );
        } else {
          setStatusMessage(
            isTe
              ? "ఈ బ్రౌజర్‌లో వాయిస్ ప్లేబ్యాక్ అందుబాటులో లేదు."
              : "Voice synthesis is not supported in this browser."
          );
        }
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
        // show an honest server notice if backend failed, or clear voice pack notice if device lacks voice
        if (isTe && !selection.hasGenuineVoice) {
          clearLoadingTimer();
          setIsLoading(false);
          isPlayingRef.current = false;
          setIsPlaying(false);
          if (isServerError) {
            setStatusMessage("వాయిస్ సర్వర్ అందుబాటులో లేదు.");
          } else {
            setStatusMessage(
              "ఈ పరికరంలో తెలుగు వాయిస్ ప్యాక్ లేదు. (డివైజ్ సెట్టింగ్స్‌లో ఇన్స్టాల్ చేయండి)"
            );
          }
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

    const currentSeq = ++requestSeqRef.current;
    isCancelledRef.current = false;
    setIsLoading(true);
    setStatusMessage(isTe ? "ఆడియో సిద్ధమవుతోంది..." : "Generating audio...");

    clearLoadingTimer();
    // 55-second frontend synthesis timeout: exceeds the 45s backend synthesis deadline by a 10s network margin
    loadingTimerRef.current = setTimeout(() => {
      if (isPlayingRef.current || isCancelledRef.current || currentSeq !== requestSeqRef.current) {
        return;
      }
      setIsLoading(false);
      abortControllerRef.current?.abort();
      playBrowserSpeechFallback(
        prepared.textToSpeak,
        isTe ? "ఆడియో సమయం ముగిసింది — పరికర ఆడియో ద్వారా" : "Audio synthesis timed out — using device audio",
        true
      );
    }, 55000);

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

      if (isCancelledRef.current || currentSeq !== requestSeqRef.current) {
        clearLoadingTimer();
        setIsLoading(false);
        return;
      }

      if (res?.audio_base64 && res.audio_base64.trim()) {
        const audioSrc = `data:${res.mime_type || "audio/wav"};base64,${res.audio_base64}`;
        const audio = new Audio(audioSrc);
        audioRef.current = audio;

        audio.onplay = () => {
          if (isCancelledRef.current || currentSeq !== requestSeqRef.current) {
            audio.pause();
            audio.src = "";
            return;
          }
          clearLoadingTimer();
          isPlayingRef.current = true;
          setIsLoading(false);
          setIsPlaying(true);
          if (prepared.wasTruncated) {
            setStatusMessage(
              isTe ? "పూర్తి వివరాలు స్క్రీన్‌పై ఉన్నాయి" : "Full details on screen"
            );
          } else {
            setStatusMessage(null);
          }
        };

        audio.onended = () => {
          isPlayingRef.current = false;
          setIsPlaying(false);
          audioRef.current = null;
        };

        audio.onerror = () => {
          clearLoadingTimer();
          if (!isCancelledRef.current && currentSeq === requestSeqRef.current) {
            playBrowserSpeechFallback(
              prepared.textToSpeak,
              isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
            );
          }
        };

        try {
          await audio.play();
          return;
        } catch (playErr: unknown) {
          clearLoadingTimer();
          if (isCancelledRef.current || currentSeq !== requestSeqRef.current) {
            return;
          }
          const errName = playErr instanceof Error ? playErr.name : "";
          if (errName === "NotAllowedError") {
            // Autoplay blocked by browser: keep audio ready and prompt user to click
            setIsLoading(false);
            setIsPlaying(false);
            setStatusMessage(
              isTe ? "ఆడియో ప్లే చేయడానికి మళ్ళీ క్లిక్ చేయండి" : "Click Listen to play audio"
            );
            return;
          }

          playBrowserSpeechFallback(
            prepared.textToSpeak,
            isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
          );
          return;
        }
      } else {
        if (!isCancelledRef.current && currentSeq === requestSeqRef.current) {
          playBrowserSpeechFallback(
            prepared.textToSpeak,
            isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio"
          );
        }
      }
    } catch (err: unknown) {
      clearLoadingTimer();
      if (isCancelledRef.current || currentSeq !== requestSeqRef.current) {
        setIsLoading(false);
        return;
      }

      let notice = isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio";
      let isServerError = true;
      if (err instanceof ApiException) {
        if (err.status === 503) {
          notice = isTe ? "సర్వర్ ఆఫ్‌లైన్ — పరికర ఆడియో ద్వారా" : "Online voice unavailable (503) — using device audio";
          isServerError = true;
        } else if (err.status === 400) {
          notice = isTe ? "పరికర ఆడియో ద్వారా ప్లే అవుతోంది" : "Playing via device audio";
          isServerError = false;
        }
      }

      playBrowserSpeechFallback(prepared.textToSpeak, notice, isServerError);
    }
  };

  return (
    <div className="audio-speak-container">
      <button
        className={`audio-speak-btn ${isPlaying ? "playing" : ""} ${isLoading ? "loading" : ""}`}
        onClick={handleToggleSpeak}
        aria-label={isPlaying ? "Stop speech" : isLoading ? "Cancel audio generation" : "Listen to response"}
        title={isPlaying ? "Stop audio" : isLoading ? "Cancel audio generation" : "Listen to audio response"}
      >
        {isLoading ? (
          <span>⏹️ {isTe ? "ఆపండి" : "Stop"}</span>
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
