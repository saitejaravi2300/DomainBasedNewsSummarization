import os
import asyncio
import sys

# Forces UTF-8 for stdout
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ['DB_MIN_ARTICLES_THRESHOLD'] = '200'
os.environ['DB_FIRST_ONLY_MODE'] = 'true'

async def run_test():
    try:
        import main
        from database import ArticleRepository
        
        topic = 'ai'
        days = 14
        
        before_articles = ArticleRepository.get_recent_articles(topic, days, limit=500)
        before_count = len(before_articles)
        
        # main._fetch_articles_for_digest is an async function
        fetched_count = await main._fetch_articles_for_digest(topic, days, None)
        
        after_articles = ArticleRepository.get_recent_articles(topic, days, limit=500)
        after_count = len(after_articles)
        
        print(f"RESULTS_START")
        print(f"Before count: {before_count}")
        print(f"Fetched count from function: {fetched_count}")
        print(f"After count: {after_count}")
        print(f"After >= Before: {after_count >= before_count}")
        print(f"Function returned non-zero: {fetched_count > 0}")
        print(f"RESULTS_END")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run_test())
