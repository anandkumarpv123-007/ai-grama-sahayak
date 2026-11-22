"use client";

import { useState } from "react";
import { getNearbyServices, GovernmentService, ApiException } from "../services/api";

interface NearbyServicesProps {
  language: string;
}

const SERVICE_TYPES = [
  { id: "", labelEn: "All Services", labelTe: "అన్ని సేవలు" },
  { id: "hospital", labelEn: "Hospitals & Primary Health Centers", labelTe: "ఆసుపత్రులు & ప్రాథమిక ఆరోగ్య కేంద్రాలు" },
  { id: "agriculture", labelEn: "Rythu Bharosa Kendram (RBK)", labelTe: "రైతు భరోసా కేంద్రం (RBK)" },
  { id: "secretariat", labelEn: "Grama / Ward Sachivalayam", labelTe: "గ్రామ / వార్డు సచివాలయం" },
  { id: "ration_shop", labelEn: "Fair Price / Ration Shop", labelTe: "రేషన్ దుకాణం" },
  { id: "education", labelEn: "Government Schools & Colleges", labelTe: "ప్రభుత్వ పాఠశాలలు & కళాశాలలు" },
];

const SUGGESTED_DISTRICTS = [
  "Kakinada",
  "East Godavari",
  "Visakhapatnam",
  "Guntur",
  "Krishna",
  "Nellore",
  "Chittoor",
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
          ? "మీ బ్రౌజర్ లొకేషన్ సేవలను సమర్ధించదు. దయచేసి జిల్లా పేరును నమోదు చేయండి."
          : "Geolocation is not supported by your browser. Please enter your district."
      );
      return;
    }

    setGeoNotice(isTe ? "లొకేషన్ అనుమతిని తనిఖీ చేస్తోంది..." : "Requesting device location...");
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
            : `Location detected (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)}) ✓`
        );
      },
      (err) => {
        setUseGeo(false);
        setGeoNotice(
          isTe
            ? `లొకేషన్ యాక్సెస్ నిరాకరించబడింది (${err.message}). దయచేసి జిల్లా పేరు ద్వారా వెతకండి.`
            : `Location permission denied (${err.message}). Please search by district name.`
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
              ? "దయచేసి జిల్లా పేరును నమోదు చేయండి లేదా లొకేషన్ ఉపయోగించండి."
              : "Please enter a district name or use device location."
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
              ? "సమీప సేవల సర్వరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉంది. (Member 4 బాధ్యత: /api/services/nearby)."
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
        <div className="tool-icon">📍</div>
        <div>
          <h3>{isTe ? "సమీప ప్రభుత్వ సేవలు & కార్యాలయాలు" : "Nearby Government Services"}</h3>
          <p className="tool-subtitle">
            {isTe
              ? "ఆసుపత్రులు, రైతు భరోసా కేంద్రాలు, సచివాలయాల వివరాలు"
              : "Locate primary health centers, Rythu Bharosa Kendrams & village secretariats"}
          </p>
        </div>
      </div>

      <div className="services-search-form">
        <div className="form-group">
          <label className="field-label" htmlFor="service-type-select">
            {isTe ? "సేవ విభాగం" : "Service Category"}
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
              🏢 {isTe ? "జిల్లా ద్వారా" : "By District"}
            </button>
            <button
              type="button"
              className={`location-tab-btn ${useGeo ? "active" : ""}`}
              onClick={requestGeolocation}
            >
              📍 {isTe ? "నా లొకేషన్" : "Device GPS"}
            </button>
          </div>

          {!useGeo ? (
            <div className="district-input-section">
              <label className="field-label" htmlFor="district-input">
                {isTe ? "జిల్లా పేరు" : "District Name"}
              </label>
              <input
                id="district-input"
                type="text"
                className="form-input"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder={isTe ? "ఉదా: Kakinada, East Godavari..." : "e.g., Kakinada, Guntur..."}
              />
              <div className="quick-district-chips">
                <small>{isTe ? "త్వరిత ఎంపిక:" : "Quick pick:"}</small>
                {SUGGESTED_DISTRICTS.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className="chip-btn"
                    onClick={() => setDistrict(d)}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="geo-active-box">
              <p>
                <strong>{isTe ? "GPS లొకేషన్ ఎంచుకోబడింది" : "GPS Mode Active"}</strong>
              </p>
              {coords ? (
                <small>Lat: {coords.lat}, Lng: {coords.lng}</small>
              ) : (
                <small>{isTe ? "లొకేషన్ పొందడానికి వేచివుంది..." : "Awaiting location..."}</small>
              )}
            </div>
          )}

          {geoNotice && <p className="geo-status-notice">{geoNotice}</p>}
        </div>

        <button
          className="primary-button search-services-btn"
          disabled={isLoading}
          onClick={handleSearch}
        >
          {isLoading
            ? isTe
              ? "వెతుకుతోంది..."
              : "Searching..."
            : isTe
            ? "సేవలను కనుగొనండి"
            : "Find Services"}
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

      {services !== null && (
        <div className="services-results-list">
          <div className="results-heading-row">
            <h4>
              {isTe
                ? `కనుగొన్న సేవలు (${services.length})`
                : `Registered Services (${services.length})`}
            </h4>
          </div>

          {services.length === 0 ? (
            <div className="empty-results-box">
              <p>
                {isTe
                  ? "ఎంచుకున్న ప్రాంతంలో ఎటువంటి సేవలు నమోదు కాలేదు. దయచేసి వేరే జిల్లా లేదా విభాగాన్ని ఎంచుకోండి."
                  : "No registered services found for this criteria. Try changing the district or service category."}
              </p>
            </div>
          ) : (
            <div className="service-cards-grid">
              {services.map((svc, idx) => (
                <div key={idx} className="service-result-card">
                  <div className="service-result-header">
                    <h5>{svc.name}</h5>
                    <span className="service-tag">{svc.service_type}</span>
                  </div>

                  <p className="service-address">
                    📍 {svc.address || (isTe ? "చిరునామా అందుబాటులో లేదు" : "Address not provided")}
                  </p>

                  {svc.phone && (
                    <p className="service-phone">
                      📞{" "}
                      <a href={`tel:${svc.phone}`} className="phone-link">
                        {svc.phone}
                      </a>
                    </p>
                  )}

                  {svc.distance_km !== null && svc.distance_km !== undefined && (
                    <p className="service-distance">
                      📏 ~{svc.distance_km.toFixed(1)} km {isTe ? "దూరంలో" : "away"}
                    </p>
                  )}

                  {svc.source_url && (
                    <a
                      href={svc.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link-btn"
                    >
                      {isTe ? "మరిన్ని వివరాలు / మ్యాప్ ↗" : "Official Details / Map ↗"}
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="privacy-disclaimer">
        <span>🛡️</span>
        <small>
          {isTe
            ? "సమాచార గమనిక: సేవల వివరాలు అధికారిక డేటాబేస్ నుండి అందించబడతాయి. ప్రయాణించే ముందు వేళలను ధృవీకరించుకోండి."
            : "Information Notice: Service entries are verified against documented directories. Real-time location is never stored."}
        </small>
      </div>
    </div>
  );
}
