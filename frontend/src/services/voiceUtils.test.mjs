import test from "node:test";
import assert from "node:assert/strict";
import {
  cleanTextForSpeech,
  prepareSpeechText,
  splitIntoSentenceChunks,
  selectBrowserVoice,
  getSupportedMimeType,
  getAudioFilenameAndType,
  formatDuration,
} from "./voiceUtils.ts";

test("cleanTextForSpeech removes markdown formatting and URLs", () => {
  const input = "### Scheme Details\n\n**Rythu Bharosa** provides financial assistance. Visit [Official Portal](https://example.com) or read `guide.pdf`.";
  const output = cleanTextForSpeech(input);
  assert.equal(output.includes("###"), false);
  assert.equal(output.includes("**"), false);
  assert.equal(output.includes("`"), false);
  assert.equal(output.includes("https://"), false);
  assert.equal(output.includes("Official Portal"), true);
  assert.equal(output.includes("Rythu Bharosa provides financial assistance"), true);
});

test("prepareSpeechText leaves text under limit intact", () => {
  const text = "Hello citizen, this is a short welfare response.";
  const res = prepareSpeechText(text, 1000, false);
  assert.equal(res.wasTruncated, false);
  assert.equal(res.textToSpeak, text);
});

test("prepareSpeechText breaks at sentence boundary when exceeding limit", () => {
  const sentence1 = "First sentence about agriculture schemes.";
  const sentence2 = "Second sentence with subsidy numbers.";
  const sentence3 = "Third sentence about documentation.";
  const fullText = `${sentence1} ${sentence2} ${sentence3}`;

  const res = prepareSpeechText(fullText, 90, false);
  assert.equal(res.wasTruncated, true);
  assert.equal(res.textToSpeak.includes(sentence1), true);
  assert.equal(res.textToSpeak.includes("Full details are displayed on screen"), true);
  assert.ok(res.textToSpeak.length <= 100);
});

test("prepareSpeechText handles Telugu sentences and danda terminator", () => {
  const sentence1 = "రైతు భరోసా పథకం ద్వారా ఆర్థిక సహాయం అందుతుంది.";
  const sentence2 = "ఇది మూడు విడతలలో చెల్లించబడుతుంది.";
  const fullText = `${sentence1} ${sentence2}`;

  const res = prepareSpeechText(fullText, 45, true);
  assert.equal(res.wasTruncated, true);
  assert.equal(res.textToSpeak.includes("మరిన్ని వివరాలు స్క్రీన్‌పై"), true);
});

test("splitIntoSentenceChunks creates short bounded segments", () => {
  const longText = "First sentence. Second sentence with details! Third question? Fourth statement। Fifth part.";
  const chunks = splitIntoSentenceChunks(longText, 50);
  assert.ok(chunks.length > 1);
  for (const chunk of chunks) {
    assert.ok(chunk.length <= 60);
  }
  // All words preserved
  assert.equal(longText.split(" ").length, chunks.join(" ").split(" ").length);
});

test("selectBrowserVoice detects Telugu voice or reports missing", () => {
  const mockVoicesOnlyEnglish = [
    { name: "Microsoft David", lang: "en-US" },
    { name: "Google UK English Female", lang: "en-GB" },
  ];

  const resTeMissing = selectBrowserVoice(mockVoicesOnlyEnglish, true);
  assert.equal(resTeMissing.hasGenuineVoice, false);
  assert.equal(resTeMissing.voice, null);

  const mockVoicesWithTelugu = [
    { name: "Microsoft David", lang: "en-US" },
    { name: "Google తెలుగు", lang: "te-IN" },
  ];

  const resTeFound = selectBrowserVoice(mockVoicesWithTelugu, true);
  assert.equal(resTeFound.hasGenuineVoice, true);
  assert.equal(resTeFound.voice.name, "Google తెలుగు");
});

test("selectBrowserVoice selects English voice for English requests", () => {
  const mockVoices = [
    { name: "Google US English", lang: "en-US" },
    { name: "Google India English", lang: "en-IN" },
  ];

  const resEn = selectBrowserVoice(mockVoices, false);
  assert.equal(resEn.hasGenuineVoice, true);
  assert.equal(resEn.voice.lang, "en-IN");

  // Fallback to general English when en-IN is unavailable
  const resGeneralEn = selectBrowserVoice([{ name: "Microsoft David", lang: "en-US" }], false);
  assert.equal(resGeneralEn.hasGenuineVoice, true);
  assert.equal(resGeneralEn.targetLang, "en-US");
  assert.equal(resGeneralEn.voice.name, "Microsoft David");

  // Handles empty voices gracefully
  const resEmptyEn = selectBrowserVoice([], false);
  assert.equal(resEmptyEn.hasGenuineVoice, true);
  assert.equal(resEmptyEn.targetLang, "en-US");

  const resEmptyTe = selectBrowserVoice([], true);
  assert.equal(resEmptyTe.hasGenuineVoice, false);
  assert.equal(resEmptyTe.targetLang, "te-IN");
});

test("getSupportedMimeType selects first supported format or falls back", () => {
  // Mock where webm is supported
  const checkWebm = (t) => t.includes("webm");
  assert.equal(getSupportedMimeType(checkWebm), "audio/webm;codecs=opus");

  // Mock where only mp4 is supported (e.g. Safari)
  const checkMp4 = (t) => t.includes("mp4");
  assert.equal(getSupportedMimeType(checkMp4), "audio/mp4");

  // Mock where nothing is supported
  assert.equal(getSupportedMimeType(() => false), "");

  // Missing function / window
  assert.equal(getSupportedMimeType(null), "");
});

test("getAudioFilenameAndType maps blob formats accurately without renaming WebM to WAV", () => {
  // WebM container
  const webm = getAudioFilenameAndType({ type: "audio/webm;codecs=opus" });
  assert.equal(webm.filename, "recording.webm");
  assert.equal(webm.mimeType, "audio/webm");

  // MP4 / M4A container (Safari)
  const mp4 = getAudioFilenameAndType({ type: "audio/mp4" });
  assert.equal(mp4.filename, "recording.m4a");
  assert.equal(mp4.mimeType, "audio/mp4");

  // Ogg container
  const ogg = getAudioFilenameAndType({ type: "audio/ogg;codecs=opus" });
  assert.equal(ogg.filename, "recording.ogg");
  assert.equal(ogg.mimeType, "audio/ogg");

  // WAV container
  const wav = getAudioFilenameAndType({ type: "audio/wav" });
  assert.equal(wav.filename, "recording.wav");
  assert.equal(wav.mimeType, "audio/wav");

  // Fallback / empty type
  const fallback = getAudioFilenameAndType({ type: "" });
  assert.equal(fallback.filename, "recording.webm");
  assert.equal(fallback.mimeType, "audio/webm");
});

test("formatDuration formats seconds to mm:ss cleanly", () => {
  assert.equal(formatDuration(0), "00:00");
  assert.equal(formatDuration(7), "00:07");
  assert.equal(formatDuration(30), "00:30");
  assert.equal(formatDuration(65), "01:05");
  assert.equal(formatDuration(-5), "00:00");
});
