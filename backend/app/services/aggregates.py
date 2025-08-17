from sqlalchemy import text

from ..db import engine


def refresh_metric_aggregates() -> None:
    """Refresh the materialized view with latest metrics."""
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY metric_aggregates"))
