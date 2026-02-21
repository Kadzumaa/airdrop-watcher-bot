from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from app.data.db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    status = Column(String(64), default="watch", nullable=False)
    chain = Column(String(64), default="", nullable=False)
    links_json = Column(Text, default="{}", nullable=False)  # {"website": "...", "docs": "...", "x": "...", "discord": "...", "github": "...", "coingecko_id": "..."}
    muted = Column(Integer, default=0, nullable=False)  # 0/1
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    project_name = Column(String(200), nullable=False)
    signal_type = Column(String(64), nullable=False)  # funding/doc/market/dropsearn/github/social
    title = Column(String(300), nullable=False)
    url = Column(Text, default="", nullable=False)
    evidence_json = Column(Text, default="{}", nullable=False)  # structured payload
    confidence = Column(Float, default=3.0, nullable=False)
    dedup_key = Column(String(300), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
