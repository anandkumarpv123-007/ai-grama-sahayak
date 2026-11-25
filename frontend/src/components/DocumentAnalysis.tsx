"use client";

import { useState, useRef, DragEvent } from "react";
import { analyzeDocument, DocumentAnalysisResponse, ApiException } from "../services/api";

interface DocumentAnalysisProps {
  language: string;
  isOffline?: boolean;
}

const DOCUMENT_TYPES = [
  { id: "income_certificate", labelEn: "Income Certificate", labelTe: "ఆదాయ ధృవీకరణ పత్రం" },
  { id: "caste_certificate", labelEn: "Caste Certificate", labelTe: "కుల ధృవీకరణ పత్రం" },
  { id: "land_record", labelEn: "Land Record (1-B / Adangal / Pattadar Passbook)", labelTe: "భూమి రికార్డు (1-బి / అడంగల్ / పట్టాదారు పాస్‌బుక్)" },
  { id: "ration_card", labelEn: "White Ration / Rice Card", labelTe: "తెల్ల రేషన్ కార్డు / బియ్యం కార్డు" },
  { id: "other", labelEn: "Other Government Welfare Document", labelTe: "ఇతర ప్రభుత్వ సంక్షేమ పత్రం" },
];

export default function DocumentAnalysis({ language, isOffline }: DocumentAnalysisProps) {
  const isTe = language === "Telugu";
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (selectedFile?: File | null) => {
    setError(null);
    setResult(null);

    if (!selectedFile) return;

    // Validate size (10 MB per API contract)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError(
        isTe
          ? "ఫైల్ పరిమాణం 10 MB కంటే ఎక్కువగా ఉంది. దయచేసి చిన్న ఫైల్‌ను ఎంచుకోండి."
          : "File size exceeds 10 MB limit. Please select a smaller document."
      );
      return;
    }

    // Validate type (PDF, JPG, PNG, WebP)
    const validTypes = ["application/pdf", "image/jpeg", "image/png", "image/jpg", "image/webp"];
    if (!validTypes.includes(selectedFile.type)) {
      setError(
        isTe
          ? "కేవలం PDF, JPG, PNG, లేదా WebP ఫైళ్లు మాత్రమే మద్దతు ఇవ్వబడతాయి."
          : "Only PDF, JPG, PNG, or WebP files are supported."
      );
      return;
    }

    setFile(selectedFile);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    validateAndSetFile(e.target.files?.[0]);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeDocument(file, docType || undefined);
      setResult(response);
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        if (err.status === 404 || err.status === 503 || err.code === "HTTP_ERROR") {
          setError(
            isTe
              ? "డాక్యుమెంట్ విశ్లేషణ సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది. (/api/documents/analyze)."
              : `Document analysis backend service is currently offline or unreachable at /api/documents/analyze. (${err.message})`
          );
        } else {
          setError(err.message);
        }
      } else {
        setError(
          isTe
            ? "సర్వరుతో అనుసంధానం కాలేకపోయింది. దయచేసి బ్యాకెండ్ సర్వరు నడుస్తుందో లేదో తనిఖీ చేయండి."
            : "Could not connect to backend server. Please verify the FastAPI backend is running."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setDocType("");
    setError(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="tool-card">
      <div className="tool-header">
        <div className="tool-icon" aria-hidden="true">📄</div>
        <div>
          <h3>{isTe ? "పత్రాల పరిశీలన & చెక్‌లిస్ట్ సహాయకుడు" : "Citizen Document Checklist & Analysis"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "ఆదాయ, కుల ధృవీకరణ పత్రాలు, రేషన్ కార్డులు, పట్టాదారు రికార్డుల లోపించిన వివరాలను పరిశీలించండి"
              : "Verify required administrative fields for certificates, rice cards & land revenue records"}
          </p>
        </div>
      </div>

      {isOffline && (
        <div className="statutory-notice-banner warning-tint" role="status">
          <span className="notice-icon">📡</span>
          <div>
            <strong>
              {isTe
                ? "నెట్‌వర్క్ అందుబాటులో లేదు (Offline Mode):"
                : "Network Connection Unavailable (Offline Mode):"}
            </strong>
            <p>
              {isTe
                ? "పత్రాల OCR మరియు ఆటోమేటెడ్ విశ్లేషణ సర్వరుకు ఇంటర్నెట్ అవసరం. నెట్‌వర్క్ పునరుద్ధరించబడిన తర్వాత పత్రాలను అప్‌లోడ్ చేయవచ్చు."
                : "Document OCR and automated extraction require an active server connection. You can review required checklist criteria offline."}
            </p>
          </div>
        </div>
      )}

      <div className="upload-controls">
        <div className="doc-select-group">
          <label className="field-label" htmlFor="doc-type-select">
            {isTe ? "పత్రం రకం ఎంపిక:" : "Document Category:"}
          </label>
          <select
            id="doc-type-select"
            className="form-select"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
          >
            <option value="">
              {isTe
                ? "✨ స్వయంచాలక గుర్తింపు (Auto-detect Document Type)"
                : "✨ Auto-detect Document Type (Recommended)"}
            </option>
            {DOCUMENT_TYPES.map((dt) => (
              <option key={dt.id} value={dt.id}>
                {isTe ? dt.labelTe : dt.labelEn}
              </option>
            ))}
          </select>
        </div>

        {/* Drag-and-drop zone */}
        <div
          className={`file-dropzone ${isDragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              fileInputRef.current?.click();
            }
          }}
          aria-label={isTe ? "ఫైల్ ఎంచుకోవడానికి ఇక్కడ నొక్కండి" : "Click or drag and drop document here"}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <span className="dropzone-icon" aria-hidden="true">
            {file ? "📋" : "📁"}
          </span>

          {file ? (
            <div className="dropzone-file-preview">
              <p className="selected-filename">
                <strong>{file.name}</strong>
              </p>
              <span className="file-size-badge">
                {(file.size / 1024).toFixed(1)} KB • {file.type || "Document"}
              </span>
              <p className="dropzone-reselect-hint">
                {isTe ? "వేరే ఫైల్ ఎంచుకోవడానికి ఇక్కడ నొక్కండి" : "Click to select a different file"}
              </p>
            </div>
          ) : (
            <div className="dropzone-empty-prompt">
              <p className="dropzone-main-text">
                <strong>
                  {isTe
                    ? "ఫైల్‌ను ఇక్కడ లాగి వదలండి (Drag & Drop) లేదా ఎంచుకోవడానికి నొక్కండి"
                    : "Drag & drop document here, or click to browse files"}
                </strong>
              </p>
              <small className="dropzone-sub-text">
                {isTe
                  ? "మద్దతు గల ఫార్మాట్లు: PDF, JPG, PNG, WebP (గరిష్టంగా 10 MB)"
                  : "Supported Formats: PDF, JPG, PNG, WebP (Maximum 10 MB)"}
              </small>
            </div>
          )}
        </div>

        {/* Upload and analysis actions */}
        <div className="action-row">
          <button
            type="button"
            className="primary-button"
            disabled={!file || isLoading}
            onClick={handleUpload}
          >
            {isLoading ? (
              <span>⏳ {isTe ? "విశ్లేషిస్తోంది..." : "Analyzing Document..."}</span>
            ) : (
              <span>🔍 {isTe ? "పత్రం పరిశీలించండి" : "Analyze Document"}</span>
            )}
          </button>

          {file && (
            <button
              type="button"
              className="secondary-button"
              onClick={resetForm}
              disabled={isLoading}
            >
              {isTe ? "రీసెట్ చేయండి" : "Reset / Clear"}
            </button>
          )}
        </div>

        {/* Loading Progress State */}
        {isLoading && (
          <div className="doc-loading-progress" role="status">
            <div className="progress-bar-track">
              <div className="progress-bar-fill"></div>
            </div>
            <p>
              {isTe
                ? "పత్రం OCR మరియు సమాచార పరిశీలన జరుగుతోంది... దయచేసి వేచి ఉండండి."
                : "Performing optical character recognition & field verification with backend..."}
            </p>
          </div>
        )}
      </div>

      {/* Error Notice */}
      {error && (
        <div className="notice-box error-notice" role="alert">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>{isTe ? "పరిశీలన గమనిక" : "Notice"}</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Structured Analysis Results */}
      {result && (
        <div className="results-container">
          <div className="results-header">
            <h4>{isTe ? "పరిశీలన ఫలితాలు" : "Document Assessment Results"}</h4>
            <span className={`status-badge status-${result.checklist_status}`}>
              {result.checklist_status === "complete"
                ? isTe ? "పూర్తయింది ✓" : "Complete ✓"
                : result.checklist_status === "partially_complete"
                ? isTe ? "పాక్షిక వివరాలు ఉన్నవి" : "Partially Complete"
                : isTe ? "అసంపూర్ణం (లోపాలున్నవి)" : "Incomplete"}
            </span>
          </div>

          <div className="doc-field-row">
            <span className="field-name">
              {isTe ? "గుర్తించిన పత్రం రకం:" : "Identified Document Type:"}
            </span>
            <span className="field-value">
              <strong>{result.document_type || (isTe ? "గుర్తించబడలేదు" : "Not Determined")}</strong>
            </span>
          </div>

          {/* Extracted Fields Table */}
          {result.extracted_fields && Object.keys(result.extracted_fields).length > 0 && (
            <div className="fields-table-wrapper">
              <h5>{isTe ? "సేకరించబడిన వివరాలు (Extracted Data):" : "Extracted Fields:"}</h5>
              <table className="fields-table">
                <thead>
                  <tr>
                    <th>{isTe ? "వివరణ ఫీల్డ్" : "Field Name"}</th>
                    <th>{isTe ? "విలువ" : "Value"}</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.extracted_fields).map(([k, v]) => (
                    <tr key={k}>
                      <td className="field-key">{k.replace(/_/g, " ")}</td>
                      <td className="field-val">
                        {v !== null && v !== undefined ? String(v) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Missing Fields Warning */}
          {result.missing_fields && result.missing_fields.length > 0 && (
            <div className="missing-fields-section">
              <h5>
                ⚠️ {isTe ? "సచివాలయ దరఖాస్తుకు అవసరమైన లోపించిన వివరాలు:" : "Required Information Missing from Document:"}
              </h5>
              <p className="missing-hint">
                {isTe
                  ? "ఈ క్రింది వివరాలు పత్రంలో స్పష్టంగా లేవు. దరఖాస్తు తిరస్కరణ కాకుండా ఉండటానికి వీటిని సిద్ధం చేసుకోండి:"
                  : "The following fields could not be substantiated. Please have these ready before submitting to Grama Sachivalayam:"}
              </p>
              <div className="tag-list">
                {result.missing_fields.map((mf, idx) => (
                  <span key={idx} className="missing-tag">
                    ✕ {mf.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Warnings & OCR Uncertainty */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="warnings-section">
              <h5>ℹ️ {isTe ? "ముఖ్య గమనికలు & పరిశీలనలు:" : "Verification Advisories & OCR Notes:"}</h5>
              <ul>
                {result.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Mandatory Privacy & Authenticity Notice */}
      <div className="privacy-disclaimer">
        <span>🔒</span>
        <small>
          {isTe
            ? "గోప్యతా & చట్టపరమైన నిరాకరణ: ఇది ప్రాథమిక అడ్మినిస్ట్రేటివ్ చెక్‌లిస్ట్ పరిశీలన సాధనం మాత్రమే. ఇది అసలైన పత్రాల చట్టపరమైన ధృవీకరణ (Authenticity Verification) కాదు. వ్యక్తిగత సున్నిత సమాచారం శాశ్వతంగా భద్రపరచబడదు. తుది ధృవీకరణ మీ గ్రామ/వార్డు సచివాలయంలో సంబంధిత అధికారులచే బయోమెట్రిక్ ద్వారా చేయబడుతుంది."
            : "Privacy & Statutory Disclaimer: Preliminary administrative completeness check only. Does not certify legal authenticity. Personal data is not stored. Final statutory verification is conducted at your Grama/Ward Sachivalayam through competent revenue authorities."}
        </small>
      </div>
    </div>
  );
}
