import test from "node:test";
import assert from "node:assert/strict";

// Mock localStorage for node environment
globalThis.localStorage = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (i) => Object.keys(store)[i] || null,
  };
})();
globalThis.window = globalThis;

const {
  validateQuestionPrivacy,
  saveQuestionForLater,
  getSavedQuestions,
  deleteSavedQuestion,
  clearAllSavedData,
  PREDEFINED_PUBLIC_QUESTIONS,
} = await import("./savedQuestions.ts");

test("validateQuestionPrivacy allows safe public questions", () => {
  const safeQuestions = [
    "What are the guidelines for PM-KISAN e-KYC?",
    "పీఎం-కిసాన్ ఈ-కేవైసీ కొరకు అవసరమైన అధికారిక పత్రాలు ఏమిటి?",
    "How to apply for Old Age Pension at Grama Sachivalayam?",
    "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద ఏ చికిత్సలు అందుబాటులో ఉంటాయి?",
  ];

  for (const q of safeQuestions) {
    const res = validateQuestionPrivacy(q);
    assert.equal(res.isValid, true, `Expected "${q}" to be valid`);
  }
});

test("validateQuestionPrivacy rejects 12-digit Aadhaar numbers", () => {
  const dangerousQuestions = [
    "My Aadhaar is 1234 5678 9012, is my pension active?",
    "నా ఆధార్ నంబర్ 987654321098 రైతు భరోసా వచ్చిందా?",
    "Check status for 1111-2222-3333 please",
  ];

  for (const q of dangerousQuestions) {
    const res = validateQuestionPrivacy(q);
    assert.equal(res.isValid, false, `Expected "${q}" to be rejected`);
    assert.match(res.reasonEn, /Aadhaar/i);
  }
});

test("validateQuestionPrivacy rejects bank account numbers", () => {
  const q = "Please credit money to account 123456789012345";
  const res = validateQuestionPrivacy(q);
  assert.equal(res.isValid, false);
  assert.match(res.reasonEn, /bank account/i);
});

test("validateQuestionPrivacy rejects 10-digit mobile numbers", () => {
  const q = "Call me back at 9876543210 regarding my application";
  const res = validateQuestionPrivacy(q);
  assert.equal(res.isValid, false);
  assert.match(res.reasonEn, /mobile number/i);
});

test("validateQuestionPrivacy rejects IFSC codes and OTP mentions", () => {
  const qIfsc = "My bank is SBIN0001234 in Kakinada";
  assert.equal(validateQuestionPrivacy(qIfsc).isValid, false);

  const qOtp = "I received OTP 458921 on my phone";
  assert.equal(validateQuestionPrivacy(qOtp).isValid, false);
});

test("saveQuestionForLater enforces consent and duplicate prevention", () => {
  clearAllSavedData();

  // Test consent enforcement
  const noConsent = saveQuestionForLater("Safe public question", "schemes", "Telugu", false);
  assert.equal(noConsent.success, false);
  assert.match(noConsent.message, /గోప్యతా నిబంధనలను/);

  // Test successful save with consent
  const saved = saveQuestionForLater("Safe public question", "schemes", "Telugu", true);
  assert.equal(saved.success, true);
  assert.equal(getSavedQuestions().length, 1);

  // Test duplicate prevention
  const dup = saveQuestionForLater("Safe public question", "schemes", "Telugu", true);
  assert.equal(dup.success, false);
  assert.match(dup.message, /ఇప్పటికే సేవ్ చేయబడింది/);
  assert.equal(getSavedQuestions().length, 1);
});

test("deleteSavedQuestion and clearAllSavedData wipe local drafts cleanly", () => {
  clearAllSavedData();
  const q1 = saveQuestionForLater("Question 1", "schemes", "English", true).question;
  const q2 = saveQuestionForLater("Question 2", "healthcare", "English", true).question;
  assert.equal(getSavedQuestions().length, 2);

  deleteSavedQuestion(q1.id);
  assert.equal(getSavedQuestions().length, 1);
  assert.equal(getSavedQuestions()[0].id, q2.id);

  clearAllSavedData();
  assert.equal(getSavedQuestions().length, 0);
});

test("PREDEFINED_PUBLIC_QUESTIONS has non-empty bilingual items", () => {
  assert.ok(PREDEFINED_PUBLIC_QUESTIONS.length >= 5);
  for (const item of PREDEFINED_PUBLIC_QUESTIONS) {
    assert.ok(item.titleTe.length > 5);
    assert.ok(item.titleEn.length > 5);
    assert.ok(["schemes", "healthcare", "education", "agriculture"].includes(item.category));
  }
});
