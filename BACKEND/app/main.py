from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.db.session import engine
from sqlalchemy import text
# from app.api.v1.auth import auth_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🤝 Starting TWINMIND API ✨NOW✨")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("🙌 Database connected")
    except Exception as e:
        print("｡°⚠︎°｡Database connection failed:", e)
        raise e
    
    yield

    # Shutdown logic
    print("｡°⚠︎°｡ Shutting down TWINMIND API ✨NOW✨")

def create_application() -> FastAPI:
    app = FastAPI(
        title="TWINMIND API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()