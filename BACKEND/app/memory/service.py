import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.memory.models import MemoryVector
from app.core.config import settings
from app.services.llm import answer_me_llama, answer_me_gemini
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

    # Generate Answer with the model

    # prompt = f"""
    # You are the user's Digital Twin. 
    # Give a direct, concise answer. 
    # DO NOT use introductory phrases like "I'd be happy to," "As an AI," or "Based on the information provided."
    # DO NOT mention "TwinMind AI."
    # Just provide the facts from the context.
    # CONTEXT:
    # {context_text}
    # QUESTION:
    # {question}
    # ANSWER:
    # """
    # async with httpx.AsyncClient() as client:
    #     llm_res = await client.post(
    #         f"{settings.LLM_API_ADDRESS}/api/generate",
    #         json={
    #             "model": "llama3.2:3b",
    #             "prompt": prompt,
    #             "stream": False
    #         },
    #         timeout=60.0
    #     )
    #     return llm_res.json().get("response").strip()

    answer= await answer_me_twinmind(context_text, question)
    return answer