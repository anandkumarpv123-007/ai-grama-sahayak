"""
Hybrid Multilingual Indexer for AI Grama Sahayak.
Combines BM25 lexical ranking, character n-grams for Telugu morphological robustness,
TF-IDF vector matching, strict assistant/domain filtering, and confidence thresholding.
Runs 100% locally with zero external vector database dependencies.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set
from app.services.retrieval.models import RetrievedChunk
from app.services.retrieval.scheme_registry import detect_named_schemes


class MultilingualTokenizer:
    """
    Tokenizer designed for English and Telugu text in public governance contexts.
    Produces word tokens, Telugu character n-grams, and bilingual keyword expansions.
    """

    # Telugu Unicode range: \u0C00 to \u0C7F
    TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]+")
    ENGLISH_RE = re.compile(r"[a-zA-Z0-9]+")

    ENGLISH_STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "at", "from", "by", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below",
        "to", "of", "in", "on", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "can", "could",
        "will", "would", "shall", "should", "how", "what", "where", "which",
        "who", "whom", "this", "that", "these", "those", "am", "i", "you",
        "he", "she", "it", "we", "they", "my", "your", "his", "her", "its",
    }

    TELUGU_STOPWORDS = {
        "ఎలా", "ఎప్పుడు", "ఎక్కడ", "ఎవరు", "ఏమిటి", "ఏది", "మరియు",
        "లేదా", "యొక్క", "పై", "కింద", "లో", "నుండి", "ద్వారా", "కోసం",
        "గురించి", "కూడా", "కాని", "అయితే", "ఉంది", "ఉన్నాయి", "ఉన్న", "అని",
    }

    # Bilingual synonym and concept map for Andhra Pradesh public services
    BILINGUAL_SYNONYMS: Dict[str, List[str]] = {
        # Agriculture
        "రైతు": ["farmer", "rythu", "kisan", "agriculture", "cultivator"],
        "రైతులు": ["farmer", "farmers", "rythu", "kisan", "agriculture"],
        "రైతులకు": ["farmer", "farmers", "rythu", "kisan", "agriculture"],
        "వ్యవసాయం": ["agriculture", "farming", "crop"],
        "పంట": ["crop", "harvest", "yield"],
        "పంటలు": ["crops", "harvest", "yield"],
        "బీమా": ["insurance", "bima", "coverage", "fasal"],
        "విత్తనాలు": ["seeds", "seed"],
        "ఎరువులు": ["fertilizer", "fertilizers", "manure"],
        "అన్నదాత": ["annadata", "sukhibhava", "pmkisan", "farmer"],
        "సుఖీభవ": ["sukhibhava", "annadata", "pmkisan"],

        # Healthcare
        "ఆరోగ్యం": ["health", "healthcare", "medical", "clinic"],
        "ఆరోగ్యశ్రీ": ["aarogyasri", "vaidya", "seva", "health", "hospital"],
        "వైద్యం": ["medical", "treatment", "medicine", "doctor"],
        "వైద్యుడు": ["doctor", "physician", "medical"],
        "ఆసుపత్రి": ["hospital", "clinic", "medical"],
        "చికిత్స": ["treatment", "cure", "therapy", "surgery"],
        "మందులు": ["medicines", "drugs", "tablets"],
        "అంబులెన్స్": ["ambulance", "emergency", "108"],
        "అత్యవసర": ["emergency", "critical", "ambulance", "108"],

        # Education
        "విద్య": ["education", "study", "learning", "school"],
        "చదువు": ["education", "study", "learning"],
        "పాఠశాల": ["school", "vidyalaya", "education"],
        "బడి": ["school", "education"],
        "కళాశాల": ["college", "institution", "university"],
        "ఫీజు": ["fee", "tuition", "rtf", "reimbursement"],
        "వసతి": ["hostel", "accommodation", "maintenance", "mtf", "vasathi"],
        "దీవెన": ["deevena", "vidya", "vasathi", "scholarship"],
        "స్కాలర్షిప్": ["scholarship", "scholarships", "post-matric", "rtf", "mtf", "vidya", "deevena"],
        "స్కాలర్‌షిప్": ["scholarship", "scholarships", "post-matric", "rtf", "mtf", "vidya", "deevena"],
        "స్కాలర్షిప్స్": ["scholarship", "scholarships", "post-matric", "rtf", "mtf", "vidya", "deevena"],
        "స్కాలర్‌షిప్స్": ["scholarship", "scholarships", "post-matric", "rtf", "mtf", "vidya", "deevena"],
        "విద్యార్థి": ["student", "students", "scholarship", "vidyarthi"],
        "విద్యార్థులు": ["students", "student", "scholarship", "vidyarthulu"],
        "వందనం": ["vandanam", "thalliki", "amma", "vodi"],
        "తల్లికి": ["mother", "thalliki", "vandanam", "amma"],
        "హాజరు": ["attendance", "present", "percentage"],

        # Schemes & Social Security
        "పింఛన్": ["pension", "pensioner", "bharosa", "monthly"],
        "పెన్షన్": ["pension", "pensioner", "bharosa", "monthly"],
        "భరోసా": ["bharosa", "pension", "support"],
        "సచివాలయం": ["sachivalayam", "secretariat", "village", "ward"],
        "గ్రామ": ["grama", "village", "rural"],
        "వార్డు": ["ward", "urban", "municipality"],
        "ఉపాధి": ["employment", "mgnregs", "work", "wage"],
        "ఉపాధి హామీ": ["mgnregs", "nrega", "employment", "wage"],
        "ఇల్లు": ["housing", "house", "patta", "illu", "apshcl"],
        "గృహ": ["housing", "house", "residence"],
        "రేషన్": ["ration", "rice", "card", "bpl"],
        "రైస్ కార్డు": ["rice", "card", "ration", "white"],

        # Intent & General Governance Concepts (Amount, Assistance, Eligibility, Documents, Application)
        "సహాయం": ["assistance", "financial", "support", "payment"],
        "సాయం": ["assistance", "financial", "support"],
        "ఆర్థిక": ["financial", "assistance", "money", "funds"],
        "ఎంత": ["amount", "assistance", "payment", "rate"],
        "డబ్బులు": ["money", "financial", "amount"],
        "చెల్లింపు": ["payment", "disbursement", "installment"],
        "చెల్లింపులు": ["payments", "disbursements", "installments"],
        "వాయిదా": ["installment", "phase", "payment"],
        "వాయిదాల": ["installments", "phases", "payment"],
        "మొత్తం": ["amount", "total", "assistance"],
        "వేతనం": ["wage", "salary", "payment"],
        "వేతనాలు": ["wages", "salaries", "payments"],
        "పరిమితి": ["limit", "ceiling", "coverage"],
        "అర్హత": ["eligibility", "eligible", "criteria"],
        "అర్హతలు": ["eligibility", "eligible", "criteria", "rules"],
        "అర్హులు": ["eligible", "beneficiary", "beneficiaries"],
        "నిబంధనలు": ["conditions", "rules", "guidelines", "criteria"],
        "పత్రాలు": ["documents", "records", "certificates"],
        "కాగితాలు": ["documents", "records"],
        "దరఖాస్తు": ["application", "apply", "enrollment", "registration"],
        "నమోదు": ["enrollment", "registration", "booking"],
    }

    def tokenize(self, text: str, include_ngrams: bool = True) -> List[str]:
        """
        Tokenizes text into words, subword n-grams, and expands domain synonyms.
        """
        if not text:
            return []

        tokens: List[str] = []
        lowered = text.lower()

        # 1. English word tokens
        for match in self.ENGLISH_RE.finditer(lowered):
            word = match.group(0)
            if len(word) >= 2:
                tokens.append(word)

        # 2. Telugu word tokens and character n-grams
        for match in self.TELUGU_RE.finditer(text):
            telugu_word = match.group(0)
            tokens.append(telugu_word)

            if include_ngrams:
                chars = list(telugu_word)
                if len(chars) >= 3:
                    for i in range(len(chars) - 2):
                        tokens.append("".join(chars[i : i + 3]))
                if len(chars) >= 4:
                    for i in range(len(chars) - 3):
                        tokens.append("".join(chars[i : i + 4]))

            # Bilingual synonym expansion
            synonyms = self.BILINGUAL_SYNONYMS.get(telugu_word)
            if synonyms:
                tokens.extend(synonyms)

        return tokens

    def extract_informative_tokens(self, text: str) -> Set[str]:
        """
        Extracts non-stopword tokens from user queries for relevance coverage gating.
        """
        raw_tokens = self.tokenize(text, include_ngrams=False)
        informative: Set[str] = set()
        for tok in raw_tokens:
            tok_lower = tok.lower()
            if tok_lower in self.ENGLISH_STOPWORDS or tok in self.TELUGU_STOPWORDS:
                continue
            if len(tok) > 1:
                informative.add(tok_lower)
        return informative



# Intent taxonomy for governance queries (Telugu and English)
INTENT_KEYWORDS: Dict[str, Dict[str, Set[str]]] = {
    "amount": {
        "en": {
            "amount", "payment", "financial", "assistance", "installment",
            "installments", "rate", "rates", "wage", "wages", "payout",
            "limit", "cost", "rupees", "rs", "fee", "fees", "subvention",
        },
        "te": {
            "ఎంత", "సహాయం", "సాయం", "డబ్బులు", "చెల్లింపు", "చెల్లింపులు",
            "వాయిదా", "వాయిదాల", "మొత్తం", "పరిమితి", "వేతనం", "వేతనాలు",
            "ఖర్చు", "రూపాయలు", "ఫీజు",
        },
    },
    "eligibility": {
        "en": {
            "eligibility", "eligible", "criteria", "conditions", "rules",
            "qualify", "qualification", "attendance", "who", "exclusion",
            "ineligibility",
        },
        "te": {
            "అర్హత", "అర్హతలు", "అర్హులు", "నిబంధనలు", "ఎవరు", "ఎవరెవరు",
            "హాజరు", "అనర్హత", "అనర్హతలు",
        },
    },
    "documents": {
        "en": {
            "document", "documents", "records", "proof", "certificate",
            "certificates", "card", "passbook", "aadhaar",
        },
        "te": {
            "పత్రాలు", "కాగితాలు", "డాక్యుమెంట్లు", "సర్టిఫికెట్లు",
            "కార్డు", "ఆధార్", "పాస్ బుక్", "పాస్‌బుక్",
        },
    },
    "application": {
        "en": {
            "apply", "application", "procedure", "process", "steps",
            "portal", "registration", "enrollment", "grievance", "status",
        },
        "te": {
            "దరఖాస్తు", "దరఖాస్తులు", "నమోదు", "విధానం", "ఎలా", "ఎక్కడ",
            "పరిష్కారం",
        },
    },
}

SECTION_INTENT_MAP: Dict[str, Set[str]] = {
    "amount": {
        "financial assistance", "payment breakdown", "payout rates", "wages",
        "coverage limit", "concessional rates", "interest subvention",
        "ఆర్థిక సహాయం", "వాయిదాల వివరాలు", "చెల్లింపులు", "వేతనాలు",
        "పరిమితి", "రేట్లు", "fees", "fee reimbursement", "రీయింబర్స్‌మెంట్",
        "benefits", "ప్రయోజనాలు", "monthly payout",
    },
    "eligibility": {
        "eligibility", "eligibility criteria", "ineligibility", "exclusions",
        "లబ్ధిదారుల అర్హత", "అర్హతలు", "అర్హత నిబంధనలు", "అనర్హతలు",
        "నిబంధనలు", "mandatory conditions",
    },
    "documents": {
        "required documents", "documents", "అవసరమైన పత్రాలు", "పత్రాలు",
        "card generation",
    },
    "application": {
        "application", "enrollment procedure", "how to apply", "how to avail",
        "how to obtain", "claim settlement", "దరఖాస్తు", "నమోదు",
        "సేవలు పొందే విధానం", "సంప్రదింపు", "grievance redressal",
    },
}


GENERIC_ADMIN_TOKENS = {
    "andhra", "pradesh", "ap", "government", "govt", "portal", "online",
    "application", "guidelines", "details", "system", "program", "programs",
    "scheme", "schemes", "apply", "rules", "services", "service", "process",
    "procedure", "official", "status", "form", "enrollment", "registration",
    "booking", "criteria", "eligible", "eligibility",
    "పథకం", "పథకాలు", "పథకానికి", "ప్రభుత్వం", "ఆంధ్రప్రదేశ్", "విధానం",
    "సేవలు", "వివరాలు", "దరఖాస్తు", "నమోదు", "పోర్టల్", "ఆన్‌లైన్", "ఆన్", "లైన్",
}


SCHEME_DOMAIN_WORDS: Set[str] = {
    "scholarship", "scholarships", "post-matric", "vidya", "vasathi", "deevena", "vandanam",
    "pension", "pensions", "housing", "house", "illu", "patta", "ration", "rice",
    "hospital", "hospitals", "medical", "treatment", "doctor", "health",
    "farmer", "farmers", "crop", "crops", "agriculture", "kisan", "sukhibhava", "bharosa",
    "mgnregs", "employment", "wage", "wages", "job", "card", "labor",
    "విద్యార్థి", "విద్యార్థులు", "స్కాలర్షిప్", "స్కాలర్‌షిప్", "స్కాలర్షిప్స్", "స్కాలర్‌షిప్స్",
}

ALL_INTENT_TOKENS: Set[str] = set()
for _intent, _lang_map in INTENT_KEYWORDS.items():
    ALL_INTENT_TOKENS.update(_lang_map["en"])
    ALL_INTENT_TOKENS.update(_lang_map["te"])
for _te_w, _syns in MultilingualTokenizer.BILINGUAL_SYNONYMS.items():
    if any(_s in ALL_INTENT_TOKENS for _s in _syns):
        ALL_INTENT_TOKENS.add(_te_w)
        ALL_INTENT_TOKENS.update(_syns)
ALL_INTENT_TOKENS.difference_update(SCHEME_DOMAIN_WORDS)


def detect_query_intents(query: str, query_tokens: List[str]) -> Set[str]:
    """
    Detects question intent categories (amount, eligibility, documents, application)
    across English and Telugu queries.
    """
    detected: Set[str] = set()
    q_lower = query.lower()
    tok_set = set(t.lower() for t in query_tokens)
    for intent, lang_map in INTENT_KEYWORDS.items():
        for kw in lang_map["en"]:
            if kw in tok_set or f" {kw} " in f" {q_lower} ":
                detected.add(intent)
        for kw in lang_map["te"]:
            if kw in tok_set or kw in q_lower:
                detected.add(intent)
    return detected


class HybridMultilingualIndexer:
    """
    In-memory BM25 + TF-IDF hybrid index with assistant domain partition and query coverage gating.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        min_score_threshold: float = 0.15,
        min_coverage_threshold: float = 0.25,
    ):
        self.k1 = k1
        self.b = b
        self.min_score_threshold = min_score_threshold
        self.min_coverage_threshold = min_coverage_threshold
        self.tokenizer = MultilingualTokenizer()

        self.chunks: List[RetrievedChunk] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_token_counts: List[Counter] = []
        self.doc_token_sets: List[Set[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0

        # Inverted index: token -> list of (doc_index, frequency)
        self.inverted_index: Dict[str, List[tuple[int, int]]] = {}
        self.idf_cache: Dict[str, float] = {}

    def index_chunks(self, chunks: List[RetrievedChunk]) -> None:
        """
        Builds the BM25 and TF-IDF index over a collection of chunks.
        """
        self.chunks = chunks
        self.doc_tokens = []
        self.doc_token_counts = []
        self.doc_token_sets = []
        self.doc_lengths = []
        self.inverted_index = {}
        self.idf_cache = {}

        if not chunks:
            self.avg_doc_len = 0.0
            return

        total_len = 0
        for idx, chunk in enumerate(chunks):
            # Index text, title, and section title
            text_to_index = f"{chunk.title} {chunk.metadata.get('section_title', '')} {chunk.text}"
            tokens = self.tokenizer.tokenize(text_to_index, include_ngrams=True)
            self.doc_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            counts = Counter(tokens)
            self.doc_token_counts.append(counts)
            self.doc_token_sets.append(set(t.lower() for t in tokens))

            for token, freq in counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((idx, freq))

        num_docs = len(chunks)
        self.avg_doc_len = total_len / num_docs if num_docs > 0 else 1.0

        # Compute IDFs: ln(1 + (N - n + 0.5) / (n + 0.5))
        for token, postings in self.inverted_index.items():
            n = len(postings)
            idf = math.log(1.0 + (num_docs - n + 0.5) / (n + 0.5))
            self.idf_cache[token] = max(0.1, idf)

    def search(
        self,
        query: str,
        assistant: str,
        language: str = "en",
        state: Optional[str] = None,
        district: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """
        Executes domain-filtered, multilingual hybrid search with intent alignment,
        continuous ranking scores, and coverage gating.
        """
        if not query or not query.strip() or not self.chunks:
            return []

        clean_query = query.strip()
        informative_tokens = self.tokenizer.extract_informative_tokens(clean_query)
        raw_query_words = set(self.tokenizer.tokenize(clean_query, include_ngrams=False))
        query_tokens = self.tokenizer.tokenize(clean_query, include_ngrams=True)
        if not query_tokens:
            return []

        intents = detect_query_intents(clean_query, query_tokens)
        named_doc_ids = detect_named_schemes(clean_query)

        # RELEVANCE SAFETY GATE: If query consists solely of generic administrative words
        # without naming any specific scheme or domain entity, reject to prevent returning unrelated schemes.
        if not named_doc_ids and informative_tokens and informative_tokens.issubset(GENERIC_ADMIN_TOKENS):
            return []

        query_counter = Counter(query_tokens)
        candidate_scores: Dict[int, float] = {}

        # 1. Compute BM25 scores for matching documents
        for token, q_freq in query_counter.items():
            idf = self.idf_cache.get(token, 0.0)
            if idf <= 0.0:
                continue

            # Weighting: direct query words 1.0, Telugu character n-grams 0.35, expanded synonyms 0.50
            is_ngram = len(token) in (3, 4) and any('\u0C00' <= c <= '\u0C7F' for c in token)
            is_direct_word = token in raw_query_words or token.lower() in raw_query_words
            if is_ngram:
                token_weight = 0.35
            elif is_direct_word:
                token_weight = 1.0
            else:
                token_weight = 0.50

            postings = self.inverted_index.get(token, [])
            for doc_idx, doc_freq in postings:
                chunk = self.chunks[doc_idx]
                chunk_domain = chunk.metadata.get("domain", "").lower()
                chunk_doc_id = chunk.metadata.get("doc_id", "")

                # SCHEME-AWARE DOMAIN FILTER:
                # If an explicit scheme was named, ONLY accept chunks belonging to that named scheme document(s).
                # This ensures cross-domain schemes (like agricultural welfare schemes queried under 'schemes')
                # are retrieved while completely preventing unrelated schemes (Housing, Pension) from polluting.
                if named_doc_ids:
                    if chunk_doc_id not in named_doc_ids:
                        continue
                else:
                    # No specific scheme was named: strictly isolate to the assistant's domain
                    if chunk_domain != assistant.lower():
                        continue

                # Geographic filter: if chunk has specific district and user specified different district
                chunk_district = chunk.metadata.get("district")
                if district and chunk_district and chunk_district.lower() != district.lower():
                    continue

                doc_len = self.doc_lengths[doc_idx]
                numerator = doc_freq * (self.k1 + 1.0)
                denominator = doc_freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                bm25_term = idf * (numerator / denominator) * token_weight

                candidate_scores[doc_idx] = candidate_scores.get(doc_idx, 0.0) + bm25_term

        if not candidate_scores:
            return []

        # Check maximum document title matches among candidates to determine if a specific scheme was named
        GENERIC_TITLE_WORDS = {
            "scheme", "schemes", "guidelines", "details", "system", "program", "programs",
            "ap", "andhra", "pradesh", "government", "govt", "portal", "rules", "services",
            "పథకం", "పథకాలు", "పథకానికి", "ప్రభుత్వం", "ఆంధ్రప్రదేశ్", "విధానం", "సేవలు", "వివరాలు",
        }
        if named_doc_ids:
            max_title_matches = 2
        else:
            max_title_matches = max(
                (sum(1 for tok in informative_tokens if tok not in GENERIC_TITLE_WORDS and tok in self.chunks[d].title.lower()) for d in candidate_scores),
                default=0,
            )

        scored_results: List[RetrievedChunk] = []

        # 2. Coverage, intent alignment, and ranking evaluation
        for doc_idx, raw_score in candidate_scores.items():
            chunk = self.chunks[doc_idx]
            chunk_doc_id = chunk.metadata.get("doc_id", "")
            doc_token_set = self.doc_token_sets[doc_idx]

            # Calculate query term coverage
            if informative_tokens:
                matched_informative = sum(1 for tok in informative_tokens if tok in doc_token_set)
                coverage = matched_informative / len(informative_tokens)
            else:
                coverage = 1.0

            # HONEST GATING: If query has informative words and document matches almost none, reject!
            if informative_tokens and len(informative_tokens) >= 2 and coverage < self.min_coverage_threshold:
                continue
            if informative_tokens and coverage == 0.0:
                continue

            # If the query contains subject tokens (tokens that are NOT purely intent or generic admin words),
            # at least one non-intent query word must match the document!
            # Otherwise, matching purely on "eligibility / criteria" or "how to apply" would falsely return
            # housing or pension for completely unsupported subjects (e.g. laptops, scooters).
            subject_tokens = [tok for tok in informative_tokens if tok not in ALL_INTENT_TOKENS and tok not in GENERIC_ADMIN_TOKENS]
            if subject_tokens:
                matched_subject = any(tok in doc_token_set for tok in subject_tokens)
                if not matched_subject and not (named_doc_ids and chunk_doc_id in named_doc_ids):
                    continue

            # Document Title match score: guaranteed 1.0 for explicitly named schemes
            if named_doc_ids and chunk_doc_id in named_doc_ids:
                title_score = 1.0
            else:
                title_lower = chunk.title.lower()
                title_matches = sum(1 for tok in informative_tokens if tok not in GENERIC_TITLE_WORDS and tok in title_lower)
                if title_matches >= 2:
                    title_score = 1.0
                elif title_matches == 1:
                    title_score = 0.40
                else:
                    title_score = 0.0

            # Section Title & Intent alignment score
            sec_title = chunk.metadata.get("section_title", "").lower()
            sec_lexical_matches = sum(1 for tok in informative_tokens if tok in sec_title)
            sec_lexical_score = min(1.0, sec_lexical_matches / 2.0) if sec_lexical_matches > 0 else 0.0

            intent_match_score = 0.0
            if intents and sec_title:
                for intent in intents:
                    section_kw_set = SECTION_INTENT_MAP.get(intent, set())
                    for target in section_kw_set:
                        if target.lower() in sec_title:
                            if title_score >= 0.40:
                                intent_match_score = 1.0
                            elif title_score > 0.0:
                                intent_match_score = 0.50
                            else:
                                intent_match_score = 0.0
                            break
                    if intent_match_score > 0:
                        break

            sec_score = max(sec_lexical_score, intent_match_score)
            if max_title_matches >= 2:
                sec_score = sec_score * (0.30 + 0.70 * title_score)

            # When no named scheme is detected and document title has zero lexical match,
            # require stronger evidence to prevent unrelated schemes from polluting unknown scheme queries
            if not named_doc_ids and title_score == 0.0:
                if coverage < 0.50 or sec_score < 0.30:
                    continue

            # Continuous, non-saturating BM25 scale
            scaled_bm25 = raw_score / (raw_score + 20.0)

            # Balanced multi-signal formula (weights sum to 1.00)
            # Internal ranking metric: BM25 (0.35) + Coverage (0.25) + Title (0.20) + Section/Intent (0.20)
            final_score = (
                (scaled_bm25 * 0.35) +
                (coverage * 0.25) +
                (title_score * 0.20) +
                (sec_score * 0.20)
            )

            # Minimum score threshold
            if final_score >= self.min_score_threshold:
                scored_chunk = RetrievedChunk(
                    text=chunk.text,
                    title=chunk.title,
                    url=chunk.url,
                    publisher=chunk.publisher,
                    verified_at=chunk.verified_at,
                    score=round(min(1.0, final_score), 4),
                    metadata=dict(chunk.metadata),
                )
                scored_results.append(scored_chunk)

        # Sort descending by score
        scored_results.sort(key=lambda c: c.score, reverse=True)
        return scored_results[:top_k]
