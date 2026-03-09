"""
PDF Text Extraction and Requirement Analysis Module.
─────────────────────────────────────────────────────
"""
import re
from collections import defaultdict

# Lazy imports to avoid conflicts
_tfidf_vectorizer = None

def _get_tfidf_vectorizer():
    """Lazy load TF-IDF vectorizer."""
    global _tfidf_vectorizer
    if _tfidf_vectorizer is not None:
        return _tfidf_vectorizer
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _tfidf_vectorizer = TfidfVectorizer()
    except ImportError as e:
        print(f"⚠️  Could not load TF-IDF: {e}")
        _tfidf_vectorizer = None
    return _tfidf_vectorizer

# Try to import spacy, fallback to simple sentence splitting
SPACY_AVAILABLE = False
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    pass

# Try to import nltk for fallback
NLTK_AVAILABLE = False
try:
    import nltk
    NLTK_AVAILABLE = True
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.download('punkt_tab', quiet=True)
        except Exception:
            pass
except ImportError:
    pass


def preprocess_text(text):
    """Preprocess full text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:()\-\'\"]+', '', text)
    return text


def clean_requirement(req):
    """Clean individual requirement."""
    cleaned = re.sub(r'^\s*[\•\-\*\○\◦\▪\▫\□\◆\◇\■\#\d+\.\)]+\s*', '', req)
    return cleaned.strip()


def identify_requirements(text):
    """Identify business requirements from text."""
    nlp = None
    if SPACY_AVAILABLE:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            nlp = None

    if nlp is None:
        if NLTK_AVAILABLE:
            try:
                from nltk import sent_tokenize
                sentences = sent_tokenize(text)
            except Exception:
                sentences = re.split(r'(?<=[.!?])\s+', text)
        else:
            sentences = re.split(r'(?<=[.!?])\s+', text)
    else:
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]

    requirements = []

    req_patterns = [
        r"(?i)(?:shall|must|will be required to|is required to) .{10,200}?[.?!]",
        r"(?i)(?:requirement|requirements)[:;]? .{10,200}?[.?!]",
        r"(?i)(?:the system|the solution|the product|the website|the vendor|the contractor) (?:shall|must|will|should) .{10,200}?[.?!]",
        r"(?i)(?:deliverable|deliverables)[:;]? .{10,200}?[.?!]",
        r"(?i)(?:functional requirement|business requirement|technical requirement)[:;]? .{10,200}?[.?!]",
        r"(?i)(?:integration|implementation) (?:of|with) .{10,200}?[.?!]",
        r"(?i)(?:is|are) (?:required|necessary|needed|essential) .{10,200}?[.?!]",
        r"(?i)(?:should be|must be|shall be) .{10,200}?[.?!]",
        r"(?i)(?:development of|creation of|provision of) .{10,200}?[.?!]",
    ]

    for pattern in req_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            req = clean_requirement(match.group(0).strip())
            if req not in requirements and len(req) > 20:
                requirements.append(req)

    key_phrases = [
        "provide", "support", "enable", "allow", "implement", "maintain",
        "ensure", "deliver", "comply", "include", "integrate", "offer",
        "manage", "process", "handle", "deploy", "develop", "design",
        "create", "build", "configure", "secure", "optimize", "establish",
    ]

    key_contexts = [
        "system", "solution", "product", "website", "application", "platform",
        "vendor", "e-commerce", "commerce", "online", "portal",
        "database", "user", "customer", "interface", "payment", "security",
        "feature", "functionality", "service", "component", "module", "design",
    ]

    for sent_text in sentences:
        if not sent_text or len(sent_text.split()) < 5:
            continue
        sent_lower = sent_text.lower()
        if any(f" {phrase} " in sent_lower for phrase in key_phrases):
            if any(context in sent_lower for context in key_contexts):
                cleaned_sent = clean_requirement(sent_text)
                if cleaned_sent not in requirements and len(cleaned_sent) > 20:
                    requirements.append(cleaned_sent)

    bullet_req_pattern = r'o\s+([A-Z][^o]{10,200}?[.?!])'
    matches = re.finditer(bullet_req_pattern, text)
    for match in matches:
        req = clean_requirement(match.group(1).strip())
        if req not in requirements and len(req) > 20:
            requirements.append(req)

    return requirements


def vectorize_requirements(requirements):
    """Vectorize requirements using TF-IDF."""
    if not requirements:
        return []
    vectorizer = _get_tfidf_vectorizer()
    if vectorizer is None:
        return []
    try:
        processed_reqs = [re.sub(r'[^\w\s]', '', req.lower()) for req in requirements]
        vectors = vectorizer.fit_transform(processed_reqs).toarray()
        return vectors
    except Exception as e:
        print(f"⚠️  Error vectorizing requirements: {e}")
        return []


def process_pdf_text(text):
    """Wrapper function for Streamlit."""
    processed_text = preprocess_text(text)
    requirements = identify_requirements(processed_text)
    tfidf_vectors = vectorize_requirements(requirements) if requirements else []
    return requirements, tfidf_vectors
