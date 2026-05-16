#!/usr/bin/env python3
"""Verify DB-first threshold behavior with concise output."""

import argparse
import asyncio
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="ai")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--threshold", type=int, default=15)
    parser.add_argument("--db-first-only", default="true", choices=["true", "false"])
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    os.environ["DB_MIN_ARTICLES_THRESHOLD"] = str(args.threshold)
    os.environ["DB_FIRST_ONLY_MODE"] = args.db_first_only

    from database import ArticleRepository
    from main import _fetch_articles_for_digest

    before_count = len(ArticleRepository.get_recent_articles(args.domain, args.days, limit=1000))
    articles, domain_label, normalized_days = await _fetch_articles_for_digest(args.domain, args.days, None)
    after_count = len(ArticleRepository.get_recent_articles(args.domain, args.days, limit=1000))

    print(f"domain={args.domain} days={normalized_days} label={domain_label}")
    print(f"db_before={before_count}")
    print(f"returned_articles={len(articles)}")
    print(f"db_after={after_count}")
    print(f"db_delta={after_count - before_count}")


if __name__ == "__main__":
    asyncio.run(main())
