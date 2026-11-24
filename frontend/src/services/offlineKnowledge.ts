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
  lastUpdated: string;
}

export const OFFLINE_PUBLIC_KNOWLEDGE: OfflineSchemeInfo[] = [
  {
    id: "annadata_sukhibhava_pmkisan",
    keywords: ["kisan", "pmkisan", "pm-kisan", "farmer", "annadata", "sukhibhava", "rythu", "రైతు", "కిసాన్", "అన్నదాత", "సుఖీభవ"],
    titleEn: "Annadata Sukhibhava / PM-KISAN (Farmer Assistance)",
    titleTe: "అన్నదాత సుఖీభవ / పీఎం-కిసాన్ (రైతు సహాయం)",
    benefitEn: "Financial support of ₹20,000 per year per eligible farmer family (combined Andhra Pradesh State ₹14,000 + Central PM-KISAN ₹6,000 disbursed across installments).",
    benefitTe: "అర్హులైన ప్రతి రైతు కుటుంబానికి ఏడాదికి ₹20,000 ఆర్థిక సహాయం (ఆంధ్రప్రదేశ్ ప్రభుత్వ ₹14,000 + కేంద్ర పీఎం-కిసాన్ ₹6,000 కలిపి విడతలలో జమ చేయబడుతుంది).",
    eligibilityEn: [
      "Landholding farmer families owning cultivable land in Andhra Pradesh.",
      "Aadhaar-linked active bank account with completed e-KYC.",
      "Land ownership updated in state revenue records (e-Crop / Webland).",
    ],
    eligibilityTe: [
      "ఆంధ్రప్రదేశ్‌లో సొంత సాగుభూమి కలిగిన రైతు కుటుంబాలు.",
      "ఆధార్‌తో లింక్ అయిన బ్యాంక్ ఖాతా మరియు పూర్తి చేసిన ఈ-కేవైసీ (e-KYC).",
      "వెబ్‌ల్యాండ్ / ఈ-క్రాప్ రెవెన్యూ రికార్డులలో నమోదైన పట్టాదారు భూమి వివరాలు.",
    ],
    exclusionsEn: [
      "Institutional landholders.",
      "Serving or retired government employees / officers.",
      "Income tax payers from the previous assessment year.",
      "Constitutional post holders and elected representatives.",
      "Pensioners receiving monthly pension of ₹10,000 or more.",
    ],
    exclusionsTe: [
      "సంస్థాగత భూ యజమానులు.",
      "ప్రభుత్వ ఉద్యోగులు / రిటైర్డ్ సర్వీస్ అధికారులు.",
      "గత అసెస్‌మెంట్ సంవత్సరంలో ఆదాయపు పన్ను చెల్లించినవారు.",
      "రాజ్యాంగ పదవులు మరియు చట్టసభల ప్రజా ప్రతినిధులు.",
      "నెలకు ₹10,000 లేదా అంతకంటే ఎక్కువ పెన్షన్ పొందుతున్నవారు.",
    ],
    procedureEn: "Complete e-KYC at your local Rythu Bharosa Kendram (RBK) or online via pmkisan.gov.in. Verify Aadhaar bank seeding with your bank branch.",
    procedureTe: "మీ స్థానిక రైతు భరోసా కేంద్రం (RBK) లో లేదా pmkisan.gov.in పోర్టల్ ద్వారా ఈ-కేవైసీ పూర్తి చేయండి. బ్యాంక్ ఖాతాకు ఆధార్ సీడింగ్ ధృవీకరించుకోండి.",
    officialPortal: "https://pmkisan.gov.in",
    helpline: "155261 / 1800-425-5143 (AP Kisan Call Centre)",
    verifiedSource: "Department of Agriculture, Government of Andhra Pradesh & Ministry of Agriculture and Farmers Welfare, GoI",
    lastUpdated: "2026-11-20",
  },
  {
    id: "thalliki_vandanam",
    keywords: ["thalliki", "vandanam", "amma", "vodi", "mother", "school", "education", "scholarship", "తల్లికి", "వందనం", "అమ్మ", "ఒడి", "పాఠశాల", "విద్య"],
    titleEn: "Thalliki Vandanam / Amma Vodi (School Education Support)",
    titleTe: "తల్లికి వందనం / అమ్మ ఒడి (పాఠశాల విద్యా సహాయం)",
    benefitEn: "Annual financial incentive of ₹15,000 credited to the bank account of eligible mothers/guardians sending children to recognized schools from Class 1 to Intermediate (12th).",
    benefitTe: "1వ తరగతి నుండి ఇంటర్మీడియట్ (12వ) వరకు గుర్తింపు పొందిన పాఠశాలలు/కళాశాలలకు పిల్లలను పంపే అర్హులైన తల్లుల బ్యాంక్ ఖాతాలో ఏడాదికి ₹15,000 జమ చేయబడుతుంది.",
    eligibilityEn: [
      "Mother or recognized legal guardian of child studying in Class 1 to 12 in AP.",
      "Student must maintain minimum 75% school attendance throughout academic year.",
      "Family must hold valid White Ration Card / Rice Card.",
    ],
    eligibilityTe: [
      "ఆంధ్రప్రదేశ్‌లో 1 నుండి 12వ తరగతి చదువుతున్న విద్యార్థుల తల్లులు లేదా సంరక్షకులు.",
      "విద్యా సంవత్సరంలో విద్యార్థి కనీసం 75% పాఠశాల హాజరును కలిగి ఉండాలి.",
      "కుటుంబం చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు / బియ్యం కార్డు కలిగి ఉండాలి.",
    ],
    exclusionsEn: [
      "Families with regular government employees or income tax payers.",
      "Students with attendance below 75% without certified medical exceptions.",
    ],
    exclusionsTe: [
      "ప్రభుత్వ ఉద్యోగులు లేదా ఆదాయపు పన్ను చెల్లించే కుటుంబాలు.",
      "వైద్య కారణాలు లేకుండా 75% కంటే తక్కువ హాజరు ఉన్న విద్యార్థులు.",
    ],
    procedureEn: "School headmasters submit student child info data. Verify school attendance records at your Village/Ward Sachivalayam Education Assistant desk.",
    procedureTe: "పాఠశాల ప్రధానోపాధ్యాయులు విద్యార్థి వివరాలను నమోదు చేస్తారు. మీ గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ & ఎడ్యుకేషన్ అసిస్టెంట్ ద్వారా రికార్డులను సరిచూసుకోండి.",
    officialPortal: "https://jaganannaammavodi.ap.gov.in",
    helpline: "1902 (Grama Sachivalayam Grievance)",
    verifiedSource: "Department of School Education, Government of Andhra Pradesh",
    lastUpdated: "2026-11-20",
  },
  {
    id: "ntr_bharosa_pension",
    keywords: ["pension", "ntr", "bharosa", "oap", "old age", "widow", "disabled", "sadarem", "పింఛను", "పెన్షన్", "వృద్ధాప్య", "వితంతు", "దివ్యాంగ", "సదరం"],
    titleEn: "NTR Bharosa Social Security Pension (OAP / Widow / Disabled)",
    titleTe: "ఎన్టీఆర్ భరోసా సామాజిక భద్రతా పింఛను (వృద్ధాప్య / వితంతు / దివ్యాంగ)",
    benefitEn: "Monthly pension of ₹4,000 for Senior Citizens (60+ years) and Widows; ₹6,000 for Persons with Disabilities (40%-79% disability); up to ₹15,000 for severe chronic kidney/dialysis patients.",
    benefitTe: "వృద్ధులకు (60 ఏళ్ళు పైబడినవారు) మరియు వితంతువులకు నెలకు ₹4,000; దివ్యాంగులకు (40%-79% సదరం సర్టిఫికెట్) నెలకు ₹6,000; తీవ్ర కిడ్నీ డయాలసిస్ రోగులకు నెలకు ₹15,000 వరకు పింఛను.",
    eligibilityEn: [
      "Age 60 years or above for Old Age Pension (OAP).",
      "Possession of White Ration Card / Rice Card.",
      "Monthly family income: Up to ₹10,000 in rural areas or ₹12,000 in urban areas.",
      "Landholding: Max 3.0 acres wetland or 10.0 acres dry land (or 10.0 acres combined).",
      "Residential electricity consumption less than 300 units per month.",
    ],
    eligibilityTe: [
      "వృద్ధాప్య పింఛను కొరకు కనీసం 60 సంవత్సరాల వయస్సు ఉండాలి.",
      "చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు లేదా బియ్యం కార్డు ఉండాలి.",
      "కుటుంబ నెలవారీ ఆదాయ పరిమితి: గ్రామీణ ప్రాంతాల్లో ₹10,000, పట్టణ ప్రాంతాల్లో ₹12,000 లోపు.",
      "భూమి పరిమితి: గరిష్టంగా 3.0 ఎకరాల మాగాణి లేదా 10.0 ఎకరాల మెట్ట భూమి.",
      "గృహ విద్యుత్ వినియోగం నెలకు 300 యూనిట్ల లోపు ఉండాలి.",
    ],
    exclusionsEn: [
      "Families with regular government employees or service pensioners.",
      "Ownership of four-wheeler (except commercial taxis, autos, tractors).",
      "Family members paying income tax.",
    ],
    exclusionsTe: [
      "ప్రభుత్వ ఉద్యోగులు లేదా సర్వీస్ పెన్షనర్లు ఉన్న కుటుంబాలు.",
      "నాలుగు చక్రాల వాహనం (కారు/జీపు) ఉన్నవారు (టాక్సీ, ఆటో, ట్రాక్టర్ మినహాయింపు).",
      "ఆదాయపు పన్ను చెల్లిస్తున్న కుటుంబ సభ్యులు.",
    ],
    procedureEn: "Submit application with Aadhaar and age proof at your local Grama / Ward Sachivalayam through the Digital Assistant.",
    procedureTe: "మీ ఆధార్ కార్డు మరియు వయస్సు ధృవీకరణ పత్రాలతో మీ గ్రామ/వార్డు సచివాలయంలో డిజిటల్ అసిస్టెంట్ ద్వారా దరఖాస్తు చేసుకోండి.",
    officialPortal: "https://sspensions.ap.gov.in",
    helpline: "1902 (SSP Toll-Free Helpline)",
    verifiedSource: "Society for Elimination of Rural Poverty (SERP), Government of Andhra Pradesh",
    lastUpdated: "2026-11-20",
  },
  {
    id: "dr_ntr_vaidya_seva",
    keywords: ["health", "hospital", "doctor", "vaidya", "aarogyasri", "aarogya", "treatment", "వైద్యం", "ఆరోగ్యం", "ఆరోగ్యశ్రీ", "ఆసుపత్రి", "చికిత్స"],
    titleEn: "Dr. NTR Vaidya Seva (formerly Dr. YSR Aarogyasri)",
    titleTe: "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీ)",
    benefitEn: "Cashless medical and surgical treatment up to ₹25 Lakhs per family per year across network public and private super-specialty hospitals.",
    benefitTe: "నెట్‌వర్క్ ఆసుపత్రుల్లో కుటుంబానికి ఏడాదికి ₹25 లక్షల వరకు ఉచిత నగదు రహిత శస్త్రచికిత్స మరియు వైద్య సేవలు.",
    eligibilityEn: [
      "Holders of White Rice Card / Aarogyasri Health Card.",
      "Non-cardholders: Family annual income ceiling up to ₹5,00,000.",
      "Resident of Andhra Pradesh.",
    ],
    eligibilityTe: [
      "తెల్ల రేషన్ కార్డు / ఆరోగ్యశ్రీ కార్డు ఉన్న కుటుంబాలు.",
      "కార్డు లేనిచో: కుటుంబ వార్షిక ఆదాయం ₹5,00,000 లోపు ఉండాలి.",
      "ఆంధ్రప్రదేశ్ రాష్ట్ర నివాసి అయి ఉండాలి.",
    ],
    exclusionsEn: [
      "Regular government employees covered under the Employees Health Scheme (EHS).",
    ],
    exclusionsTe: [
      "ఉద్యోగుల ఆరోగ్య పథకం (EHS) వర్తించే రెగ్యులర్ ప్రభుత్వ ఉద్యోగులు.",
    ],
    procedureEn: "Visit any empanelled hospital with your Rice Card / Aarogyasri Card and meet the Aarogyamithra desk for instant biometric pre-authorization.",
    procedureTe: "మీ బియ్యం కార్డు లేదా ఆరోగ్యశ్రీ కార్డుతో నెట్‌వర్క్ ఆసుపత్రిలోని ఆరోగ్యమిత్ర డెస్క్‌ను సంప్రదించండి.",
    officialPortal: "https://ysraarogyasri.ap.gov.in",
    helpline: "104 (24x7 Health Helpline) / 1800-599-1111",
    verifiedSource: "Dr. NTR Vaidya Seva Trust, Government of Andhra Pradesh",
    lastUpdated: "2026-11-20",
  },
  {
    id: "emergency_assistance",
    keywords: ["emergency", "ambulance", "police", "fire", "disaster", "helpline", "108", "104", "1902", "112", "అత్యవసర", "హెల్ప్‌లైన్", "పోలీస్", "అంబులెన్స్"],
    titleEn: "Emergency Civic Services & Helpline Directory",
    titleTe: "అత్యవసర ప్రజా సేవలు & హెల్ప్‌లైన్ నంబర్లు",
    benefitEn: "24x7 toll-free public emergency numbers and grievance redressal channels for all citizens of Andhra Pradesh.",
    benefitTe: "ఆంధ్రప్రదేశ్ పౌరులందరికీ 24 గంటల ఉచిత అత్యవసర సహాయ మరియు ప్రజా ఫిర్యాదుల హెల్ప్‌లైన్ నంబర్లు.",
    eligibilityEn: ["Available to all residents and citizens in Andhra Pradesh."],
    eligibilityTe: ["ఆంధ్రప్రదేశ్ లోని ప్రజలందరికీ ఉచితంగా అందుబాటులో ఉన్నాయి."],
    exclusionsEn: ["None."],
    exclusionsTe: ["ఏమీ లేవు."],
    procedureEn: "Dial the toll-free numbers directly from any mobile or landline without internet or balance.",
    procedureTe: "ఇంటర్నెట్ లేదా బ్యాలెన్స్ లేకుండా మొబైల్ లేదా ల్యాండ్‌లైన్ నుండి నేరుగా డయల్ చేయండి.",
    officialPortal: "https://spandana.ap.gov.in",
    helpline: "108 (Ambulance) / 104 (Medical Advice) / 1902 (Public Grievances) / 112 (All Emergencies)",
    verifiedSource: "Government of Andhra Pradesh Emergency Directory",
    lastUpdated: "2026-11-20",
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
