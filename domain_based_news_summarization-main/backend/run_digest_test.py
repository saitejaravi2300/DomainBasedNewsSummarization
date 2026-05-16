import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from main import _fetch_articles_for_digest, generate_real_digest

async def main():
    try:
        # _fetch_articles_for_digest returns (articles, domain_str, days)
        articles_result = await _fetch_articles_for_digest('ai', 14, None)
        articles = articles_result[0]
        print(f"Article count: {len(articles)}")
        
        digest = await generate_real_digest('ai', 14)
        
        # DigestResponse is likely a Pydantic model based on typical FastAPI apps
        if hasattr(digest, 'dict'):
            d_dict = digest.dict()
        elif hasattr(digest, 'model_dump'):
            d_dict = digest.model_dump()
        else:
            d_dict = digest if isinstance(digest, dict) else vars(digest)
            
        print(f"Total trends: {len(d_dict.get('trends', []))}")
        print(f"Summary engine: {d_dict.get('summary_engine')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
