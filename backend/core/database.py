from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from core.config import settings

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(String(64), primary_key=True, index=True)
    teacher_id = Column(String(64), default="teacher_1", index=True)
    title = Column(String(255), default="Classroom Session")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Relationships
    persons = relationship("PersonModel", back_populates="session", cascade="all, delete-orphan")
    person_metrics = relationship("PersonMetricModel", back_populates="session", cascade="all, delete-orphan")
    audio_metrics = relationship("AudioMetricModel", back_populates="session", cascade="all, delete-orphan")
    suggestions = relationship("SuggestionModel", back_populates="session", cascade="all, delete-orphan")

class PersonModel(Base):
    __tablename__ = "persons"
    
    id = Column(String(64), primary_key=True, index=True) # e.g. "person_1"
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    label = Column(String(100), default="Student") # Anonymized: Student_01
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    presence_seconds = Column(Float, default=0.0)
    attendance_status = Column(String(32), default="Absent") # "Present", "Partial", "Absent"
    
    session = relationship("SessionModel", back_populates="persons")

class PersonMetricModel(Base):
    __tablename__ = "person_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    person_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    attention = Column(Float, default=0.0) # 0 to 100
    engagement_label = Column(String(32), default="neutral") # focused, distracted, inactive
    movement = Column(Float, default=0.0) # 0 to 100
    
    session = relationship("SessionModel", back_populates="person_metrics")

class AudioMetricModel(Base):
    __tablename__ = "audio_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    noise_db = Column(Float, default=-40.0)
    speech_ratio = Column(Float, default=0.0)
    state = Column(String(32), default="silence") # silence, background noise, active speech
    
    session = relationship("SessionModel", back_populates="audio_metrics")

class SuggestionModel(Base):
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    type = Column(String(32), default="info") # alert, warning, info
    message = Column(Text, nullable=False)
    rule_id = Column(String(64), nullable=False) # e.g. "RULE_SUSTAINED_DISENGAGEMENT"
    
    session = relationship("SessionModel", back_populates="suggestions")

# Engine & Session Setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
