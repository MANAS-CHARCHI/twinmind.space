from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import uuid
from app.db.session import get_db
from app.memory.service import store_embedding, ask_memory

router = APIRouter(
    prefix="/memory",
    tags=["Memory"]
)

class MemoryCreate(BaseModel):
    user_id: uuid.UUID
    text: str
    source_type: str = "manual"
    source_id: str = None

@router.post("/store")
async def store_user_memory(data: MemoryCreate, db: AsyncSession = Depends(get_db)):
    try:
        memory_record = await store_embedding(
            db=db,
            user_id=data.user_id,
            text=data.text,
            source_type=data.source_type,
            source_id=data.source_id or str(uuid.uuid4())
        )
        return {"status": "success", "id": memory_record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class MemoryQuery(BaseModel):
    user_id: uuid.UUID
    question: str

@router.post("/ask")
async def ask_stored_memory(query: MemoryQuery, db: AsyncSession = Depends(get_db)):
    try:
        answer = await ask_memory(db=db, user_id=query.user_id, question=query.question)
        return {"status": "success", "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))