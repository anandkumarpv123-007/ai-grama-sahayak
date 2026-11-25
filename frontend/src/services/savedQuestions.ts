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
 * Predefined public questions that are guaranteed to be safe and contain no personal data.
 */
export const PREDEFINED_PUBLIC_QUESTIONS = [
  {
    category: "schemes",
    titleTe: "పీఎం-కిసాన్ ఈ-కేవైసీ కొరకు అవసరమైన అధికారిక పత్రాలు ఏమిటి?",
    titleEn: "What are the required documents for PM-KISAN e-KYC?",
  },
  {
    category: "schemes",
    titleTe: "ఎన్టీఆర్ భరోసా వృద్ధాప్య పింఛను అర్హత వయస్సు మరియు దరఖాస్తు విధానం ఏమిటి?",
    titleEn: "What is the qualifying age and Sachivalayam process for NTR Bharosa Pension?",
  },
  {
    category: "healthcare",
    titleTe: "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద నెట్‌వర్క్ ఆసుపత్రుల్లో ఏ చికిత్సలు వర్తిస్తాయి?",
    titleEn: "Which treatments and hospital procedures are covered under Dr. NTR Vaidya Seva?",
  },
  {
    category: "education",
    titleTe: "పాఠశాల విద్యా ప్రోత్సాహకం కొరకు తల్లికి వందనం పథకం మార్గదర్శకాలు ఏమిటి?",
    titleEn: "What are the guidelines for Thalliki Vandanam school education assistance?",
  },
  {
    category: "agriculture",
    titleTe: "రైతు భరోసా కేంద్రం (RBK) ద్వారా ఈ-క్రాప్ నమోదు ఎలా సరిచూసుకోవాలి?",
    titleEn: "How to verify e-Crop booking through the Rythu Bharosa Kendram (RBK)?",
  },
];

/**
 * Validates text for sensitive personal identifiers before saving.
 * Rejects Aadhaar-like numbers, bank accounts, phone numbers, IFSC, OTPs, etc.
 *
 * NOTE: Pattern detection is an automated preliminary filter and cannot guarantee
 * complete privacy. Citizens are explicitly instructed not to store confidential details.
 */
export function validateQuestionPrivacy(text: string): { isValid: boolean; reasonEn?: string; reasonTe?: string } {
  const trimmed = text.trim();
  if (!trimmed) {
    return {
      isValid: false,
      reasonEn: "Question cannot be empty.",
      reasonTe: "ప్రశ్న ఖాళీగా ఉండకూడదు.",
    };
  }

  // 1. Aadhaar-like 12-digit number (continuous or 4-4-4)
  const aadhaarRegex = /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/;
  if (aadhaarRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Sensitive identifier detected: Potential 12-digit Aadhaar number found. Please remove personal IDs before saving.",
      reasonTe: "వ్యక్తిగత వివరాలు గుర్తించబడ్డాయి: 12 అంకెల ఆధార్ సంఖ్యను పోలిన వివరాలు ఉన్నాయి. దయచేసి వ్యక్తిగత సమాచారాన్ని తొలగించండి.",
    };
  }

  // 2. Indian Mobile numbers (10 digits starting with 6, 7, 8, or 9)
  const phoneRegex = /\b[6-9]\d{9}\b/;
  if (phoneRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Personal identifier detected: 10-digit mobile number found. Please remove contact numbers before saving.",
      reasonTe: "వ్యక్తిగత ఫోన్ నంబర్ గుర్తించబడింది. దయచేసి ఫోన్ నంబర్లను తొలగించి సాధారణ ప్రశ్నను మాత్రమే సేవ్ చేయండి.",
    };
  }

  // 3. Bank account numbers (9 to 18 consecutive digits)
  const bankAccRegex = /\b\d{9,18}\b/;
  if (bankAccRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Sensitive financial data detected: Long numeric string resembling a bank account or card number. Please remove before saving.",
      reasonTe: "బ్యాంక్ ఖాతా లేదా కార్డు సంఖ్యను పోలిన అంకెలు గుర్తించబడ్డాయి. దయచేసి ఆర్థిక వివరాలను తొలగించండి.",
    };
  }

  // 4. IFSC code pattern (4 letters, 0, 6 alphanumerics)
  const ifscRegex = /\b[A-Za-z]{4}0[A-Za-z0-9]{6}\b/;
  if (ifscRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Banking code detected: IFSC code found. Please remove financial institution codes before saving.",
      reasonTe: "బ్యాంక్ ఐఎఫ్‌ఎస్‌సీ (IFSC) కోడ్ గుర్తించబడింది. దయచేసి బ్యాంకింగ్ వివరాలను తొలగించండి.",
    };
  }

  // 5. OTP / PIN / Passcode mentions with nearby numbers
  const otpWordRegex = /\b(?:otp|one[\s-]?time[\s-]?password|cvv|passcode|ఓటీపీ|పిన్|పాస్‌వర్డ్)\b/i;
  if (otpWordRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Security credential keyword detected (OTP/PIN/Passcode). Never record security codes.",
      reasonTe: "భద్రతా కోడ్ (OTP/PIN) వివరాలు గుర్తించబడ్డాయి. పాస్‌వర్డ్‌లు లేదా ఓటీపీలను ఎప్పుడూ నమోదు చేయవద్దు.",
    };
  }

  // 6. Explicit Aadhaar or bank account labels with digits
  const sensitiveLabelRegex = /\b(?:aadhaar|aadhar|bank account|account no|ac no|ఖాతా సంఖ్య|ఆధార్ నంబర్)\s*[:=]?\s*\d+/i;
  if (sensitiveLabelRegex.test(trimmed)) {
    return {
      isValid: false,
      reasonEn: "Confidential account/identity reference detected. Please remove sensitive details before saving.",
      reasonTe: "వ్యక్తిగత ఖాతా లేదా గుర్తింపు వివరాలు గుర్తించబడ్డాయి. దయచేసి గోప్యతా సమాచారాన్ని తొలగించండి.",
    };
  }

  return { isValid: true };
}

/**
 * Retrieves pending saved questions from local storage.
 * Privacy safe: Only contains non-sensitive public inquiries saved explicitly by the user.
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
 * Saves a non-sensitive public question for later manual submission when online.
 * Enforces explicit citizen consent, duplicate prevention, and sensitive identifier rejection.
 * Saved questions are NEVER automatically transmitted.
 */
export function saveQuestionForLater(
  text: string,
  category: string,
  language: string,
  consentGiven: boolean = true
): { success: boolean; question?: SavedQuestion; message?: string } {
  const isTe = language === "Telugu";
  const trimmed = text.trim();

  if (!trimmed) {
    return {
      success: false,
      message: isTe ? "ప్రశ్న ఖాళీగా ఉండకూడదు." : "Question cannot be empty.",
    };
  }

  // 1. Enforce explicit citizen consent
  if (!consentGiven) {
    return {
      success: false,
      message: isTe
        ? "ప్రశ్నను సేవ్ చేయడానికి దయచేసి గోప్యతా నిబంధనలను అంగీకరించండి."
        : "Citizen consent is required to store questions locally.",
    };
  }

  // 2. Reject obvious sensitive identifiers
  const validation = validateQuestionPrivacy(trimmed);
  if (!validation.isValid) {
    return {
      success: false,
      message: isTe ? validation.reasonTe : validation.reasonEn,
    };
  }

  const existing = getSavedQuestions();

  // 3. Prevent duplicate submissions
  const isDuplicate = existing.some(
    (q) => q.text.toLowerCase().trim() === trimmed.toLowerCase()
  );
  if (isDuplicate) {
    return {
      success: false,
      message: isTe
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
    return {
      success: false,
      message: isTe ? "బ్రౌజర్ మెమరీ అందుబాటులో లేదు." : "Storage quota exceeded or unavailable.",
    };
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
 * Privacy Action: Wipes all locally saved question drafts from this browser.
 * Does not alter official Sachivalayam records or server databases.
 */
export function clearAllSavedData(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    // Also clean up any other local draft keys
    const keysToRemove = Object.keys(localStorage).filter((k) => k.startsWith("grama_"));
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  } catch {
    // ignore
  }
}
