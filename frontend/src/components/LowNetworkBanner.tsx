"use client";

import { useState } from "react";
import { ConnectivityState, probeBackendHealth } from "../services/connectivity";
import { OFFLINE_PUBLIC_KNOWLEDGE, OfflineSchemeInfo } from "../services/offlineKnowledge";
import {
  SavedQuestion,
  deleteSavedQuestion,
  clearAllSavedData,
  PREDEFINED_PUBLIC_QUESTIONS,
} from "../services/savedQuestions";

interface LowNetworkBannerProps {
  language: string;
  connectivity: ConnectivityState;
  savedQuestions: SavedQuestion[];
  onRefreshSavedQuestions: () => void;
  onSubmitSavedQuestion: (text: string, category: string) => void;
}

export default function LowNetworkBanner({
  language,
  connectivity,
  savedQuestions,
  onRefreshSavedQuestions,
  onSubmitSavedQuestion,
}: LowNetworkBannerProps) {
  const isTe = language === "Telugu";
  const [isOpen, setIsOpen] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<OfflineSchemeInfo | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [clearedNotice, setClearedNotice] = useState(false);

  const isOnline = connectivity.status === "online";
  const isOffline = connectivity.status === "offline";

  const handleManualCheck = async () => {
    setIsChecking(true);
    await probeBackendHealth();
    setIsChecking(false);
  };

  const handleDeleteQuestion = (id: string) => {
    deleteSavedQuestion(id);
    onRefreshSavedQuestions();
  };

  const handleClearAll = () => {
    clearAllSavedData();
    onRefreshSavedQuestions();
    setClearedNotice(true);
    setTimeout(() => setClearedNotice(false), 3000);
  };

  return (
    <>
      {/* Compact Header Connectivity Indicator */}
      <div className="connectivity-wrapper">
        <button
          type="button"
          className={`connectivity-pill ${connectivity.status}`}
          onClick={() => setIsOpen(true)}
          aria-label={isTe ? "నెట్‌వర్క్ మరియు ఆఫ్‌లైన్ సమాచారం" : "Connection and offline status"}
          title={isTe ? "ఆఫ్‌లైన్ సమాచారం మరియు సేవ్ చేసిన ప్రశ్నలు" : "Low-network assistance & saved questions"}
        >
          <span className="status-dot" aria-hidden="true"></span>
          <span className="status-label">
            {isOnline
              ? isTe ? "ఆన్‌లైన్" : "Online"
              : isOffline
              ? isTe ? "ఆఫ్‌లైన్ (నెట్‌వర్క్ లేదు)" : "Offline (No Net)"
              : isTe ? "సర్వర్ ఆఫ్‌లైన్" : "Server Offline"}
          </span>
          {savedQuestions.length > 0 && (
            <span className="saved-count-chip" title={isTe ? "సేవ్ చేసిన ప్రశ్నలు" : "Saved questions"}>
              {savedQuestions.length}
            </span>
          )}
        </button>
      </div>

      {/* Persistent Quiet Warning when Disconnected (Non-intrusive) */}
      {!isOnline && (
        <div className="offline-notice-bar" role="status">
          <div className="offline-notice-content">
            <span className="notice-icon">📡</span>
            <p>
              <strong>
                {isOffline
                  ? isTe ? "ఇంటర్నెట్ అనుసంధానం లేదు: " : "No Internet Connection: "
                  : isTe ? "సర్వరుతో అనుసంధానం కాలేదు: " : "Backend Server Unreachable: "}
              </strong>
              {isTe
                ? "ధృవీకరించబడిన ఆఫ్‌లైన్ ప్రభుత్వ మార్గదర్శకాలను చూడవచ్చు లేదా ప్రశ్నలను తర్వాత అడగడానికి సేవ్ చేసుకోవచ్చు."
                : "You can view verified cached public welfare rules or save questions to send upon reconnection."}
            </p>
          </div>
          <button
            type="button"
            className="offline-open-btn"
            onClick={() => setIsOpen(true)}
          >
            {isTe ? "ఆఫ్‌లైన్ సమాచారం ↗" : "Offline Info ↗"}
          </button>
        </div>
      )}

      {/* Full Low-Network Assistance Modal / Drawer */}
      {isOpen && (
        <div className="low-net-modal-overlay" onClick={() => setIsOpen(false)}>
          <div className="low-net-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <span className="modal-icon">📡</span>
                <div>
                  <h3>
                    {isTe
                      ? "తక్కువ నెట్‌వర్క్ సహాయ వేదిక (Low-Network Assistance)"
                      : "Low-Network Citizen Assistance"}
                  </h3>
                  <p className="modal-subtitle">
                    {isTe
                      ? "నెట్‌వర్క్ లేనప్పుడు కూడా అందుబాటులో ఉండే ధృవీకరించబడిన ప్రజా సమాచారం"
                      : "Access verified public welfare knowledge & manage saved questions offline"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setIsOpen(false)}
                aria-label={isTe ? "మూసివేయండి" : "Close"}
              >
                ✕
              </button>
            </div>

            {/* Current Connectivity Card */}
            <div className={`connection-status-card ${connectivity.status}`}>
              <div className="status-info-col">
                <strong>
                  {isOnline
                    ? isTe ? "✅ నెట్‌వర్క్ అనుసంధానమై ఉంది (Connected)" : "✅ Live Connection Active"
                    : isOffline
                    ? isTe ? "⚠️ ఇంటర్నెట్ డిస్‌కనెక్ట్ అయింది (Offline)" : "⚠️ Device Internet Offline"
                    : isTe ? "⚠️ బ్యాకెండ్ సర్వరు అందుబాటులో లేదు (Server Unreachable)" : "⚠️ Backend Server Unreachable"}
                </strong>
                <small>
                  {isTe
                    ? `చివరి తనిఖీ సమయం: ${new Date(connectivity.lastChecked).toLocaleTimeString()}`
                    : `Last checked: ${new Date(connectivity.lastChecked).toLocaleTimeString()}`}
                </small>
              </div>
              <button
                type="button"
                className="recheck-btn"
                onClick={handleManualCheck}
                disabled={isChecking}
              >
                {isChecking
                  ? isTe ? "తనిఖీ చేస్తోంది..." : "Checking..."
                  : isTe ? "🔄 పునఃపరిశీలించండి" : "🔄 Recheck"}
              </button>
            </div>

            {/* Pending Saved Questions */}
            <div className="saved-questions-section">
              <div className="section-title-bar">
                <h4>
                  📋 {isTe ? "తర్వాత అడగడానికి సేవ్ చేసిన ప్రశ్నలు:" : "Saved Questions for Later:"}
                  <span className="queue-count">({savedQuestions.length})</span>
                </h4>
                {savedQuestions.length > 0 && (
                  <button
                    type="button"
                    className="clear-all-btn"
                    onClick={handleClearAll}
                    title={isTe ? "ఈ బ్రౌజర్‌లోని ముసాయిదా ప్రశ్నలను తొలగించండి" : "Clear local question drafts from this browser"}
                  >
                    🗑️ {isTe ? "అన్నీ క్లియర్ చేయండి" : "Clear All"}
                  </button>
                )}
              </div>

              {clearedNotice && (
                <p className="cleared-toast" role="status">
                  ✓ {isTe
                    ? "ఈ బ్రౌజర్‌లో సేవ్ చేసిన ముసాయిదా ప్రశ్నలు తొలగించబడ్డాయి (అధికారిక రికార్డులకు ఎటువంటి మార్పు ఉండదు)."
                    : "Local question drafts cleared from this browser (official records remain unaffected)."}
                </p>
              )}

              {savedQuestions.length === 0 ? (
                <div className="empty-saved-box">
                  <p>
                    {isTe
                      ? "ప్రస్తుతం సేవ్ చేసిన ప్రశ్నలు లేవు. నెట్‌వర్క్ లేనప్పుడు లేదా తర్వాత అడగడానికి మీ ప్రశ్నను చాట్ బాక్స్ ద్వారా సేవ్ చేసుకోవచ్చు."
                      : "No pending saved questions. When offline, you can save non-sensitive queries to submit once reconnected."}
                  </p>
                </div>
              ) : (
                <div className="saved-questions-list">
                  {savedQuestions.map((sq) => (
                    <div key={sq.id} className="saved-question-item">
                      <div className="saved-item-text">
                        <p className="saved-q-text">&ldquo;{sq.text}&rdquo;</p>
                        <div className="saved-q-meta">
                          <span className="q-cat-tag">{sq.category}</span>
                          <span className="q-time">
                            {new Date(sq.savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      </div>

                      <div className="saved-item-actions">
                        {isOnline ? (
                          <button
                            type="button"
                            className="submit-saved-btn"
                            onClick={() => {
                              onSubmitSavedQuestion(sq.text, sq.category);
                              handleDeleteQuestion(sq.id);
                              setIsOpen(false);
                            }}
                          >
                            {isTe ? "సమర్పించండి →" : "Submit Now →"}
                          </button>
                        ) : (
                          <span className="awaiting-conn-tag">
                            {isTe ? "నెట్‌వర్క్ కోసం వేచివుంది" : "Awaiting Net"}
                          </span>
                        )}

                        <button
                          type="button"
                          className="delete-saved-btn"
                          onClick={() => handleDeleteQuestion(sq.id)}
                          aria-label={isTe ? "తొలగించండి" : "Delete"}
                          title={isTe ? "తొలగించండి" : "Delete"}
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Predefined Non-Sensitive Public Questions (Directive 2) */}
            <div className="predefined-questions-section">
              <h5>
                💡 {isTe ? "ధృవీకరించబడిన ప్రజా ప్రశ్నలు (గోప్యతా-సురక్షితమైనవి):" : "Predefined Public Questions (Privacy-Safe):"}
              </h5>
              <div className="predefined-q-list">
                {PREDEFINED_PUBLIC_QUESTIONS.map((pq, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="predefined-q-btn"
                    onClick={() => {
                      onSubmitSavedQuestion(isTe ? pq.titleTe : pq.titleEn, pq.category);
                      setIsOpen(false);
                    }}
                  >
                    <span>💬 {isTe ? pq.titleTe : pq.titleEn}</span>
                    <span className="predefined-q-arrow">→</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Offline Public Information Directory */}
            <div className="offline-directory-section">
              <h4>
                🏛️ {isTe ? "ఆఫ్‌లైన్ ప్రభుత్వ సమాచార నిల్వ (Verified Public Cache):" : "Cached Public Welfare Knowledge:"}
              </h4>
              <p className="offline-dir-subtitle">
                {isTe
                  ? "ఆంధ్రప్రదేశ్ ప్రభుత్వ గెజిట్లు మరియు మార్గదర్శకాల ఆధారంగా నిల్వ చేయబడిన ప్రజా సమాచారం."
                  : "Verified statutory guidelines cached locally for low-connectivity rural access."}
              </p>

              <div className="offline-scheme-pills">
                {OFFLINE_PUBLIC_KNOWLEDGE.map((scheme) => (
                  <button
                    key={scheme.id}
                    type="button"
                    className={`offline-scheme-pill ${selectedScheme?.id === scheme.id ? "active" : ""}`}
                    onClick={() =>
                      setSelectedScheme(selectedScheme?.id === scheme.id ? null : scheme)
                    }
                  >
                    <span>{isTe ? scheme.titleTe : scheme.titleEn}</span>
                    <span>{selectedScheme?.id === scheme.id ? "▲" : "▼"}</span>
                  </button>
                ))}
              </div>

              {/* Selected Scheme Detail Card */}
              {selectedScheme && (
                <div className="offline-scheme-detail-card">
                  <div className="cache-meta-banner">
                    <span className="cache-indicator-tag">
                      📦 {isTe ? "ఆఫ్‌లైన్ నిల్వ సమాచారం" : "Cached Public Information"}
                    </span>
                    <span className="cache-timestamp">
                      🕒 {isTe
                        ? `ధృవీకరణ: ${selectedScheme.verifiedDate} | నిల్వ: ${selectedScheme.cachedAt}`
                        : `Verified: ${selectedScheme.verifiedDate} | Cached: ${selectedScheme.cachedAt}`}
                    </span>
                  </div>

                  <h5>{isTe ? selectedScheme.titleTe : selectedScheme.titleEn}</h5>

                  <div className="scheme-detail-block">
                    <strong>{isTe ? "ప్రయోజనాలు (Benefits):" : "Statutory Benefits:"}</strong>
                    <p>{isTe ? selectedScheme.benefitTe : selectedScheme.benefitEn}</p>
                  </div>

                  <div className="scheme-detail-block">
                    <strong>{isTe ? "అర్హత నిబంధనలు (Eligibility):" : "Eligibility Criteria:"}</strong>
                    <ul>
                      {(isTe ? selectedScheme.eligibilityTe : selectedScheme.eligibilityEn).map(
                        (el, eIdx) => (
                          <li key={eIdx}>{el}</li>
                        )
                      )}
                    </ul>
                  </div>

                  <div className="scheme-detail-block">
                    <strong>{isTe ? "మినహాయింపులు (Exclusions):" : "Exclusions:"}</strong>
                    <ul>
                      {(isTe ? selectedScheme.exclusionsTe : selectedScheme.exclusionsEn).map(
                        (ex, xIdx) => (
                          <li key={xIdx}>{ex}</li>
                        )
                      )}
                    </ul>
                  </div>

                  <div className="scheme-detail-block">
                    <strong>{isTe ? "దరఖాస్తు విధానం (Procedure):" : "Application Channel:"}</strong>
                    <p>{isTe ? selectedScheme.procedureTe : selectedScheme.procedureEn}</p>
                  </div>

                  <div className="scheme-footer-row">
                    <small>
                      🏛️ <strong>{isTe ? "ధృవీకరించబడిన ఆధారం:" : "Verified Source:"}</strong>{" "}
                      {selectedScheme.verifiedSource}
                    </small>
                    <small>
                      📞 <strong>{isTe ? "హెల్ప్‌లైన్:" : "Helpline:"}</strong>{" "}
                      {selectedScheme.helpline}
                    </small>
                  </div>

                  <div className="offline-statutory-warning">
                    <span>⚖️</span>
                    <small>
                      {isTe
                        ? "గమనిక: ప్రభుత్వ సంక్షేమ మార్గదర్శకాలు కాలక్రమేణా మారవచ్చు. ఇది నిల్వ చేయబడిన ప్రాథమిక సమాచారం మాత్రమే. నెట్‌వర్క్ ఉన్నప్పుడు లేదా మీ గ్రామ సచివాలయంలో ప్రస్తుత అర్హతను నిర్ధారించుకోండి."
                        : "Caution: Government welfare rules may change. This is cached preliminary public information. Confirm live eligibility through your Grama Sachivalayam."}
                    </small>
                  </div>
                </div>
              )}
            </div>

            {/* Privacy Guidance & Warning Box */}
            <div className="privacy-guarantee-box">
              <span>🔒</span>
              <div>
                <p>
                  <strong>{isTe ? "గోప్యతా మార్గదర్శకం & పౌరుల హెచ్చరిక: " : "Privacy Guidance & Citizen Warning: "}</strong>
                  {isTe
                    ? "ఆధార్ నంబర్లు, బ్యాంక్ ఖాతాలు, ఫోన్ నంబర్లు, ఓటీపీలు లేదా వ్యక్తిగత సమాచారాన్ని ఎప్పుడూ సేవ్ చేయవద్దు. ఆటోమేటిక్ ప్యాటర్న్ డిటెక్షన్ ప్రాథమిక రక్షణ మాత్రమే; పూర్తి గోప్యతకు పౌరులు వ్యక్తిగత వివరాలను నమోదు చేయరాదు."
                    : "Never save Aadhaar numbers, bank accounts, phone numbers, OTPs, or confidential personal data. Pattern detection is a preliminary filter and does not guarantee total privacy."}
                </p>
                <small style={{ display: "block", marginTop: "4px", color: "var(--forest-green-dark)" }}>
                  {isTe
                    ? "✓ సేవ్ చేసిన ప్రశ్నలు మీ అనుమతి లేకుండా లేదా ఆటోమేటిక్‌గా ఎప్పటికీ పంపబడవు; మీరు 'సమర్పించండి' నొక్కినప్పుడు మాత్రమే మాన్యువల్‌గా పంపబడతాయి."
                    : "✓ Saved questions are never automatically transmitted without your explicit click on 'Submit Now'."}
                </small>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
