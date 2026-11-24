"use client";

export interface OfflineSchemeInfo {
  id: string;
  keywords: string[];
  titleEn: string;
  titleTe: string;
  benefitEn: string;
  benefitTe: string;
  eligibilityEn: string[];
  eligibilityTe: string[];
  exclusionsEn: string[];
  exclusionsTe: string[];
  procedureEn: string;
  procedureTe: string;
  officialPortal: string;
  helpline: string;
  verifiedSource: string;
  verifiedDate: string; // Source verification date from official baseline docs (2026-11-21)
  cachedAt: string;     // Local cache timestamp in application
}

export const OFFLINE_PUBLIC_KNOWLEDGE: OfflineSchemeInfo[] = [
  {
    id: "annadata_sukhibhava_pmkisan",
    keywords: ["kisan", "pmkisan", "pm-kisan", "farmer", "annadata", "sukhibhava", "rythu", "రైతు", "కిసాన్", "అన్నదాత", "సుఖీభవ"],
    titleEn: "Annadata Sukhibhava / PM-KISAN (Farmer Income Support)",
    titleTe: "అన్నదాత సుఖీభవ / పీఎం-కిసాన్ (రైతు ఆదాయ సహాయం)",
    benefitEn: "Central PM-KISAN provides direct income support of ₹6,000 per year in three equal four-monthly installments of ₹2,000 to eligible landholder farmers. The Government of Andhra Pradesh plans supplemental state financial assistance as a state top-up under the Annadata Sukhibhava initiative; exact state installment amounts, disbursement dates, and tenant farmer criteria are governed by published departmental notifications.",
    benefitTe: "కేంద్ర ప్రభుత్వ పీఎం-కిసాన్ ద్వారా అర్హులైన భూయజమానులకు ఏడాదికి రూ. 6,000 (మూడు విడతల్లో రూ. 2,000 చొప్పున) జమ అవుతుంది. దీనికి తోడుగా ఆంధ్రప్రదేశ్ ప్రభుత్వం అన్నదాత సుఖీభవ కింద రాష్ట్ర టాప్-అప్ సహాయాన్ని రూపొందిస్తోంది; ఖచ్చితమైన విడతల చెల్లింపులు, తేదీలు మరియు కౌలు రైతుల నిబంధనలు ప్రభుత్వం విడుదల చేసే అధికారిక ఉత్తర్వులకు లోబడి ఉంటాయి.",
    eligibilityEn: [
      "Bonafide resident farmers cultivating agricultural land in Andhra Pradesh.",
      "Small and marginal landholder farmer families with land records updated in Webland / e-Crop.",
      "Active bank account seeded with Aadhaar and mapped with NPCI for Direct Benefit Transfer (DBT).",
      "Completed biometric or OTP-based e-KYC on PM-Kisan / Annadata Sukhibhava portals.",
      "Tenant farmers cultivating under registered Crop Cultivator Rights Cards (CCRC), subject to departmental guidelines.",
    ],
    eligibilityTe: [
      "ఆంధ్రప్రదేశ్‌లో సొంత సాగుభూమి కలిగి వ్యవసాయం చేస్తున్న రైతు కుటుంబాలు.",
      "వెబ్‌ల్యాండ్ / ఈ-క్రాప్ రెవెన్యూ రికార్డులలో నమోదైన భూమి వివరాలు.",
      "డీబీటీ (DBT) కొరకు ఆధార్ మరియు ఎన్‌పీసీఐ (NPCI) తో అనుసంధానమైన బ్యాంక్ ఖాతా.",
      "పీఎం-కిసాన్ / అన్నదాత సుఖీభవ పోర్టల్ ద్వారా పూర్తి చేసిన ఈ-కేవైసీ (e-KYC).",
      "ప్రస్తుత సీజన్‌కు చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) కార్డులు కలిగిన కౌలు రైతులు (నిబంధనల ప్రకారం).",
    ],
    exclusionsEn: [
      "Institutional landholders.",
      "Serving or retired government employees and regular officers.",
      "Income tax payees from the previous assessment year.",
      "Constitutional post holders and elected representatives.",
      "Pensioners drawing monthly pension of ₹10,000 or more.",
    ],
    exclusionsTe: [
      "సంస్థాగత భూ యజమానులు.",
      "ప్రభుత్వ ఉద్యోగులు మరియు రిటైర్డ్ సర్వీస్ అధికారులు.",
      "గత అసెస్‌మెంట్ సంవత్సరంలో ఆదాయపు పన్ను చెల్లించినవారు.",
      "రాజ్యాంగ పదవులు మరియు చట్టసభల ప్రజా ప్రతినిధులు.",
      "నెలకు ₹10,000 లేదా అంతకంటే ఎక్కువ పెన్షన్ పొందుతున్నవారు.",
    ],
    procedureEn: "Complete biometric/OTP e-KYC and verify land and Aadhaar bank seeding at your local Rythu Seva Kendram (RSK) / Rythu Bharosa Kendram (RBK) or via pmkisan.gov.in.",
    procedureTe: "మీ స్థానిక రైతు సేవా కేంద్రం (RSK) / రైతు భరోసా కేంద్రం (RBK) వద్ద లేదా pmkisan.gov.in పోర్టల్ ద్వారా ఈ-కేవైసీ పూర్తి చేసి, ఆధార్ సీడింగ్ సరిచూసుకోండి.",
    officialPortal: "https://annadathasukhibhava.ap.gov.in",
    helpline: "155251 (Kisan Helpline) / 1902 (Public Grievance)",
    verifiedSource: "Department of Agriculture, Government of Andhra Pradesh & Ministry of Agriculture and Farmers Welfare, GoI",
    verifiedDate: "2026-11-21",
    cachedAt: "2026-11-24",
  },
  {
    id: "thalliki_vandanam",
    keywords: ["thalliki", "vandanam", "amma", "vodi", "mother", "school", "education", "scholarship", "తల్లికి", "వందనం", "అమ్మ", "ఒడి", "పాఠశాల", "విద్య"],
    titleEn: "Thalliki Vandanam (School Education Incentive Framework)",
    titleTe: "తల్లికి వందనం (పాఠశాల విద్యా ప్రోత్సాహక పథకం)",
    benefitEn: "Educational financial support framework for mothers/guardians sending children from Class 1 to Intermediate (Class 12). Specific disbursement amounts, installment schedules, and deduction norms are governed by published operational guidelines and administrative orders issued by the School Education Department.",
    benefitTe: "1వ తరగతి నుండి ఇంటర్మీడియట్ (12వ తరగతి) వరకు పిల్లలను పాఠశాలలు/కళాశాలలకు పంపే అర్హులైన తల్లులకు విద్యా ప్రోత్సాహక ఆర్థిక సహాయం అందించే విధానం. చెల్లింపుల మొత్తం, విడతలు మరియు నిబంధనలు పాఠశాల విద్యాశాఖ విడుదల చేసే అధికారిక ఉత్తర్వులకు లోబడి ఉంటాయి.",
    eligibilityEn: [
      "Student enrolled and studying in Classes 1 to 12 in recognized AP schools or junior colleges.",
      "Prescribed institutional attendance benchmarks recorded in school Child Info database.",
      "Possession of valid Rice Card / BPL card verified by Grama/Ward Sachivalayam.",
      "Permanent resident of Andhra Pradesh; excludes regular government employees and income tax payers.",
    ],
    eligibilityTe: [
      "ఆంధ్రప్రదేశ్‌లోని గుర్తింపు పొందిన పాఠశాల లేదా కళాశాలలో 1 నుండి 12వ తరగతి చదువుతున్న విద్యార్థులు.",
      "పాఠశాల చైల్డ్ ఇన్ఫో రికార్డుల ప్రకారం విద్యాశాఖ నిర్ణయించిన హాజరు నిబంధనలు పాటించాలి.",
      "సచివాలయం ద్వారా ధృవీకరించబడిన చెల్లుబాటు అయ్యే రైస్ కార్డు / తెల్ల రేషన్ కార్డు కలిగి ఉండాలి.",
      "ఆంధ్రప్రదేశ్ నివాసి అయి ఉండాలి; ప్రభుత్వ ఉద్యోగులు మరియు ఆదాయపు పన్ను చెల్లించేవారు మినహాయింపు.",
    ],
    exclusionsEn: [
      "Families with regular government employees or service pensioners.",
      "Income tax payees.",
      "Students failing to satisfy departmental enrollment and attendance norms.",
    ],
    exclusionsTe: [
      "రెగ్యులర్ ప్రభుత్వ ఉద్యోగులు లేదా పెన్షనర్లు ఉన్న కుటుంబాలు.",
      "ఆదాయపు పన్ను చెల్లించే కుటుంబాలు.",
      "విద్యాశాఖ నిర్ణీత నమోదు మరియు హాజరు నిబంధనలు పాటించని విద్యార్థులు.",
    ],
    procedureEn: "Student details are verified via school Child Info / UDISE+ database and synchronized through the Grama/Ward Sachivalayam Welfare Assistant.",
    procedureTe: "పాఠశాల చైల్డ్ ఇన్ఫో / యు-డైస్ డేటా ఆధారంగా మీ గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ అసిస్టెంట్ ద్వారా వివరాలు సరిచూసుకోండి.",
    officialPortal: "https://schooledu.ap.gov.in",
    helpline: "1902 (Grama Sachivalayam / Spandana)",
    verifiedSource: "Department of School Education, Government of Andhra Pradesh",
    verifiedDate: "2026-11-21",
    cachedAt: "2026-11-24",
  },
  {
    id: "ntr_bharosa_pension",
    keywords: ["pension", "ntr", "bharosa", "oap", "old age", "widow", "disabled", "sadarem", "పింఛను", "పెన్షన్", "వృద్ధాప్య", "వితంతు", "దివ్యాంగ", "సదరం"],
    titleEn: "NTR Bharosa Social Security Pension Scheme",
    titleTe: "ఎన్టీఆర్ భరోసా సామాజిక భద్రతా పింఛన్ల పథకం",
    benefitEn: "Direct monthly cash pensions for vulnerable citizens. Old Age Pension (OAP) benchmarked at ₹4,000 per month for senior citizens aged 60+. Monthly assistance rates for widow pensions, certified disability (SADAREM), and severe chronic illnesses (such as CKD dialysis patients) are governed by prevailing departmental orders and administrative notifications.",
    benefitTe: "నిస్సహాయ వర్గాల ప్రజలకు ప్రత్యక్ష నెలవారీ నగదు పింఛను. 60 ఏళ్లు నిండిన వృద్ధులకు వృద్ధాప్య పింఛను (ప్రస్తుతం నెలకు రూ. 4,000 మార్గదర్శకాల ప్రకారం). వితంతువులు, సదరం (SADAREM) ధృవీకరణ కలిగిన దివ్యాంగులు మరియు కిడ్నీ డయాలసిస్ వంటి తీవ్ర అనారోగ్య బాధితులకు నెలవారీ సహాయం మరియు నిబంధనలు ప్రభుత్వం విడుదల చేసే అధికారిక ఉత్తర్వులకు లోబడి ఉంటాయి.",
    eligibilityEn: [
      "Age 60 years or above for Old Age Pension (OAP).",
      "Valid BPL White Ration Card / Rice Card.",
      "Monthly family income benchmarked below ₹10,000 in rural areas and ₹12,000 in urban areas.",
      "Agricultural landholding within notified ceilings (up to 3.0 acres wet or 10.0 acres dry land).",
      "Excludes families owning four-wheelers (commercial livelihood vehicles exempted) or with regular government employees.",
    ],
    eligibilityTe: [
      "వృద్ధాప్య పింఛను కొరకు కనీసం 60 సంవత్సరాల వయస్సు ఉండాలి.",
      "చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు / బియ్యం కార్డు కలిగి ఉండాలి.",
      "కుటుంబ నెలవారీ ఆదాయం గ్రామీణ ప్రాంతాల్లో రూ. 10,000, పట్టణాల్లో రూ. 12,000 లోపు ఉండాలి.",
      "భూమి పరిమితి: గరిష్టంగా 3.0 ఎకరాల మాగాణి లేదా 10.0 ఎకరాల మెట్ట భూమి.",
      "నాలుగు చక్రాల ప్రైవేట్ వాహనం ఉండరాదు (వాణిజ్య వాహనాలు మినహాయింపు); ప్రభుత్వ ఉద్యోగులు ఉండరాదు.",
    ],
    exclusionsEn: [
      "Serving or retired government employees.",
      "Income tax payees.",
      "Holders of four-wheeler private personal vehicles.",
      "Recipients of other statutory government pensions.",
    ],
    exclusionsTe: [
      "ప్రభుత్వ ఉద్యోగులు మరియు సర్వీస్ పెన్షనర్లు.",
      "ఆదాయపు పన్ను చెల్లిస్తున్న కుటుంబాలు.",
      "సొంత కారు లేదా జీపు కలిగిన కుటుంబాలు.",
      "ఇతర ప్రభుత్వ పింఛన్లు పొందుతున్నవారు.",
    ],
    procedureEn: "Submit application with Aadhaar, age/category proof, and Rice Card at your local Grama / Ward Sachivalayam for field verification by Welfare Assistant and Social Audit.",
    procedureTe: "మీ ఆధార్ కార్డు, వయస్సు/కేటగిరీ ధృవీకరణ పత్రాలు మరియు రైస్ కార్డుతో గ్రామ/వార్డు సచివాలయంలో దరఖాస్తు సమర్పించండి; సామాజిక తనిఖీ (సోషల్ ఆడిట్) ద్వారా మంజూరు చేయబడుతుంది.",
    officialPortal: "https://sspensions.ap.gov.in",
    helpline: "1902 (Grama Sachivalayam / SSP Helpline)",
    verifiedSource: "Society for Elimination of Rural Poverty (SERP), Government of Andhra Pradesh",
    verifiedDate: "2026-11-21",
    cachedAt: "2026-11-24",
  },
  {
    id: "dr_ntr_vaidya_seva",
    keywords: ["health", "hospital", "doctor", "vaidya", "aarogyasri", "aarogya", "treatment", "వైద్యం", "ఆరోగ్యం", "ఆరోగ్యశ్రీ", "ఆసుపత్రి", "చికిత్స"],
    titleEn: "Dr. NTR Vaidya Seva (formerly Dr. YSR Aarogyasri)",
    titleTe: "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీ)",
    benefitEn: "Cashless secondary and tertiary medical/surgical treatment up to ₹25 Lakhs per eligible family per year strictly for listed procedures in empaneled network hospitals, subject to Dr. NTR Vaidya Seva Trust pre-authorization approval and package tariffs (not a general cash grant or unconditional private hospital reimbursement).",
    benefitTe: "గుర్తింపు పొందిన నెట్‌వర్క్ ఆసుపత్రులలో ట్రస్ట్ ప్రొసీజర్ మాస్టర్ పరిధిలోని వ్యాధులకు నిర్ణీత ప్యాకేజీల ప్రకారం కుటుంబానికి ఏడాదికి ₹25 లక్షల వరకు నగదు రహిత చికిత్స (ఇది ముందస్తు ప్రీ-ఆథరైజేషన్ అనుమతులకు లోబడి ఉంటుంది; సాధారణ నగదు చెల్లింపు లేదా ఏ ప్రైవేట్ ఆసుపత్రుల్లోనైనా వర్తించే ఉచిత పథకం కాదు).",
    eligibilityEn: [
      "Holders of valid BPL White Ration Card / Rice Card or Aarogyasri Health Card.",
      "Non-cardholders: Verified annual family income within notified eligibility ceiling (up to ₹5,00,000 per annum).",
      "Permanent resident of Andhra Pradesh.",
    ],
    eligibilityTe: [
      "చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు / బియ్యం కార్డు లేదా ఆరోగ్యశ్రీ హెల్త్ కార్డు ఉన్నవారు.",
      "కార్డు లేనిచో: వార్షిక కుటుంబ ఆదాయం ప్రభుత్వం నిర్ణయించిన పరిమితికి (రూ. 5 లక్షల లోపు) లోబడి ఉండాలి.",
      "ఆంధ్రప్రదేశ్ శాశ్వత నివాసి అయి ఉండాలి.",
    ],
    exclusionsEn: [
      "Regular government employees and service pensioners covered under Employees Health Scheme (EHS).",
      "Unlisted general OPD treatments and non-empaneled healthcare facilities.",
    ],
    exclusionsTe: [
      "ఉద్యోగుల ఆరోగ్య పథకం (EHS) వర్తించే రెగ్యులర్ ప్రభుత్వ ఉద్యోగులు మరియు పెన్షనర్లు.",
      "ప్రొసీజర్ జాబితాలో లేని సాధారణ ఓపీడీ చికిత్సలు మరియు గుర్తింపు లేని ఆసుపత్రులు.",
    ],
    procedureEn: "Approach the Aarogyamithra Help Desk at any empaneled network hospital with Rice Card or Aadhaar. In emergency life-threatening cases, dial 108 immediately.",
    procedureTe: "ఏదైనా నెట్‌వర్క్ ఆసుపత్రిలోని ఆరోగ్యమిత్ర డెస్క్‌ను మీ బియ్యం కార్డు లేదా ఆధార్‌తో సంప్రదించండి. ప్రాణాపాయ అత్యవసర పరిస్థితుల్లో వెంటనే 108 కు కాల్ చేయండి.",
    officialPortal: "https://drntrvaidyaseva.ap.gov.in",
    helpline: "104 (24x7 Health Advice) / 108 (Emergency Ambulance)",
    verifiedSource: "Dr. NTR Vaidya Seva Trust, Government of Andhra Pradesh",
    verifiedDate: "2026-11-21",
    cachedAt: "2026-11-24",
  },
  {
    id: "emergency_assistance",
    keywords: ["emergency", "ambulance", "police", "fire", "disaster", "helpline", "108", "104", "1902", "112", "అత్యవసర", "హెల్ప్‌లైన్", "పోలీస్", "అంబులెన్స్"],
    titleEn: "Emergency Public Services & Helplines",
    titleTe: "అత్యవసర ప్రజా సేవలు & హెల్ప్‌లైన్ నంబర్లు",
    benefitEn: "24x7 toll-free public emergency numbers accessible without internet or phone balance anywhere in Andhra Pradesh.",
    benefitTe: "ఇంటర్నెట్ లేదా ఫోన్ బ్యాలెన్స్ లేకుండా ఆంధ్రప్రదేశ్ అంతటా 24 గంటలు అందుబాటులో ఉండే ఉచిత అత్యవసర సహాయ నంబర్లు.",
    eligibilityEn: ["Available to all residents and citizens in Andhra Pradesh."],
    eligibilityTe: ["ఆంధ్రప్రదేశ్ లోని ప్రజలందరికీ ఉచితంగా అందుబాటులో ఉన్నాయి."],
    exclusionsEn: ["None."],
    exclusionsTe: ["ఏమీ లేవు."],
    procedureEn: "Dial toll-free directly from any mobile or landline: 108 for Emergency Ambulance, 104 for 24x7 Health Advice, 1902 for Sachivalayam Grievances, 112 for All Emergencies.",
    procedureTe: "ఏదైనా ఫోన్ నుండి నేరుగా డయల్ చేయండి: 108 (అత్యవసర అంబులెన్స్), 104 (వైద్య సలహాలు), 1902 (ప్రజా సమస్యలు/ఫిర్యాదులు), 112 (అన్ని రకాల అత్యవసరాలు).",
    officialPortal: "https://spandana.ap.gov.in",
    helpline: "108 (Ambulance) / 104 (Health) / 1902 (Grievance) / 112 (Emergency)",
    verifiedSource: "Government of Andhra Pradesh Emergency Directory",
    verifiedDate: "2026-11-21",
    cachedAt: "2026-11-24",
  },
];

/**
 * Searches the verified offline knowledge base for matches against user query keywords.
 */
export function findOfflinePublicInfo(query: string): OfflineSchemeInfo | null {
  const normalized = query.toLowerCase().trim();
  if (!normalized) return null;

  for (const item of OFFLINE_PUBLIC_KNOWLEDGE) {
    for (const kw of item.keywords) {
      if (normalized.includes(kw.toLowerCase())) {
        return item;
      }
    }
  }

  return null;
}
