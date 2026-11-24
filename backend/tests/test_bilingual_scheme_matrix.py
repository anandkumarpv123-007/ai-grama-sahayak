"""
Comprehensive Bilingual Regression Matrix (80 Test Cases) for AI Grama Sahayak.
Phase 5F.6 Systemic RAG Reliability and Final Acceptance.
"""

from fastapi.testclient import TestClient
from app.main import app
import re

client = TestClient(app)

# 56 Positive Test Cases across 14 documents (4 per document)
POSITIVE_TEST_CASES = [
    # 1. agri_annadata_sukhibhava_pmkisan
    {
        "id": "POS_01_EN",
        "doc_id": "agri_annadata_sukhibhava_pmkisan",
        "query": "What is the Annadata Sukhibhava scheme for farmers in Andhra Pradesh?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_02_EN",
        "doc_id": "agri_annadata_sukhibhava_pmkisan",
        "query": "How are tenant farmers and land records verified for PM Kisan and Annadata Sukhibhava?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_03_TE",
        "doc_id": "agri_annadata_sukhibhava_pmkisan",
        "query": "ఆంధ్రప్రదేశ్ అన్నదాత సుఖీభవ పథకం వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_04_TE",
        "doc_id": "agri_annadata_sukhibhava_pmkisan",
        "query": "అన్నదాత సుఖీభవ పథకానికి ఈ-కేవైసీ ఎలా పూర్తి చేయాలి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },

    # 2. agri_kisan_credit_card
    {
        "id": "POS_05_EN",
        "doc_id": "agri_kisan_credit_card",
        "query": "What are the rules and credit limits for Kisan Credit Card (KCC)?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Kisan Credit Card (KCC) Scheme Rules and Institutional Credit",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_06_EN",
        "doc_id": "agri_kisan_credit_card",
        "query": "Which documents are required to apply for a KCC crop loan at the bank?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Kisan Credit Card (KCC) Scheme Rules and Institutional Credit",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_07_TE",
        "doc_id": "agri_kisan_credit_card",
        "query": "కిసాన్ క్రెడిట్ కార్డు (కేసీసీ) పథకం నిబంధనలు ఏమిటి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Kisan Credit Card (KCC) Scheme Rules and Institutional Credit",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_08_TE",
        "doc_id": "agri_kisan_credit_card",
        "query": "బ్యాంకులో పంట రుణం కోసం కిసాన్ క్రెడిట్ కార్డ్ ఎలా పొందాలి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Kisan Credit Card (KCC) Scheme Rules and Institutional Credit",
        "expected_assistant": "agriculture",
    },

    # 3. agri_pm_crop_insurance_ap
    {
        "id": "POS_09_EN",
        "doc_id": "agri_pm_crop_insurance_ap",
        "query": "How does free crop insurance and PM Fasal Bima Yojana operate in AP?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "PM Fasal Bima Yojana (PMFBY) & Crop Insurance in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_10_EN",
        "doc_id": "agri_pm_crop_insurance_ap",
        "query": "Is e-Panta crop booking mandatory for crop insurance claim settlement?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "PM Fasal Bima Yojana (PMFBY) & Crop Insurance in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_11_TE",
        "doc_id": "agri_pm_crop_insurance_ap",
        "query": "ఆంధ్రప్రదేశ్ ఉచిత పంటల బీమా పథకం వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "PM Fasal Bima Yojana (PMFBY) & Crop Insurance in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_12_TE",
        "doc_id": "agri_pm_crop_insurance_ap",
        "query": "పంట నష్టం పరిహారం కోసం ఈ-పంట నమోదు ఎలా చేసుకోవాలి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "PM Fasal Bima Yojana (PMFBY) & Crop Insurance in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },

    # 4. agri_soil_health_card_polam_badi
    {
        "id": "POS_13_EN",
        "doc_id": "agri_soil_health_card_polam_badi",
        "query": "What is the Soil Health Card scheme and Polam Badi training program?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Soil Health Card Scheme and Polam Badi Program in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_14_EN",
        "doc_id": "agri_soil_health_card_polam_badi",
        "query": "How can farmers get soil samples tested for macronutrients at RBKs?",
        "lang": "en",
        "assistant": "agriculture",
        "expected_source": "Soil Health Card Scheme and Polam Badi Program in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_15_TE",
        "doc_id": "agri_soil_health_card_polam_badi",
        "query": "సాయిల్ హెల్త్ కార్డు మరియు పొలం బడి కార్యక్రమం వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Soil Health Card Scheme and Polam Badi Program in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },
    {
        "id": "POS_16_TE",
        "doc_id": "agri_soil_health_card_polam_badi",
        "query": "రైతు భరోసా కేంద్రం ద్వారా భూసార పరీక్ష ఎలా చేయించుకోవాలి?",
        "lang": "te",
        "assistant": "agriculture",
        "expected_source": "Soil Health Card Scheme and Polam Badi Program in Andhra Pradesh",
        "expected_assistant": "agriculture",
    },

    # 5. edu_samagra_shiksha_ap
    {
        "id": "POS_17_EN",
        "doc_id": "edu_samagra_shiksha_ap",
        "query": "What school initiatives are provided under Samagra Shiksha Andhra Pradesh?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Samagra Shiksha AP and Mid-Day Meal (PM POSHAN / School Nutrition Programs)",
        "expected_assistant": "education",
    },
    {
        "id": "POS_18_EN",
        "doc_id": "edu_samagra_shiksha_ap",
        "query": "Are school uniforms, textbooks and mid-day meals provided free to students?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Samagra Shiksha AP and Mid-Day Meal (PM POSHAN / School Nutrition Programs)",
        "expected_assistant": "education",
    },
    {
        "id": "POS_19_TE",
        "doc_id": "edu_samagra_shiksha_ap",
        "query": "సమగ్ర శిక్ష ఆంధ్రప్రదేశ్ పాఠశాల విద్య కార్యక్రమాల వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Samagra Shiksha AP and Mid-Day Meal (PM POSHAN / School Nutrition Programs)",
        "expected_assistant": "education",
    },
    {
        "id": "POS_20_TE",
        "doc_id": "edu_samagra_shiksha_ap",
        "query": "ప్రభుత్వ పాఠశాలల్లో ఉచిత పాఠ్యపుస్తకాలు మరియు గోరుముద్ద మధ్యాహ్న భోజనం నిబంధనలు ఏమిటి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Samagra Shiksha AP and Mid-Day Meal (PM POSHAN / School Nutrition Programs)",
        "expected_assistant": "education",
    },

    # 6. edu_thalliki_vandanam_scheme
    {
        "id": "POS_21_EN",
        "doc_id": "edu_thalliki_vandanam_scheme",
        "query": "What are the guidelines for Thalliki Vandanam scheme for school students?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },
    {
        "id": "POS_22_EN",
        "doc_id": "edu_thalliki_vandanam_scheme",
        "query": "What is the mandatory 75% attendance rule for Thalliki Vandanam eligibility?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },
    {
        "id": "POS_23_TE",
        "doc_id": "edu_thalliki_vandanam_scheme",
        "query": "తల్లికి వందనం పథకం మార్గదర్శకాలు ఏమిటి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },
    {
        "id": "POS_24_TE",
        "doc_id": "edu_thalliki_vandanam_scheme",
        "query": "తల్లికి వందనం పొందడానికి విద్యార్థి హాజరు మరియు రైస్ కార్డు నిబంధనలు ఏమిటి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },

    # 7. edu_vidya_deevena_vasathi_deevena
    {
        "id": "POS_25_EN",
        "doc_id": "edu_vidya_deevena_vasathi_deevena",
        "query": "What are Jagananna Vidya Deevena and Vasathi Deevena post-matric scholarships?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Post-Matric Scholarships (RTF & MTF) / Jagananna Vidya Deevena & Vasathi Deevena",
        "expected_assistant": "education",
    },
    {
        "id": "POS_26_EN",
        "doc_id": "edu_vidya_deevena_vasathi_deevena",
        "query": "How is college fee reimbursement (RTF) applied on the Jnanabhumi portal?",
        "lang": "en",
        "assistant": "education",
        "expected_source": "Post-Matric Scholarships (RTF & MTF) / Jagananna Vidya Deevena & Vasathi Deevena",
        "expected_assistant": "education",
    },
    {
        "id": "POS_27_TE",
        "doc_id": "edu_vidya_deevena_vasathi_deevena",
        "query": "జగనన్న విద్యా దీవెన మరియు వసతి దీవెన పథకాల వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Post-Matric Scholarships (RTF & MTF) / Jagananna Vidya Deevena & Vasathi Deevena",
        "expected_assistant": "education",
    },
    {
        "id": "POS_28_TE",
        "doc_id": "edu_vidya_deevena_vasathi_deevena",
        "query": "జ్ఞానభూమి పోర్టల్ ద్వారా కాలేజీ ఫీజు రీయింబర్స్మెంట్ ఎలా దరఖాస్తు చేసుకోవాలి?",
        "lang": "te",
        "assistant": "education",
        "expected_source": "Post-Matric Scholarships (RTF & MTF) / Jagananna Vidya Deevena & Vasathi Deevena",
        "expected_assistant": "education",
    },

    # 8. health_104_108_emergency_health_services
    {
        "id": "POS_29_EN",
        "doc_id": "health_104_108_emergency_health_services",
        "query": "How do 104 mobile medical units and 108 emergency ambulance services work?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "104 Mobile Medical Units and 108 Emergency Ambulance Services in AP",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_30_EN",
        "doc_id": "health_104_108_emergency_health_services",
        "query": "Is 108 emergency ambulance service completely free of cost for road accidents?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "104 Mobile Medical Units and 108 Emergency Ambulance Services in AP",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_31_TE",
        "doc_id": "health_104_108_emergency_health_services",
        "query": "104 మరియు 108 అత్యవసర ఆరోగ్య సేవల వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "104 Mobile Medical Units and 108 Emergency Ambulance Services in AP",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_32_TE",
        "doc_id": "health_104_108_emergency_health_services",
        "query": "గ్రామాల్లో 104 మొబైల్ మెడికల్ యూనిట్ ద్వారా ఉచిత మందులు ఎలా అందిస్తారు?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "104 Mobile Medical Units and 108 Emergency Ambulance Services in AP",
        "expected_assistant": "healthcare",
    },

    # 9. health_ayushman_bharat_pmjay_ap
    {
        "id": "POS_33_EN",
        "doc_id": "health_ayushman_bharat_pmjay_ap",
        "query": "What is the Ayushman Bharat PM-JAY scheme convergence in Andhra Pradesh?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "Ayushman Bharat - PM-JAY Convergence in Andhra Pradesh",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_34_EN",
        "doc_id": "health_ayushman_bharat_pmjay_ap",
        "query": "How can eligible families download the Ayushman Bharat Golden Card?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "Ayushman Bharat - PM-JAY Convergence in Andhra Pradesh",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_35_TE",
        "doc_id": "health_ayushman_bharat_pmjay_ap",
        "query": "ఆంధ్రప్రదేశ్ ఆయుష్మాన్ భారత్ పీఎంజేఏవై పథకం వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "Ayushman Bharat - PM-JAY Convergence in Andhra Pradesh",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_36_TE",
        "doc_id": "health_ayushman_bharat_pmjay_ap",
        "query": "ఆయుష్మాన్ భారత్ హెల్త్ కార్డు అర్హతలు ఎలా తనిఖీ చేయాలి?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "Ayushman Bharat - PM-JAY Convergence in Andhra Pradesh",
        "expected_assistant": "healthcare",
    },

    # 10. health_dr_ntr_vaidya_seva_aarogyasri
    {
        "id": "POS_37_EN",
        "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
        "query": "What treatments are covered under Dr. NTR Vaidya Seva health insurance?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_38_EN",
        "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
        "query": "How can patients receive cashless inpatient treatment under NTR Vaidya Seva?",
        "lang": "en",
        "assistant": "healthcare",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_39_TE",
        "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
        "query": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ ఆరోగ్య బీమా పథకం వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },
    {
        "id": "POS_40_TE",
        "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
        "query": "నెట్‌వర్క్ ఆసుపత్రుల్లో ఎన్టీఆర్ వైద్య సేవ కింద ఉచిత చికిత్స ఎలా పొందాలి?",
        "lang": "te",
        "assistant": "healthcare",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },

    # 11. schemes_pedalandariki_illu_housing
    {
        "id": "POS_41_EN",
        "doc_id": "schemes_pedalandariki_illu_housing",
        "query": "What are the guidelines for Pedalandariki Illu housing scheme?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "Pedalandariki Illu Housing Scheme Guidelines and Construction Subsidies",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_42_EN",
        "doc_id": "schemes_pedalandariki_illu_housing",
        "query": "Who is eligible for house site patta and construction subsidies through APSHCL?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "Pedalandariki Illu Housing Scheme Guidelines and Construction Subsidies",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_43_TE",
        "doc_id": "schemes_pedalandariki_illu_housing",
        "query": "పేదలందరికీ ఇళ్లు గృహ నిర్మాణ పథకం నిబంధనలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "Pedalandariki Illu Housing Scheme Guidelines and Construction Subsidies",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_44_TE",
        "doc_id": "schemes_pedalandariki_illu_housing",
        "query": "ఇళ్ల స్థలాల పట్టాలు మరియు గృహ నిర్మాణ రాయితీ కోసం ఎవరు అర్హులు?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "Pedalandariki Illu Housing Scheme Guidelines and Construction Subsidies",
        "expected_assistant": "schemes",
    },

    # 12. schemes_ntr_bharosa_pension
    {
        "id": "POS_45_EN",
        "doc_id": "schemes_ntr_bharosa_pension",
        "query": "What are the eligibility categories for NTR Bharosa social security pension?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_46_EN",
        "doc_id": "schemes_ntr_bharosa_pension",
        "query": "How can senior citizens apply for Old Age Pension (OAP) under NTR Bharosa?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_47_TE",
        "doc_id": "schemes_ntr_bharosa_pension",
        "query": "ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛన్ అర్హతలు మరియు వర్గాలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_48_TE",
        "doc_id": "schemes_ntr_bharosa_pension",
        "query": "వృద్ధాప్య మరియు వితంతు పింఛన్ కోసం సచివాలయంలో ఎలా దరఖాస్తు చేసుకోవాలి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },

    # 13. schemes_mgnregs_andhra_pradesh
    {
        "id": "POS_49_EN",
        "doc_id": "schemes_mgnregs_andhra_pradesh",
        "query": "What are the wage rights and guidelines under MGNREGS in Andhra Pradesh?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "MGNREGS Andhra Pradesh Guidelines and Wage Rights",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_50_EN",
        "doc_id": "schemes_mgnregs_andhra_pradesh",
        "query": "How can rural households apply for an MGNREGS Job Card and 100 days work?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "MGNREGS Andhra Pradesh Guidelines and Wage Rights",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_51_TE",
        "doc_id": "schemes_mgnregs_andhra_pradesh",
        "query": "ఆంధ్రప్రదేశ్ ఉపాధి హామీ పథకం మార్గదర్శకాలు మరియు వేతన హక్కులు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "MGNREGS Andhra Pradesh Guidelines and Wage Rights",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_52_TE",
        "doc_id": "schemes_mgnregs_andhra_pradesh",
        "query": "ఉపాధి హామీ జాబ్ కార్డు ఎలా పొందాలి మరియు 100 రోజుల పని హక్కు వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "MGNREGS Andhra Pradesh Guidelines and Wage Rights",
        "expected_assistant": "schemes",
    },

    # 14. schemes_grama_ward_sachivalayam
    {
        "id": "POS_53_EN",
        "doc_id": "schemes_grama_ward_sachivalayam",
        "query": "What citizen services are delivered by Grama and Ward Sachivalayam system in AP?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "Grama and Ward Sachivalayam Citizen Service Delivery System",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_54_EN",
        "doc_id": "schemes_grama_ward_sachivalayam",
        "query": "How can citizens track certificate applications and service delivery timelines at Sachivalayam?",
        "lang": "en",
        "assistant": "schemes",
        "expected_source": "Grama and Ward Sachivalayam Citizen Service Delivery System",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_55_TE",
        "doc_id": "schemes_grama_ward_sachivalayam",
        "query": "గ్రామ మరియు వార్డు సచివాలయం ద్వారా అందే ప్రజా సేవలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "Grama and Ward Sachivalayam Citizen Service Delivery System",
        "expected_assistant": "schemes",
    },
    {
        "id": "POS_56_TE",
        "doc_id": "schemes_grama_ward_sachivalayam",
        "query": "గ్రామ సచివాలయంలో కుల, ఆదాయ ధ్రువపత్రాల కోసం దరఖాస్తు ప్రక్రియ ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "expected_source": "Grama and Ward Sachivalayam Citizen Service Delivery System",
        "expected_assistant": "schemes",
    },
]

# 24 Negative, Adversarial, Historical, Disambiguation, Emergency and Service Cases
NEGATIVE_ADVERSARIAL_CASES = [
    # Historical Scheme Handling
    {
        "id": "HIST_01_EN",
        "query": "Explain about Ammavodi, Andhra Pradesh.",
        "lang": "en",
        "assistant": "schemes",
        "check": "historical_ammavodi",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },
    {
        "id": "HIST_02_TE",
        "query": "అమ్మఒడి పథకం గురించి వివరించండి.",
        "lang": "te",
        "assistant": "schemes",
        "check": "historical_ammavodi",
        "expected_source": "Thalliki Vandanam Scheme Guidelines and School Education Support",
        "expected_assistant": "education",
    },
    {
        "id": "HIST_03_EN",
        "query": "How to register for Rythu Bharosa in Andhra Pradesh?",
        "lang": "en",
        "assistant": "schemes",
        "check": "historical_rythu_bharosa",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },
    {
        "id": "HIST_04_TE",
        "query": "వైఎస్సార్ రైతు భరోసా నమోదు విధానం ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "check": "historical_rythu_bharosa",
        "expected_source": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "expected_assistant": "agriculture",
    },
    {
        "id": "HIST_05_EN",
        "query": "How to apply for YSR Pension Kanuka?",
        "lang": "en",
        "assistant": "schemes",
        "check": "historical_pension_kanuka",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },
    {
        "id": "HIST_06_TE",
        "query": "పెన్షన్ కానుక అర్హతలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "check": "historical_pension_kanuka",
        "expected_source": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "expected_assistant": "schemes",
    },
    {
        "id": "HIST_07_EN",
        "query": "What treatments are covered in Aarogyasri?",
        "lang": "en",
        "assistant": "schemes",
        "check": "historical_aarogyasri",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },
    {
        "id": "HIST_08_TE",
        "query": "ఆరోగ్యశ్రీ పథకం కింద ఉచిత చికిత్స వివరాలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "check": "historical_aarogyasri",
        "expected_source": "Dr. NTR Vaidya Seva Scheme (Aarogyasri) Guidelines and Covered Treatments",
        "expected_assistant": "healthcare",
    },

    # Ambiguous NTR Queries (Disambiguation)
    {
        "id": "DISAMB_01_EN",
        "query": "Tell me about NTR in Andhra Pradesh",
        "lang": "en",
        "assistant": "schemes",
        "check": "ambiguous_ntr",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "DISAMB_02_TE",
        "query": "ఎన్టీఆర్ పథకం గురించి చెప్పండి",
        "lang": "te",
        "assistant": "schemes",
        "check": "ambiguous_ntr",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },

    # Unnamed Scheme Ambiguity (Under general schemes)
    {
        "id": "UNNAMED_01_EN",
        "query": "How to apply for the government scheme?",
        "lang": "en",
        "assistant": "schemes",
        "check": "unnamed_scheme_clarification",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "UNNAMED_02_TE",
        "query": "ప్రభుత్వ పథకానికి ఎలా దరఖాస్తు చేయాలి?",
        "lang": "te",
        "assistant": "schemes",
        "check": "unnamed_scheme_clarification",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },

    # Unsupported / Non-existent Schemes (Truthful reporting)
    {
        "id": "UNSUPP_01_EN",
        "query": "Free Electric Scooter Scheme for women subsidy in AP",
        "lang": "en",
        "assistant": "schemes",
        "check": "unsupported_scheme",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "UNSUPP_02_TE",
        "query": "ఉచిత ల్యాప్‌టాప్ పంపిణీ అర్హతలు ఏమిటి?",
        "lang": "te",
        "assistant": "schemes",
        "check": "unsupported_scheme",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },

    # Clinical Emergency Safety Bypass
    {
        "id": "EMERG_01_EN",
        "query": "Patient is having severe chest pain, breathing difficulty, and sweating!",
        "lang": "en",
        "assistant": "healthcare",
        "check": "clinical_emergency_108",
        "expected_sources_empty": True,
    },
    {
        "id": "EMERG_02_TE",
        "query": "తీవ్రమైన గుండె నొప్పి మరియు శ్వాస ఆడకపోవడం వల్ల రోగి స్పృహ తప్పుతున్నాడు!",
        "lang": "te",
        "assistant": "healthcare",
        "check": "clinical_emergency_108",
        "expected_sources_empty": True,
    },

    # Nearby Service Intent Routing
    {
        "id": "SERVICE_01_EN",
        "query": "Where is the nearest hospital in Kakinada?",
        "lang": "en",
        "assistant": "healthcare",
        "check": "verified_hospital_lookup",
        "expected_source": "Government General Hospital (GGH) Kakinada",
    },
    {
        "id": "SERVICE_02_TE",
        "query": "విశాఖపట్నంలో సమీపంలోని ఆసుపత్రి ఎక్కడ ఉంది?",
        "lang": "te",
        "assistant": "healthcare",
        "check": "verified_hospital_lookup",
        "expected_source": "King George Hospital (KGH) Visakhapatnam",
    },
    {
        "id": "SERVICE_03_EN",
        "query": "Where is the nearest hospital?",
        "lang": "en",
        "assistant": "healthcare",
        "check": "hospital_district_prompt",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "SERVICE_04_EN",
        "query": "Where is my nearest Rythu Bharosa Kendram (RBK)?",
        "lang": "en",
        "assistant": "agriculture",
        "check": "rbk_honest_guidance",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "SERVICE_05_TE",
        "query": "సమీపంలోని రైతు భరోసా కేంద్రం ఎక్కడ ఉంది?",
        "lang": "te",
        "assistant": "agriculture",
        "check": "rbk_honest_guidance",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },
    {
        "id": "SERVICE_06_EN",
        "query": "How to find my nearest village secretariat (Grama Sachivalayam)?",
        "lang": "en",
        "assistant": "schemes",
        "check": "sachivalayam_honest_guidance",
        "expected_sources_empty": True,
        "expected_needs_follow_up": True,
    },

    # Generic Administrative Query
    {
        "id": "GENERIC_01_EN",
        "query": "Andhra Pradesh government online application portal guidelines",
        "lang": "en",
        "assistant": "schemes",
        "check": "generic_admin_no_false_scheme",
    },
    {
        "id": "GENERIC_02_TE",
        "query": "ఆంధ్రప్రదేశ్ ప్రభుత్వం ఆన్‌లైన్ దరఖాస్తు విధానం",
        "lang": "te",
        "assistant": "schemes",
        "check": "generic_admin_no_false_scheme",
    },
]



import pytest

@pytest.mark.parametrize("tc", POSITIVE_TEST_CASES, ids=[c["id"] for c in POSITIVE_TEST_CASES])
def test_positive_scheme_cases(tc):
    res = client.post(
        "/api/chat",
        json={
            "message": tc["query"],
            "assistant": tc["assistant"],
            "language": tc["lang"],
            "state": "Andhra Pradesh",
        },
    )
    assert res.status_code == 200, f"HTTP {res.status_code} for {tc['id']}"
    data = res.json()
    sources = [s["title"] for s in data.get("sources", [])]
    answer = data.get("answer", "")

    assert len(sources) >= 1, f"Expected sources for {tc['id']} but got 0"
    assert any(tc["expected_source"].lower() in s.lower() for s in sources), (
        f"Expected source '{tc['expected_source']}' not in returned sources: {sources}"
    )
    assert data.get("assistant") == tc["expected_assistant"], (
        f"Expected assistant '{tc['expected_assistant']}' but got '{data.get('assistant')}'"
    )
    if tc["lang"] == "en":
        for line in answer.split("\n"):
            te_count = len(re.findall(r"[ఀ-౿]", line))
            assert not (te_count >= 5 and (te_count > len(line) * 0.10)), (
                f"Telugu character leak detected in English response for {tc['id']}: {line}"
            )
    elif tc["lang"] == "te":
        te_total = len(re.findall(r"[ఀ-౿]", answer))
        assert te_total >= 30, f"Telugu response for {tc['id']} lacks sufficient Telugu text ({te_total})"
        te_words = re.findall(r"[\u0c00-\u0c7f]+", answer)
        assert len(te_words) >= 5, f"Telugu response for {tc['id']} lacks core Telugu content words ({len(te_words)})"


@pytest.mark.parametrize("tc", NEGATIVE_ADVERSARIAL_CASES, ids=[c["id"] for c in NEGATIVE_ADVERSARIAL_CASES])
def test_negative_adversarial_cases(tc):
    res = client.post(
        "/api/chat",
        json={
            "message": tc["query"],
            "assistant": tc["assistant"],
            "language": tc["lang"],
            "state": "Andhra Pradesh",
        },
    )
    assert res.status_code == 200, f"HTTP {res.status_code} for {tc['id']}"
    data = res.json()
    sources = [s["title"] for s in data.get("sources", [])]
    answer = data.get("answer", "")
    check_type = tc["check"]

    if "historical" in check_type:
        assert any(tc["expected_source"].lower() in s.lower() for s in sources), (
            f"Expected successor source '{tc['expected_source']}' in {sources}"
        )
        assert data.get("assistant") == tc["expected_assistant"]
        if tc["lang"] == "en":
            for line in answer.split("\n"):
                te_count = len(re.findall(r"[ఀ-౿]", line))
                assert not (te_count >= 5 and (te_count > len(line) * 0.10))

    elif check_type == "ambiguous_ntr":
        assert len(sources) == 0
        assert data.get("needs_follow_up") is True
        assert "1" in answer and "2" in answer

    elif check_type == "unnamed_scheme_clarification":
        assert len(sources) == 0
        assert data.get("needs_follow_up") is True

    elif check_type == "unsupported_scheme":
        assert len(sources) == 0
        has_unavail = (
            "unavailable" in answer.lower()
            or "అందుబాటులో లేదు" in answer
            or "specify which" in answer.lower()
            or "స్పష్టం" in answer
        )
        assert has_unavail
        assert data.get("needs_follow_up") is True

    elif check_type == "clinical_emergency_108":
        assert len(sources) == 0
        assert "108" in answer
        # Prioritize immediate emergency care without delay; eliminate unsupported 24-48h timeline
        assert "24" not in answer and "48" not in answer
        if tc["lang"] == "te":
            assert "వెంటనే" in answer or "అత్యవసర" in answer
        else:
            assert "immediate" in answer.lower() or "emergency" in answer.lower()

    elif check_type == "verified_hospital_lookup":
        assert any(tc["expected_source"].lower() in s.lower() for s in sources)

    elif check_type == "hospital_district_prompt":
        assert len(sources) == 0
        assert ("district" in answer.lower() or "జిల్లా" in answer)

    elif check_type in ("rbk_honest_guidance", "sachivalayam_honest_guidance"):
        assert len(sources) == 0
        assert ("ap.gov.in" in answer or "sachivalayam" in answer.lower())

    elif check_type == "generic_admin_no_false_scheme":
        assert len(sources) == 0


def test_canonical_registry_parity():
    """Verify that every indexed document matches SCHEME_REGISTRY exactly (14 documents)."""
    from app.services.retrieval.service import get_retrieval_service
    from app.services.retrieval.scheme_registry import SCHEME_REGISTRY

    service = get_retrieval_service()
    service.initialize()
    loaded_doc_ids = set(c.metadata.get("doc_id") for c in service.indexer.chunks)
    registry_doc_ids = set(SCHEME_REGISTRY.keys())
    assert loaded_doc_ids == registry_doc_ids
    assert len(loaded_doc_ids) == 14
