"use client";

import { useState } from "react";
import { getNearbyServices, GovernmentService, ApiException } from "../services/api";

interface NearbyServicesProps {
  language: string;
}

const SERVICE_TYPES = [
  { id: "", labelEn: "All Public Facilities", labelTe: "అన్ని ప్రభుత్వ సేవలు" },
  { id: "hospital", labelEn: "Government Teaching & District Hospitals", labelTe: "ప్రభుత్వ జనరల్ & జిల్లా ఆసుపత్రులు" },
  { id: "community_health_centre", labelEn: "Community Health Centres (CHC)", labelTe: "కమ్యూనిటీ హెల్త్ సెంటర్లు (CHC)" },
  { id: "secretariat", labelEn: "Grama / Ward Sachivalayam", labelTe: "గ్రామ / వార్డు సచివాలయం" },
  { id: "agriculture", labelEn: "Rythu Bharosa Kendram (RBK)", labelTe: "రైతు భరోసా కేంద్రం (RBK)" },
];

// Verified Andhra Pradesh Districts from official Member 4 database inventory
const VERIFIED_DISTRICTS = [
  { id: "Kakinada", labelEn: "Kakinada (GGH Kakinada)", labelTe: "కాకినాడ (GGH కాకినాడ)" },
  { id: "Visakhapatnam", labelEn: "Visakhapatnam (KGH)", labelTe: "విశాఖపట్నం (KGH)" },
  { id: "Guntur", labelEn: "Guntur (GGH Guntur)", labelTe: "గుంటూరు (GGH గుంటూరు)" },
  { id: "NTR", labelEn: "NTR / Vijayawada (New GGH)", labelTe: "ఎన్టీఆర్ / విజయవాడ (New GGH)" },
  { id: "Tirupati", labelEn: "Tirupati (SVRR Hospital)", labelTe: "తిరుపతి (SVRR ఆసుపత్రి)" },
  { id: "Kurnool", labelEn: "Kurnool (GGH Kurnool)", labelTe: "కర్నూలు (GGH కర్నూలు)" },
  { id: "East Godavari", labelEn: "East Godavari (Rajamahendravaram)", labelTe: "తూర్పు గోదావరి (రాజమహేంద్రవరం)" },
  { id: "Krishna", labelEn: "Krishna (Machilipatnam)", labelTe: "కృష్ణా (మచిలీపట్నం)" },
  { id: "Anakapalli", labelEn: "Anakapalli (Area Hospital)", labelTe: "అనకాపల్లి (ఏరియా ఆసుపత్రి)" },
  { id: "Dr. B.R. Ambedkar Konaseema", labelEn: "Konaseema (Ramachandrapuram)", labelTe: "కోనసీమ (రామచంద్రపురం)" },
];

export default function NearbyServices({ language }: NearbyServicesProps) {
  const isTe = language === "Telugu";

  const [serviceType, setServiceType] = useState<string>("");
  const [district, setDistrict] = useState<string>("Kakinada");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [useGeo, setUseGeo] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [geoNotice, setGeoNotice] = useState<string | null>(null);
  const [services, setServices] = useState<GovernmentService[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const requestGeolocation = () => {
    if (!navigator.geolocation) {
      setGeoNotice(
        isTe
          ? "మీ బ్రౌజర్ లొకేషన్ సేవలను సమర్ధించదు. దయచేసి జిల్లాను ఎంచుకోండి."
          : "Geolocation is not supported by your browser. Please select your district."
      );
      return;
    }

    setGeoNotice(isTe ? "లొకేషన్ అనుమతిని తనిఖీ చేస్తోంది..." : "Requesting device GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({
          lat: Number(pos.coords.latitude.toFixed(4)),
          lng: Number(pos.coords.longitude.toFixed(4)),
        });
        setUseGeo(true);
        setGeoNotice(
          isTe
            ? `లొకేషన్ గుర్తించబడింది (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)}) ✓`
            : `GPS Location identified (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)}) ✓`
        );
      },
      (err) => {
        setUseGeo(false);
        setGeoNotice(
          isTe
            ? `లొకేషన్ యాక్సెస్ నిరాకరించబడింది (${err.message}). దయచేసి జిల్లా పేరు ద్వారా వెతకండి.`
            : `Location access denied (${err.message}). Please search by district name.`
        );
      },
      { timeout: 10000 }
    );
  };

  const handleSearch = async () => {
    setIsLoading(true);
    setError(null);
    setServices(null);

    try {
      const params: {
        service_type?: string;
        district?: string;
        latitude?: number;
        longitude?: number;
      } = {};

      if (serviceType) params.service_type = serviceType;

      if (useGeo && coords) {
        params.latitude = coords.lat;
        params.longitude = coords.lng;
      } else {
        if (!district.trim()) {
          setError(
            isTe
              ? "దయచేసి జిల్లాను ఎంచుకోండి లేదా లొకేషన్ ఉపయోగించండి."
              : "Please select a district name or use device location."
          );
          setIsLoading(false);
          return;
        }
        params.district = district.trim();
      }

      const response = await getNearbyServices(params);
      setServices(response.services || []);
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        if (err.status === 404 || err.status === 503 || err.code === "HTTP_ERROR") {
          setError(
            isTe
              ? "సమీప సేవల సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది (/api/services/nearby)."
              : `Nearby services backend service is currently offline or unreachable at /api/services/nearby. (${err.message})`
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

  return (
    <div className="tool-card">
      <div className="tool-header">
        <div className="tool-icon" aria-hidden="true">📍</div>
        <div>
          <h3>{isTe ? "సమీప ప్రభుత్వ సేవలు & ఆసుపత్రుల శోధన" : "Nearby Public Health Facilities & Services"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "ఆంధ్రప్రదేశ్ ప్రభుత్వ అధికారిక డైరెక్టరీ ఆధారంగా బోధనాసుపత్రులు మరియు కమ్యూనిటీ హెల్త్ సెంటర్ల వివరాలు"
              : "Locate verified teaching hospitals & public health centers sourced from official state directories"}
          </p>
        </div>
      </div>

      <div className="services-search-form">
        <div className="form-group">
          <label className="field-label" htmlFor="service-type-select">
            {isTe ? "సేవ / ఆసుపత్రి వర్గం:" : "Facility Classification:"}
          </label>
          <select
            id="service-type-select"
            className="form-select"
            value={serviceType}
            onChange={(e) => setServiceType(e.target.value)}
          >
            {SERVICE_TYPES.map((st) => (
              <option key={st.id} value={st.id}>
                {isTe ? st.labelTe : st.labelEn}
              </option>
            ))}
          </select>
        </div>

        <div className="location-options-box">
          <div className="location-toggle">
            <button
              type="button"
              className={`location-tab-btn ${!useGeo ? "active" : ""}`}
              onClick={() => setUseGeo(false)}
            >
              🏢 {isTe ? "జిల్లా ఎంపిక" : "Select District"}
            </button>
            <button
              type="button"
              className={`location-tab-btn ${useGeo ? "active" : ""}`}
              onClick={requestGeolocation}
            >
              📍 {isTe ? "GPS లొకేషన్" : "Device GPS"}
            </button>
          </div>

          {!useGeo ? (
            <div className="district-input-section">
              <label className="field-label" htmlFor="district-select">
                {isTe ? "ఆంధ్రప్రదేశ్ జిల్లా (ధృవీకరించబడిన డైరెక్టరీ):" : "Andhra Pradesh District (Verified Dataset):"}
              </label>

              <select
                id="district-select"
                className="form-select"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
              >
                {VERIFIED_DISTRICTS.map((d) => (
                  <option key={d.id} value={d.id}>
                    {isTe ? d.labelTe : d.labelEn}
                  </option>
                ))}
              </select>

              <div className="quick-district-chips">
                <small>{isTe ? "త్వరిత ఎంపిక (హబ్‌లు):" : "Verified Regional Hubs:"}</small>
                {VERIFIED_DISTRICTS.slice(0, 5).map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className={`chip-btn ${district === d.id ? "active-chip" : ""}`}
                    onClick={() => setDistrict(d.id)}
                  >
                    {isTe ? d.labelTe.split(" ")[0] : d.id}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="geo-active-box">
              <p>
                <strong>{isTe ? "📍 GPS మోడ్ సక్రియంగా ఉంది" : "📍 GPS Mode Active"}</strong>
              </p>
              {coords ? (
                <small className="geo-coords-text">
                  Latitude: {coords.lat}, Longitude: {coords.lng} (Andhra Pradesh Region)
                </small>
              ) : (
                <small className="geo-waiting-text">
                  {isTe ? "పరికర లొకేషన్ కోసం వేచివుంది..." : "Awaiting device GPS coordinates..."}
                </small>
              )}
            </div>
          )}

          {geoNotice && <p className="geo-status-notice">{geoNotice}</p>}
        </div>

        <button
          type="button"
          className="primary-button search-services-btn"
          disabled={isLoading}
          onClick={handleSearch}
        >
          {isLoading ? (
            <span>⏳ {isTe ? "వెతుకుతోంది..." : "Searching Directories..."}</span>
          ) : (
            <span>🔍 {isTe ? "సేవలను కనుగొనండి" : "Find Verified Facilities"}</span>
          )}
        </button>
      </div>

      {error && (
        <div className="notice-box error-notice" role="alert">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>{isTe ? "గమనిక" : "Notice"}</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {services !== null && (
        <div className="services-results-list">
          <div className="results-heading-row">
            <h4>
              {isTe
                ? `ధృవీకరించబడిన ప్రభుత్వ సేవలు (${services.length})`
                : `Verified Government Facilities (${services.length})`}
            </h4>
            <span className="dataset-badge">
              {isTe ? "అధికారిక DME / APVVP డేటా" : "Official DME / APVVP Dataset"}
            </span>
          </div>

          {services.length === 0 ? (
            <div className="empty-results-box">
              <div className="empty-icon">🏥</div>
              <h5>
                {isTe
                  ? "ఎంచుకున్న జిల్లా / వర్గంలో ప్రస్తుతం డిజిటల్ సౌకర్యాలు నమోదు కాలేదు."
                  : "No registered facilities found for this specific criteria."}
              </h5>
              <p className="empty-explanation">
                {isTe
                  ? "ఈ జిల్లాలోని ఆరోగ్య సౌకర్యాల రికార్డులు ఆన్‌బోర్డింగ్ ప్రక్రియలో ఉన్నాయి. అత్యవసర లేదా ఇతర ప్రభుత్వ సేవల కోసం ఈ క్రింది అధికారిక మార్గాలను సంప్రదించండి:"
                  : "Digitized records for this area are currently undergoing formal directory onboarding. For immediate government health assistance, please use these official statutory channels:"}
              </p>
              <div className="official-directory-links">
                <a
                  href="tel:104"
                  className="helpline-btn"
                  title="Dial AP Health Helpline"
                >
                  📞 104 {isTe ? "ఆరోగ్య ఉచిత హెల్ప్‌లైన్ (24x7)" : "AP Health Helpline (Toll-Free)"}
                </a>
                <a
                  href="https://gramawardsachivalayam.ap.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="directory-link-btn"
                >
                  🏛️ {isTe ? "గ్రామ / వార్డు సచివాలయం పోర్టల్" : "Grama / Ward Sachivalayam Portal"} ↗
                </a>
                <a
                  href="http://cfw.ap.nic.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="directory-link-btn"
                >
                  🏥 {isTe ? "ఆరోగ్య & కుటుంబ సంక్షేమ శాఖ" : "AP Health & Family Welfare"} ↗
                </a>
              </div>
            </div>
          ) : (
            <div className="service-cards-grid">
              {services.map((svc, idx) => (
                <div key={idx} className="service-result-card">
                  <div className="service-result-header">
                    <h5>{svc.name}</h5>
                    <span className="service-tag">
                      {svc.service_type.replace(/_/g, " ")}
                    </span>
                  </div>

                  <p className="service-address">
                    📍 {svc.address || (isTe ? "చిరునామా అందుబాటులో లేదు" : "Address not substantiated")}
                  </p>

                  {svc.phone ? (
                    <p className="service-phone">
                      📞{" "}
                      <a href={`tel:${svc.phone}`} className="phone-link">
                        {svc.phone}
                      </a>
                    </p>
                  ) : (
                    <p className="service-phone-unlisted">
                      📞 <small>{isTe ? "నేరుగా ఫోన్ నంబరు డైరెక్టరీలో నమోదు కాలేదు" : "Direct landline unlisted in central directory"}</small>
                    </p>
                  )}

                  {/* Strictly labeled as approximate straight-line distance per Task 6 */}
                  {svc.distance_km !== null && svc.distance_km !== undefined && (
                    <p className="service-distance">
                      📏 ~{svc.distance_km.toFixed(1)} km{" "}
                      <span className="distance-clarification">
                        ({isTe ? "సుమారు వైమానిక దూరం / straight-line distance" : "approximate straight-line distance"})
                      </span>
                    </p>
                  )}

                  {svc.source_url && (
                    <a
                      href={svc.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link-btn"
                    >
                      {isTe ? "అధికారిక డైరెక్టరీ ఆధారాలు ↗" : "Official Directory Record ↗"}
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Mandatory Accuracy Disclaimer */}
      <div className="privacy-disclaimer">
        <span>🛡️</span>
        <small>
          {isTe
            ? "ఖచ్చితత్వ గమనిక: సౌకర్యాల స్థానాలు నగరం/ప్రాంత స్థాయి సుమారు స్థానాలు (approximate city-level centers). దూరాలు ఖచ్చితమైన రోడ్డు ప్రయాణ దూరం కాదు, సుమారు వైమానిక దూరం మాత్రమే. అత్యవసర పరిస్థితుల్లో ఎల్లప్పుడూ 108 లేదా 104 కు కాల్ చేయండి."
            : "Dataset & Distance Accuracy Notice: Facility coordinates represent approximate locality-level centers, not surveyed building GPS pins. Distances are approximate straight-line estimates for general discovery, not driving or road navigation distances. For medical emergencies, call 108 immediately."}
        </small>
      </div>
    </div>
  );
}
