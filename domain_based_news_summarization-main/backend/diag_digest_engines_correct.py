import asyncio
from main import _fetch_articles_for_digest, DomainNewsNLPPipeline, generate_real_digest, MIN_CLUSTER_SIZE

async def run(days):
    print(f"\n--- Running for days={days} ---")
    articles, label, normalized_days = await _fetch_articles_for_digest('ai', days, None)
    pipeline = DomainNewsNLPPipeline()
    clustered = pipeline.cluster_articles(articles)
    cluster_sizes = sorted([len(v) for v in clustered.values()], reverse=True)
    valid_clusters = sum(1 for v in clustered.values() if len(v) >= MIN_CLUSTER_SIZE)
    
    print(f"Days: {days}")
    print(f"Articles: {len(articles)}")
    print(f"Cluster count: {len(clustered)}")
    print(f"Cluster sizes: {cluster_sizes}")
    print(f"Valid clusters (>= {MIN_CLUSTER_SIZE}): {valid_clusters}")
    
    digest = await generate_real_digest('ai', days)
    print(f"Total trends: {len(digest.trends)}")
    print(f"Global summary engine: {digest.summary_engine}")
    engines = [t.summary_engine for t in digest.trends]
    print(f"Trend summary engines: {engines}")

async def main():
    await run(3)
    await run(14)

if __name__ == '__main__':
    asyncio.run(main())
