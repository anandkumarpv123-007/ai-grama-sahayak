from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String(64), unique=True, index=True, nullable=False)
    assistant = Column(String(32), nullable=False)
    language = Column(String(8), nullable=False)
    state = Column(String(64), nullable=True)
    district = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
