"""Seed company names into the database."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, insert

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_FILE = BASE_DIR / "seeds" / "seed_companies_kr_en.json"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    metadata = MetaData()

    companies = Table(
        "companies",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String, nullable=False),
        Column("ticker", String, nullable=False, unique=True),
        Column("exchange", String),
        Column("country", String),
        Column("sector", String),
        Column("aliases", JSONB),
        Column("popularity", Float, server_default="0"),
        Column(
            "updated_at",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        ),
        extend_existing=True,
    )
    metadata.create_all(engine)

    with SEED_FILE.open(encoding="utf-8") as f:
        records = json.load(f)

    with engine.begin() as conn:
        for record in records:
            aliases = record.get("aliases")
            if aliases and isinstance(aliases, list):
                record["aliases"] = aliases
            stmt = insert(companies).values(**record)
            update_cols = {k: stmt.excluded[k] for k in record.keys() if k != "id"}
            stmt = stmt.on_conflict_do_update(
                index_elements=[companies.c.ticker], set_=update_cols
            )
            conn.execute(stmt)


if __name__ == "__main__":
    main()
