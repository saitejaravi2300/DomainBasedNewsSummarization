from database import _get_db, ArticleRepository
from datetime import datetime, timedelta

def diag():
    db = _get_db()
    try:
        db.command("ping")
        print("Mongo ping: OK")
    except Exception as e:
        print(f"Mongo ping: FAILED ({e})")

    domains = ["ai", "geopolitics", "market-finance"]
    
    for domain in domains:
        print(f"\n--- Domain: {domain} ---")
        articles = ArticleRepository.get_recent_articles(domain=domain, days=30)
        print(f"Article count: {len(articles)}")
        
    print("\nDigest engine: Gemini (default configuration)")
    print("Per-trend engines: Gemini (default configuration)")
    print("Cluster sizes: N/A (pipeline import issue)")
    print("Total trends: N/A (pipeline import issue)")

if __name__ == '__main__':
    diag()
