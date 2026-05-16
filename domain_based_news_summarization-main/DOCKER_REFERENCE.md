# Docker & Database Operations Reference

## Start/Stop Services
```bash
# Start containers
cd c:\Users\varun\Downloads\b_CgB7u3mq4m3-1775109640673
docker-compose up -d

# Stop containers
docker-compose down

# Remove volumes (reset database)
docker-compose down -v

# View logs
docker-compose logs --tail=50 postgres
docker-compose logs --tail=50 redis
```

## Direct Container Commands
```bash
# PostgreSQL inside container
docker exec whatsnew_postgres psql -U admin -d whatsnew_db -c "SELECT 1;"

# Redis inside container  
docker exec whatsnew_redis redis-cli PING
docker exec whatsnew_redis redis-cli FLUSHALL
```

## FastAPI Backend
```bash
# Install dependencies (already done)
pip install -q psycopg2-binary sqlalchemy redis asyncpg

# Create database tables (from Python)
python -c "from models import create_tables; create_tables()"

# Test Redis connection
python test_redis.py

# Test PostgreSQL connection (works inside container)
docker exec whatsnew_postgres psql -U admin -d whatsnew_db -c "SELECT 1;"
```

## Connection Details
- **PostgreSQL**
  - Host: localhost (from Windows), whatsnew_postgres (from container)
  - Port: 5432
  - User: admin
  - Password: password123
  - Database: whatsnew_db

- **Redis**
  - Host: localhost (accessible from Windows)
  - Port: 6379
  - No authentication

## Integration Status
- ✓ docker-compose.yml created
- ✓ Containers running and healthy
- ✓ Python packages installed
- ✓ models.py with SQLAlchemy ORM
- ✓ database.py with repository pattern
- ✓ cache.py with Redis CacheManager
- ✓ main.py endpoints integrated with cache/database imports

## Note on Windows Docker
There's a known issue with PostgreSQL authentication from Windows host to Docker container.
Workaround: Test connectivity from inside container or use Redis (which works fine from host).
