"use client";

import { useState } from "react";
import { draftGrievance, GrievanceDraftResponse, ApiException } from "../services/api";

interface GrievanceDraftingProps {
  language: string;
}

const GRIEVANCE_CATEGORIES = [
  { id: "water_supply", labelEn: "Drinking Water Supply & Borewell Repairs", labelTe: "తాగునీటి సరఫరా & బోర్‌వెల్ మరమ్మత్తులు" },
  { id: "electricity", labelEn: "Electricity, Street Lights & Transformers", labelTe: "విద్యుత్ సరఫరా, వీధి దీపాలు & ట్రాన్స్‌ఫార్మర్ సమస్యలు" },
  { id: "roads", labelEn: "Village Roads & Pothole Repairs", labelTe: "గ్రామీణ రహదారులు & గుంతల మరమ్మత్తులు" },
  { id: "ration", labelEn: "PDS Ration Distribution & Rice Card Issues", labelTe: "రేషన్ పంపిణీ & బియ్యం కార్డు సమస్యలు" },
  { id: "drainage", labelEn: "Sanitation, Drain Cleaning & Waste Removal", labelTe: "పారిశుధ్యం, మురుగు కాలువలు & చెత్త తొలగింపు" },
  { id: "welfare", labelEn: "Welfare Scheme Delay & Pension Issues", labelTe: "సంక్షేమ పథకాలు & పింఛను మంజూరులో ఆలస్యం" },
  { id: "other", labelEn: "Other Citizen Public Grievances", labelTe: "ఇతర ప్రజా సమస్యలు / ఫిర్యాదులు" },
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
          ? "దయచేసి మీ సమస్య వివరాలను కనీసం రెండు వాక్యాలలో వివరించండి."
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
              ? "ఫిర్యాదు ముసాయిదా సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది (/api/grievances/draft)."
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
      setTimeout(() => setCopied(false), 3500);
    });
  };

  return (
    <div className="tool-card">
      <div className="tool-header">
        <div className="tool-icon" aria-hidden="true">📝</div>
        <div>
          <h3>{isTe ? "ప్రజా సమస్యల ఫిర్యాదు ముసాయిదా సహాయకుడు" : "Citizen Grievance Petition Drafting"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "మీ గ్రామంలోని సమస్యను వివరించండి — స్పందన లేదా సచివాలయానికి సమర్పించడానికి అధికారిక ముసాయిదా దరఖాస్తును రూపొందించుకోండి"
              : "Describe your village issue and generate a structured formal petition ready for submission"}
          </p>
        </div>
      </div>

      {/* Prominent Non-Submission Statutory Banner (Task 7) */}
      <div className="statutory-notice-banner" role="note">
        <span className="notice-icon" aria-hidden="true">ℹ️</span>
        <div>
          <strong>
            {isTe
              ? "ముఖ్య గమనిక: ఇది ఫిర్యాదు దరఖాస్తు ముసాయిదాను సిద్ధం చేసే సహాయక సాధనం మాత్రమే."
              : "Important Notice: This tool assists in drafting formal petitions for your convenience."}
          </strong>
          <p>
            {isTe
              ? "ఈ సాధనం ద్వారా ఫిర్యాదు ప్రభుత్వ విభాగానికి నేరుగా సమర్పించబడదు. ఇక్కడ రూపొందించబడిన ముసాయిదాను కాపీ చేసుకుని ఆంధ్రప్రదేశ్ ప్రభుత్వ 'స్పందన (Spandana / 1902)' పోర్టల్ లేదా మీ గ్రామ/వార్డు సచివాలయంలో స్వయంగా సమర్పించాలి."
              : "This tool does NOT submit petitions to government departments. Copy the generated draft and submit it via the official AP Spandana Portal (spandana.ap.gov.in / dial 1902) or submit a physical copy at your local Grama Sachivalayam."}
          </p>
        </div>
      </div>

      <form onSubmit={handleGenerateDraft} className="grievance-form">
        <div className="form-grid">
          <div className="form-group">
            <label className="field-label" htmlFor="grievance-category">
              {isTe ? "సమస్య విభాగం:" : "Grievance Category:"}
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
              {isTe ? "దరఖాస్తు ముసాయిదా భాష:" : "Petition Language:"}
            </label>
            <select
              id="grievance-lang"
              className="form-select"
              value={draftLang}
              onChange={(e) => setDraftLang(e.target.value as "te" | "en")}
            >
              <option value="te">తెలుగు (Telugu - Recommended for AP)</option>
              <option value="en">English</option>
            </select>
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="grievance-district">
              {isTe ? "జిల్లా పేరు (తప్పనిసరి) *" : "District Name (Required) *"}
            </label>
            <input
              id="grievance-district"
              type="text"
              className="form-input"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              placeholder={isTe ? "ఉదా: కాకినాడ, గుంటూరు..." : "e.g. Kakinada, Guntur..."}
              required
            />
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="grievance-mandal">
              {isTe ? "మండలం / గ్రామం (తప్పనిసరి) *" : "Mandal / Village (Required) *"}
            </label>
            <input
              id="grievance-mandal"
              type="text"
              className="form-input"
              value={mandal}
              onChange={(e) => setMandal(e.target.value)}
              placeholder={isTe ? "ఉదా: సామర్లకోట, తాడికొండ..." : "e.g. Samalkota, Tadikonda..."}
              required
            />
          </div>
        </div>

        <div className="form-group full-width">
          <label className="field-label" htmlFor="grievance-desc">
            {isTe ? "సమస్య పూర్తి వివరణ *" : "Detailed Issue Description *"}
          </label>
          <textarea
            id="grievance-desc"
            className="form-textarea"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={
              isTe
                ? "గ్రామంలో సమస్య ఏమిటి, ఎన్ని రోజుల నుండి ఉంది, ఎంతమంది ప్రజలు ఇబ్బంది పడుతున్నారు, ఇప్పటివరకు ఎవరికైనా విన్నవించారా వంటి వివరాలను రాయండి..."
                : "Describe what the issue is, how long it has persisted, which streets/localities are affected, and any previous representations made..."
            }
          />
        </div>

        <button
          type="submit"
          className="primary-button generate-draft-btn"
          disabled={!description.trim() || !district.trim() || !mandal.trim() || isLoading}
        >
          {isLoading ? (
            <span>⏳ {isTe ? "అధికారిక ముసాయిదా సిద్ధం చేస్తోంది..." : "Drafting Official Petition..."}</span>
          ) : (
            <span>✍️ {isTe ? "ముసాయిదా దరఖాస్తును రూపొందించండి" : "Generate Official Petition Draft"}</span>
          )}
        </button>
      </form>

      {error && (
        <div className="notice-box error-notice" role="alert">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>{isTe ? "పరిశీలన గమనిక" : "Notice"}</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Generated Grievance Draft Card */}
      {draftResult && (
        <div className="draft-output-card">
          <div className="draft-header-row">
            <div className="draft-badge-row">
              <span className="draft-tag">
                {isTe ? "సిద్ధమైన ముసాయిదా దరఖాస్తు" : "Formal Petition Draft"}
              </span>
              <span className="draft-lang-pill">
                {draftLang === "te" ? "తెలుగు (Telugu)" : "English"}
              </span>
            </div>

            <button
              type="button"
              className={`copy-btn ${copied ? "copied" : ""}`}
              onClick={handleCopy}
              aria-label={isTe ? "దరఖాస్తును కాపీ చేయండి" : "Copy full petition"}
            >
              {copied ? (
                <span>✓ {isTe ? "కాపీ చేయబడింది!" : "Copied to Clipboard!"}</span>
              ) : (
                <span>📋 {isTe ? "దరఖాస్తు కాపీ చేయండి" : "Copy Petition"}</span>
              )}
            </button>
          </div>

          <div className="draft-subject-box">
            <span className="subject-label">{isTe ? "విషయం (Subject):" : "Subject:"}</span>
            <strong className="subject-text">{draftResult.subject}</strong>
          </div>

          <div className="editable-body-box">
            <div className="editable-label-row">
              <label className="field-label" htmlFor="editable-body-area">
                {isTe
                  ? "దరఖాస్తు పాఠ్యం (అవసరమైతే ఇక్కడ నేరుగా మార్పులు చేయవచ్చు):"
                  : "Petition Body (Editable text area):"}
              </label>
              <small className="edit-hint-text">
                {isTe ? "మీ పేరు, ఫోన్ నంబరు జోడించవచ్చు" : "Add citizen name & contact details"}
              </small>
            </div>
            <textarea
              id="editable-body-area"
              className="form-textarea draft-body-area"
              rows={9}
              value={editableBody}
              onChange={(e) => setEditableBody(e.target.value)}
            />
          </div>

          {draftResult.recommended_next_steps && draftResult.recommended_next_steps.length > 0 && (
            <div className="next-steps-section">
              <h5>📌 {isTe ? "తదుపరి సిఫార్సు చేయబడిన చర్యలు:" : "Recommended Submission Steps:"}</h5>
              <ol className="steps-list">
                {draftResult.recommended_next_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Submission Gateways and Portals */}
          <div className="official-links-section">
            <h5>🏛️ {isTe ? "అధికారిక సమర్పణ మార్గాలు & పోర్టల్‌లు:" : "Official Submission Portals & Contacts:"}</h5>
            <div className="link-chips">
              <a
                href="https://spandana.ap.gov.in"
                target="_blank"
                rel="noopener noreferrer"
                className="portal-link-btn"
              >
                🌐 స్పందన (Spandana Portal) ↗
              </a>
              <a
                href="tel:1902"
                className="portal-link-btn helpline-link"
              >
                📞 1902 టోల్‌ఫ్రీ స్పందన కాల్ సెంటర్
              </a>
              <a
                href="https://gramawardsachivalayam.ap.gov.in"
                target="_blank"
                rel="noopener noreferrer"
                className="portal-link-btn"
              >
                🏢 గ్రామ / వార్డు సచివాలయం పోర్టల్ ↗
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
