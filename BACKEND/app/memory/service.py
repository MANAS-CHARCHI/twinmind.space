import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import MemoryVector

async def store_embedding(
    db: AsyncSession, 
    user_id: str, 
    text: str, 
    source_type: str, 
    source_id: str
):
    # 1. Get embedding from Ollama (Async)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://192.168.0.220:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=30.0
        )
        embedding_data = response.json()["embedding"]

    # 2. Create the record
    new_memory = MemoryVector(
        user_id=user_id,
        content=text,
        embedding=embedding_data,
        source_type=source_type,
        source_id=source_id
    )

    # 3. Add to DB
    db.add(new_memory)
    await db.commit()
    await db.refresh(new_memory)
    return new_memory