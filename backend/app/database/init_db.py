from __future__ import annotations

from sqlalchemy import text
import structlog

from app.database.session import engine
from app.database.models import Base

logger = structlog.get_logger(__name__)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _try_init_timescale()


def _try_init_timescale() -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            conn.execute(
                text(
                    """
                    SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);
                    """
                )
            )
            conn.execute(
                text(
                    """
                    SELECT create_hypertable('anomalies', 'timestamp', if_not_exists => TRUE);
                    """
                )
            )
    except Exception as exc:
        logger.warning("timescaledb_init_skipped", error=str(exc))
