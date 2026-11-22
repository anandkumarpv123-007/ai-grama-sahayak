/**
 * AI Grama Sahayak API Client
 * Author: Member 3
 * Adheres strictly to docs/api_contracts.md
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export interface Source {
  title: string;
  url: string;
  publisher: string;
  verified_at: string;
}

export interface ChatRequest {
  message: string;
  assistant: "agriculture" | "healthcare" | "education" | "schemes";
  language: "en" | "te";
  state?: string;
  district?: string | null;
  conversation_id?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  assistant: string;
  language: string;
  sources: Source[];
  needs_follow_up: boolean;
  follow_up_questions: string[];
  safety_notice: string | null;
}

export interface VoiceTranscribeResponse {
  transcribed_text: string;
  language: string;
  confidence: number;
}

export interface VoiceSpeakResponse {
  audio_base64: string;
  mime_type: string;
  language: string;
}

export interface DocumentAnalysisResponse {
  document_type: string;
  extracted_fields: Record<string, string | number | null>;
  checklist_status: string;
  missing_fields: string[];
  warnings: string[];
}

export interface GovernmentService {
  name: string;
  service_type: string;
  address: string;
  phone: string | null;
  distance_km: number | null;
  source_url: string | null;
}

export interface NearbyServicesResponse {
  services: GovernmentService[];
}

export interface GrievanceDraftRequest {
  category: string;
  description: string;
  district: string;
  mandal: string;
  language: "en" | "te";
}

export interface GrievanceOfficialLink {
  title?: string;
  url: string;
}

export interface GrievanceDraftResponse {
  subject: string;
  complaint_body: string;
  recommended_next_steps: string[];
  official_links: (string | GrievanceOfficialLink)[];
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown[];
}

export class ApiException extends Error {
  code: string;
  status: number;
  details?: unknown[];

  constructor(message: string, code: string = "API_ERROR", status: number = 500, details?: unknown[]) {
    super(message);
    this.name = "ApiException";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorCode = "HTTP_ERROR";
    let errorMessage = `Server returned error status ${res.status} (${res.statusText})`;
    let details: unknown[] | undefined;

    try {
      const errorJson = await res.json();
      if (errorJson?.error) {
        errorCode = errorJson.error.code || errorCode;
        errorMessage = errorJson.error.message || errorMessage;
        details = errorJson.error.details;
      }
    } catch {
      // response body was not valid JSON
    }

    throw new ApiException(errorMessage, errorCode, res.status, details);
  }

  return (await res.json()) as T;
}

/**
 * Send chat message to backend (Member 1)
 */
export async function sendChatMessage(
  payload: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const url = `${API_BASE_URL}/api/chat`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  return handleResponse<ChatResponse>(res);
}

/**
 * Transcribe recorded audio (Member 3)
 */
export async function transcribeAudio(
  audioBlob: Blob,
  language: "en" | "te" = "en",
  signal?: AbortSignal
): Promise<VoiceTranscribeResponse> {
  const url = `${API_BASE_URL}/api/voice/transcribe`;
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.wav");
  formData.append("language", language);

  const res = await fetch(url, {
    method: "POST",
    body: formData,
    signal,
  });

  return handleResponse<VoiceTranscribeResponse>(res);
}

/**
 * Synthesize text into speech (Member 3)
 */
export async function synthesizeSpeech(
  text: string,
  language: "en" | "te" = "en",
  signal?: AbortSignal
): Promise<VoiceSpeakResponse> {
  const url = `${API_BASE_URL}/api/voice/speak`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, language }),
    signal,
  });

  return handleResponse<VoiceSpeakResponse>(res);
}

/**
 * Upload and analyze citizen document (Member 4)
 */
export async function analyzeDocument(
  file: File,
  documentType?: string,
  signal?: AbortSignal
): Promise<DocumentAnalysisResponse> {
  const url = `${API_BASE_URL}/api/documents/analyze`;
  const formData = new FormData();
  formData.append("file", file);
  if (documentType) {
    formData.append("document_type", documentType);
  }

  const res = await fetch(url, {
    method: "POST",
    body: formData,
    signal,
  });

  return handleResponse<DocumentAnalysisResponse>(res);
}

/**
 * Fetch nearby government services (Member 4)
 */
export async function getNearbyServices(
  params: {
    service_type?: string;
    district?: string;
    latitude?: number;
    longitude?: number;
  },
  signal?: AbortSignal
): Promise<NearbyServicesResponse> {
  const query = new URLSearchParams();
  if (params.service_type) query.append("service_type", params.service_type);
  if (params.district) query.append("district", params.district);
  if (params.latitude !== undefined && params.longitude !== undefined) {
    query.append("latitude", params.latitude.toString());
    query.append("longitude", params.longitude.toString());
  }

  const url = `${API_BASE_URL}/api/services/nearby?${query.toString()}`;
  const res = await fetch(url, {
    method: "GET",
    signal,
  });

  return handleResponse<NearbyServicesResponse>(res);
}

/**
 * Draft a citizen grievance (Member 4)
 */
export async function draftGrievance(
  payload: GrievanceDraftRequest,
  signal?: AbortSignal
): Promise<GrievanceDraftResponse> {
  const url = `${API_BASE_URL}/api/grievances/draft`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  return handleResponse<GrievanceDraftResponse>(res);
}
