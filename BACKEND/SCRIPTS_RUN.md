<!-- Scripts run initialy -->

uv add fastapi uvicorn[standard] pydantic python-dotenv sqlalchemy asyncpg psycopg[binary] alembic pgvector apscheduler python-jose[cryptography] passlib[bcrypt] redis httpx authlib google-auth langchain langgraph python-multipart pypdf python-docx pillow

<!-- Run once at begging to create  the migration file alembic migration -->
alembic init migrations

<!-- generate migration -->
alembic revision --autogenerate -m "create_memory_vectors"

<!-- applies all outstanding, unapplied migration scripts to your database, ensuring your database schema is brought to the latest available version -->
alembic upgrade head


<!-- Call ollama -->
curl -X POST http://192.168.0.220:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:3b","prompt":"Hello","stream":false}'

<!-- RUN BACKEND -->
uvicorn app.main:app --reload

