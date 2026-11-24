"use client";

export interface SavedQuestion {
  id: string;
  text: string;
  category: string;
  language: string;
  savedAt: string;
}

const STORAGE_KEY = "grama_saved_questions_v1";

/**
 * Retrieves pending saved questions from local storage.
 * Privacy safe: Only contains citizen questions saved explicitly by the user.
 */
export function getSavedQuestions(): SavedQuestion[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * Saves a question for later manual retry when online.
 * Prevents exact duplicate submissions.
 */
export function saveQuestionForLater(
  text: string,
  category: string,
  language: string
): { success: boolean; question?: SavedQuestion; message?: string } {
  const trimmed = text.trim();
  if (!trimmed) {
    return { success: false, message: "Question cannot be empty" };
  }

  const existing = getSavedQuestions();

  // Prevent duplicate submissions
  const isDuplicate = existing.some(
    (q) => q.text.toLowerCase().trim() === trimmed.toLowerCase()
  );
  if (isDuplicate) {
    return {
      success: false,
      message:
        language === "Telugu"
          ? "ఈ ప్రశ్న ఇప్పటికే సేవ్ చేయబడింది."
          : "This question is already in your saved queue.",
    };
  }

  const newQuestion: SavedQuestion = {
    id: `q_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    text: trimmed,
    category,
    language,
    savedAt: new Date().toISOString(),
  };

  try {
    const updated = [newQuestion, ...existing];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    return { success: true, question: newQuestion };
  } catch {
    return { success: false, message: "Storage quota exceeded or unavailable." };
  }
}

/**
 * Deletes an individual saved question by ID.
 */
export function deleteSavedQuestion(id: string): SavedQuestion[] {
  const existing = getSavedQuestions();
  const updated = existing.filter((q) => q.id !== id);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // ignore
  }
  return updated;
}

/**
 * Privacy Action: Wipes all saved citizen questions and cached data completely.
 * Satisfies Task 5 Privacy requirements.
 */
export function clearAllSavedData(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    // Also remove any other local offline caches
    const keysToRemove = Object.keys(localStorage).filter((k) => k.startsWith("grama_"));
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  } catch {
    // ignore
  }
}
