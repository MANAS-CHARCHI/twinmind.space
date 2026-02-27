from sqlalchemy.orm import Session
from app.memory.models import EmailEmbedding
from app.db.models.user_model import UserEmails
from app.db.session import engine

async def process_email_to_vector(db: Session, email_id: int):
    email = db.query(UserEmails).filter(UserEmails.id == email_id).first()
    if not email or email.is_processed:
        return

    # 1. Simple Chunking (Keep it around 500 chars for better retrieval)
    chunks = [email.body_plain[i:i+500] for i in range(0, len(email.body_plain), 400)]

    for chunk in chunks:
        vector = engine.generate(chunk)
        
        new_embedding = EmailEmbedding(
            email_id=email.id,
            user_id=email.user_id,
            embedding=vector,
            content_chunk=chunk
        )
        db.add(new_embedding)

    email.is_processed = True
    db.commit()