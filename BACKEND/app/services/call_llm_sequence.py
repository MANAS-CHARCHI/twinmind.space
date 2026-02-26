
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.memory.models import MemoryVector
from app.core.config import settings
import httpx
from app.services.llm import answer_me_llama, answer_me_gemini

async def answer_me_twinmind(context_text: str, question: str) -> str:
    try:
        answer= await answer_me_gemini(context_text, question)
        if answer is not None:
            return answer
        else:
            raise Exception("Gemini returned no answer.")
    except Exception as e:
        try:
            answer= await answer_me_llama(context_text, question)
        except Exception:
            answer="I'm having trouble connecting to my brain right now."
    return answer