"""SQLAlchemy schema (SQLite for dev/tests, PostgreSQL via DATABASE_URL). All timestamps UTC."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (JSON, BigInteger, DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawXPost(Base):
    __tablename__ = "raw_x_posts"
    post_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    asset_symbol: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    text: Mapped[str] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(String(64))
    author_id: Mapped[str | None] = mapped_column(String(32))
    followers_count: Mapped[int | None] = mapped_column(BigInteger)
    likes: Mapped[int | None] = mapped_column(BigInteger)
    reposts: Mapped[int | None] = mapped_column(BigInteger)
    replies: Mapped[int | None] = mapped_column(BigInteger)
    views: Mapped[int | None] = mapped_column(BigInteger)
    language: Mapped[str | None] = mapped_column(String(8))
    query_source: Mapped[str | None] = mapped_column(String(128))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    extra: Mapped[dict | None] = mapped_column(JSON)


class SentimentPrediction(Base):
    __tablename__ = "sentiment_predictions"
    __table_args__ = (UniqueConstraint("post_id", "model_name", name="uq_sent_post_model"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("raw_x_posts.post_id"), index=True)
    model_name: Mapped[str] = mapped_column(String(64))
    p_positive: Mapped[float] = mapped_column(Float)
    p_neutral: Mapped[float] = mapped_column(Float)
    p_negative: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"
    __table_args__ = (UniqueConstraint("symbol", "interval", "bar_start_utc", name="uq_price_bar"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    interval: Mapped[str] = mapped_column(String(4))
    bar_start_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adj_close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)


class NewsArticle(Base):
    __tablename__ = "news_articles"
    article_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    asset: Mapped[str] = mapped_column(String(16), index=True)
    headline: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, unique=True)
    source: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime)
    content: Mapped[str | None] = mapped_column(Text)
    query: Mapped[str | None] = mapped_column(String(256))


class ModelRun(Base):
    __tablename__ = "model_runs"
    run_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    model_name: Mapped[str] = mapped_column(String(64))
    feature_set: Mapped[str] = mapped_column(String(32))
    config: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    artifact_path: Mapped[str | None] = mapped_column(Text)


class ModelPrediction(Base):
    """Append-only: rows are never updated or deleted when models are retrained."""
    __tablename__ = "model_predictions"
    __table_args__ = (
        UniqueConstraint("run_id", "asset", "model_name", "feature_set", "prediction_ts", "horizon", name="uq_pred"),
        Index("ix_pred_ts", "asset", "prediction_ts"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("model_runs.run_id"))
    asset: Mapped[str] = mapped_column(String(16))
    model_name: Mapped[str] = mapped_column(String(64))
    feature_set: Mapped[str] = mapped_column(String(32))
    fold: Mapped[int | None] = mapped_column(Integer)
    prediction_ts: Mapped[datetime] = mapped_column(DateTime)
    horizon: Mapped[int] = mapped_column(Integer)
    pred_return: Mapped[float] = mapped_column(Float)
    pred_price: Mapped[float] = mapped_column(Float)
    actual_return: Mapped[float | None] = mapped_column(Float)
    actual_price: Mapped[float | None] = mapped_column(Float)


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16))
    n_retrieved: Mapped[int] = mapped_column(Integer, default=0)
    n_new: Mapped[int] = mapped_column(Integer, default=0)
    n_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    latest_post_ts: Mapped[datetime | None] = mapped_column(DateTime)
    last_post_id: Mapped[str | None] = mapped_column(String(32))
    error: Mapped[str | None] = mapped_column(Text)
