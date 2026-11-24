"use client";

import { useState } from "react";
import { checkEligibility, EligibilityResponse, Source, ApiException } from "../services/api";

interface SchemeEligibilityProps {
  language: string;
}

interface SchemeOption {
  id: string;
  nameEn: string;
  nameTe: string;
  descriptionEn: string;
  descriptionTe: string;
  badgeEn?: string;
  badgeTe?: string;
}

const SUPPORTED_SCHEMES: SchemeOption[] = [
  {
    id: "ntr_bharosa_pension",
    nameEn: "NTR Bharosa — Old Age Pension",
    nameTe: "ఎన్టీఆర్ భరోసా — వృద్ధాప్య పింఛను",
    descriptionEn: "Preliminary eligibility assessment for old-age pension assistance.",
    descriptionTe: "వృద్ధాప్య పింఛను సహాయం కోసం ప్రాథమిక అర్హత పరిశీలన.",
    badgeEn: "Active (OAP Only)",
    badgeTe: "అమలులో ఉంది (వృద్ధాప్యం మాత్రమే)",
  },
  {
    id: "pm_kisan",
    nameEn: "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    nameTe: "ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి (పీఎం-కిసాన్)",
    descriptionEn: "Preliminary eligibility assessment for farmer income support.",
    descriptionTe: "రైతుల ఆదాయ సహాయం కోసం ప్రాథమిక అర్హత పరిశీలన.",
    badgeEn: "Active",
    badgeTe: "అమలులో ఉంది",
  },
  {
    id: "dr_ntr_vaidya_seva",
    nameEn: "Dr. NTR Vaidya Seva (formerly Dr. YSR Aarogyasri)",
    nameTe: "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీ)",
    descriptionEn: "Preliminary eligibility assessment for government healthcare assistance.",
    descriptionTe: "ప్రభుత్వ వైద్య సహాయం కోసం ప్రాథమిక అర్హత పరిశీలన.",
    badgeEn: "Active",
    badgeTe: "అమలులో ఉంది",
  },
  {
    id: "amma_vodi",
    nameEn: "Jagananna Amma Vodi / Thalliki Vandanam",
    nameTe: "జగనన్న అమ్మ ఒడి / తల్లికి వందనం",
    descriptionEn: "Financial assistance for mothers sending children to school (under state policy restructuring).",
    descriptionTe: "పిల్లలను పాఠశాలకు పంపే తల్లులకు ఆర్థిక సహాయం (ప్రభుత్వ పునఃపరిశీలనలో ఉంది).",
    badgeEn: "Under Transition",
    badgeTe: "పునఃపరిశీలనలో ఉంది",
  },
  {
    id: "ysr_rythu_bharosa",
    nameEn: "YSR Rythu Bharosa",
    nameTe: "వైఎస్సార్ రైతు భరోసా",
    descriptionEn: "State farmer assistance framework (under administrative restructuring in AP).",
    descriptionTe: "రైతు సంక్షేమ పథక మార్గదర్శకాలు (ప్రభుత్వ పునఃపరిశీలనలో ఉన్నాయి).",
    badgeEn: "Restructuring",
    badgeTe: "పునఃపరిశీలనలో ఉంది",
  },
];

export default function SchemeEligibility({ language }: SchemeEligibilityProps) {
  const isTe = language === "Telugu";

  const [selectedSchemeId, setSelectedSchemeId] = useState<string>("ntr_bharosa_pension");

  // Form State for ntr_bharosa_pension (Yes/No fields start as null to prevent silent 'No' assumption)
  const [pensionAge, setPensionAge] = useState<string>("62");
  const [hasWhiteCard, setHasWhiteCard] = useState<boolean | null>(true);
  const [pensionAreaType, setPensionAreaType] = useState<string>("rural");
  const [pensionIncome, setPensionIncome] = useState<string>("8000");
  const [pensionGovtEmployee, setPensionGovtEmployee] = useState<boolean | null>(false);
  const [pensionTaxPayer, setPensionTaxPayer] = useState<boolean | null>(false);
  const [pensionFourWheeler, setPensionFourWheeler] = useState<boolean | null>(false);

  // Form State for pm_kisan (Defaults allow full testing, unselected fields start as null)
  const [isLandholding, setIsLandholding] = useState<boolean | null>(true);
  const [hasAadhaarBank, setHasAadhaarBank] = useState<boolean | null>(true);
  const [isEkycCompleted, setIsEkycCompleted] = useState<boolean | null>(true);
  const [isInstitutionalLandholder, setIsInstitutionalLandholder] = useState<boolean>(false);
  const [holdsConstitutionalPost, setHoldsConstitutionalPost] = useState<boolean>(false);
  const [isElectedRep, setIsElectedRep] = useState<boolean>(false);
  const [isKisanGovtEmployee, setIsKisanGovtEmployee] = useState<boolean>(false);
  const [isPensioner10k, setIsPensioner10k] = useState<boolean>(false);
  const [paidIncomeTaxKisan, setPaidIncomeTaxKisan] = useState<boolean>(false);
  const [isProfessional, setIsProfessional] = useState<boolean>(false);

  // Form State for dr_ntr_vaidya_seva
  const [hasHealthCard, setHasHealthCard] = useState<boolean | null>(true);
  const [healthIncome, setHealthIncome] = useState<string>("240000");
  const [isEhsEmployee, setIsEhsEmployee] = useState<boolean | null>(false);

  // UI Processing State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EligibilityResponse | null>(null);

  const selectedScheme = SUPPORTED_SCHEMES.find((s) => s.id === selectedSchemeId) || SUPPORTED_SCHEMES[0];

  const resetFormStateForScheme = (schemeId: string) => {
    setSelectedSchemeId(schemeId);
    setResult(null);
    setError(null);

    // Reset fields cleanly when switching schemes
    if (schemeId === "ntr_bharosa_pension") {
      setPensionAge("62");
      setHasWhiteCard(true);
      setPensionAreaType("rural");
      setPensionIncome("8000");
      setPensionGovtEmployee(false);
      setPensionTaxPayer(false);
      setPensionFourWheeler(false);
    } else if (schemeId === "pm_kisan") {
      setIsLandholding(true);
      setHasAadhaarBank(true);
      setIsEkycCompleted(true);
      setIsInstitutionalLandholder(false);
      setHoldsConstitutionalPost(false);
      setIsElectedRep(false);
      setIsKisanGovtEmployee(false);
      setIsPensioner10k(false);
      setPaidIncomeTaxKisan(false);
      setIsProfessional(false);
    } else if (schemeId === "dr_ntr_vaidya_seva") {
      setHasHealthCard(true);
      setHealthIncome("240000");
      setIsEhsEmployee(false);
    }
  };

  const handleClearForm = () => {
    setResult(null);
    setError(null);
    if (selectedSchemeId === "ntr_bharosa_pension") {
      setPensionAge("");
      setHasWhiteCard(null);
      setPensionGovtEmployee(null);
      setPensionTaxPayer(null);
      setPensionFourWheeler(null);
      setPensionIncome("");
    } else if (selectedSchemeId === "pm_kisan") {
      setIsLandholding(null);
      setHasAadhaarBank(null);
      setIsEkycCompleted(null);
      setIsInstitutionalLandholder(false);
      setIsKisanGovtEmployee(false);
      setIsPensioner10k(false);
      setPaidIncomeTaxKisan(false);
      setIsProfessional(false);
      setHoldsConstitutionalPost(false);
      setIsElectedRep(false);
    } else if (selectedSchemeId === "dr_ntr_vaidya_seva") {
      setHasHealthCard(null);
      setHealthIncome("");
      setIsEhsEmployee(null);
    }
  };

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    const applicantProfile: Record<string, unknown> = {
      state: "Andhra Pradesh",
    };

    try {
      if (selectedSchemeId === "ntr_bharosa_pension") {
        if (pensionAge.trim() !== "") {
          const parsedAge = parseInt(pensionAge.trim(), 10);
          if (isNaN(parsedAge)) {
            setError(
              isTe
                ? "దయచేసి సరైన వయస్సును పూర్ణాంకంగా నమోదు చేయండి."
                : "Please enter a valid numeric age."
            );
            setIsLoading(false);
            return;
          }
          if (parsedAge < 0) {
            setError(
              isTe
                ? "వయస్సు రుణాత్మకంగా (నెగటివ్) ఉండకూడదు."
                : "Age cannot be a negative number."
            );
            setIsLoading(false);
            return;
          }
          applicantProfile.age = parsedAge;
        }

        // Only populate if explicitly answered (never silently default unanswered to false)
        if (hasWhiteCard !== null) {
          applicantProfile.has_white_ration_or_rice_card = hasWhiteCard;
          if (hasWhiteCard === false) {
            applicantProfile.area_type = pensionAreaType;
            if (pensionIncome.trim() !== "") {
              const inc = parseFloat(pensionIncome.trim());
              if (!isNaN(inc) && inc >= 0) {
                applicantProfile.annual_income = inc;
              }
            }
          }
        }

        if (pensionGovtEmployee !== null) {
          applicantProfile.is_govt_employee_or_pensioner = pensionGovtEmployee;
        }
        if (pensionTaxPayer !== null) {
          applicantProfile.is_income_tax_payer = pensionTaxPayer;
        }
        if (pensionFourWheeler !== null) {
          applicantProfile.owns_four_wheeler = pensionFourWheeler;
        }
      } else if (selectedSchemeId === "pm_kisan") {
        if (isLandholding !== null) applicantProfile.is_landholding_farmer = isLandholding;
        if (hasAadhaarBank !== null) applicantProfile.has_aadhaar_linked_bank_account = hasAadhaarBank;
        if (isEkycCompleted !== null) applicantProfile.e_kyc_completed = isEkycCompleted;
        applicantProfile.is_institutional_landholder = isInstitutionalLandholder;
        applicantProfile.holds_constitutional_post = holdsConstitutionalPost;
        applicantProfile.is_elected_representative = isElectedRep;
        applicantProfile.is_regular_govt_employee = isKisanGovtEmployee;
        applicantProfile.is_pensioner_10k_plus = isPensioner10k;
        applicantProfile.paid_income_tax_last_ay = paidIncomeTaxKisan;
        applicantProfile.is_registered_professional = isProfessional;
      } else if (selectedSchemeId === "dr_ntr_vaidya_seva") {
        if (hasHealthCard !== null) {
          applicantProfile.has_rice_card_or_aarogyasri_card = hasHealthCard;
          if (hasHealthCard === false) {
            if (healthIncome.trim() !== "") {
              const inc = parseFloat(healthIncome.trim());
              if (!isNaN(inc) && inc >= 0) {
                applicantProfile.annual_income = inc;
              }
            }
          }
        }
        if (isEhsEmployee !== null) {
          applicantProfile.is_regular_govt_employee_with_ehs = isEhsEmployee;
        }
      }

      const response = await checkEligibility({
        scheme_id: selectedSchemeId,
        language: isTe ? "te" : "en",
        applicant_profile: applicantProfile,
      });

      setResult(response);
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        setError(
          isTe
            ? `అర్హత తనిఖీ సర్వర్ లోపం [${err.code}]: ${err.message}`
            : `Eligibility check error [${err.code}]: ${err.message}`
        );
      } else {
        setError(
          isTe
            ? "సర్వరుతో అనుసంధానం కాలేకపోయింది. దయచేసి బ్యాకెండ్ సర్వరు నడుస్తుందో లేదో తనిఖీ చేయండి."
            : "Could not connect to backend server. Please verify the backend is running."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "eligible":
        return {
          label: isTe ? "ప్రాథమికంగా అర్హులు" : "Preliminarily Eligible",
          className: "eligibility-badge eligible",
          icon: "✅",
        };
      case "ineligible":
        return {
          label: isTe ? "అర్హులు కారు" : "Ineligible",
          className: "eligibility-badge ineligible",
          icon: "❌",
        };
      case "needs_more_information":
        return {
          label: isTe ? "మరిన్ని వివరాలు అవసరం" : "Needs More Information",
          className: "eligibility-badge needs-info",
          icon: "ℹ️",
        };
      case "unable_to_verify":
      default:
        return {
          label: isTe ? "ధృవీకరించలేము (పునఃపరిశీలనలో ఉంది)" : "Unable to Verify / Under Transition",
          className: "eligibility-badge unable-verify",
          icon: "⚠️",
        };
    }
  };

  return (
    <div className="eligibility-card-container">
      <div className="eligibility-header">
        <div className="eligibility-title-row">
          <span className="eligibility-icon">📋</span>
          <div>
            <h3>{isTe ? "పథకం అర్హత తనిఖీ" : "Check Scheme Eligibility"}</h3>
            <p className="eligibility-subtitle">
              {isTe
                ? "నియమ నిబంధనల ఆధారంగా ప్రభుత్వ సంక్షేమ పథకాల ప్రాథమిక అర్హతను పరిశీలించండి"
                : "Evaluate eligibility deterministically against official Government criteria"}
            </p>
          </div>
        </div>
      </div>

      {/* Scheme Selection Tabs/Pills */}
      <div className="scheme-select-group">
        <label className="field-label">
          {isTe ? "పథకాన్ని ఎంచుకోండి:" : "Select Government Scheme:"}
        </label>
        <div className="scheme-pills">
          {SUPPORTED_SCHEMES.map((scheme) => (
            <button
              key={scheme.id}
              type="button"
              className={`scheme-pill-btn ${selectedSchemeId === scheme.id ? "active" : ""}`}
              onClick={() => resetFormStateForScheme(scheme.id)}
            >
              <span className="pill-name">{isTe ? scheme.nameTe : scheme.nameEn}</span>
              {scheme.badgeEn && (
                <span className={`pill-badge ${scheme.id.includes("amma") || scheme.id.includes("rythu") ? "restructure" : "active"}`}>
                  {isTe ? scheme.badgeTe : scheme.badgeEn}
                </span>
              )}
            </button>
          ))}
        </div>
        <p className="scheme-selected-desc">
          💡 {isTe ? selectedScheme.descriptionTe : selectedScheme.descriptionEn}
        </p>
      </div>

      {/* Dedicated Scope Notice for Pension */}
      {selectedSchemeId === "ntr_bharosa_pension" && (
        <div className="scheme-scope-notice" role="note">
          <span className="scope-icon">ℹ️</span>
          <div className="scope-text">
            <strong>{isTe ? "పింఛను పరిధి గమనిక (Scope Notice):" : "Pension Scope Clarification:"}</strong>
            <p>
              {isTe
                ? "ఈ స్వయంచాలక సాధనం కేవలం 'ఎన్టీఆర్ భరోసా — వృద్ధాప్య పింఛను (Old Age Pension)' నియమాలను మాత్రమే పరిశీలిస్తుంది. ఇతర పింఛను వర్గాలు (వితంతు పింఛను, దివ్యాంగుల పింఛను / SADAREM, చేనేత, కల్లుగీత, లేదా దీర్ఘకాలిక కిడ్నీ వ్యాధిగ్రస్తుల పింఛను) వేర్వేరు ప్రత్యేక నిబంధనలను కలిగి ఉంటాయి మరియు అవి ఈ ఆటోమేటెడ్ మూల్యాంకనం పరిధికి వెలుపల ఉన్నాయి. ఆ పథకాల కొరకు దయచేసి స్థానిక సచివాలయాన్ని సంప్రదించండి."
                : "This automated evaluator checks criteria strictly for 'NTR Bharosa — Old Age Pension'. Other pension categories (Widow Pension, Disabled/SADAREM Pension, Weavers, Toddy Tappers, or CKD Dialysis Pensions) operate under separate statutory guidelines and are outside the scope of this automated tool. Please consult your local Grama / Ward Sachivalayam for those schemes."}
            </p>
          </div>
        </div>
      )}

      {/* Dynamic Form per Selected Scheme */}
      <form onSubmit={handleEvaluate} className="eligibility-form">
        {selectedSchemeId === "ntr_bharosa_pension" && (
          <div className="form-fields-grid">
            <div className="form-field">
              <label htmlFor="pensionAge" className="field-label">
                {isTe ? "దరఖాస్తుదారు వయస్సు (సంవత్సరాలు)*" : "Applicant Age (Years)*"}
              </label>
              <input
                id="pensionAge"
                type="number"
                min="0"
                max="120"
                value={pensionAge}
                onChange={(e) => setPensionAge(e.target.value)}
                className="form-input"
                placeholder={isTe ? "ఉదా: 62" : "e.g. 62"}
              />
              <span className="field-help">
                {isTe ? "వృద్ధాప్య పింఛను దరఖాస్తుదారు వయస్సును నమోదు చేయండి" : "Enter applicant age for Old Age Pension evaluation"}
              </span>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "వైట్ రేషన్ కార్డు లేదా బియ్యం కార్డు ఉందా?*" : "Possesses White Ration Card or Rice Card?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasWhiteCard"
                    checked={hasWhiteCard === true}
                    onChange={() => setHasWhiteCard(true)}
                  />
                  <span>{isTe ? "అవును (కార్డు ఉంది)" : "Yes (Has Card)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasWhiteCard"
                    checked={hasWhiteCard === false}
                    onChange={() => setHasWhiteCard(false)}
                  />
                  <span>{isTe ? "లేదు (కార్డు లేదు)" : "No (No Card)"}</span>
                </label>
              </div>
            </div>

            {hasWhiteCard === false && (
              <>
                <div className="form-field">
                  <label htmlFor="pensionAreaType" className="field-label">
                    {isTe ? "నివాస ప్రాంతం*" : "Locality / Area Type*"}
                  </label>
                  <select
                    id="pensionAreaType"
                    value={pensionAreaType}
                    onChange={(e) => setPensionAreaType(e.target.value)}
                    className="form-input"
                  >
                    <option value="rural">{isTe ? "గ్రామీణ ప్రాంతం (Rural Area)" : "Rural Area"}</option>
                    <option value="urban">{isTe ? "పట్టణ ప్రాంతం (Urban Area)" : "Urban Area"}</option>
                  </select>
                </div>

                <div className="form-field">
                  <label htmlFor="pensionIncome" className="field-label">
                    {isTe ? "కుటుంబ నెలవారీ ఆదాయం (రూపాయలు)*" : "Monthly Family Income (₹)*"}
                  </label>
                  <input
                    id="pensionIncome"
                    type="number"
                    min="0"
                    value={pensionIncome}
                    onChange={(e) => setPensionIncome(e.target.value)}
                    className="form-input"
                    placeholder="8000"
                  />
                </div>
              </>
            )}

            <div className="form-field">
              <label className="field-label">
                {isTe ? "ప్రభుత్వ ఉద్యోగి లేదా సర్వీస్ పెన్షనరా?*" : "Government Employee or Service Pensioner?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionGovtEmployee"
                    checked={pensionGovtEmployee === false}
                    onChange={() => setPensionGovtEmployee(false)}
                  />
                  <span>{isTe ? "కాదు (అర్హులు)" : "No (Eligible)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionGovtEmployee"
                    checked={pensionGovtEmployee === true}
                    onChange={() => setPensionGovtEmployee(true)}
                  />
                  <span>{isTe ? "అవును (మినహాయింపు)" : "Yes (Excluded)"}</span>
                </label>
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "కుటుంబంలో ఆదాయపు పన్ను (Income Tax) చెల్లిస్తున్నారా?*" : "Income Tax Payer in Family?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionTaxPayer"
                    checked={pensionTaxPayer === false}
                    onChange={() => setPensionTaxPayer(false)}
                  />
                  <span>{isTe ? "కాదు" : "No"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionTaxPayer"
                    checked={pensionTaxPayer === true}
                    onChange={() => setPensionTaxPayer(true)}
                  />
                  <span>{isTe ? "అవును" : "Yes"}</span>
                </label>
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "నాలుగు చక్రాల వాహనం (కారు / జీపు) కలిగి ఉన్నారా?*" : "Owns a Four-Wheeler (Car/Jeep)?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionFourWheeler"
                    checked={pensionFourWheeler === false}
                    onChange={() => setPensionFourWheeler(false)}
                  />
                  <span>{isTe ? "లేదు" : "No"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="pensionFourWheeler"
                    checked={pensionFourWheeler === true}
                    onChange={() => setPensionFourWheeler(true)}
                  />
                  <span>{isTe ? "ఉంది" : "Yes"}</span>
                </label>
              </div>
              <span className="field-help">{isTe ? "ట్రాక్టర్లు / వాణిజ్య టాక్సీలు మినహాయింపు" : "Tractors and commercial taxis exempt"}</span>
            </div>
          </div>
        )}

        {selectedSchemeId === "pm_kisan" && (
          <div className="form-fields-grid">
            <div className="form-field">
              <label className="field-label">
                {isTe ? "సాగు భూమి ఉన్న రైతు కుటుంబమా?*" : "Landholding Farmer Family?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isLandholding"
                    checked={isLandholding === true}
                    onChange={() => setIsLandholding(true)}
                  />
                  <span>{isTe ? "అవును (సాగుభూమి ఉంది)" : "Yes (Has cultivable land)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isLandholding"
                    checked={isLandholding === false}
                    onChange={() => setIsLandholding(false)}
                  />
                  <span>{isTe ? "లేదు" : "No"}</span>
                </label>
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "ఆధార్ లింక్ అయిన బ్యాంక్ ఖాతా ఉందా?*" : "Aadhaar-Linked Active Bank Account?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasAadhaarBank"
                    checked={hasAadhaarBank === true}
                    onChange={() => setHasAadhaarBank(true)}
                  />
                  <span>{isTe ? "అవును" : "Yes"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasAadhaarBank"
                    checked={hasAadhaarBank === false}
                    onChange={() => setHasAadhaarBank(false)}
                  />
                  <span>{isTe ? "లేదు" : "No"}</span>
                </label>
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "పీఎం-కిసాన్ ఈ-కేవైసీ (e-KYC) పూర్తయిందా?*" : "PM-KISAN e-KYC Completed?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isEkycCompleted"
                    checked={isEkycCompleted === true}
                    onChange={() => setIsEkycCompleted(true)}
                  />
                  <span>{isTe ? "అవును (పూర్తయింది)" : "Yes (Completed)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isEkycCompleted"
                    checked={isEkycCompleted === false}
                    onChange={() => setIsEkycCompleted(false)}
                  />
                  <span>{isTe ? "లేదు" : "No"}</span>
                </label>
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">
                {isTe ? "మినహాయింపు ప్రమాణాలు (ఏదైనా వర్తిస్తుందా?)*" : "Exclusion Criteria Check*"}
              </label>
              <div className="exclusion-checkboxes">
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={isInstitutionalLandholder}
                    onChange={(e) => setIsInstitutionalLandholder(e.target.checked)}
                  />
                  <span>{isTe ? "సంస్థాగత భూ యజమాని (Institutional Landholder)" : "Institutional Landholder"}</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={isKisanGovtEmployee}
                    onChange={(e) => setIsKisanGovtEmployee(e.target.checked)}
                  />
                  <span>{isTe ? "ప్రభుత్వ ఉద్యోగి / రిటైర్డ్ సర్వీస్ ఉద్యోగి" : "Regular Govt Employee / Officer"}</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={paidIncomeTaxKisan}
                    onChange={(e) => setPaidIncomeTaxKisan(e.target.checked)}
                  />
                  <span>{isTe ? "గత అసెస్‌మెంట్ ఇయర్‌లో ఆదాయపు పన్ను చెల్లించారు" : "Paid Income Tax in last assessment year"}</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={isPensioner10k}
                    onChange={(e) => setIsPensioner10k(e.target.checked)}
                  />
                  <span>{isTe ? "నెలవారీ పెన్షన్ ₹10,000 లేదా అంతకంటే ఎక్కువ" : "Monthly Pension of ₹10,000 or more"}</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={isProfessional}
                    onChange={(e) => setIsProfessional(e.target.checked)}
                  />
                  <span>{isTe ? "రిజిస్టర్డ్ ప్రొఫెషనల్ (డాక్టర్ / ఇంజనీర్ / లాయర్ / CA)" : "Registered Professional (Doctor/CA/Lawyer)"}</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={holdsConstitutionalPost || isElectedRep}
                    onChange={(e) => {
                      setHoldsConstitutionalPost(e.target.checked);
                      setIsElectedRep(e.target.checked);
                    }}
                  />
                  <span>{isTe ? "రాజ్యాంగ పదవి / ప్రజా ప్రతినిధి (ఎమ్మెల్యే, ఎంపీ, మేయర్)" : "Constitutional Post / Elected Representative"}</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {selectedSchemeId === "dr_ntr_vaidya_seva" && (
          <div className="form-fields-grid">
            <div className="form-field">
              <label className="field-label">
                {isTe ? "ఆరోగ్యశ్రీ కార్డు లేదా బియ్యం కార్డు (Rice Card) ఉందా?*" : "Possesses Rice Card or Aarogyasri Card?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasHealthCard"
                    checked={hasHealthCard === true}
                    onChange={() => setHasHealthCard(true)}
                  />
                  <span>{isTe ? "అవును (కార్డు ఉంది)" : "Yes (Has Card)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="hasHealthCard"
                    checked={hasHealthCard === false}
                    onChange={() => setHasHealthCard(false)}
                  />
                  <span>{isTe ? "లేదు" : "No"}</span>
                </label>
              </div>
            </div>

            {hasHealthCard === false && (
              <div className="form-field">
                <label htmlFor="healthIncome" className="field-label">
                  {isTe ? "కుటుంబ వార్షిక ఆదాయం (రూపాయలు)*" : "Annual Family Income (₹)*"}
                </label>
                <input
                  id="healthIncome"
                  type="number"
                  min="0"
                  value={healthIncome}
                  onChange={(e) => setHealthIncome(e.target.value)}
                  className="form-input"
                  placeholder="240000"
                />
                <span className="field-help">
                  {isTe ? "బియ్యం కార్డు లేదా ఆరోగ్యశ్రీ కార్డు లేనిచో వార్షిక కుటుంబ ఆదాయం అవసరం" : "Required if not holding a White Rice Card or Aarogyasri Card"}
                </span>
              </div>
            )}

            <div className="form-field">
              <label className="field-label">
                {isTe ? "ఉద్యోగుల ఆరోగ్య పథకం (EHS) కింద రక్షణ పొందుతున్న రెగ్యులర్ ప్రభుత్వ ఉద్యోగా?*" : "Regular Govt Employee covered under EHS?*"}
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isEhsEmployee"
                    checked={isEhsEmployee === false}
                    onChange={() => setIsEhsEmployee(false)}
                  />
                  <span>{isTe ? "కాదు (అర్హులు)" : "No (Eligible)"}</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="isEhsEmployee"
                    checked={isEhsEmployee === true}
                    onChange={() => setIsEhsEmployee(true)}
                  />
                  <span>{isTe ? "అవును (EHS పథకం వర్తిస్తుంది)" : "Yes (Covered under EHS)"}</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {(selectedSchemeId === "amma_vodi" || selectedSchemeId === "ysr_rythu_bharosa") && (
          <div className="transition-notice-box">
            <p>
              ℹ️ {isTe
                ? "ఈ పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వంచే సమీక్ష మరియు పునఃరూపకల్పనలో ఉంది. అధికారిక గెజిట్ నోటిఫికేషన్ విడుదలయ్యే వరకు ఈ పథక నియమాలను ధృవీకరించలేము. అధికారిక స్థితిని తనిఖీ చేయడానికి క్రింది బటన్ నొక్కండి."
                : "This scheme is currently undergoing state policy restructuring in Andhra Pradesh. Official guidelines are pending gazette release. Click below to verify the current certified administrative status."}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="form-actions">
          <button
            type="button"
            className="clear-form-btn"
            onClick={handleClearForm}
            title={isTe ? "ఫారమ్ వివరాలను క్లియర్ చేయండి" : "Clear form fields to test missing info"}
          >
            {isTe ? "క్లియర్" : "Clear / Reset"}
          </button>
          <button
            type="submit"
            className="check-eligibility-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span>⏳ {isTe ? "పరిశీలిస్తోంది..." : "Checking Rules..."}</span>
            ) : (
              <span>🔍 {isTe ? "అర్హతను తనిఖీ చేయండి" : "Check Eligibility"}</span>
            )}
          </button>
        </div>
      </form>

      {/* Error Banner */}
      {error && (
        <div className="eligibility-error-banner" role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Evaluation Result View */}
      {result && (
        <div className="eligibility-result-card">
          <div className="result-header">
            {(() => {
              const badge = getStatusBadge(result.status);
              return (
                <div className={badge.className}>
                  <span>{badge.icon}</span>
                  <strong>{badge.label}</strong>
                </div>
              );
            })()}
            <span className="result-scheme-name">
              {isTe ? selectedScheme.nameTe : selectedScheme.nameEn}
            </span>
          </div>

          {/* Reasons */}
          {result.reasons && result.reasons.length > 0 && (
            <div className="result-section">
              <h4>{isTe ? "నిర్ణయ కారణాలు:" : "Evaluation Findings & Reasons:"}</h4>
              <ul className="result-list">
                {result.reasons.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Fields */}
          {result.missing_fields && result.missing_fields.length > 0 && (
            <div className="result-section missing-info">
              <h4>{isTe ? "అర్హత నిర్ణయానికి అవసరమైన సమాచారం:" : "Information Required for Evaluation:"}</h4>
              <div className="missing-chips">
                {result.missing_fields.map((mf, idx) => (
                  <span key={idx} className="missing-chip">
                    {mf}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Benefits */}
          {result.benefits && result.benefits.length > 0 && (
            <div className="result-section benefits">
              <h4>🎁 {isTe ? "పథకం ద్వారా లభించే ప్రయోజనాలు:" : "Scheme Benefits:"}</h4>
              <ul className="result-list">
                {result.benefits.map((benefit, idx) => (
                  <li key={idx}>{benefit}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Required Documents */}
          {result.required_documents && result.required_documents.length > 0 && (
            <div className="result-section documents">
              <h4>📄 {isTe ? "అవసరమైన అధికారిక పత్రాలు:" : "Required Official Documents:"}</h4>
              <ul className="result-list">
                {result.required_documents.map((doc, idx) => (
                  <li key={idx}>{doc}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Application Steps */}
          {result.application_steps && result.application_steps.length > 0 && (
            <div className="result-section steps">
              <h4>📌 {isTe ? "దరఖాస్తు చేసుకునే విధానం:" : "Application Procedure:"}</h4>
              <ol className="result-steps-list">
                {result.application_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Sources */}
          {result.sources && result.sources.length > 0 && (
            <div className="result-section sources">
              <h4>🏛️ {isTe ? "ధృవీకరించబడిన ప్రభుత్వ ఆధారాలు:" : "Verified Government Sources:"}</h4>
              <div className="result-sources-list">
                {result.sources.map((src: Source, idx: number) => (
                  <div key={idx} className="source-item">
                    <a href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">
                      {src.title}
                    </a>
                    {src.publisher && <span className="source-meta"> — {src.publisher}</span>}
                    {src.verified_at && <span className="source-meta"> ({isTe ? `ధృవీకరించబడింది: ${src.verified_at}` : `Verified: ${src.verified_at}`})</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Official Government Disclaimer (Mandatory Requirement) */}
          <div className="statutory-disclaimer">
            <span>⚖️</span>
            <div>
              <strong>{isTe ? "ప్రభుత్వ మార్గదర్శక సూచన:" : "Official Statutory Advisory:"}</strong>
              <p>
                {isTe
                  ? "ఈ సాధనం అధికారిక ప్రభుత్వ నిబంధనల ఆధారంగా కేవలం ప్రాథమిక సమాచార మార్గదర్శకత్వాన్ని మాత్రమే అందిస్తుంది. ఇది తుది ప్రభుత్వ మంజూరు లేదా అధికారిక ఆమోదానికి హామీ ఇవ్వదు. అర్హత మరియు మంజూరు సంబంధిత ప్రభుత్వ అధికారుల (గ్రామ/వార్డు సచివాలయం, రెవెన్యూ విభాగం) క్షేత్రస్థాయి విచారణ మరియు బయోమెట్రిక్ పరిశీలనపై ఆధారపడి ఉంటుంది."
                  : "This tool provides preliminary informational guidance based strictly on published government guidelines. It does NOT guarantee official sanction or government approval. Final sanction is subject to physical verification, biometric authentication, and formal administrative approval by competent government authorities (Grama / Ward Sachivalayam / Revenue Dept)."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
