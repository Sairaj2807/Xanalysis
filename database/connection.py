from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import DDL, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base, ModelPrediction

# Immutability of stored forecasts: prediction fields can never change and rows can never be deleted.
# Only the actual_* outcome columns may be filled in later (when the outcome becomes known).
SQLITE_IMMUTABLE_TRIGGERS = [
    DDL("""CREATE TRIGGER IF NOT EXISTS trg_pred_no_delete BEFORE DELETE ON model_predictions
           BEGIN SELECT RAISE(ABORT, 'model_predictions is append-only'); END;"""),
    DDL("""CREATE TRIGGER IF NOT EXISTS trg_pred_no_update BEFORE UPDATE ON model_predictions
           WHEN OLD.pred_return IS NOT NEW.pred_return OR OLD.pred_price IS NOT NEW.pred_price
             OR OLD.prediction_ts IS NOT NEW.prediction_ts OR OLD.horizon IS NOT NEW.horizon
             OR OLD.model_name IS NOT NEW.model_name OR OLD.run_id IS NOT NEW.run_id
           BEGIN SELECT RAISE(ABORT, 'forecast fields are immutable'); END;"""),
]
for _ddl in SQLITE_IMMUTABLE_TRIGGERS:
    event.listen(ModelPrediction.__table__, "after_create", _ddl.execute_if(dialect="sqlite"))


def make_engine(url: str):
    if url.startswith("sqlite:///") and ":memory:" not in url:
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _fk(dbapi_conn, _):  # enforce foreign keys on SQLite
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def session_scope(engine):
    """Transactional scope: commit on success, rollback on any error."""
    s: Session = sessionmaker(engine, future=True)()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def insert_ignore_duplicates(session: Session, model, rows: list[dict]) -> int:
    """Idempotent insert (ON CONFLICT DO NOTHING) for SQLite and PostgreSQL. Returns rows actually inserted.
    The PostgreSQL branch is implemented but has NOT been tested against a PostgreSQL server."""
    if not rows:
        return 0
    name = session.get_bind().dialect.name
    if name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
    n_cols = max(len(rows[0]), 1)
    step = max(900 // n_cols, 1)           # stay below SQLite's bound-variable limit
    total = 0
    for i in range(0, len(rows), step):
        res = session.execute(dialect_insert(model).values(rows[i:i + step]).on_conflict_do_nothing())
        total += max(res.rowcount, 0)
    return total
