from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import sqlite3
from config import config

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    subscription_plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    alerts = relationship("Alert", back_populates="user")

class App(Base):
    __tablename__ = "apps"
    
    id = Column(Integer, primary_key=True, index=True)
    app_store_id = Column(String(100), unique=True, index=True)
    title = Column(String(255), nullable=False)
    developer = Column(String(255))
    category = Column(String(100))
    country = Column(String(10))
    icon_url = Column(String(500))
    description = Column(Text)
    release_date = Column(DateTime)
    current_rank = Column(Integer)
    previous_rank = Column(Integer)
    rank_velocity = Column(Float, default=0.0)
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    reviews = relationship("Review", back_populates="app")
    iap_products = relationship("IAPProduct", back_populates="app")
    scores = relationship("Score", back_populates="app")
    clones = relationship("Clone", foreign_keys="Clone.app_id", back_populates="app")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    country = Column(String(10))
    
    app = relationship("App", back_populates="reviews")

class IAPProduct(Base):
    __tablename__ = "iap_products"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_id = Column(String(255))
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    category = Column(String(100))
    
    app = relationship("App", back_populates="iap_products")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    event_type = Column(String(100))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    description = Column(Text)
    source = Column(String(100))
    region = Column(String(100))
    tags = Column(JSON)

class SteamGame(Base):
    __tablename__ = "steam_games"
    
    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(50), unique=True, index=True)
    title = Column(String(255), nullable=False)
    developer = Column(String(255))
    publisher = Column(String(255))
    release_date = Column(DateTime)
    genre = Column(String(255))
    tags = Column(JSON)
    price = Column(Float)
    discount_percent = Column(Float, default=0.0)
    review_score = Column(Float)
    review_count = Column(Integer, default=0)
    hype_score = Column(Float, default=0.0)
    player_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class Clone(Base):
    __tablename__ = "clones"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    matched_app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    similarity_type = Column(String(50))  # icon, title, description, theme
    detection_date = Column(DateTime(timezone=True), server_default=func.now())
    
    app = relationship("App", foreign_keys=[app_id], back_populates="clones")
    matched_app = relationship("App", foreign_keys=[matched_app_id])

class Score(Base):
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    success_score = Column(Float, nullable=False)  # 0-100
    breakdown = Column(JSON)  # Detailed scoring breakdown
    model_version = Column(String(50))
    prediction_confidence = Column(Float)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    app = relationship("App", back_populates="scores")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition_json = Column(JSON, nullable=False)  # Alert conditions
    alert_type = Column(String(50))  # rank_change, new_app, score_threshold
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="alerts")

class Database:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def close_session(self, session):
        session.close()

# Global database instance
database = Database()