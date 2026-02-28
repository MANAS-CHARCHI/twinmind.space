import uuid
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from app.db.models.user_model import UserEmails, User

class MemoryVector(Base):
    __tablename__ = "memory_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # The actual text content being embedded
    content = Column(Text, nullable=False)

    # Nomic-embed-text = 768 dimensions
    # 'half_vec' or 'vector' can be used; Vector is standard for pgvector
    embedding = Column(Vector(768)) 

    # Metadata for filtering
    source_type = Column(String, nullable=True) # e.g., 'email', 'linkedin', 'pdf'
    source_id = Column(String, nullable=True)   # e.g., 'msg-123'
    embedding_model = Column(String, nullable=False, default="nomic-embed-text")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmailEmbedding(Base):
    __tablename__ = "email_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(Integer, ForeignKey("user_emails.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    embedding=Column(Vector(768))
    content_chunk = Column(Text)
    