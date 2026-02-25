import uuid
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.session import Base  # Import the Base you already created

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