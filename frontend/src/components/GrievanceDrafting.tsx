"use client";

import { useState } from "react";
import { draftGrievance, GrievanceDraftResponse, ApiException } from "../services/api";

interface GrievanceDraftingProps {
  language: string;
}

const GRIEVANCE_CATEGORIES = [
  { id: "water_supply", labelEn: "Drinking Water Supply", labelTe: "తాగునీటి సరఫరా సమస్య" },
  { id: "electricity", labelEn: "Electricity & Power Outage", labelTe: "విద్యుత్ సరఫరా & స్తంభాల సమస్య" },
  { id: "roads", labelEn: "Roads & Street Infrastructure", labelTe: "రహదారులు & వీధి లైట్ల మరమ్మత్తు" },
  { id: "ration", labelEn: "Ration & PDS Distribution", labelTe: "రేషన్ & పౌరసరఫరాల సమస్య" },
  { id: "drainage", labelEn: "Sanitation & Drainage Cleaning", labelTe: "పారిశుధ్యం & డ్రైనేజీ సమస్య" },
  { id: "welfare", labelEn: "Welfare Scheme Delay / Issue", labelTe: "సంక్షేమ పథకం మంజూరులో ఆలస్యం" },
  { id: "other", labelEn: "Other Citizen Grievance", labelTe: "ఇతర ప్రజా ఫిర్యాదు" },
];

export default function GrievanceDrafting({ language }: GrievanceDraftingProps) {
  const isTe = language === "Telugu";

  const [category, setCategory] = useState<string>("water_supply");
  const [description, setDescription] = useState<string>("");
  const [district, setDistrict] = useState<string>("");
  const [mandal, setMandal] = useState<string>("");
  const [draftLang, setDraftLang] = useState<"te" | "en">(isTe ? "te" : "en");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [draftResult, setDraftResult] = useState<GrievanceDraftResponse | null>(null);
  const [editableBody, setEditableBody] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);

  const handleGenerateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setError(
        isTe
          ? "దయచేసి మీ సమస్య వివరాలను వివరించండి."
          : "Please describe your grievance in a few sentences."
      );
      return;
    }

    if (!district.trim()) {
      setError(
        isTe
          ? "దయచేసి మీ జిల్లా పేరును నమోదు చేయండి."
          : "Please enter your district name."
      );
      return;
    }

    if (!mandal.trim()) {
      setError(
        isTe
          ? "దయచేసి మీ మండలం లేదా గ్రామం పేరును నమోదు చేయండి."
          : "Please enter your mandal or village name."
      );
      return;
    }

    setIsLoading(true);
    setError(null);
    setCopied(false);

    try {
      const response = await draftGrievance({
        category,
        description: description.trim(),
        district: district.trim(),
        mandal: mandal.trim(),
        language: draftLang,
      });

      setDraftResult(response);
      setEditableBody(response.complaint_body);
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        if (err.status === 404 || err.status === 503 || err.code === "HTTP_ERROR") {
          setError(
            isTe
              ? "ఫిర్యాదు ముసాయిదా సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది. (Member 4 బాధ్యత: /api/grievances/draft)."
              : `Grievance drafting backend service is currently offline or unreachable at /api/grievances/draft. (${err.message})`
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

  const handleCopy = () => {
    if (!draftResult) return;
    const fullText = `${isTe ? "విషయం:" : "Subject:"} ${draftResult.subject}\n\n${editableBody}`;
    navigator.clipboard.writeText(fullText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    });
  };

  return (
    <div className="tool-card">
      <div className="tool-header">
        <div className="tool-icon">📝</div>
        <div>
          <h3>{isTe ? "ప్రజా ఫిర్యాదు ముసాయిదా సహాయకుడు" : "Citizen Grievance Drafting"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "సమస్యను వివరించండి — అధికారిక దరఖాస్తు ముసాయిదాను సిద్ధం చేసుకోండి"
              : "Describe your village issue and generate a formal petition for submission"}
          </p>
        </div>
      </div>

      <form onSubmit={handleGenerateDraft} className="grievance-form">
        <div className="form-grid">
          <div className="form-group">
            <label className="field-label" htmlFor="grievance-category">
              {isTe ? "సమస్య విభాగం" : "Category"}
            </label>
            <select
              id="grievance-category"
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {GRIEVANCE_CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {isTe ? c.labelTe : c.labelEn}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="grievance-lang">
              {isTe ? "ముసాయిదా భాష" : "Draft Language"}
            </label>
            <select
              id="grievance-lang"
              className="form-select"
              value={draftLang}
              onChange={(e) => setDraftLang(e.target.value as "te" | "en")}
            >
              <option value="te">తెలుగు (Telugu)</option>
              <option value="en">English</option>
            </select>
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="grievance-district">
              {isTe ? "జిల్లా *" : "District *"}
            </label>
            <input
              id="grievance-district"
              type="text"
              className="form-input"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              placeholder={isTe ? "ఉదా: కాకినాడ (తప్పనిసరి)" : "e.g. Kakinada (required)"}
              required
            />
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="grievance-mandal">
              {isTe ? "మండలం / గ్రామం *" : "Mandal / Village *"}
            </label>
            <input
              id="grievance-mandal"
              type="text"
              className="form-input"
              value={mandal}
              onChange={(e) => setMandal(e.target.value)}
              placeholder={isTe ? "ఉదా: సామర్లకోట మండలం (తప్పనిసరి)" : "e.g. Samalkota Mandal (required)"}
              required
            />
          </div>
        </div>

        <div className="form-group full-width">
          <label className="field-label" htmlFor="grievance-desc">
            {isTe ? "సమస్య వివరణ *" : "Describe the Issue *"}
          </label>
          <textarea
            id="grievance-desc"
            className="form-textarea"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={
              isTe
                ? "సమస్య ఏమిటి, ఎన్ని రోజుల నుండి ఉంది, ప్రభావిత ప్రాంతం వివరాలను రాయండి..."
                : "Describe what the issue is, how long it has persisted, and affected areas..."
            }
          />
        </div>

        <button
          type="submit"
          className="primary-button generate-draft-btn"
          disabled={!description.trim() || !district.trim() || !mandal.trim() || isLoading}
        >
          {isLoading
            ? isTe
              ? "ముసాయిదాను సిద్ధం చేస్తోంది..."
              : "Drafting Grievance..."
            : isTe
            ? "ముసాయిదా దరఖాస్తును రూపొందించండి"
            : "Generate Grievance Draft"}
        </button>
      </form>

      {error && (
        <div className="notice-box error-notice" role="alert">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>{isTe ? "గమనిక" : "Notice"}</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {draftResult && (
        <div className="draft-output-card">
          <div className="draft-header-row">
            <h4>{isTe ? "సిద్ధమైన ఫిర్యాదు ముసాయిదా" : "Generated Grievance Draft"}</h4>
            <button className="copy-btn" onClick={handleCopy}>
              {copied ? (isTe ? "కాపీ చేయబడింది! ✓" : "Copied! ✓") : isTe ? "📋 కాపీ చేయండి" : "📋 Copy Application"}
            </button>
          </div>

          <div className="draft-subject-box">
            <span className="subject-label">{isTe ? "విషయం:" : "Subject:"}</span>
            <strong>{draftResult.subject}</strong>
          </div>

          <div className="editable-body-box">
            <label className="field-label" htmlFor="editable-body-area">
              {isTe
                ? "దరఖాస్తు పాఠ్యం (మీరు అవసరమైన మార్పులు చేసుకోవచ్చు):"
                : "Application Body (You can edit details directly):"}
            </label>
            <textarea
              id="editable-body-area"
              className="form-textarea draft-body-area"
              rows={8}
              value={editableBody}
              onChange={(e) => setEditableBody(e.target.value)}
            />
          </div>

          {draftResult.recommended_next_steps && draftResult.recommended_next_steps.length > 0 && (
            <div className="next-steps-section">
              <h5>{isTe ? "తదుపరి సిఫార్సు చేయబడిన చర్యలు:" : "Recommended Next Steps:"}</h5>
              <ol className="steps-list">
                {draftResult.recommended_next_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {draftResult.official_links && draftResult.official_links.length > 0 && (
            <div className="official-links-section">
              <h5>{isTe ? "అధికారిక సమర్పణ లింకులు:" : "Official Submission Links:"}</h5>
              <div className="link-chips">
                {draftResult.official_links.map((link, idx) => {
                  const url = typeof link === "string" ? link : link.url;
                  const label = typeof link === "string" ? link : (link.title || link.url);
                  return (
                    <a
                      key={idx}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="portal-link-btn"
                    >
                      🔗 {label}
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          <div className="drafting-disclaimer">
            <span>⚠️</span>
            <p>
              <strong>
                {isTe
                  ? "ముఖ్య గమనిక: ఇది ఫిర్యాదు దరఖాస్తు ముసాయిదా మాత్రమే."
                  : "Important Notice: This tool drafts petitions for your convenience."}
              </strong>{" "}
              {isTe
                ? "ఇది ప్రభుత్వ విభాగానికి నేరుగా సమర్పించబడదు. దయచేసి దీన్ని స్పందన (Spandana) పోర్టల్ లేదా మీ గ్రామ సచివాలయంలో సమర్పించండి."
                : "It does NOT submit petitions to government departments. Please submit your drafted complaint through the Spandana grievance portal or your local Grama Sachivalayam."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
