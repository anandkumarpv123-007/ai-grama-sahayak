/**
 * Voice Utilities for Speech Synthesis and Text Processing
 * Member 3: Frontend Voice Reliability
 */

export interface PreparedSpeech {
  textToSpeak: string;
  wasTruncated: boolean;
  originalLength: number;
}

/**
 * Cleans markdown formatting, links, and code blocks from text so it can be spoken naturally.
 */
export function cleanTextForSpeech(rawText: string): string {
  if (!rawText || !rawText.trim()) {
    return "";
  }

  let text = rawText;

  // Remove code blocks ```...```
  text = text.replace(/```[\s\S]*?```/g, " ");

  // Remove inline code `...`
  text = text.replace(/`([^`]+)`/g, "$1");

  // Convert markdown links [Label](url) -> Label
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

  // Remove markdown headings (# Heading -> Heading)
  text = text.replace(/^#{1,6}\s+/gm, "");

  // Remove bold/italic markers (*, **, _, __)
  text = text.replace(/(\*\*|__)(.*?)\1/g, "$2");
  text = text.replace(/(\*|_)(.*?)\1/g, "$2");

  // Remove blockquotes (> ...)
  text = text.replace(/^>\s+/gm, "");

  // Remove bullet points / list numbers (- item, * item, 1. item)
  text = text.replace(/^\s*[-*+]\s+/gm, "");
  text = text.replace(/^\s*\d+\.\s+/gm, "");

  // Remove raw URL links
  text = text.replace(/https?:\/\/\S+/gi, " ");

  // Collapse multiple whitespace / newlines
  text = text.replace(/\s+/g, " ").trim();

  return text;
}

/**
 * Prepares text for speech output, ensuring it does not exceed backend limits (4000 chars)
 * while preserving full semantic content through sensible sentence-based segmentation.
 */
export function prepareSpeechText(
  rawText: string,
  maxChars: number = 3800,
  isTe: boolean = false
): PreparedSpeech {
  const clean = cleanTextForSpeech(rawText);
  const originalLength = clean.length;

  if (originalLength <= maxChars) {
    return {
      textToSpeak: clean,
      wasTruncated: false,
      originalLength,
    };
  }

  // Find the last sentence terminator before maxChars
  const suffix = isTe
    ? " ... మరిన్ని వివరాలు స్క్రీన్‌పై అందుబాటులో ఉన్నాయి."
    : " ... Full details are displayed on screen.";

  const targetLength = Math.max(20, maxChars - suffix.length);
  const candidate = clean.slice(0, targetLength);

  // Look for sentence boundary (. ! ? । \n)
  const lastBoundary = Math.max(
    candidate.lastIndexOf(". "),
    candidate.lastIndexOf("? "),
    candidate.lastIndexOf("! "),
    candidate.lastIndexOf("। "),
    candidate.lastIndexOf("\n")
  );

  let truncatedText: string;
  if (lastBoundary > targetLength * 0.6) {
    truncatedText = candidate.slice(0, lastBoundary + 1).trim() + suffix;
  } else {
    // If no good sentence boundary, break at last word boundary
    const lastSpace = candidate.lastIndexOf(" ");
    truncatedText = (lastSpace > 0 ? candidate.slice(0, lastSpace) : candidate).trim() + suffix;
  }

  return {
    textToSpeak: truncatedText,
    wasTruncated: true,
    originalLength,
  };
}

/**
 * Splits text into short, natural sentence chunks (150-250 chars) for browser SpeechSynthesis.
 * This completely avoids Chromium/WebKit's 15-second speech synthesis engine timeout/freeze bug.
 */
export function splitIntoSentenceChunks(text: string, maxChunkLength: number = 220): string[] {
  if (!text || !text.trim()) {
    return [];
  }

  const clean = text.trim();
  if (clean.length <= maxChunkLength) {
    return [clean];
  }

  // Split on sentence terminators while preserving them
  const rawSentences = clean.split(/(?<=[.?!।\n])\s+/);
  const chunks: string[] = [];
  let currentChunk = "";

  for (const sentence of rawSentences) {
    const s = sentence.trim();
    if (!s) continue;

    if (s.length > maxChunkLength) {
      // Long sentence: break at commas or clause boundaries
      const clauses = s.split(/(?<=[,;:])\s+/);
      for (const clause of clauses) {
        const c = clause.trim();
        if (!c) continue;

        if (currentChunk.length + c.length + 1 <= maxChunkLength) {
          currentChunk = currentChunk ? `${currentChunk} ${c}` : c;
        } else {
          if (currentChunk) chunks.push(currentChunk);
          if (c.length <= maxChunkLength) {
            currentChunk = c;
          } else {
            // Unusually long clause without punctuation: split on words
            const words = c.split(" ");
            let subChunk = "";
            for (const word of words) {
              if (subChunk.length + word.length + 1 <= maxChunkLength) {
                subChunk = subChunk ? `${subChunk} ${word}` : word;
              } else {
                if (subChunk) chunks.push(subChunk);
                subChunk = word;
              }
            }
            currentChunk = subChunk;
          }
        }
      }
    } else {
      if (currentChunk.length + s.length + 1 <= maxChunkLength) {
        currentChunk = currentChunk ? `${currentChunk} ${s}` : s;
      } else {
        if (currentChunk) chunks.push(currentChunk);
        currentChunk = s;
      }
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk);
  }

  return chunks;
}

export interface VoiceSelectionResult {
  voice: SpeechSynthesisVoice | null;
  targetLang: string;
  hasGenuineVoice: boolean;
}

/**
 * Selects an appropriate SpeechSynthesisVoice for the requested language.
 * Strictly verifies genuine Telugu support for Telugu requests, returning hasGenuineVoice: false
 * if no genuine Telugu voice is installed on the user's browser/system.
 */
export function selectBrowserVoice(
  voices: SpeechSynthesisVoice[],
  isTe: boolean
): VoiceSelectionResult {
  if (!voices || voices.length === 0) {
    return {
      voice: null,
      targetLang: isTe ? "te-IN" : "en-US",
      hasGenuineVoice: !isTe,
    };
  }

  if (isTe) {
    // Check for Telugu voice
    const teluguVoice = voices.find((v) => {
      const lang = (v.lang || "").toLowerCase();
      const name = (v.name || "").toLowerCase();
      return (
        lang.startsWith("te") ||
        lang === "te-in" ||
        lang.includes("telugu") ||
        name.includes("telugu")
      );
    });

    if (teluguVoice) {
      return {
        voice: teluguVoice,
        targetLang: teluguVoice.lang || "te-IN",
        hasGenuineVoice: true,
      };
    }

    // No genuine Telugu voice found on this device/browser
    return {
      voice: null,
      targetLang: "te-IN",
      hasGenuineVoice: false,
    };
  }

  // English voice selection: prefer en-IN, then any en voice
  const enInVoice = voices.find((v) => (v.lang || "").toLowerCase() === "en-in");
  if (enInVoice) {
    return {
      voice: enInVoice,
      targetLang: "en-IN",
      hasGenuineVoice: true,
    };
  }

  const generalEnVoice = voices.find((v) => (v.lang || "").toLowerCase().startsWith("en"));
  if (generalEnVoice) {
    return {
      voice: generalEnVoice,
      targetLang: generalEnVoice.lang || "en-US",
      hasGenuineVoice: true,
    };
  }

  // Fallback to default voice if English
  return {
    voice: voices[0] || null,
    targetLang: "en-US",
    hasGenuineVoice: true,
  };
}
