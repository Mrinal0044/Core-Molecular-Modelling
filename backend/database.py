from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# Database URL from environment (Render/Neon) or fallback to local SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'quantum_pharmx.db')
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Neon Postgres URLs often start with postgres://, but SQLAlchemy needs postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Only use check_same_thread for SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    company_address = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, nullable=False)
    whatsapp = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="owner")
    otps = relationship("OTPRequest", back_populates="user")


class OTPRequest(Base):
    __tablename__ = "otp_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, index=True, nullable=False)
    otp = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="otps")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    data = Column(Text, nullable=False) # Store JSON string of the form data
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="submissions")


class DockingJob(Base):
    __tablename__ = "docking_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="Pending") # Pending, Processing, Completed, Failed
    result_data = Column(Text, nullable=True) # JSON results
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class BindingAffinityPrediction(Base):
    __tablename__ = "binding_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    smiles = Column(String, nullable=False)
    protein_sequence = Column(Text, nullable=False)
    affinity_score = Column(String, nullable=True)
    confidence_score = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
