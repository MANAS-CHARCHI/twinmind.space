<!-- Scripts run initialy -->

uv add fastapi uvicorn[standard] pydantic python-dotenv sqlalchemy asyncpg psycopg[binary] alembic pgvector apscheduler python-jose[cryptography] passlib[bcrypt] redis httpx authlib google-auth langchain langgraph python-multipart pypdf python-docx pillow

<!-- Run alembic migration -->
alembic init migrations

<!-- applies all outstanding, unapplied migration scripts to your database, ensuring your database schema is brought to the latest available version -->
alembic upgrade head


<!-- RUN BACKEND -->
uvicorn app.main:app --reload