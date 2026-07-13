import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class DockingJob(Base):
    __tablename__ = "docking_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    protein_path = Column(String, nullable=False)
    ligand_path = Column(String, nullable=False)
    status = Column(String, default="Pending", nullable=False)  # Pending, Running, Completed, Failed
    score = Column(Float, nullable=True)  # Best docking score
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    output_directory = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="docking_jobs")
