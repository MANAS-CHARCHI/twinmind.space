from sqlalchemy import Column, Integer, LargeBinary, String, Text, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.session import Base
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    google_refresh_token = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def verify_password(self, plain_password: str):
        """
        Verifies the plain text password against the stored hash.
        """
        return pwd_context.verify(plain_password, self.hashed_password)

class UserEmails(Base):
    __tablename__ = "user_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    message_id = Column(Text, nullable=False)
    subject = Column(Text)
    sender = Column(Text)
    body_plain = Column(Text)
    received_at = Column(DateTime(timezone=True))
    is_processed = Column(Boolean, default=False)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", backref="refresh_tokens")