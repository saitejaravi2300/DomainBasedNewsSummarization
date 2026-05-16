import asyncio
import sys
import os

# Ensure the backend directory is in the path for imports
sys.path.append(os.getcwd())

try:
    from main import (
        generate_real_digest, 
        _fetch_articles_for_digest, 
        DomainNewsNLPPipeline, 
        MIN_CLUSTER_SIZE
    )
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def main():
    for days in [3, 14]:
        print(f"\n--- Testing for {days} days ---")
        try:
            # a) fetch
            articles = await _fetch_articles_for_digest('ai', days, None)
            article_count = len(articles)
            
            # b) print article_count
            print(f"Article count: {article_count}")
            
            if article_count == 0:
                print("No articles found, skipping clustering and digest.")
                continue

            # c) cluster
            pipeline = DomainNewsNLPPipeline()
            clusters = pipeline.cluster_articles(articles)
            
            # d) print cluster info
            cluster_count = len(clusters)
            cluster_sizes = sorted([len(c) for c in clusters], reverse=True)
            min_size_count = len([s for s in cluster_sizes if s >= MIN_CLUSTER_SIZE])
            
            print(f"Cluster count: {cluster_count}")
            print(f"Sorted cluster sizes: {cluster_sizes}")
            print(f"Clusters >= MIN_CLUSTER_SIZE ({MIN_CLUSTER_SIZE}): {min_size_count}")
            
            # e) generate digest
            digest = await generate_real_digest('ai', days)
            
            # f) print digest info
            if digest:
                total_trends = len(digest.trends)
                print(f"Total trends: {total_trends}")
                print(f"Digest summary_engine: {digest.summary_engine}")
                
                trend_engines = [t.summary_engine for t in digest.trends]
                print(f"Per-trend summary_engine list: {trend_engines}")
            else:
                print("Digest generation returned None (possibly no trends found).")
                
        except Exception as e:
            print(f"Error during processing {days} days: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
