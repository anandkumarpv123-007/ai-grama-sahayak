"use client";

import { useState, useRef } from "react";
import { analyzeDocument, DocumentAnalysisResponse, ApiException } from "../services/api";

interface DocumentAnalysisProps {
  language: string;
}

const DOCUMENT_TYPES = [
  { id: "income_certificate", labelEn: "Income Certificate", labelTe: "ఆదాయ ధృవీకరణ పత్రం" },
  { id: "caste_certificate", labelEn: "Caste Certificate", labelTe: "కుల ధృవీకరణ పత్రం" },
  { id: "land_record", labelEn: "Land Record (1-B / Adangal)", labelTe: "భూమి రికార్డు (1-బి / అడంగల్)" },
  { id: "ration_card", labelEn: "Ration Card", labelTe: "రేషన్ కార్డు" },
  { id: "other", labelEn: "Other Official Document", labelTe: "ఇతర అధికారిక పత్రం" },
];

export default function DocumentAnalysis({ language }: DocumentAnalysisProps) {
  const isTe = language === "Telugu";
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setResult(null);

    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate size (10 MB per contract)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError(
        isTe
          ? "ఫైల్ పరిమాణం 10 MB కంటే ఎక్కువగా ఉంది. దయచేసి చిన్న ఫైల్‌ను ఎంచుకోండి."
          : "File size exceeds 10 MB limit. Please select a smaller file."
      );
      return;
    }

    // Validate type (PDF, JPG, PNG)
    const validTypes = ["application/pdf", "image/jpeg", "image/png", "image/jpg"];
    if (!validTypes.includes(selectedFile.type)) {
      setError(
        isTe
          ? "కేవలం PDF, JPG, లేదా PNG ఫైళ్లు మాత్రమే మద్దతు ఇవ్వబడతాయి."
          : "Only PDF, JPG, or PNG files are supported."
      );
      return;
    }

    setFile(selectedFile);
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
              ? "డాక్యుమెంట్ విశ్లేషణ సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది. (Member 4 బాధ్యత: /api/documents/analyze)."
              : `Document analysis backend service is currently offline or unavailable at /api/documents/analyze. (${err.message})`
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
        <div className="tool-icon">📄</div>
        <div>
          <h3>{isTe ? "పత్రాల విశ్లేషణ & ధృవీకరణ" : "Document Analysis & Verification"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "ధృవీకరణ పత్రాలు, రేషన్ కార్డులు, భూమి రికార్డులను తనిఖీ చేయండి"
              : "Check income, caste certificates, land records & welfare documents"}
          </p>
        </div>
      </div>

      <div className="upload-controls">
        <label className="field-label" htmlFor="doc-type-select">
          {isTe ? "పత్రం రకం (ఐచ్ఛికం)" : "Document Type (Optional)"}
        </label>
        <select
          id="doc-type-select"
          className="form-select"
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
        >
          <option value="">{isTe ? "-- స్వయంచాలక గుర్తింపు --" : "-- Auto-detect --"}</option>
          {DOCUMENT_TYPES.map((dt) => (
            <option key={dt.id} value={dt.id}>
              {isTe ? dt.labelTe : dt.labelEn}
            </option>
          ))}
        </select>

        <div className="file-dropzone" onClick={() => fileInputRef.current?.click()}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <span className="dropzone-icon">📁</span>
          {file ? (
            <p className="selected-filename">
              <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
            </p>
          ) : (
            <div>
              <p>
                <strong>{isTe ? "ఫైల్ ఎంచుకోవడానికి ఇక్కడ నొక్కండి" : "Click to select a file"}</strong>
              </p>
              <small>{isTe ? "మద్దతు గల ఫార్మాట్లు: PDF, JPG, PNG (గరిష్టంగా 10 MB)" : "Supported: PDF, JPG, PNG (Max 10 MB)"}</small>
            </div>
          )}
        </div>

        <div className="action-row">
          <button
            className="primary-button"
            disabled={!file || isLoading}
            onClick={handleUpload}
          >
            {isLoading
              ? isTe
                ? "విశ్లేషిస్తోంది..."
                : "Analyzing..."
              : isTe
              ? "పత్రం విశ్లేషించండి"
              : "Analyze Document"}
          </button>

          {file && (
            <button className="secondary-button" onClick={resetForm} disabled={isLoading}>
              {isTe ? "రీసెట్" : "Reset"}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="notice-box error-notice" role="alert">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>{isTe ? "సమాచారం" : "Notice"}</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="results-container">
          <div className="results-header">
            <h4>{isTe ? "విశ్లేషణ ఫలితాలు" : "Analysis Results"}</h4>
            <span className={`status-badge status-${result.checklist_status}`}>
              {result.checklist_status === "complete"
                ? isTe ? "పూర్తయింది ✓" : "Complete ✓"
                : result.checklist_status === "partially_complete"
                ? isTe ? "పాక్షికంగా ఉంది" : "Partially Complete"
                : isTe ? "అసంపూర్ణం" : "Incomplete"}
            </span>
          </div>

          <div className="doc-field-row">
            <span className="field-name">{isTe ? "గుర్తించిన పత్రం రకం:" : "Identified Type:"}</span>
            <span className="field-value">{result.document_type || "N/A"}</span>
          </div>

          {result.extracted_fields && Object.keys(result.extracted_fields).length > 0 && (
            <div className="fields-table-wrapper">
              <h5>{isTe ? "సేకరించిన వివరాలు:" : "Extracted Fields:"}</h5>
              <table className="fields-table">
                <tbody>
                  {Object.entries(result.extracted_fields).map(([k, v]) => (
                    <tr key={k}>
                      <td className="field-key">{k.replace(/_/g, " ")}</td>
                      <td className="field-val">{v !== null && v !== undefined ? String(v) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.missing_fields && result.missing_fields.length > 0 && (
            <div className="missing-fields-section">
              <h5>{isTe ? "లోపించిన వివరాలు:" : "Missing Fields:"}</h5>
              <div className="tag-list">
                {result.missing_fields.map((mf, idx) => (
                  <span key={idx} className="missing-tag">
                    {mf.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.warnings && result.warnings.length > 0 && (
            <div className="warnings-section">
              <h5>{isTe ? "హెచ్చరికలు:" : "Warnings:"}</h5>
              <ul>
                {result.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="privacy-disclaimer">
        <span>🔒</span>
        <small>
          {isTe
            ? "గోప్యతా గమనిక: దయచేసి పరీక్షించడానికి డెమో పత్రాలను మాత్రమే ఉపయోగించండి. వ్యక్తిగత సున్నిత వివరాలు భద్రపరచబడవు."
            : "Privacy Notice: Use synthetic or non-confidential sample documents for testing. Extracted information must always be verified against official originals."}
        </small>
      </div>
    </div>
  );
}
