import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.memory.models import MemoryVector
from app.core.config import settings
from app.services.call_llm_sequence import answer_me_twinmind

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
            f"{settings.LLM_API_ADDRESS}/api/embeddings",
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

async def ask_memory(db: AsyncSession, user_id: str, question: str):
    #Convert Question to Vector
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{settings.LLM_API_ADDRESS}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt":question}
        )
        question_vector = res.json()["embedding"]

    # Find the top 3 most relevant snippets for this user
    THRESHOLD = 0.5
    distance_score = MemoryVector.embedding.cosine_distance(question_vector)
    stmt = (
        select(MemoryVector.content)
        .filter(MemoryVector.user_id == user_id, distance_score < THRESHOLD)
        .order_by(distance_score)
        .limit(3)
    )
    result = await db.execute(stmt)
    context_chunks = result.scalars().all()
    context_text = "\n\n".join(context_chunks)

    answer= await answer_me_twinmind(context_text, question)
    return answer