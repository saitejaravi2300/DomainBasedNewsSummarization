from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from pymongo import DESCENDING, MongoClient

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "whatsnew_db")

_mongo_client: Optional[MongoClient] = None
_mongo_db = None


def _get_db():
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db

    # This backend is a long-running FastAPI server process (not serverless).
    # Keep a single shared client and moderate pool sizing for local development.
    _mongo_client = MongoClient(
        MONGODB_URI,
        maxPoolSize=40,
        minPoolSize=5,
        connectTimeoutMS=10000,
        serverSelectionTimeoutMS=10000,
        socketTimeoutMS=30000,
    )
    _mongo_db = _mongo_client[MONGODB_DB_NAME]

    # Ensure core indexes used by lookup-heavy endpoints.
    _mongo_db.users.create_index("email", unique=True)
    _mongo_db.saved_trends.create_index([("user_id", DESCENDING), ("saved_at", DESCENDING)])
    _mongo_db.custom_domains.create_index([("user_id", DESCENDING), ("created_at", DESCENDING)])
    _mongo_db.articles.create_index([("domain", DESCENDING), ("published_at", DESCENDING)])
    _mongo_db.articles.create_index("url", unique=True)
    _mongo_db.digests.create_index([("user_id", DESCENDING), ("generated_at", DESCENDING)])

    return _mongo_db


@dataclass
class UserRecord:
    id: str
    email: str
    name: str
    password_hash: str
    avatar_url: Optional[str]
    preferences: dict
    created_at: datetime
    last_active_at: datetime


@dataclass
class DigestRecord:
    id: str
    user_id: str
    domain: str
    days: int
    total_trends: int
    total_articles: int
    content: dict
    generated_at: datetime
    cached: bool


@dataclass
class SavedTrendRecord:
    id: str
    user_id: str
    digest_id: str
    trend_id: int
    trend_data: dict
    saved_at: datetime


@dataclass
class CustomDomainRecord:
    id: str
    user_id: str
    domain_name: str
    keywords: Optional[str]
    description: Optional[str]
    created_at: datetime


@dataclass
class ArticleRecord:
    id: str
    domain: str
    query_term: Optional[str]
    title: str
    source: Optional[str]
    url: str
    published_at: Optional[datetime]
    fetched_at: datetime
    description: Optional[str]
    content: Optional[str]


def _to_user_record(doc: dict) -> UserRecord:
    return UserRecord(
        id=str(doc.get("id")),
        email=str(doc.get("email", "")),
        name=str(doc.get("name", "")),
        password_hash=str(doc.get("password_hash", "")),
        avatar_url=doc.get("avatar_url"),
        preferences=doc.get("preferences") or {},
        created_at=doc.get("created_at") or datetime.utcnow(),
        last_active_at=doc.get("last_active_at") or datetime.utcnow(),
    )


def _to_digest_record(doc: dict) -> DigestRecord:
    return DigestRecord(
        id=str(doc.get("id")),
        user_id=str(doc.get("user_id")),
        domain=str(doc.get("domain", "")),
        days=int(doc.get("days", 7) or 7),
        total_trends=int(doc.get("total_trends", 0) or 0),
        total_articles=int(doc.get("total_articles", 0) or 0),
        content=doc.get("content") or {},
        generated_at=doc.get("generated_at") or datetime.utcnow(),
        cached=bool(doc.get("cached", False)),
    )


def _to_saved_trend_record(doc: dict) -> SavedTrendRecord:
    return SavedTrendRecord(
        id=str(doc.get("id")),
        user_id=str(doc.get("user_id")),
        digest_id=str(doc.get("digest_id")),
        trend_id=int(doc.get("trend_id", 0) or 0),
        trend_data=doc.get("trend_data") or {},
        saved_at=doc.get("saved_at") or datetime.utcnow(),
    )


def _to_custom_domain_record(doc: dict) -> CustomDomainRecord:
    return CustomDomainRecord(
        id=str(doc.get("id")),
        user_id=str(doc.get("user_id")),
        domain_name=str(doc.get("domain_name", "")),
        keywords=doc.get("keywords"),
        description=doc.get("description"),
        created_at=doc.get("created_at") or datetime.utcnow(),
    )


def _to_article_record(doc: dict) -> ArticleRecord:
    return ArticleRecord(
        id=str(doc.get("id")),
        domain=str(doc.get("domain", "")),
        query_term=doc.get("query_term"),
        title=str(doc.get("title", "")),
        source=doc.get("source"),
        url=str(doc.get("url", "")),
        published_at=doc.get("published_at"),
        fetched_at=doc.get("fetched_at") or datetime.utcnow(),
        description=doc.get("description"),
        content=doc.get("content"),
    )

class UserRepository:
    @staticmethod
    def create_user(email: str, name: str, password_hash: str) -> UserRecord:
        db = _get_db()
        now = datetime.utcnow()
        doc = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "password_hash": password_hash,
            "avatar_url": None,
            "preferences": {},
            "created_at": now,
            "last_active_at": now,
        }
        db.users.insert_one(doc)
        return _to_user_record(doc)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[UserRecord]:
        db = _get_db()
        doc = db.users.find_one({"email": email})
        return _to_user_record(doc) if doc else None
    
    @staticmethod
    def get_user(user_id: str) -> Optional[UserRecord]:
        db = _get_db()
        doc = db.users.find_one({"id": user_id})
        return _to_user_record(doc) if doc else None

    @staticmethod
    def update_user_last_active(user_id: str) -> None:
        db = _get_db()
        db.users.update_one({"id": user_id}, {"$set": {"last_active_at": datetime.utcnow()}})

    @staticmethod
    def update_user_preferences(user_id: str, preferences: dict) -> bool:
        db = _get_db()
        result = db.users.update_one(
            {"id": user_id},
            {"$set": {"preferences": preferences, "last_active_at": datetime.utcnow()}},
        )
        return result.matched_count > 0

    @staticmethod
    def update_user_profile(user_id: str, name: Optional[str], email: Optional[str]) -> Optional[UserRecord]:
        db = _get_db()
        updates = {"last_active_at": datetime.utcnow()}
        if name:
            updates["name"] = name
        if email:
            updates["email"] = email
        db.users.update_one({"id": user_id}, {"$set": updates})
        doc = db.users.find_one({"id": user_id})
        return _to_user_record(doc) if doc else None

class DigestRepository:
    @staticmethod
    def save_digest(user_id: str, domain: str, days: int, content: dict) -> DigestRecord:
        db = _get_db()
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "domain": domain,
            "days": days,
            "total_trends": len(content.get("trends", [])),
            "total_articles": content.get("total_articles", 0),
            "content": content,
            "generated_at": datetime.utcnow(),
            "cached": bool(content.get("cached", False)),
        }
        db.digests.insert_one(doc)
        return _to_digest_record(doc)
    
    @staticmethod
    def get_user_digests(user_id: str, limit: int = 10) -> list[DigestRecord]:
        db = _get_db()
        docs = list(db.digests.find({"user_id": user_id}).sort("generated_at", DESCENDING).limit(limit))
        return [_to_digest_record(d) for d in docs]

class SavedTrendRepository:
    @staticmethod
    def save_trend(user_id: str, digest_id: str, trend_id: int, trend_data: dict) -> SavedTrendRecord:
        db = _get_db()
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "digest_id": digest_id,
            "trend_id": trend_id,
            "trend_data": trend_data,
            "saved_at": datetime.utcnow(),
        }
        db.saved_trends.insert_one(doc)
        return _to_saved_trend_record(doc)
    
    @staticmethod
    def get_user_saved_trends(user_id: str) -> list[SavedTrendRecord]:
        db = _get_db()
        docs = list(db.saved_trends.find({"user_id": user_id}).sort("saved_at", DESCENDING))
        return [_to_saved_trend_record(d) for d in docs]

    @staticmethod
    def delete_saved_trend(user_id: str, saved_id: str) -> bool:
        db = _get_db()
        result = db.saved_trends.delete_one({"id": saved_id, "user_id": user_id})
        return result.deleted_count > 0


class CustomDomainRepository:
    @staticmethod
    def create_domain(user_id: str, domain_name: str, keywords: str | None, description: str | None) -> CustomDomainRecord:
        db = _get_db()
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "domain_name": domain_name,
            "keywords": keywords,
            "description": description,
            "created_at": datetime.utcnow(),
        }
        db.custom_domains.insert_one(doc)
        return _to_custom_domain_record(doc)

    @staticmethod
    def get_user_domains(user_id: str) -> list[CustomDomainRecord]:
        db = _get_db()
        docs = list(db.custom_domains.find({"user_id": user_id}).sort("created_at", DESCENDING))
        return [_to_custom_domain_record(d) for d in docs]

    @staticmethod
    def delete_domain(user_id: str, domain_id: str) -> bool:
        db = _get_db()
        result = db.custom_domains.delete_one({"id": domain_id, "user_id": user_id})
        return result.deleted_count > 0


class ArticleRepository:
    @staticmethod
    def get_recent_articles(domain: str, days: int, limit: int = 250) -> list[ArticleRecord]:
        db = _get_db()
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = {
            "domain": domain,
            "$or": [
                {"published_at": {"$gte": cutoff}},
                {"published_at": None, "fetched_at": {"$gte": cutoff}},
            ],
        }
        docs = list(db.articles.find(query).sort("published_at", DESCENDING).limit(limit))
        return [_to_article_record(d) for d in docs]

    @staticmethod
    def upsert_articles(domain: str, query_term: str | None, articles: list[dict]) -> int:
        """Insert new articles (unique by URL). Returns count inserted."""
        db = _get_db()
        inserted = 0
        for a in articles:
            if not isinstance(a, dict):
                continue
            url = (a.get("url") or "").strip()
            title = (a.get("title") or "").strip()
            if not url or not title:
                continue

            published_at = a.get("published_at")
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except ValueError:
                    published_at = None

            now = datetime.utcnow()
            result = db.articles.update_one(
                {"url": url},
                {
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "fetched_at": now,
                    },
                    "$set": {
                        "domain": domain,
                        "query_term": query_term,
                        "title": title,
                        "source": (a.get("source") or None),
                        "published_at": published_at,
                        "description": (a.get("description") or None),
                        "content": (a.get("content") or None),
                    },
                },
                upsert=True,
            )
            if result.upserted_id is not None:
                inserted += 1

        return inserted
