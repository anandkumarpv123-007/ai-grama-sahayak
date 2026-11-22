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
        "ఎలా", "ఎప్పుడు", "ఎక్కడ", "ఎవరు", "ఏమిటి", "ఏది", "ఎంత", "మరియు",
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
        Executes domain-filtered, multilingual hybrid search with confidence and coverage gating.
        """
        if not query or not query.strip() or not self.chunks:
            return []

        clean_query = query.strip()
        informative_tokens = self.tokenizer.extract_informative_tokens(clean_query)
        query_tokens = self.tokenizer.tokenize(clean_query, include_ngrams=True)
        if not query_tokens:
            return []

        query_counter = Counter(query_tokens)
        candidate_scores: Dict[int, float] = {}

        # 1. Compute BM25 scores for matching documents
        for token, q_freq in query_counter.items():
            idf = self.idf_cache.get(token, 0.0)
            if idf <= 0.0:
                continue

            # Give full weight to words and synonyms, reduced weight to character n-grams
            token_weight = 0.35 if (len(token) in (3, 4) and any('\u0C00' <= c <= '\u0C7F' for c in token)) else 1.0

            postings = self.inverted_index.get(token, [])
            for doc_idx, doc_freq in postings:
                chunk = self.chunks[doc_idx]

                # STRICT DOMAIN FILTER: Match assistant identifier against chunk domain
                chunk_domain = chunk.metadata.get("domain", "").lower()
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

        scored_results: List[RetrievedChunk] = []

        # 2. Coverage and confidence evaluation
        for doc_idx, raw_score in candidate_scores.items():
            chunk = self.chunks[doc_idx]
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

            # Title and section matching bonus
            title_lower = chunk.title.lower()
            bonus = 0.0
            for token in informative_tokens:
                if token in title_lower:
                    bonus += 0.25

            # Combine coverage, raw BM25, and title bonus
            # Scale raw BM25 safely without artificial 100% inflation
            scaled_bm25 = min(1.0, raw_score / 12.0)
            final_score = (coverage * 0.45) + (scaled_bm25 * 0.35) + bonus

            # Minimum score threshold
            if final_score >= self.min_score_threshold:
                scored_chunk = RetrievedChunk(
                    text=chunk.text,
                    title=chunk.title,
                    url=chunk.url,
                    publisher=chunk.publisher,
                    verified_at=chunk.verified_at,
                    score=min(1.0, final_score),
                    metadata=dict(chunk.metadata),
                )
                scored_results.append(scored_chunk)

        # Sort descending by score
        scored_results.sort(key=lambda c: c.score, reverse=True)
        return scored_results[:top_k]
