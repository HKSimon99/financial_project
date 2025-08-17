"""Seed company names into the database."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import insert

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
        Column("name_kr", String, unique=True, nullable=False),
        Column("name_en", String, nullable=False),
        extend_existing=True,
    )
    metadata.create_all(engine)

    with SEED_FILE.open(encoding="utf-8") as f:
        records = json.load(f)

    with engine.begin() as conn:
        for record in records:
            stmt = insert(companies).values(**record)
            stmt = stmt.on_conflict_do_update(
                index_elements=[companies.c.name_kr],
                set_={"name_en": stmt.excluded.name_en},
            )
            conn.execute(stmt)


if __name__ == "__main__":
    main()
