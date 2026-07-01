 # app/database.py

from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./financegpt.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    ntfy_topic = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete")
    portfolio = relationship("PortfolioPosition", back_populates="user", cascade="all, delete")
    alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete")


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="watchlist")


class PortfolioPosition(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="portfolio")


class PriceAlert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    target_price = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    fired = Column(Boolean, default=False)
    fired_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="alerts")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()