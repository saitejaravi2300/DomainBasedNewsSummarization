#!/usr/bin/env python3
"""
Test MongoDB connection and repository operations.
"""

from datetime import datetime
import sys

try:
    from database import _get_db, UserRepository, ArticleRepository
except Exception as exc:
    print(f"Import error: {exc}")
    sys.exit(1)


def test_mongodb_ping() -> bool:
    try:
        db = _get_db()
        db.command("ping")
        print("MongoDB ping: OK")
        return True
    except Exception as exc:
        print(f"MongoDB ping failed: {exc}")
        return False


def test_user_repository() -> bool:
    email = f"diag_{int(datetime.utcnow().timestamp())}@example.com"
    try:
        user = UserRepository.create_user(email=email, name="Diag User", password_hash="hashed")
        fetched = UserRepository.get_user_by_email(email)
        ok = fetched is not None and fetched.id == user.id
        print("User repository:", "OK" if ok else "FAILED")
        return ok
    except Exception as exc:
        print(f"User repository failed: {exc}")
        return False


def test_article_upsert() -> bool:
    try:
        inserted = ArticleRepository.upsert_articles(
            domain="ai",
            query_term="artificial intelligence",
            articles=[
                {
                    "title": "Diagnostic article",
                    "source": "diag-source",
                    "url": f"https://example.com/diag-{int(datetime.utcnow().timestamp())}",
                    "published_at": datetime.utcnow().isoformat(),
                    "description": "Diagnostic description",
                    "content": "Diagnostic content",
                }
            ],
        )
        recent = ArticleRepository.get_recent_articles(domain="ai", days=7, limit=5)
        ok = inserted >= 1 and len(recent) >= 1
        print("Article upsert/get:", "OK" if ok else "FAILED")
        return ok
    except Exception as exc:
        print(f"Article repository failed: {exc}")
        return False


if __name__ == "__main__":
    checks = [test_mongodb_ping(), test_user_repository(), test_article_upsert()]
    passed = sum(1 for c in checks if c)
    print(f"Passed {passed}/{len(checks)} checks")
    sys.exit(0 if all(checks) else 1)
