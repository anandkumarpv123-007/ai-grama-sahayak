from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.database.session import Base


class EligibilityAudit(Base):
    __tablename__ = "eligibility_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scheme_id = Column(String(64), index=True, nullable=False)
    status = Column(String(32), nullable=False)
    language = Column(String(8), nullable=False)
    missing_fields = Column(JSON, nullable=True)
    evaluated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
