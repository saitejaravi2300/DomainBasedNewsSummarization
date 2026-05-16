#!/usr/bin/env python3
"""Bulk-ingest news articles into MongoDB to reduce API calls during digest generation."""

import argparse
import asyncio
from datetime import datetime

from database import ArticleRepository
from main import DOMAIN_QUERIES, _build_news_query, fetch_news_from_newsapi, fetch_news_from_gnews


def _normalize_for_upsert(raw_articles: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for a in raw_articles:
        normalized.append(
            {
                "title": a.get("title", ""),
                "source": a.get("source", "Unknown"),
                "url": a.get("url", ""),
                "published_at": a.get("published", ""),
                "description": a.get("description", ""),
                "content": a.get("content", ""),
            }
        )
    return normalized


async def seed_domain(domain: str, days: int) -> dict:
    query = _build_news_query(domain=domain, custom_keywords=None)

    newsapi_articles = await fetch_news_from_newsapi(query, days)
    gnews_articles = await fetch_news_from_gnews(query, days)
    combined = _normalize_for_upsert(newsapi_articles + gnews_articles)

    inserted = ArticleRepository.upsert_articles(
        domain=domain,
        query_term=query,
        articles=combined,
    )

    recent_count = len(ArticleRepository.get_recent_articles(domain=domain, days=days, limit=500))
    return {
        "domain": domain,
        "fetched": len(combined),
        "inserted": inserted,
        "recent_in_db": recent_count,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MongoDB articles for domains.")
    parser.add_argument("--days", type=int, default=14, help="Lookback window in days")
    parser.add_argument(
        "--domains",
        type=str,
        default=",".join(sorted(DOMAIN_QUERIES.keys())),
        help="Comma-separated domains (default: all configured domains)",
    )
    args = parser.parse_args()

    domains = [d.strip().lower() for d in args.domains.split(",") if d.strip()]
    started = datetime.utcnow()

    print(f"Starting article seed for {len(domains)} domains, days={args.days}")
    totals = {"fetched": 0, "inserted": 0}

    for domain in domains:
        try:
            result = await seed_domain(domain, args.days)
            totals["fetched"] += result["fetched"]
            totals["inserted"] += result["inserted"]
            print(
                f"[{domain}] fetched={result['fetched']} inserted={result['inserted']} recent_in_db={result['recent_in_db']}"
            )
        except Exception as exc:
            print(f"[{domain}] failed: {exc}")

    elapsed = (datetime.utcnow() - started).total_seconds()
    print(
        f"Done in {elapsed:.1f}s | total_fetched={totals['fetched']} total_inserted={totals['inserted']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
