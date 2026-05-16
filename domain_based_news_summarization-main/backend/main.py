"""
What's New? - Domain Intelligence Backend
FastAPI backend with news fetching, NLP processing, and AI summarization
"""

import os
import json
import hashlib
import asyncio
import re
import html
import importlib
from pathlib import Path
from threading import Lock
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import fastapi
import fastapi.middleware.cors
import httpx
from pydantic import BaseModel, Field
import google.generativeai as genai
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Import database and cache modules
from database import UserRepository, DigestRepository, SavedTrendRepository, ArticleRepository, CustomDomainRepository

# API Keys
# NOTE: The hardcoded keys are for testing/demo only. They have limited permissions.
# Set environment variables for production use:
#   GEMINI_API_KEY - Get from https://aistudio.google.com/app/apikey
#   NEWS_API_KEY - Get from https://newsapi.org
#   GNEWS_API_KEY - Get from https://gnews.io
#
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "").strip()
GEMINI_ENABLED = os.environ.get("GEMINI_ENABLED", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant").strip()
GROQ_ENABLED = os.environ.get("GROQ_ENABLED", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
GEMMA_PRIMARY_ENABLED = os.environ.get("GEMMA_PRIMARY_ENABLED", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
GEMMA_BASE_MODEL_ID = os.environ.get("GEMMA_BASE_MODEL_ID", "google/gemma-2-2b").strip()
GEMMA_ADAPTER_DIR = os.environ.get("GEMMA_ADAPTER_DIR", "").strip()
GEMMA_MAX_NEW_TOKENS = int(os.environ.get("GEMMA_MAX_NEW_TOKENS", "160"))
GEMMA_TIMEOUT_SECONDS = float(os.environ.get("GEMMA_TIMEOUT_SECONDS", "90"))
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "").strip()
ALLOW_MOCK_FALLBACK = os.environ.get("ALLOW_MOCK_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
DB_FIRST_ONLY_MODE = os.environ.get("DB_FIRST_ONLY_MODE", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
DB_MIN_ARTICLES_THRESHOLD = int(os.environ.get("DB_MIN_ARTICLES_THRESHOLD", "15"))

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-super-secret-key-change-this-in-production-min-32-chars-12345")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure Gemini (only if enabled and a key is present)
if GEMINI_ENABLED and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Domain keyword mappings for expanded searches
DOMAIN_QUERIES = {
    "ai": "artificial intelligence OR machine learning OR LLM OR GPT",
    "finance": "stock market OR Federal Reserve OR interest rates OR banking",
    "healthcare": "FDA OR clinical trial OR pharmaceutical OR biotech",
    "climate": "climate change OR renewable energy OR sustainability",
    "crypto": "cryptocurrency OR Bitcoin OR Ethereum OR blockchain",
    "legal": "Supreme Court OR litigation OR regulatory OR legislation",
    "policy": "Congress OR federal policy OR regulation",
    "cybersecurity": "data breach OR ransomware OR cyber attack OR security"
}

DOMAIN_LABELS = {
    "ai": "AI & ML",
    "finance": "Finance",
    "healthcare": "Healthcare",
    "climate": "Climate",
    "crypto": "Crypto",
    "legal": "Legal",
    "policy": "Policy",
    "cybersecurity": "Cybersecurity"
}

NLP_CONFIG = {
    "n_clusters": 3,
    "max_articles": 30,
    "max_timeline_days": 29,
    "min_timeline_days": 1,
    "top_trends": 6,
}

# Quality controls for better domain precision and trend trustworthiness.
MIN_CLUSTER_SIZE = 2
MIN_SOURCE_QUALITY = 0.15
MIN_RELEVANCE_DEFAULT = 0.20
MIN_RELEVANCE_CUSTOM = 0.26

NEWS_INTENT_TERMS = {
    "launch", "released", "release", "announced", "announcement", "model", "models",
    "policy", "bill", "regulation", "court", "funding", "investment", "acquisition",
    "security", "vulnerability", "research", "study", "breakthrough", "deployment",
    "enterprise", "product", "roadmap", "benchmark", "efficiency", "accuracy",
}

AI_NOISE_TERMS = {
    "wordcamp", "surreal", "landscape", "collage", "gallery", "art show", "apple tv",
    "podcast rewind", "macstories",
}

GENERIC_NOISE_TERMS = {
    "please check your connection",
    "disable any ad blockers",
    "this may be due to a browser extension",
    "network issues",
    "browser settings",
    "accept all cookies",
    "enable javascript",
    "sign in to continue",
    "subscribe to continue",
}

SOURCE_QUALITY_BOOST = {
    "reuters": 0.30,
    "associated press": 0.30,
    "ap news": 0.30,
    "bbc": 0.28,
    "financial times": 0.30,
    "wall street journal": 0.30,
    "new york times": 0.28,
    "bloomberg": 0.28,
    "techcrunch": 0.22,
    "the verge": 0.20,
    "arstechnica": 0.20,
    "wired": 0.18,
}

SOURCE_QUALITY_PENALTY = {
    "usa herald": -0.35,
    "watts up with that": -0.35,
    "markets insider": -0.15,
    "new york post": -0.12,
    "bgr": -0.10,
}

DOMAIN_RELEVANCE_ANCHORS = {
    "ai": {"ai", "artificial intelligence", "machine learning", "llm", "model", "inference", "gpt", "agent"},
    "finance": {"market", "stock", "fed", "interest", "bank", "inflation", "earnings", "ipo"},
    "healthcare": {"clinical", "trial", "fda", "hospital", "biotech", "drug", "health"},
    "climate": {"climate", "emission", "renewable", "sustainability", "carbon", "energy"},
    "crypto": {"crypto", "bitcoin", "ethereum", "blockchain", "token", "exchange"},
    "legal": {"court", "litigation", "regulation", "law", "ruling", "legal"},
    "policy": {"policy", "bill", "congress", "regulation", "federal", "government"},
    "cybersecurity": {"breach", "ransomware", "security", "vulnerability", "threat", "malware"},
}

_NLP_DEPS: Optional[dict] = None
_GEMMA_RUNTIME: Optional[dict] = None
_GEMMA_RUNTIME_LOCK = Lock()


def _load_nlp_deps() -> dict:
    global _NLP_DEPS
    if _NLP_DEPS is not None:
        return _NLP_DEPS

    try:
        np_module = importlib.import_module("numpy")
        nltk_module = importlib.import_module("nltk")
        sklearn_text = importlib.import_module("sklearn.feature_extraction.text")
        sklearn_cluster = importlib.import_module("sklearn.cluster")
        sklearn_metrics = importlib.import_module("sklearn.metrics")
        sklearn_pairwise = importlib.import_module("sklearn.metrics.pairwise")
        nltk_corpus = importlib.import_module("nltk.corpus")
        nltk_stem = importlib.import_module("nltk.stem")
        nltk_tokenize = importlib.import_module("nltk.tokenize")
    except Exception as e:
        raise RuntimeError(
            "NLP dependencies are missing. Install backend deps (including numpy, nltk, scikit-learn)."
        ) from e

    _NLP_DEPS = {
        "np": np_module,
        "nltk": nltk_module,
        "TfidfVectorizer": sklearn_text.TfidfVectorizer,
        "KMeans": sklearn_cluster.KMeans,
        "silhouette_score": sklearn_metrics.silhouette_score,
        "cosine_similarity": sklearn_pairwise.cosine_similarity,
        "stopwords": nltk_corpus.stopwords,
        "WordNetLemmatizer": nltk_stem.WordNetLemmatizer,
        "sent_tokenize": nltk_tokenize.sent_tokenize,
        "word_tokenize": nltk_tokenize.word_tokenize,
    }
    return _NLP_DEPS

# ========================
# JWT Utilities
# ========================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Ensure password is a string and encode it properly
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    # BCrypt has a 72-byte limit
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify a JWT token and return its data"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

async def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current user from token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    payload = verify_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"user_id": user_id, "email": payload.get("email")}

# Pydantic models
class DigestRequest(BaseModel):
    domain: str
    days: int = 7
    keywords: Optional[str] = None  # Optional custom keywords for user-defined domains
    skip_cache: Optional[bool] = False  # Force fresh digest generation

class AuthRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class CustomDomainRequest(BaseModel):
    domain_name: str
    keywords: Optional[str] = None
    description: Optional[str] = None

class Article(BaseModel):
    title: str
    source: str
    url: str
    published: str
    description: Optional[str] = None
    content: Optional[str] = None

class TimelineEvent(BaseModel):
    date: str
    event: str


class TrendEvidence(BaseModel):
    confidence_level: str = "low"
    confidence_score: float = 0.0
    unique_source_count: int = 0
    article_count: int = 0
    valid_link_ratio: float = 0.0
    duplicate_ratio: float = 0.0
    recency_days: int = 30
    avg_relevance: float = 0.0
    warning_flags: list[str] = Field(default_factory=list)

class Trend(BaseModel):
    trend_id: int
    trend_title: str
    tldr: str
    summary: str
    timeline: list[TimelineEvent]
    so_what: str
    signal_score: int
    contrast: Optional[str]
    key_entities: list[str]
    source_count: int
    articles: list[Article]
    confidence_level: Optional[str] = None
    evidence: Optional[TrendEvidence] = None
    model_version: str = "unspecified"
    summary_engine: str = "unknown"

class DigestResponse(BaseModel):
    digest_id: str
    domain: str
    days: int
    generated_at: str
    total_trends: int
    total_articles: int
    cached: bool
    trends: list[Trend]
    model_version: Optional[str] = None
    summary_engine: Optional[str] = None

class UserPreferences(BaseModel):
    default_domain: str = "ai"
    default_days: int = 7
    daily_digest_enabled: bool = False
    daily_digest_time: str = "08:00"
    daily_digest_domain: str = "ai"

class User(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    preferences: UserPreferences
    created_at: str
    last_active_at: str


class SaveTrendRequest(BaseModel):
    domain: str
    trend: Trend
    digest_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Application lifespan manager"""
    print("=" * 60)
    print("Starting What's New? backend with real APIs...")
    print("=" * 60)
    
    # Check Gemma configuration
    adapter_path = _resolve_adapter_path(GEMMA_ADAPTER_DIR)
    if GEMMA_PRIMARY_ENABLED and adapter_path and HF_TOKEN:
        print(f"[OK] GEMMA PRIMARY: enabled")
        print(f"     Adapter: {adapter_path}")
        print(f"     Model: {GEMMA_BASE_MODEL_ID}")
    elif GEMMA_PRIMARY_ENABLED:
        if not HF_TOKEN:
            print("[WARN] GEMMA PRIMARY: HF_TOKEN not set")
        if not adapter_path:
            print(f"[WARN] GEMMA PRIMARY: adapter path not found ({GEMMA_ADAPTER_DIR})")
        print("     → Will use Groq or extractive fallback")
    else:
        print("[INFO] GEMMA PRIMARY: disabled")

    # Check Groq configuration
    if GROQ_ENABLED and GROQ_API_KEY:
        print(f"[OK] GROQ API: enabled (model={GROQ_MODEL})")
    elif GROQ_ENABLED and not GROQ_API_KEY:
        print("[WARN] GROQ API: GROQ_API_KEY not set")
        print("     → Using extractive summaries")
    else:
        print("[INFO] GROQ API: disabled")

    # Check news API
    if NEWS_API_KEY:
        print(f"[OK] NEWS API: configured")
    else:
        print("[WARN] NEWS API: NEWS_API_KEY not set")

    if GNEWS_API_KEY:
        print(f"[OK] GNEWS API: configured")
    else:
        print("[WARN] GNEWS API: GNEWS_API_KEY not set")

    print("=" * 60)
    print("Summarization Engine Priority: Gemma → Groq → Extractive")
    print("=" * 60)
    yield
    print("Shutting down What's New? backend...")


app = fastapi.FastAPI(
    title="What's New? API",
    description="Domain-specific news intelligence API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _active_model_version() -> str:
    configured = os.environ.get("DIGEST_MODEL_VERSION", "").strip()
    if configured:
        return configured
    if GROQ_ENABLED and GROQ_API_KEY:
        return f"groq:{(GROQ_MODEL or 'auto').strip() or 'auto'}"
    return "extractive:v2"


async def fetch_news_from_gnews(query: str, days: int) -> list[dict]:
    """Fetch news articles from GNews API"""
    if not GNEWS_API_KEY:
        print("[WARNING] GNews API key not configured (GNEWS_API_KEY missing)")
        return []
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "lang": "en",
        "country": "us",
        "max": 50,  # Increased from 10 to 50 for better coverage
        "from": from_date,
        "apikey": GNEWS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                return [
                    {
                        "title": a.get("title", ""),
                        "source": a.get("source", {}).get("name", "Unknown"),
                        "url": a.get("url", ""),
                        "published": a.get("publishedAt", ""),
                        "description": a.get("description", ""),
                        "content": a.get("content", "")
                    }
                    for a in articles
                ]
            else:
                snippet = (response.text or "").replace("\n", " ")[:400]
                print(f"[WARNING] GNews non-200: {response.status_code} body={snippet}")
        except Exception as e:
            print(f"GNews API error: {e}")
    
    return []


async def fetch_news_from_newsapi(query: str, days: int) -> list[dict]:
    """Fetch news articles from NewsAPI"""
    if not NEWS_API_KEY:
        print("[WARNING] NewsAPI key not configured (NEWS_API_KEY missing)")
        return []
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 50,  # Increased from 10 to 50 for better coverage
        "from": from_date,
        "apiKey": NEWS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                return [
                    {
                        "title": a.get("title", ""),
                        "source": a.get("source", {}).get("name", "Unknown"),
                        "url": a.get("url", ""),
                        "published": a.get("publishedAt", ""),
                        "description": a.get("description", ""),
                        "content": a.get("content", "")
                    }
                    for a in articles
                ]
            else:
                snippet = (response.text or "").replace("\n", " ")[:400]
                print(f"[WARNING] NewsAPI non-200: {response.status_code} body={snippet}")
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    return []


def cluster_articles_simple(articles: list[dict]) -> list[list[dict]]:
    """Simple clustering based on title similarity - groups related articles"""
    if not articles:
        return []
    
    # Simple approach: group by finding common keywords
    clusters = []
    used = set()
    
    for i, article in enumerate(articles):
        if i in used:
            continue
            
        cluster = [article]
        used.add(i)
        
        title_words = set(article.get("title", "").lower().split())
        
        for j, other in enumerate(articles):
            if j in used:
                continue
            other_words = set(other.get("title", "").lower().split())
            # If they share significant words, cluster together
            common = title_words & other_words - {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "was", "were"}
            if len(common) >= 2:
                cluster.append(other)
                used.add(j)
        
        if len(cluster) >= 1:
            clusters.append(cluster)
    
    # Sort clusters by size (most articles first)
    clusters.sort(key=lambda x: len(x), reverse=True)
    
    return clusters[:15]  # Return top 15 clusters for more comprehensive coverage


async def summarize_with_gemini(articles: list[dict], domain: str) -> dict:
    """Legacy wrapper: route LLM fallback summarization through Groq."""
    return await summarize_with_groq(articles, domain)


def _extract_json_object(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    if s.startswith("```json"):
        s = s[7:]
    if s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    return s


def _build_summary_prompt(articles: list[dict], domain: str) -> str:
    articles_text = "\n\n".join([
        f"Title: {a.get('title', '')}\nSource: {a.get('source', '')}\nDescription: {a.get('description', '')}"
        for a in articles[:6]
    ])

    return f"""Analyze these news articles about {domain} and create a professional intelligence briefing.

ARTICLES:
{articles_text}

Generate a JSON response with exactly this structure:
{{
    "trend_title": "A concise, compelling headline (8-12 words)",
    "tldr": "One sentence summary (max 25 words)",
    "summary": "A 2-3 paragraph executive summary explaining the trend, its context, and implications",
    "timeline": [
        {{"date": "YYYY-MM-DD", "event": "What happened"}},
        {{"date": "YYYY-MM-DD", "event": "What happened"}}
    ],
    "so_what": "A sentence explaining why this matters for professionals in this domain",
    "signal_score": 7,
    "contrast": "Any contrasting viewpoints or debates around this topic (or null if none)",
    "key_entities": ["Entity1", "Entity2", "Entity3"]
}}

Requirements:
- signal_score: 1-10 rating of importance/impact
- timeline: 2-4 key events with dates
- key_entities: 3-5 important people, companies, or organizations mentioned
- Be specific and factual, cite sources when possible
- Write in a professional, analytical tone

Respond ONLY with valid JSON, no markdown or extra text."""


def _resolve_adapter_path(raw_path: str) -> Optional[Path]:
    path_text = (raw_path or "").strip()
    if not path_text:
        print("[WARNING] GEMMA_ADAPTER_DIR is empty")
        return None

    direct = Path(path_text)
    if direct.exists():
        print(f"[INFO] GEMMA adapter found at absolute path: {direct.resolve()}")
        return direct.resolve()

    # If a relative path is provided, resolve from backend working directory.
    candidate = (Path.cwd() / path_text).resolve()
    if candidate.exists():
        print(f"[INFO] GEMMA adapter found at cwd-relative path: {candidate}")
        return candidate
    
    # Try resolving from the backend directory itself
    backend_dir = Path(__file__).parent.resolve()
    candidate = (backend_dir / path_text).resolve()
    if candidate.exists():
        print(f"[INFO] GEMMA adapter found at backend-relative path: {candidate}")
        return candidate
    
    print(f"[ERROR] GEMMA adapter path not found: {raw_path}")
    print(f"  Tried: {direct} (absolute)")
    print(f"  Tried: {Path.cwd() / path_text} (cwd-relative)")
    print(f"  Tried: {candidate} (backend-relative)")
    return None


def _load_gemma_runtime() -> dict:
    global _GEMMA_RUNTIME
    if _GEMMA_RUNTIME is not None:
        return _GEMMA_RUNTIME

    with _GEMMA_RUNTIME_LOCK:
        if _GEMMA_RUNTIME is not None:
            return _GEMMA_RUNTIME

        adapter_path = _resolve_adapter_path(GEMMA_ADAPTER_DIR)
        if not adapter_path:
            raise RuntimeError("GEMMA_ADAPTER_DIR is missing or invalid")

        if not HF_TOKEN:
            raise RuntimeError("HF_TOKEN is required to load Gemma base model")

        torch_module = importlib.import_module("torch")
        transformers_module = importlib.import_module("transformers")
        peft_module = importlib.import_module("peft")

        AutoTokenizer = transformers_module.AutoTokenizer
        AutoModelForCausalLM = transformers_module.AutoModelForCausalLM
        PeftModel = peft_module.PeftModel

        tokenizer = AutoTokenizer.from_pretrained(
            GEMMA_BASE_MODEL_ID,
            token=HF_TOKEN,
            use_fast=True,
        )
        if tokenizer.pad_token_id is None and tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            GEMMA_BASE_MODEL_ID,
            token=HF_TOKEN,
            torch_dtype=torch_module.float32,
            low_cpu_mem_usage=True,
        )
        model = PeftModel.from_pretrained(model, str(adapter_path), token=HF_TOKEN)
        model.to("cpu")
        model.eval()

        _GEMMA_RUNTIME = {
            "torch": torch_module,
            "tokenizer": tokenizer,
            "model": model,
        }
        return _GEMMA_RUNTIME


def _summarize_with_gemma_sync(articles: list[dict], domain: str) -> dict:
    runtime = _load_gemma_runtime()
    torch_module = runtime["torch"]
    tokenizer = runtime["tokenizer"]
    model = runtime["model"]

    prompt = _build_summary_prompt(articles, domain)
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=3072,
    )

    with torch_module.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max(64, GEMMA_MAX_NEW_TOKENS),
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

    prompt_tokens = int(inputs["input_ids"].shape[-1])
    completion_tokens = generated[0][prompt_tokens:]
    raw_text = tokenizer.decode(completion_tokens, skip_special_tokens=True)
    result = json.loads(_extract_json_object(raw_text))
    result["_engine"] = "gemma_primary"
    return result


async def summarize_with_gemma_primary(articles: list[dict], domain: str) -> Optional[dict]:
    if not GEMMA_PRIMARY_ENABLED:
        print("[INFO] Gemma summarization disabled (GEMMA_PRIMARY_ENABLED=false)")
        return None

    if not HF_TOKEN:
        print("[WARNING] Gemma summarization skipped: HF_TOKEN not set")
        return None

    adapter_path = _resolve_adapter_path(GEMMA_ADAPTER_DIR)
    if not adapter_path:
        print(f"[WARNING] Gemma summarization skipped: adapter path not found")
        return None

    print(f"[INFO] Starting Gemma summarization with {len(articles)} articles...")
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_summarize_with_gemma_sync, articles, domain),
            timeout=GEMMA_TIMEOUT_SECONDS,
        )
        print(f"[INFO] Gemma summarization completed successfully")
        return result
    except asyncio.TimeoutError:
        print(f"[WARNING] Gemma summarization timed out after {GEMMA_TIMEOUT_SECONDS}s")
        return None
    except Exception as e:
        print(f"[WARNING] Gemma primary summarization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def summarize_cluster_hybrid(articles: list[dict], domain: str) -> dict:
    print(f"[DEBUG] summarize_cluster_hybrid: {len(articles)} articles for domain '{domain}'")
    
    gemma_result = await summarize_with_gemma_primary(articles, domain)
    if gemma_result:
        print(f"[INFO] Using Gemma-generated summary")
        return gemma_result

    print("[INFO] Falling back to Groq summarization...")
    groq_result = await summarize_with_groq(articles, domain)
    if isinstance(groq_result, dict) and groq_result.get("_engine"):
        print(f"[INFO] Using Groq-generated summary (engine: {groq_result.get('_engine')})")
        return groq_result

    print("[WARNING] Falling back to extractive summarization (no LLM available)")
    fallback = _get_mock_trend_summary(articles, domain)
    fallback["_engine"] = "extractive_fallback"
    return fallback


async def summarize_with_groq(articles: list[dict], domain: str) -> dict:
    """Use Groq to generate trend summary from clustered articles."""

    if (not GROQ_ENABLED):
        print("[INFO] Groq summarization disabled (GROQ_ENABLED=false)")
        result = _get_mock_trend_summary(articles, domain)
        result["_engine"] = "extractive_fallback"
        return result

    if (not GROQ_API_KEY):
        print("[WARNING] Groq summarization skipped: GROQ_API_KEY not set")
        result = _get_mock_trend_summary(articles, domain)
        result["_engine"] = "extractive_fallback"
        return result

    print(f"[INFO] Using Groq for summarization (model: {GROQ_MODEL})...")
    prompt = _build_summary_prompt(articles, domain)

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "temperature": 0.3,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise analyst. Return strict JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        raw_text = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        text = _extract_json_object(raw_text)
        result = json.loads(text)
        result["_engine"] = "groq_fallback"
        return result
        
    except Exception as e:
        print(f"[WARNING] Groq API error: {e}")
        try:
            # Helpful for debugging why we fell back to mock summaries.
            snippet = (locals().get('raw_text') or '')
            snippet = snippet.replace("\n", " ")
            print(f"[WARNING] Groq raw response (first 300 chars): {snippet[:300]}")
        except Exception:
            pass
        print(f"[INFO] Falling back to extractive trend data")
        result = _get_mock_trend_summary(articles, domain)
        result["_engine"] = "extractive_fallback"
        return result


def _get_mock_trend_summary(articles: list[dict], domain: str) -> dict:
    """Generate a non-LLM summary from real clustered articles.

    This is used when Gemini is unavailable/rate-limited. It should still reflect
    the actual news (titles/descriptions/sources/dates), not generic template text.
    """

    if not articles:
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "trend_title": "News Update",
            "tldr": "No articles were available for this trend.",
            "summary": "No source articles were returned by the news providers for this query.",
            "timeline": [{"date": today, "event": "No events available"}],
            "so_what": f"If you rely on this trend, consider refining keywords for {domain}.",
            "signal_score": 3,
            "contrast": None,
            "key_entities": []
        }

    def _clean(s: str) -> str:
        # Normalize whitespace and common mojibake sequences seen in news feeds.
        text = (s or "")
        replacements = {
            "\u2014": "-",
            "\u2013": "-",
            "â€”": "—",
            "â€“": "–",
            "â€™": "’",
            "â€˜": "‘",
            "â€œ": "“",
            "â€�": "”",
            "Â": "",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return " ".join(text.split())

    # Pick the top article as the anchor.
    anchor = articles[0] if isinstance(articles[0], dict) else {}
    title = _clean(anchor.get("title", "News Update"))
    desc = _clean(anchor.get("description") or anchor.get("content") or "")
    if not desc:
        desc = "Multiple sources report on this development."

    # Collect sources and dates across the cluster.
    sources: list[str] = []
    dates: list[str] = []
    for a in articles:
        if not isinstance(a, dict):
            continue
        src = _clean(a.get("source", ""))
        if src and src not in sources:
            sources.append(src)
        pub = _clean(a.get("published", ""))
        if len(pub) >= 10:
            d = pub[:10]
            if d and d not in dates:
                dates.append(d)

    dates_sorted = sorted(dates) if dates else []
    newest = dates_sorted[-1] if dates_sorted else datetime.now().strftime("%Y-%m-%d")
    oldest = dates_sorted[0] if dates_sorted else newest

    # Build a timeline based on article publication dates and titles.
    # Use up to 3 unique dates to show evolution.
    timeline: list[dict] = []
    used_dates = set()
    for a in sorted([x for x in articles if isinstance(x, dict)], key=lambda x: _clean(x.get("published", ""))):
        pub = _clean(a.get("published", ""))
        if len(pub) < 10:
            continue
        d = pub[:10]
        if d in used_dates:
            continue
        used_dates.add(d)
        timeline.append({
            "date": d,
            "event": _clean(a.get("title", "Report published"))[:120] or "Report published"
        })
        if len(timeline) >= 3:
            break
    if not timeline:
        timeline = [{"date": newest, "event": "Coverage emerged"}]

    # So-what: domain-aware but grounded in this cluster.
    # Keep it concise and use the fact that this cluster spans sources/dates.
    src_phrase = ", ".join(sources[:3])
    if src_phrase:
        src_phrase = f" across {src_phrase}"

    so_what = (
        f"This topic is developing from {oldest} to {newest}{src_phrase}. "
        f"Track it for near-term impact on decisions and strategy in {domain}."
    )

    # Build a richer, multi-paragraph summary from real article text.
    # Pull a few additional, distinct angles from other articles in the cluster.
    supporting_points: list[str] = []
    for a in articles[1:]:
        if not isinstance(a, dict):
            continue
        point = _clean(a.get("description") or "")
        if not point:
            # Fall back to title if description is missing.
            point = _clean(a.get("title") or "")
        point = point.strip("-•* ")
        if not point:
            continue
        # Avoid duplicating the anchor description.
        if point and point != desc and point not in supporting_points:
            supporting_points.append(point)
        if len(supporting_points) >= 3:
            break

    if supporting_points:
        points_text = "\n".join([f"- {p[:220]}" for p in supporting_points])
        details_block = f"\n\nAdditional details reported:\n{points_text}"
    else:
        details_block = ""

    overview_block = f"Overview: {desc}"

    coverage_block = (
        f"\n\nCoverage spans {len(articles)} source articles{src_phrase} over {oldest}–{newest}. "
        f"Key details can vary by outlet, so triangulating across sources is recommended."
    )

    watch_block = (
        f"\n\nWhat to watch next: follow updates from primary sources and verify any claims with direct links, "
        f"especially if the story affects policy, pricing, security, or major product changes in {domain}."
    )

    summary = f"{overview_block}{details_block}{coverage_block}{watch_block}"

    # Signal score: based on cluster size and recency.
    size_score = min(10, 3 + (len(articles) // 2))
    signal_score = max(3, min(10, size_score))

    return {
        "trend_title": title[:120] or "News Update",
        "tldr": desc[:140],
        "summary": summary,
        "timeline": timeline,
        "so_what": so_what,
        "signal_score": signal_score,
        "contrast": None,
        "key_entities": sources[:5],
    }


def _ensure_nltk_resources() -> None:
    deps = _load_nlp_deps()
    nltk_module = deps["nltk"]
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
    ]
    for lookup_path, package_name in resources:
        try:
            nltk_module.data.find(lookup_path)
        except LookupError:
            try:
                nltk_module.download(package_name, quiet=True)
            except Exception:
                pass


def _clean_article_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = html.unescape(str(text))

    # Repair common mojibake artifacts from upstream feeds.
    try:
        if any(token in cleaned for token in ("â", "Ã", "Â")):
            repaired = cleaned.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if repaired:
                cleaned = repaired
    except Exception:
        pass

    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€�": '"',
        "â€“": "-",
        "â€”": "-",
        " â ": " - ",
        "â€¦": "...",
        "Â": "",
        "�": "",
        "\u00c3\u00a9": "é",
        "\u00c3\u00a8": "è",
        "\u00c3\u00aa": "ê",
        "\u00c3\u00ab": "ë",
        "\u00c3\u00a1": "á",
        "\u00c3\u00a0": "à",
        "\u00c3\u00a2": "â",
        "\u00c3\u00a3": "ã",
        "\u00c3\u00a4": "ä",
        "\u00c3\u00ad": "í",
        "\u00c3\u00ac": "ì",
        "\u00c3\u00ae": "î",
        "\u00c3\u00af": "ï",
        "\u00c3\u00b3": "ó",
        "\u00c3\u00b2": "ò",
        "\u00c3\u00b4": "ô",
        "\u00c3\u00b6": "ö",
        "\u00c3\u00ba": "ú",
        "\u00c3\u00b9": "ù",
        "\u00c3\u00bb": "û",
        "\u00c3\u00bc": "ü",
        "\u00c3\u00b1": "ñ",
        "\u00c3\u0087": "Ç",
        "\u00c3\u00a7": "ç",
    }
    for bad, good in replacements.items():
        cleaned = cleaned.replace(bad, good)

    # Repair broken contractions/possessives from feeds (e.g., Appleâs -> Apple's).
    cleaned = re.sub(r"([A-Za-z])[â’`´]([A-Za-z])", r"\1'\2", cleaned)

    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\[\+\d+\s+chars\]", " ", cleaned)
    # Drop noisy feed boilerplate that can leak into summaries.
    for marker in GENERIC_NOISE_TERMS:
        cleaned = re.sub(re.escape(marker), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _contains_feed_noise(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in GENERIC_NOISE_TERMS)


def _is_version_release_article(article: dict) -> bool:
    title = _clean_article_text(article.get("title", "")).lower()
    description = _clean_article_text(article.get("description", "")).lower()
    source = _normalize_source_name(article.get("source", ""))
    url = str(article.get("url", "") or "").lower()

    has_semver = bool(re.search(r"\b(v?\d+\.\d+(?:\.\d+)?(?:[a-z0-9\-\.]+)?)\b", title))
    release_terms = any(term in title for term in ("release", "changelog", "toolkit", "cli", "package", "library"))
    package_host = ("pypi.org" in url) or ("npmjs.com" in url) or ("rubygems.org" in url)
    package_source = any(s in source for s in ("pypi", "npm", "rubygems"))
    return has_semver and (release_terms or package_host or package_source or "agent-friendly cli" in description)


def _normalize_title(title: str | None) -> str:
    t = _clean_article_text(title).lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_source_name(source: str | None) -> str:
    s = _clean_article_text(source).lower()
    s = re.sub(r"\b(the|news|daily|online)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _source_quality_score(source: str | None) -> float:
    normalized = _normalize_source_name(source)
    score = 0.45

    for key, boost in SOURCE_QUALITY_BOOST.items():
        if key in normalized:
            score += boost
            break

    for key, penalty in SOURCE_QUALITY_PENALTY.items():
        if key in normalized:
            score += penalty
            break

    return max(0.0, min(1.0, score))


def _split_terms(raw: str) -> list[str]:
    parts = [p.strip().lower() for p in re.split(r"[,/|]+", raw or "") if p.strip()]
    if not parts and raw:
        parts = [raw.strip().lower()]
    return parts


def _is_valid_http_url(raw_url: str | None) -> bool:
    if not raw_url:
        return False
    url = str(raw_url).strip()
    if not url or url == "#":
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _source_identity_key(article: dict) -> str:
    """Build a stable source identity, preferring article host over feed-provided source labels."""
    raw_url = str(article.get("url", "") or "").strip()
    if _is_valid_http_url(raw_url):
        host = (urlparse(raw_url).hostname or "").lower()
        if host:
            if host.startswith("www."):
                host = host[4:]
            return f"host:{host}"

    source = _normalize_source_name(str(article.get("source", "") or "unknown"))
    return f"source:{source or 'unknown'}"


def _extract_domain_terms(domain: str, custom_keywords: Optional[str]) -> tuple[set[str], set[str]]:
    phrase_terms: set[str] = set()
    token_terms: set[str] = set()

    if custom_keywords and custom_keywords.strip():
        for phrase in _split_terms(custom_keywords):
            phrase_terms.add(phrase)
            for tok in re.findall(r"[a-z0-9]+", phrase):
                if len(tok) > 2:
                    token_terms.add(tok)
    else:
        mapped = DOMAIN_RELEVANCE_ANCHORS.get(domain, set())
        for item in mapped:
            phrase_terms.add(item.lower())
            for tok in re.findall(r"[a-z0-9]+", item.lower()):
                if len(tok) > 2:
                    token_terms.add(tok)

    if domain and domain.lower() not in DOMAIN_RELEVANCE_ANCHORS:
        d = domain.lower().replace("_", " ")
        phrase_terms.add(d)
        for tok in re.findall(r"[a-z0-9]+", d):
            if len(tok) > 2:
                token_terms.add(tok)

    return phrase_terms, token_terms


def _article_relevance_score(article: dict, phrase_terms: set[str], token_terms: set[str]) -> float:
    title = _clean_article_text(article.get("title", "")).lower()
    description = _clean_article_text(article.get("description", "")).lower()
    content = _clean_article_text(article.get("content", "")).lower()

    title_hits = sum(1 for term in token_terms if term in title)
    desc_hits = sum(1 for term in token_terms if term in description)
    content_hits = sum(1 for term in token_terms if term in content)
    phrase_hits = sum(1 for phrase in phrase_terms if phrase in f"{title} {description}")

    weighted = (title_hits * 0.22) + (desc_hits * 0.14) + (content_hits * 0.06) + (phrase_hits * 0.28)
    max_reasonable = max(1.0, (len(token_terms) * 0.28) + (len(phrase_terms) * 0.28))
    lexical_score = min(1.0, weighted / max_reasonable)

    source_score = _source_quality_score(article.get("source"))
    final_score = (lexical_score * 0.78) + (source_score * 0.22)
    return max(0.0, min(1.0, final_score))


def _passes_domain_gate(
    domain: str,
    title: str,
    description: str,
    relevance_score: float,
    source_quality: float,
    phrase_terms: Optional[set[str]] = None,
    token_terms: Optional[set[str]] = None,
    custom_keywords: Optional[str] = None,
) -> bool:
    combined = f"{title} {description}".lower()

    if _contains_feed_noise(combined):
        return False

    phrase_terms = phrase_terms or set()
    token_terms = token_terms or set()
    token_hits = sum(1 for term in token_terms if term in combined)
    phrase_hits = sum(1 for phrase in phrase_terms if phrase and phrase in combined)
    intent_hits = sum(1 for term in NEWS_INTENT_TERMS if term in combined)

    if domain != "ai":
        # For custom domains, require direct lexical grounding in provided keywords.
        if custom_keywords and custom_keywords.strip():
            if phrase_hits == 0 and token_hits < 2:
                return False
            if relevance_score < 0.28 and source_quality < 0.30:
                return False
            return True

        # For known non-AI domains, require at least weak anchor evidence.
        if domain in DOMAIN_RELEVANCE_ANCHORS:
            if token_hits == 0 and phrase_hits == 0:
                return False
            if intent_hits == 0 and relevance_score < 0.30:
                return False
            return True

        # Generic arbitrary domains: keep only well-supported matches.
        if token_hits == 0 and phrase_hits == 0:
            return False
        return relevance_score >= 0.30 and source_quality >= 0.25

    # Exclude common feed noise that is often AI-adjacent but not a strong AI trend signal.
    if any(noise in combined for noise in AI_NOISE_TERMS):
        return False

    ai_anchor_terms = DOMAIN_RELEVANCE_ANCHORS.get("ai", set())
    title_hits = sum(1 for term in ai_anchor_terms if term in title.lower())
    combined_hits = sum(1 for term in ai_anchor_terms if term in combined)
    if title_hits == 0 and combined_hits < 2:
        return False

    # Without a clear news/action cue, require stronger relevance and source quality.
    if intent_hits == 0 and (relevance_score < 0.40 or source_quality < 0.30):
        return False

    return True


def _build_news_query(domain: str, custom_keywords: Optional[str] = None) -> str:
    if custom_keywords and custom_keywords.strip():
        # Use exact phrase matching first for custom domains to avoid broad off-topic matches.
        custom_terms = _split_terms(custom_keywords)
        quoted = [f'"{term}"' for term in custom_terms if term]
        if not quoted:
            quoted = [f'"{custom_keywords.strip()}"']
        return " OR ".join(quoted)

    mapped = DOMAIN_QUERIES.get(domain)
    if mapped:
        return f"({mapped})"

    if domain and domain.strip():
        return f'"{domain.strip()}"'

    raise ValueError("Provide at least a domain or custom keywords")


def _pick_cluster_count(matrix, n_articles: int) -> int:
    deps = _load_nlp_deps()
    kmeans_cls = deps["KMeans"]
    silhouette = deps["silhouette_score"]
    if n_articles < 4:
        return 1

    max_k = min(5, n_articles - 1)
    min_k = 2

    if n_articles < 8:
        return min(3, max_k)

    best_k = min(3, max_k)
    best_score = -1.0

    for k in range(min_k, max_k + 1):
        try:
            labels = kmeans_cls(n_clusters=k, random_state=42, n_init=10).fit_predict(matrix)
            if len(set(labels)) < 2:
                continue
            score = silhouette(matrix, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            continue

    return best_k


def _clean_sentence_for_summary(sentence: str) -> str:
    s = re.sub(r"\s+", " ", str(sentence)).strip()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -")
    s = s.replace(" ,", ",").replace(" .", ".")
    s = re.sub(r"\.{2,}", ".", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"\[\+\d+\s+chars\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    if s[0].islower():
        s = s[0].upper() + s[1:]
    if len(s.split()) < 8:
        return ""
    if any(marker in s.lower() for marker in ["read more", "follow us", "click here"]):
        return ""
    if any(marker in s.lower() for marker in ["subscribe", "newsletter", "copyright", "all rights reserved"]):
        return ""
    if s.endswith(":") or s.endswith(";"):
        return ""
    if len(set(re.findall(r"[a-z0-9]+", s.lower()))) < 6:
        return ""
    if s[-1] not in ".!?":
        s += "."
    return s


def _is_near_duplicate_sentence(a: str, b: str) -> bool:
    a_tokens = set(re.findall(r"[a-z0-9]+", a.lower()))
    b_tokens = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not a_tokens or not b_tokens:
        return False
    overlap = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    jaccard = overlap / max(1, union)
    return jaccard >= 0.82


def _split_sentences(text: str) -> list[str]:
    deps = _load_nlp_deps()
    sent_tokenize_fn = deps["sent_tokenize"]
    try:
        sentences = sent_tokenize_fn(text)
    except LookupError:
        sentences = [s.strip() for s in text.split(".") if s.strip()]

    cleaned: list[str] = []
    noise_markers = [
        "accept all",
        "consent",
        "cookie",
        "privacy policy",
    ]
    for s in sentences:
        s = re.sub(r"\s+", " ", s).strip()
        lowered = s.lower()
        if any(marker in lowered for marker in noise_markers):
            continue
        if "[+" in s or "http://" in s or "https://" in s:
            continue
        if 35 <= len(s) <= 280:
            cleaned.append(s)
    return cleaned


class DomainNewsNLPPipeline:
    def __init__(self):
        deps = _load_nlp_deps()
        _ensure_nltk_resources()
        self.np = deps["np"]
        self.kmeans_cls = deps["KMeans"]
        self.tfidf_cls = deps["TfidfVectorizer"]
        self.cosine_similarity = deps["cosine_similarity"]
        self.word_tokenize = deps["word_tokenize"]
        self.WordNetLemmatizer = deps["WordNetLemmatizer"]
        self.stopwords = deps["stopwords"]

        self.lemmatizer = self.WordNetLemmatizer()
        self.stop_words = set(self.stopwords.words("english"))
        self.tfidf = self.tfidf_cls(max_features=2500, stop_words="english", ngram_range=(1, 2))

    def preprocess_text(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return ""

        text = _clean_article_text(text).lower()
        try:
            tokens = self.word_tokenize(text)
        except LookupError:
            tokens = text.split()

        tokens = [t for t in tokens if t.isalnum()]
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        return " ".join(tokens)

    def cluster_articles(self, articles: list[dict], target_clusters: Optional[int] = None) -> dict[int, list[dict]]:
        if len(articles) < 2:
            return {0: articles}

        combined_texts = [
            " ".join(
                [
                    str(a.get("title", "") or ""),
                    str(a.get("description", "") or ""),
                    str(a.get("content", "") or ""),
                ]
            )
            for a in articles
        ]
        processed_texts = [self.preprocess_text(t) for t in combined_texts]

        try:
            matrix = self.tfidf.fit_transform(processed_texts)
            if target_clusters is not None:
                n_clusters = max(1, min(int(target_clusters), len(articles)))
            else:
                n_clusters = _pick_cluster_count(matrix, len(articles))

            if n_clusters <= 1:
                return {0: articles}

            kmeans = self.kmeans_cls(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(matrix)

            singleton_count = sum(1 for c in self.np.bincount(labels) if c == 1)
            if target_clusters is None and singleton_count > max(1, len(articles) // 3) and n_clusters > 2:
                kmeans = self.kmeans_cls(n_clusters=n_clusters - 1, random_state=42, n_init=10)
                labels = kmeans.fit_predict(matrix)

            grouped: dict[int, list[dict]] = {}
            for idx, label in enumerate(labels):
                grouped.setdefault(int(label), []).append(articles[idx])
            return grouped
        except Exception:
            return {idx: [article] for idx, article in enumerate(articles)}

    def summarize_cluster(self, cluster_articles: list[dict]) -> str:
        docs = [str(a.get("content", "") or "") for a in cluster_articles]
        all_sentences: list[str] = []
        for doc in docs:
            all_sentences.extend(_split_sentences(doc))

        if not all_sentences:
            fallback = " ".join(docs)[:280].strip()
            return fallback if fallback else "No summary available."

        vectorizer = self.tfidf_cls(stop_words="english", ngram_range=(1, 2), max_features=1500)
        sentence_matrix = vectorizer.fit_transform(all_sentences)
        cluster_text = " ".join(docs)
        cluster_vec = vectorizer.transform([cluster_text])
        sims = self.cosine_similarity(sentence_matrix, cluster_vec).ravel()

        ranked_idx = self.np.argsort(sims)[::-1]
        selected: list[str] = []
        seen: set[str] = set()

        for i in ranked_idx:
            sentence = all_sentences[int(i)]
            key = re.sub(r"[^a-z0-9 ]", "", sentence.lower())
            if key in seen:
                continue
            seen.add(key)
            cleaned = _clean_sentence_for_summary(sentence)
            if not cleaned:
                continue
            if any(_is_near_duplicate_sentence(cleaned, existing) for existing in selected):
                continue
            selected.append(cleaned)
            if len(selected) == 3:
                break

        if not selected:
            fallback_parts = [_clean_sentence_for_summary(s) for s in all_sentences[:4]]
            fallback_parts = [p for p in fallback_parts if p]
            if fallback_parts:
                return " ".join(fallback_parts[:2])
            return "No clear summary available for this trend."

        return " ".join(selected[:3])

    def generate_trend_title(self, cluster_articles: list[dict]) -> str:
        title_candidates = [str(a.get("title", "") or "").strip() for a in cluster_articles if str(a.get("title", "") or "").strip()]
        if title_candidates:
            try:
                basis = [
                    f"{str(a.get('title', '') or '')} {str(a.get('description', '') or '')}".strip()
                    for a in cluster_articles
                ]
                vec = self.tfidf_cls(stop_words="english", ngram_range=(1, 2), max_features=1000)
                m = vec.fit_transform(basis)
                centroid = self.np.asarray(m.mean(axis=0))
                sims = self.cosine_similarity(m, centroid).ravel()
                best_idx = int(self.np.argmax(sims))
                best_title = title_candidates[best_idx]
                if len(best_title) > 90:
                    best_title = best_title[:90].rsplit(" ", 1)[0]
                return best_title
            except Exception:
                title = title_candidates[0]
                if len(title) > 90:
                    title = title[:90].rsplit(" ", 1)[0]
                return title

        return "News Trend"


def _generate_impact(summary: str) -> str:
    deps = _load_nlp_deps()
    sent_tokenize_fn = deps["sent_tokenize"]
    try:
        sentences = sent_tokenize_fn(summary)
    except LookupError:
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
    if sentences:
        impact = sentences[0]
        if len(impact) > 150:
            impact = impact[:150].rstrip() + "..."
        return impact
    return "Breaking development in this area."


def _coerce_timeline_hint(raw_timeline: object) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    if not isinstance(raw_timeline, list):
        return events

    for item in raw_timeline[:4]:
        if not isinstance(item, dict):
            continue
        date = _clean_article_text(str(item.get("date", "") or "")).strip()
        event = _clean_article_text(str(item.get("event", "") or "")).strip()
        if not event:
            continue
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        events.append(TimelineEvent(date=date[:10], event=event[:120]))
    return events


def _model_version_for_engine(summary_engine: str, default_model_version: str) -> str:
    engine = (summary_engine or "").strip().lower()
    if engine == "gemma_primary":
        return default_model_version
    if engine == "groq_fallback":
        return f"groq:{(GROQ_MODEL or 'auto').strip() or 'auto'}"
    return "extractive:v2"


def _parse_published_datetime(published: str | None) -> Optional[datetime]:
    raw = (published or "").strip()
    if not raw:
        return None

    # Prefer full ISO timestamps when available.
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        pass

    # Fallback: accept plain YYYY-MM-DD within noisy strings.
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None


def _smart_truncate(text: str, max_len: int) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= max_len:
        return cleaned

    # Prefer ending on sentence boundary; otherwise cut on a word boundary.
    sentence_split = re.split(r"(?<=[.!?])\s+", cleaned)
    built: list[str] = []
    current_len = 0
    for sentence in sentence_split:
        if not sentence:
            continue
        next_len = current_len + len(sentence) + (1 if built else 0)
        if next_len > max_len:
            break
        built.append(sentence)
        current_len = next_len

    if built:
        return " ".join(built).strip()

    truncated = cleaned[:max_len].rsplit(" ", 1)[0].strip()
    return truncated if truncated else cleaned[:max_len].strip()


def _finalize_snippet(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"[,:;\-]+$", "", cleaned).strip()
    cleaned = re.sub(r"\b(and|or|with|to|from|for|in|on|at)\s*$", "", cleaned, flags=re.IGNORECASE).strip()

    if cleaned and cleaned[-1] not in ".!?" and not cleaned.endswith("..."):
        cleaned += "."
    return cleaned


def _dedupe_summary_sentences(text: str, max_sentences: int = 4) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]
    selected: list[str] = []

    def _token_set(s: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", s.lower()))

    for sentence in sentences:
        toks = _token_set(sentence)
        if not toks:
            continue

        duplicate = False
        for existing in selected:
            existing_toks = _token_set(existing)
            overlap = len(toks & existing_toks) / max(1, len(toks | existing_toks))
            if overlap >= 0.72:
                duplicate = True
                break

        if duplicate:
            continue

        selected.append(sentence)
        if len(selected) >= max_sentences:
            break

    if not selected:
        return _finalize_snippet(text)

    return " ".join(selected)


def _choose_cluster_tldr(cluster_articles: list[dict], trend_title: str) -> str:
    if not cluster_articles:
        return ""

    title_tokens = set(re.findall(r"[a-z0-9]+", _clean_article_text(trend_title).lower()))
    best_text = ""
    best_score = -1.0

    for article in cluster_articles:
        a_title = _clean_article_text(article.get("title", ""))
        a_desc = _clean_article_text(article.get("description", ""))
        candidate = a_desc or a_title
        if not candidate:
            continue
        if len(candidate.split()) < 9:
            continue

        candidate_tokens = set(re.findall(r"[a-z0-9]+", a_title.lower()))
        overlap = len(title_tokens & candidate_tokens)
        relevance = float(article.get("relevance_score", 0.0) or 0.0)
        score = (overlap * 0.7) + (relevance * 2.0)

        if score > best_score:
            best_score = score
            best_text = candidate

    return best_text


def _generate_so_what(
    domain_label: str,
    summary: str,
    cluster_articles: list[dict],
    unique_source_count: int,
    avg_relevance: float,
) -> str:
    def _cue_count(text: str, keywords: set[str]) -> int:
        return sum(1 for kw in keywords if kw in text)

    def _top_team_tags(articles: list[dict]) -> list[str]:
        tags: list[str] = []
        for article in articles[:6]:
            title = str(article.get("title", "") or "")
            for token in re.findall(r"\b[A-Z]{2,4}\b", title):
                if token not in tags:
                    tags.append(token)
            if len(tags) >= 3:
                break
        return tags

    most_recent_days_ago = min(_days_ago_from_published(a.get("published")) for a in cluster_articles) if cluster_articles else 30
    recency_phrase = (
        "in the last 24 hours" if most_recent_days_ago <= 1
        else "in the last 72 hours" if most_recent_days_ago <= 3
        else "this week"
    )
    confidence_phrase = (
        "high confidence" if unique_source_count >= 5 and avg_relevance >= 0.45
        else "moderate confidence" if unique_source_count >= 3 and avg_relevance >= 0.3
        else "early signal"
    )

    priority = (
        "high" if unique_source_count >= 5 and most_recent_days_ago <= 2
        else "medium" if unique_source_count >= 3
        else "watchlist"
    )

    joined = " ".join(
        [
            _clean_article_text(a.get("title", "")) + " " + _clean_article_text(a.get("description", ""))
            for a in cluster_articles[:6]
        ]
    ).lower()

    domain_lower = (domain_label or "").lower()
    is_sports = any(tok in domain_lower for tok in ("ipl", "cricket", "sports", "football", "nba", "nfl"))

    regulatory_hits = _cue_count(joined, {"bill", "regulation", "policy", "court", "ban", "compliance"})
    security_hits = _cue_count(joined, {"vulnerability", "exploit", "breach", "attack", "prompt injection", "rce"})
    product_hits = _cue_count(joined, {"launch", "released", "release", "preview", "model", "feature", "platform"})
    market_hits = _cue_count(joined, {"funding", "investment", "revenue", "adoption", "competition", "market"})
    sports_lineup_hits = _cue_count(joined, {"playing 11", "lineup", "squad", "toss", "captain", "injury", "pitch", "rain"})
    sports_form_hits = _cue_count(joined, {"defeat", "win", "slump", "streak", "form", "table"})

    if is_sports:
        teams = _top_team_tags(cluster_articles)
        teams_text = ", ".join(teams[:3]) if teams else "key teams"
        if sports_lineup_hits >= sports_form_hits and sports_lineup_hits > 0:
            implication = (
                f"Why it matters: lineup and match-condition changes can swing short-term outcomes for {teams_text}."
            )
            action = (
                "Next action (today): re-check confirmed playing XI, toss, and weather 60-90 minutes before match start "
                "before making final picks or decisions."
            )
        else:
            implication = (
                f"Why it matters: recent form signals are shifting expectations for {teams_text}, so momentum assumptions may be outdated."
            )
            action = (
                "Next action (24h): track post-match updates and injury notes before adjusting your watchlist, picks, or projections."
            )
    elif security_hits >= max(regulatory_hits, product_hits, market_hits) and security_hits > 0:
        implication = "Why it matters: this points to near-term security and reliability risk, not just narrative noise."
        action = (
            "Next action (24-48h): verify exploitability/impact in your environment, map exposed dependencies, and queue mitigations "
            "if multiple trusted sources continue to confirm details."
        )
    elif regulatory_hits >= max(security_hits, product_hits, market_hits) and regulatory_hits > 0:
        implication = "Why it matters: policy/regulatory direction can change rollout timing, compliance scope, and cost assumptions."
        action = (
            "Next action (this week): identify affected workflows, list compliance gaps, and prepare a decision memo before the next policy update."
        )
    elif market_hits >= max(security_hits, regulatory_hits, product_hits) and market_hits > 0:
        implication = "Why it matters: this may signal a competitive or budget shift that can quickly alter priority bets."
        action = (
            "Next action (this week): benchmark alternatives, update ROI assumptions, and set trigger thresholds for reprioritization."
        )
    else:
        implication = "Why it matters: this trend is becoming decision-relevant as coverage broadens across independent outlets."
        action = (
            "Next action (24-72h): track two follow-up confirmations from distinct sources, then update roadmap scope only if signal strength improves."
        )

    evidence = (
        f"Evidence: {unique_source_count} sources, {confidence_phrase}, {recency_phrase}, relevance {avg_relevance:.2f}."
    )

    return (
        f"Priority: {priority}. {implication} {evidence} {action}"
    )


def _build_timeline(cluster_articles: list[dict]) -> list[TimelineEvent]:
    timeline: list[TimelineEvent] = []
    seen_dates: set[str] = set()

    sorted_articles = sorted(
        cluster_articles,
        key=lambda a: _parse_published_datetime(str(a.get("published", "") or "")) or datetime.utcnow(),
    )
    for article in sorted_articles:
        parsed = _parse_published_datetime(str(article.get("published", "") or ""))
        date_str = (parsed.date().isoformat() if parsed else datetime.utcnow().date().isoformat())
        if date_str in seen_dates:
            continue
        seen_dates.add(date_str)
        timeline.append(
            TimelineEvent(
                date=date_str,
                event=_clean_article_text(str(article.get("title", "Report published") or "Report published"))[:120]
                or "Report published",
            )
        )
        if len(timeline) >= 3:
            break

    if not timeline:
        timeline = [TimelineEvent(date=datetime.utcnow().strftime("%Y-%m-%d"), event="Initial reports published")]
    return timeline


def _signal_score(
    cluster_size: int,
    unique_source_count: int,
    avg_relevance: float,
    most_recent_days_ago: int,
    valid_link_ratio: float,
    package_release_ratio: float = 0.0,
) -> int:
    # Multi-factor score: volume + source diversity + relevance + recency.
    volume = min(1.0, cluster_size / 5.0)
    diversity = min(1.0, unique_source_count / 4.0)
    relevance = max(0.0, min(1.0, avg_relevance))
    recency = 1.0 if most_recent_days_ago <= 1 else (0.75 if most_recent_days_ago <= 3 else 0.5)

    composite = (volume * 0.35) + (diversity * 0.2) + (relevance * 0.35) + (recency * 0.1)

    # Weak source diversity should visibly dampen score.
    if unique_source_count < 2:
        composite *= 0.65

    # Package/changelog-only clusters are lower-signal by default.
    if package_release_ratio > 0.5:
        composite *= max(0.55, 1.0 - (package_release_ratio * 0.45))

    score = int(round(1 + (composite * 9)))

    # Trust gating: low link quality cannot produce top-priority signal.
    if valid_link_ratio < 0.4:
        score = min(score, 5)
    elif valid_link_ratio < 0.6:
        score = min(score, 7)

    if unique_source_count < 2:
        score = min(score, 6)

    return max(1, min(10, score))


def _build_trend_evidence(
    cluster_articles: list[dict],
    unique_source_count: int,
    avg_relevance: float,
    most_recent_days_ago: int,
) -> TrendEvidence:
    article_count = len(cluster_articles)
    valid_urls = sum(1 for a in cluster_articles if _is_valid_http_url(str(a.get("url", "") or "")))
    valid_link_ratio = (valid_urls / article_count) if article_count else 0.0
    duplicate_ratio = 1.0 - (unique_source_count / article_count) if article_count else 0.0
    duplicate_ratio = max(0.0, min(1.0, duplicate_ratio))

    source_strength = min(1.0, unique_source_count / 5.0)
    recency_strength = 1.0 if most_recent_days_ago <= 1 else (0.75 if most_recent_days_ago <= 3 else 0.45)
    relevance_strength = max(0.0, min(1.0, avg_relevance))
    link_strength = max(0.0, min(1.0, valid_link_ratio))
    dedupe_strength = 1.0 - duplicate_ratio
    confidence_score = (
        (source_strength * 0.30)
        + (relevance_strength * 0.25)
        + (recency_strength * 0.20)
        + (link_strength * 0.15)
        + (dedupe_strength * 0.10)
    )

    warning_flags: list[str] = []
    if unique_source_count < 3:
        warning_flags.append("low_source_diversity")
    if valid_link_ratio < 0.6:
        warning_flags.append("weak_citation_links")
    if duplicate_ratio > 0.4:
        warning_flags.append("high_duplicate_coverage")
    if most_recent_days_ago > 3:
        warning_flags.append("stale_coverage")
    if avg_relevance < 0.30:
        warning_flags.append("low_relevance")

    confidence_level = (
        "high" if confidence_score >= 0.75
        else "medium" if confidence_score >= 0.50
        else "low"
    )

    if valid_link_ratio < 0.4:
        confidence_level = "low"
    elif valid_link_ratio < 0.6 and confidence_level == "high":
        confidence_level = "medium"

    return TrendEvidence(
        confidence_level=confidence_level,
        confidence_score=round(confidence_score, 3),
        unique_source_count=unique_source_count,
        article_count=article_count,
        valid_link_ratio=round(valid_link_ratio, 3),
        duplicate_ratio=round(duplicate_ratio, 3),
        recency_days=most_recent_days_ago,
        avg_relevance=round(avg_relevance, 3),
        warning_flags=warning_flags,
    )


def _days_ago_from_published(published: str | None) -> int:
    dt = _parse_published_datetime(published)
    if not dt:
        return 30
    try:
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
        days = (now.date() - dt.date()).days
        return max(0, days)
    except Exception:
        return 30


async def _fetch_articles_for_digest(domain: str, days: int, custom_keywords: Optional[str]) -> tuple[list[dict], str, int]:
    normalized_days = max(
        NLP_CONFIG["min_timeline_days"],
        min(int(days), NLP_CONFIG["max_timeline_days"]),
    )
    domain_label = DOMAIN_LABELS.get(domain, domain.replace("_", " ").title())
    search_query = _build_news_query(domain=domain, custom_keywords=custom_keywords)
    phrase_terms, token_terms = _extract_domain_terms(domain=domain, custom_keywords=custom_keywords)
    relevance_threshold = MIN_RELEVANCE_CUSTOM if (custom_keywords and custom_keywords.strip()) else MIN_RELEVANCE_DEFAULT
    cutoff_dt = datetime.utcnow() - timedelta(days=normalized_days)

    stored_articles = ArticleRepository.get_recent_articles(domain=domain, days=normalized_days, limit=max(120, NLP_CONFIG["max_articles"]))
    normalized_from_store: list[dict] = []
    for row in stored_articles:
        normalized_from_store.append(
            {
                "title": _clean_article_text(row.title),
                "description": _clean_article_text(row.description or ""),
                "content": _clean_article_text(row.content or ""),
                "source": _clean_article_text(row.source or "Unknown") or "Unknown",
                "url": row.url or "",
                "published": (row.published_at.isoformat() if row.published_at else row.fetched_at.isoformat()),
            }
        )

    async def _fetch_and_persist_from_apis() -> list[dict]:
        newsapi_articles = await fetch_news_from_newsapi(search_query, normalized_days)
        gnews_articles = await fetch_news_from_gnews(search_query, normalized_days)
        fetched = newsapi_articles + gnews_articles
        if not fetched:
            return []

        ArticleRepository.upsert_articles(
            domain=domain,
            query_term=search_query,
            articles=[
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", "Unknown"),
                    "url": a.get("url", ""),
                    "published_at": a.get("published", ""),
                    "description": a.get("description", ""),
                    "content": a.get("content", ""),
                }
                for a in fetched
            ],
        )
        return fetched

    # Reduce API dependency: use stored articles first and only top up when local coverage is thin.
    articles = normalized_from_store
    min_articles_for_fresh = max(1, DB_MIN_ARTICLES_THRESHOLD)
    should_fetch_api = (not DB_FIRST_ONLY_MODE) or (len(articles) < min_articles_for_fresh)

    if should_fetch_api:
        fresh = await _fetch_and_persist_from_apis()
        if fresh:
            articles.extend(fresh)
            print(f"[DB-FIRST] API top-up fetched={len(fresh)} db_count_before={len(normalized_from_store)}")
    else:
        print(
            f"[DB-FIRST] Skipping API fetch; db_count={len(articles)} threshold={min_articles_for_fresh} mode=DB_FIRST_ONLY"
        )

    if not articles:
        return [], domain_label, normalized_days

    cleaned_articles: list[dict] = []
    seen_titles: set[str] = set()
    max_articles = NLP_CONFIG["max_articles"]

    for article in articles:
        title = _clean_article_text(article.get("title", ""))
        description = _clean_article_text(article.get("description", ""))
        content = _clean_article_text(article.get("content", ""))
        normalized_title = _normalize_title(title)

        if not title or normalized_title in seen_titles:
            continue
        if not content and not description:
            continue

        joined = f"{title} {description} {content}".strip()
        if _contains_feed_noise(joined):
            continue

        parsed_published = _parse_published_datetime(article.get("published", ""))
        if parsed_published:
            published_cmp = parsed_published.replace(tzinfo=None) if parsed_published.tzinfo else parsed_published
            if published_cmp < cutoff_dt:
                continue

        relevance_score = _article_relevance_score(
            {"title": title, "description": description, "content": content, "source": article.get("source", "Unknown")},
            phrase_terms=phrase_terms,
            token_terms=token_terms,
        )
        source_quality = _source_quality_score(article.get("source", "Unknown"))

        release_like = _is_version_release_article({
            "title": title,
            "description": description,
            "source": article.get("source", "Unknown"),
            "url": article.get("url", ""),
        })
        if release_like:
            # Keep but down-weight low-context package/version churn.
            relevance_score *= 0.72
            source_quality = min(source_quality, 0.42)

        if source_quality < MIN_SOURCE_QUALITY:
            continue
        if relevance_score < relevance_threshold:
            continue
        if not _passes_domain_gate(
            domain=domain,
            title=title,
            description=description,
            relevance_score=relevance_score,
            source_quality=source_quality,
            phrase_terms=phrase_terms,
            token_terms=token_terms,
            custom_keywords=custom_keywords,
        ):
            continue

        full_text = f"{title}. {description}. {content}".strip()
        source = _clean_article_text(article.get("source", "Unknown")) or "Unknown"
        cleaned_articles.append(
            {
                "title": title,
                "description": description,
                "content": full_text,
                "source": source,
                "url": article.get("url", "") or "",
                "published": (
                    parsed_published.isoformat() if parsed_published else datetime.utcnow().isoformat()
                ),
                "relevance_score": relevance_score,
                "source_quality": source_quality,
                "is_package_release": release_like,
            }
        )
        seen_titles.add(normalized_title)

        if len(cleaned_articles) >= max_articles:
            break

    return cleaned_articles, domain_label, normalized_days


async def generate_real_digest(domain: str, days: int, custom_keywords: Optional[str] = None) -> DigestResponse:
    """Generate digest using the same logic as the nlp app pipeline.

    Flow: fetch -> clean/dedup -> preprocess -> TF-IDF + KMeans -> extractive summaries.
    """
    articles, domain_label, normalized_days = await _fetch_articles_for_digest(
        domain=domain,
        days=days,
        custom_keywords=custom_keywords,
    )
    if not articles:
        raise RuntimeError("No articles available for selected domain/keywords")

    pipeline = DomainNewsNLPPipeline()
    model_version = _active_model_version()
    top_n = int(NLP_CONFIG["top_trends"])
    clustered = pipeline.cluster_articles(articles)

    trend_entries: list[dict] = []
    singleton_pool: list[dict] = []
    for cluster_id, cluster_articles in clustered.items():
        if len(cluster_articles) < MIN_CLUSTER_SIZE:
            singleton_pool.extend(cluster_articles)
            continue

        extractive_title = pipeline.generate_trend_title(cluster_articles)
        extractive_summary = pipeline.summarize_cluster(cluster_articles)
        llm_payload = await summarize_cluster_hybrid(cluster_articles, domain_label)
        summary_engine = str(llm_payload.get("_engine", "extractive_fallback") or "extractive_fallback")

        title = _clean_article_text(str(llm_payload.get("trend_title") or extractive_title or "News Trend"))
        summary = _clean_article_text(str(llm_payload.get("summary") or extractive_summary or "No summary available."))
        impact = _generate_impact(summary)
        tldr_hint = _clean_article_text(str(llm_payload.get("tldr") or "")) or None
        so_what_hint = _clean_article_text(str(llm_payload.get("so_what") or "")) or None
        contrast_hint = _clean_article_text(str(llm_payload.get("contrast") or "")) or None
        timeline_hint = _coerce_timeline_hint(llm_payload.get("timeline"))
        entity_hint_raw = llm_payload.get("key_entities")
        entities_hint: list[str] = []
        if isinstance(entity_hint_raw, list):
            entities_hint = [
                cleaned
                for item in entity_hint_raw
                if isinstance(item, str) and (cleaned := _clean_article_text(item))
            ][:5]
        avg_relevance = sum(float(a.get("relevance_score", 0.0)) for a in cluster_articles) / max(1, len(cluster_articles))
        package_release_ratio = (
            sum(1 for a in cluster_articles if bool(a.get("is_package_release", False))) / max(1, len(cluster_articles))
        )
        cluster_unique_sources = len({_source_identity_key(a) for a in cluster_articles})

        # Collapse pure package/changelog clusters from a single source.
        if package_release_ratio >= 0.8 and cluster_unique_sources < 2:
            continue

        trend_entries.append(
            {
                "cluster_id": cluster_id,
                "title": title,
                "summary": summary,
                "impact": impact,
                "articles": cluster_articles,
                "articles_count": len(cluster_articles),
                "avg_relevance": avg_relevance,
                "package_release_ratio": package_release_ratio,
                "tldr_hint": tldr_hint,
                "so_what_hint": so_what_hint,
                "contrast_hint": contrast_hint,
                "timeline_hint": timeline_hint,
                "entities_hint": entities_hint,
                "summary_engine": summary_engine,
            }
        )

    # Avoid publishing many single-article "trends"; aggregate leftover singleton signals.
    if len(singleton_pool) >= MIN_CLUSTER_SIZE and len(trend_entries) < top_n:
        singleton_pool = sorted(singleton_pool, key=lambda a: float(a.get("relevance_score", 0.0)), reverse=True)
        pooled = singleton_pool[: max(3, MIN_CLUSTER_SIZE)]
        trend_entries.append(
            {
                "cluster_id": -1,
                "title": f"Other Signals in {domain_label}",
                "summary": pipeline.summarize_cluster(pooled),
                "impact": "Multiple lower-volume but relevant signals are emerging and should be monitored.",
                "articles": pooled,
                "articles_count": len(pooled),
                "avg_relevance": sum(float(a.get("relevance_score", 0.0)) for a in pooled) / max(1, len(pooled)),
                "summary_engine": "extractive_fallback",
            }
        )

    trend_entries = sorted(trend_entries, key=lambda item: item["articles_count"], reverse=True)[:top_n]

    if not trend_entries and articles:
        # Final safeguard: if strict filtering creates no clusters, publish one aggregated trend.
        pooled = sorted(articles, key=lambda a: float(a.get("relevance_score", 0.0)), reverse=True)[: max(3, MIN_CLUSTER_SIZE)]
        trend_entries = [
            {
                "cluster_id": -2,
                "title": f"Emerging Signals in {domain_label}",
                "summary": pipeline.summarize_cluster(pooled),
                "impact": "Early-stage coverage is limited; monitor for stronger multi-source confirmation.",
                "articles": pooled,
                "articles_count": len(pooled),
                "avg_relevance": sum(float(a.get("relevance_score", 0.0)) for a in pooled) / max(1, len(pooled)),
                "summary_engine": "extractive_fallback",
            }
        ]

    trends: list[Trend] = []
    for index, entry in enumerate(trend_entries, start=1):
        cluster_articles = entry["articles"]
        unique_source_names: list[str] = []
        unique_source_keys: set[str] = set()
        for a in cluster_articles:
            key = _source_identity_key(a)
            if key in unique_source_keys:
                continue
            unique_source_keys.add(key)
            display_name = str(a.get("source", "Unknown") or "Unknown")
            unique_source_names.append(display_name)

        summary_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", entry["summary"]) if s.strip()]
        tldr_seed = entry.get("tldr_hint") or _choose_cluster_tldr(cluster_articles, entry["title"])
        tldr = tldr_seed or (summary_sentences[0] if summary_sentences else entry["summary"])
        tldr = _finalize_snippet(tldr)
        if len(tldr.split()) < 8 or len(tldr) < 45:
            tldr = _finalize_snippet(_clean_article_text(entry["title"]))
        summary = entry["summary"]
        summary_engine = str(entry.get("summary_engine") or "extractive_fallback")
        trend_model_version = _model_version_for_engine(summary_engine, model_version)

        timeline_events = entry.get("timeline_hint")
        if not timeline_events:
            timeline_events = _build_timeline(cluster_articles)

        most_recent_days_ago = min(_days_ago_from_published(a.get("published")) for a in cluster_articles) if cluster_articles else 30
        evidence = _build_trend_evidence(
            cluster_articles=cluster_articles,
            unique_source_count=len(unique_source_keys),
            avg_relevance=float(entry.get("avg_relevance", 0.0)),
            most_recent_days_ago=most_recent_days_ago,
        )

        signal_score = _signal_score(
            cluster_size=entry["articles_count"],
            unique_source_count=len(unique_source_keys),
            avg_relevance=float(entry.get("avg_relevance", 0.0)),
            most_recent_days_ago=most_recent_days_ago,
            valid_link_ratio=float(evidence.valid_link_ratio),
            package_release_ratio=float(entry.get("package_release_ratio", 0.0)),
        )

        trends.append(
            Trend(
                trend_id=index,
                trend_title=entry["title"],
                tldr=tldr or "No summary available.",
                summary=summary or "No summary available.",
                timeline=timeline_events,
                so_what=(
                    entry.get("so_what_hint")
                    or _generate_so_what(
                        domain_label=domain_label,
                        summary=entry["summary"],
                        cluster_articles=cluster_articles,
                        unique_source_count=len(unique_source_keys),
                        avg_relevance=float(entry.get("avg_relevance", 0.0)),
                    )
                ),
                signal_score=signal_score,
                contrast=entry.get("contrast_hint"),
                key_entities=(entry.get("entities_hint") or unique_source_names[:5]),
                source_count=len(unique_source_keys),
                confidence_level=evidence.confidence_level,
                evidence=evidence,
                model_version=trend_model_version,
                summary_engine=summary_engine,
                articles=[
                    Article(
                        title=_clean_article_text(str(a.get("title", "") or "")),
                        source=_clean_article_text(str(a.get("source", "Unknown") or "Unknown")) or "Unknown",
                        url=(str(a.get("url", "") or "") if _is_valid_http_url(str(a.get("url", "") or "")) else ""),
                        published=str(a.get("published", datetime.now().isoformat()) or datetime.now().isoformat()),
                        description=_clean_article_text(a.get("description")),
                        content=_clean_article_text(a.get("content")),
                    )
                    for a in cluster_articles[:5]
                ],
            )
        )

    trends.sort(key=lambda t: t.signal_score, reverse=True)

    for trend in trends:
        trend.trend_title = _clean_article_text(trend.trend_title)
        trend.tldr = _clean_article_text(trend.tldr)
        trend.summary = _clean_article_text(trend.summary)
        trend.so_what = _clean_article_text(trend.so_what)
        trend.key_entities = [
            cleaned for entity in trend.key_entities if (cleaned := _clean_article_text(entity))
        ]
        trend.timeline = [
            TimelineEvent(date=event.date, event=_clean_article_text(event.event)[:120] or "Report published")
            for event in trend.timeline
        ]
        trend.articles = [
            Article(
                title=_clean_article_text(article.title),
                source=_clean_article_text(article.source) or "Unknown",
                url=article.url,
                published=article.published,
                description=_clean_article_text(article.description),
                content=_clean_article_text(article.content),
            )
            for article in trend.articles
        ]

    digest_id = hashlib.md5(f"{domain}:{normalized_days}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

    summary_engines = {t.summary_engine for t in trends if t.summary_engine}
    digest_summary_engine = next(iter(summary_engines)) if len(summary_engines) == 1 else ("mixed" if summary_engines else "extractive_fallback")
    trend_model_versions = {t.model_version for t in trends if t.model_version}
    digest_model_version = next(iter(trend_model_versions)) if len(trend_model_versions) == 1 else ("mixed" if trend_model_versions else model_version)

    # Log summarization engine used
    print(f"\n{'='*60}")
    print(f"DIGEST GENERATED")
    print(f"{'='*60}")
    print(f"  Domain: {domain_label}")
    print(f"  Trends: {len(trends)}")
    print(f"  Articles: {len(articles)}")
    print(f"  Summarization Engine: {digest_summary_engine}")
    print(f"  Model Version: {digest_model_version}")
    print(f"{'='*60}\n")
    
    return DigestResponse(
        digest_id=digest_id,
        domain=domain_label,
        days=normalized_days,
        generated_at=datetime.now().isoformat(),
        total_trends=len(trends),
        total_articles=len(articles),
        cached=False,
        trends=trends,
        model_version=digest_model_version,
        summary_engine=digest_summary_engine,
    )


def generate_mock_digest(domain: str, days: int) -> DigestResponse:
    """Fallback mock digest if real APIs fail"""
    domain_label = DOMAIN_LABELS.get(domain, domain.replace("_", " ").title())
    digest_id = hashlib.md5(f"{domain}:{days}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    mock_trends = [
        Trend(
            trend_id=1,
            trend_title=f"Major Development in {domain_label} Sector",
            tldr=f"Key players in {domain_label} announce significant changes affecting the industry landscape.",
            summary=f"""The {domain_label} sector has seen remarkable developments this week, with major announcements from industry leaders.

Multiple sources confirm that these changes represent a significant shift in how organizations approach {domain_label} challenges. Analysts suggest this could have far-reaching implications for professionals in the field.

While the immediate impact remains to be seen, early indicators suggest positive market reception and increased investment activity.""",
            timeline=[
                TimelineEvent(date=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), event="Initial announcements made"),
                TimelineEvent(date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), event="Market reaction begins"),
                TimelineEvent(date=datetime.now().strftime("%Y-%m-%d"), event="Further details emerge"),
            ],
            so_what=f"Professionals in {domain_label} should monitor these developments closely.",
            signal_score=8,
            contrast="Some analysts remain cautious about the pace of change.",
            key_entities=["Industry Leader A", "Industry Leader B", "Regulatory Body"],
            source_count=8,
            summary_engine="extractive_fallback",
            articles=[
                Article(title=f"Breaking: {domain_label} Industry Sees Major Shift", source="TechCrunch", url="#", published=(datetime.now() - timedelta(days=1)).isoformat()),
                Article(title=f"Analysis: What {domain_label} Changes Mean", source="Reuters", url="#", published=datetime.now().isoformat()),
            ]
        ),
    ]
    
    return DigestResponse(
        digest_id=digest_id,
        domain=domain_label,
        days=days,
        generated_at=datetime.now().isoformat(),
        total_trends=len(mock_trends),
        total_articles=sum(len(t.articles) for t in mock_trends),
        cached=False,
        trends=mock_trends,
        model_version=_active_model_version(),
        summary_engine=(mock_trends[0].summary_engine if mock_trends else "extractive_fallback"),
    )


def _sanitize_digest_response(digest: DigestResponse) -> DigestResponse:
    digest.model_version = _clean_article_text(digest.model_version) if digest.model_version else _active_model_version()

    for trend in digest.trends:
        trend.trend_title = _clean_article_text(trend.trend_title)
        trend.tldr = _clean_article_text(trend.tldr)
        trend.summary = _clean_article_text(trend.summary)
        trend.so_what = _clean_article_text(trend.so_what)
        trend.key_entities = [
            cleaned for entity in trend.key_entities if (cleaned := _clean_article_text(entity))
        ]
        trend.timeline = [
            TimelineEvent(date=event.date, event=_clean_article_text(event.event)[:120] or "Report published")
            for event in trend.timeline
        ]
        trend.articles = [
            Article(
                title=_clean_article_text(article.title),
                source=_clean_article_text(article.source) or "Unknown",
                url=article.url,
                published=article.published,
                description=_clean_article_text(article.description),
                content=_clean_article_text(article.content),
            )
            for article in trend.articles
        ]
        # Always set model_version and summary_engine to a string for serialization
        if trend.model_version:
            trend.model_version = _clean_article_text(trend.model_version)
        elif digest.model_version:
            trend.model_version = digest.model_version or "unspecified"
        else:
            trend.model_version = "unspecified"

        if trend.summary_engine:
            trend.summary_engine = _clean_article_text(trend.summary_engine).lower().replace(" ", "_")
        else:
            trend.summary_engine = "unknown"

        if trend.evidence is not None:
            trend.evidence.warning_flags = [
                _clean_article_text(flag).lower().replace(" ", "_")
                for flag in trend.evidence.warning_flags
                if _clean_article_text(flag)
            ]

            if not trend.confidence_level:
                trend.confidence_level = trend.evidence.confidence_level

    if digest.summary_engine:
        digest.summary_engine = _clean_article_text(digest.summary_engine).lower().replace(" ", "_")
    elif digest.trends:
        engines = {t.summary_engine for t in digest.trends if t.summary_engine}
        digest.summary_engine = next(iter(engines)) if len(engines) == 1 else ("mixed" if engines else "extractive_fallback")
    return digest


# ============== API Routes ==============

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "whatsnew-backend"}


@app.post("/digest/generate")
async def generate_digest(request: DigestRequest) -> DigestResponse:
    """Generate a news digest for a domain using real APIs
    
    Supports both predefined domains and custom user-defined domains with custom keywords.
    Caching is disabled. Every request returns a freshly generated digest.
    """
    print("[DEBUG] generate_digest called (cache disabled)")
    try:
        digest = await generate_real_digest(request.domain, request.days, request.keywords)
    except Exception as e:
        print(f"Error generating digest: {e}")
        if ALLOW_MOCK_FALLBACK:
            print("[DEBUG] Falling back to mock digest for uncached request (ALLOW_MOCK_FALLBACK=true)")
            digest = generate_mock_digest(request.domain, request.days)
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Live digest unavailable: {str(e)}"
            )

    digest.cached = False
    digest = _sanitize_digest_response(digest)

    print(f"[DEBUG] Generated fresh digest, cached flag: {digest.cached}")
    return digest


@app.post("/cache/clear")
async def clear_cache(current_user: dict = Depends(get_current_user_from_token)) -> dict[str, str]:
    """Legacy endpoint retained for compatibility. Caching is disabled."""
    print("[INFO] /cache/clear called while caching is disabled")
    return {
        "status": "cleared",
        "message": "Caching is disabled; all digest requests are fresh by design."
    }


@app.get("/digest/history")
async def get_digest_history(
    limit: int = 10,
    offset: int = 0,
    domain: Optional[str] = None
) -> list[dict]:
    """Get user's digest history"""
    history = [
        {"id": "digest-001", "domain": "AI & ML", "date": "2026-04-02", "trends": 6, "articles": 43},
        {"id": "digest-002", "domain": "Finance", "date": "2026-04-01", "trends": 5, "articles": 38},
        {"id": "digest-003", "domain": "AI & ML", "date": "2026-03-28", "trends": 7, "articles": 52},
    ]
    
    if domain:
        history = [h for h in history if h["domain"].lower() == domain.lower()]
    
    return history[offset:offset + limit]


@app.get("/digest/{digest_id}")
async def get_digest(digest_id: str) -> DigestResponse:
    """Get a specific digest by ID"""
    return generate_mock_digest("ai", 7)


@app.post("/user/saved-trends")
async def save_trend(request: SaveTrendRequest, current_user: dict = Depends(get_current_user_from_token)) -> dict:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    domain = _clean_article_text(request.domain)
    trend_payload = request.trend.model_dump()
    trend_id = int(trend_payload.get("trend_id", 0) or 0)
    digest_id = (request.digest_id or "ad-hoc-digest").strip() or "ad-hoc-digest"

    existing = SavedTrendRepository.get_user_saved_trends(user_id)
    normalized_title = _normalize_title(trend_payload.get("trend_title", ""))
    for saved in existing:
        data = saved.trend_data or {}
        saved_domain = _clean_article_text(data.get("domain", ""))
        saved_trend = data.get("trend", {}) if isinstance(data.get("trend", {}), dict) else {}
        saved_title = _normalize_title(saved_trend.get("trend_title", ""))
        saved_trend_id = int(saved_trend.get("trend_id", 0) or 0)

        if saved_domain == domain and saved_trend_id == trend_id and saved_title == normalized_title:
            return {
                "status": "already_saved",
                "id": saved.id,
                "digest_id": saved.digest_id,
                "trend_id": saved.trend_id,
            }

    saved = SavedTrendRepository.save_trend(
        user_id=user_id,
        digest_id=digest_id,
        trend_id=trend_id,
        trend_data={
            "domain": domain,
            "trend": trend_payload,
        },
    )

    return {
        "status": "saved",
        "id": saved.id,
        "digest_id": saved.digest_id,
        "trend_id": saved.trend_id,
        "saved_at": saved.saved_at.isoformat() if saved.saved_at else datetime.utcnow().isoformat(),
    }


@app.get("/user/saved-trends")
async def get_saved_trends(current_user: dict = Depends(get_current_user_from_token)) -> list[dict]:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    saved_items = SavedTrendRepository.get_user_saved_trends(user_id)
    result: list[dict] = []
    for item in saved_items:
        data = item.trend_data or {}
        trend_raw = data.get("trend", {}) if isinstance(data.get("trend", {}), dict) else {}
        domain = _clean_article_text(data.get("domain", "Unknown")) or "Unknown"

        try:
            trend = Trend(**trend_raw)
        except Exception:
            continue

        result.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "digest_id": item.digest_id,
                "trend_id": item.trend_id,
                "saved_at": item.saved_at.isoformat() if item.saved_at else datetime.utcnow().isoformat(),
                "domain": domain,
                "trend": trend.model_dump(),
            }
        )

    result.sort(key=lambda s: s.get("saved_at", ""), reverse=True)
    return result


@app.delete("/user/saved-trends/{saved_id}")
async def delete_saved_trend(saved_id: str, current_user: dict = Depends(get_current_user_from_token)) -> dict[str, str]:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    deleted = SavedTrendRepository.delete_saved_trend(user_id=user_id, saved_id=saved_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved trend not found")

    return {"status": "deleted", "id": saved_id}


@app.get("/user/me")
async def get_user_me(current_user: dict = Depends(get_current_user_from_token)) -> User:
    """Get current authenticated user profile"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = UserRepository.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs_dict = user.preferences if isinstance(user.preferences, dict) else None
    if not prefs_dict:
        prefs_dict = UserPreferences().model_dump()

    created_at = user.created_at.isoformat() if getattr(user, "created_at", None) else datetime.utcnow().isoformat()
    last_active_at = user.last_active_at.isoformat() if getattr(user, "last_active_at", None) else datetime.utcnow().isoformat()

    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        preferences=UserPreferences(**prefs_dict),
        created_at=created_at,
        last_active_at=last_active_at,
    )


@app.patch("/user/preferences")
async def update_preferences(preferences: UserPreferences, current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Update user preferences"""
    user_id = current_user.get("user_id", "user-001")
    
    # Get user from database
    user = UserRepository.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user preferences in MongoDB
    UserRepository.update_user_preferences(user_id, preferences.model_dump())
    
    return {
        "status": "updated",
        "preferences": preferences.model_dump()
    }


@app.get("/user/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Get user preferences"""
    user_id = current_user.get("user_id", "user-001")

    # Get from MongoDB
    user = UserRepository.get_user(user_id)
    if not user:
        # Return default preferences
        return {
            "status": "retrieved",
            "preferences": UserPreferences().model_dump()
        }
    
    prefs = user.preferences if user.preferences else UserPreferences().model_dump()
    
    return {
        "status": "retrieved",
        "preferences": prefs
    }


@app.put("/user/profile")
async def update_profile(body: dict, current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Update user profile information (name, email)"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = UserRepository.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()

    if not name and not email:
        raise HTTPException(status_code=400, detail="At least one field (name or email) is required")

    if email and email != user.email:
        existing = UserRepository.get_user_by_email(email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = email

    if name:
        user.name = name

    updated = UserRepository.update_user_profile(user_id=user.id, name=name, email=user.email)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return {
        "status": "updated",
        "user": {
            "id": updated.id,
            "name": updated.name,
            "email": updated.email,
        },
    }


@app.get("/export/pdf/{digest_id}")
async def export_pdf(digest_id: str) -> dict[str, str]:
    return {
        "status": "generated",
        "url": f"/downloads/{digest_id}.pdf",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
    }


@app.get("/export/share/{digest_id}")
async def create_share_link(digest_id: str) -> dict[str, str]:
    import secrets
    share_token = secrets.token_urlsafe(16)
    return {
        "share_url": f"/public/{share_token}",
        "token": share_token,
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }


@app.post("/auth/register")
async def register(req: AuthRequest) -> dict:
    """Register a new user"""
    try:
        email = (req.email or "").strip().lower()
        name = (req.name or "").strip()
        password = req.password or ""

        # Validation
        if not email or not password or not name:
            raise HTTPException(status_code=400, detail="Email, password, and name are required")
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if user already exists
        existing_user = UserRepository.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user in database
        user = UserRepository.create_user(email, name, hashed_password)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        
        return {
            "status": "registered",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login")
async def login(req: AuthRequest) -> dict:
    """Login user"""
    try:
        email = (req.email or "").strip().lower()
        password = req.password or ""

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        # Get user from database
        user = UserRepository.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        UserRepository.update_user_last_active(user.id)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        
        return {
            "status": "logged_in",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/user/custom-domains")
async def create_custom_domain(req: CustomDomainRequest, current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Create a custom domain for news alerts with custom keywords"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        domain_name = (req.domain_name or "").strip()
        if not domain_name:
            raise HTTPException(status_code=400, detail="domain_name is required")
        
        # Use domain name as keywords if not provided
        keywords = (req.keywords or domain_name).strip()
        description = (req.description or "").strip() or None

        domain = CustomDomainRepository.create_domain(
            user_id=user_id,
            domain_name=domain_name,
            keywords=keywords,
            description=description,
        )

        print(f"✓ Custom domain created: {domain_name}")
        print(f"  Keywords: {keywords}")
        if description:
            print(f"  Description: {description}")
        print(f"  User: {user_id}")
        
        return {
            "status": "created",
            "domain": {
                "id": domain.id,
                "name": domain.domain_name,
                "keywords": keywords,
                "description": description,
                "user_id": user_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create domain: {str(e)}")

@app.get("/user/custom-domains")
async def get_custom_domains(current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Get all custom domains for a user"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    domains = CustomDomainRepository.get_user_domains(user_id)
    return {
        "user_id": user_id,
        "domains": [
            {
                "id": d.id,
                "name": d.domain_name,
                "keywords": d.keywords,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in domains
        ]
    }


@app.delete("/user/custom-domains/{domain_id}")
async def delete_custom_domain(domain_id: str, current_user: dict = Depends(get_current_user_from_token)) -> dict:
    """Delete a custom domain for a user"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    deleted = CustomDomainRepository.delete_domain(user_id=user_id, domain_id=domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custom domain not found")

    return {
        "status": "deleted",
        "domain_id": domain_id,
    }

@app.post("/digest/generate-custom")
async def generate_custom_digest(domain_id: str, keywords: str, days: int = 7) -> DigestResponse:
    """Generate digest for custom domain with specific keywords
    
    Args:
        domain_id: Custom domain identifier
        keywords: Comma-separated keywords for article filtering
        days: Number of days to fetch articles for
    """
    print(f"✓ Generating custom digest")
    print(f"  Domain ID: {domain_id}")
    print(f"  Keywords: {keywords}")  
    print(f"  Days: {days}")
    
    # Generate digest using custom keywords
    return await generate_real_digest(domain_id, days, keywords)


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting What's New? Backend API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
