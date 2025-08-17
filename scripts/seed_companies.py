"""Seed company names into the database with aliases and search terms."""

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
    inspect,
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
        Column("name_en", String, nullable=False),
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

    search_terms = Table(
        "search_terms",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("company_id", Integer, nullable=False),
        Column("term", String, nullable=False),
        Column("weight", Float, server_default="1"),
        extend_existing=True,
    )

    metadata.create_all(engine, tables=[companies])

    with SEED_FILE.open(encoding="utf-8") as f:
        records = json.load(f)

    with engine.begin() as conn:
        insp = inspect(conn)
        has_search_terms = "search_terms" in insp.get_table_names()
        if has_search_terms:
            search_terms.create(conn, checkfirst=True)

        for record in records:
            raw_aliases = record.get("aliases", [])
            alias_terms = []
            alias_strings = []
            for alias in raw_aliases:
                if isinstance(alias, dict):
                    term = alias.get("term")
                    weight = float(alias.get("weight", 1))
                    if term:
                        alias_terms.append({"term": term, "weight": weight})
                        alias_strings.append(term)
                else:
                    alias_terms.append({"term": alias, "weight": 1.0})
                    alias_strings.append(alias)
            record["aliases"] = alias_strings

            stmt = insert(companies).values(**record)
            update_cols = {k: stmt.excluded[k] for k in record.keys() if k != "id"}
            stmt = stmt.on_conflict_do_update(
                index_elements=[companies.c.ticker], set_=update_cols
            ).returning(companies.c.id)
            company_id = conn.execute(stmt).scalar_one()

            if has_search_terms:
                for term in alias_terms:
                    st_stmt = insert(search_terms).values(
                        company_id=company_id,
                        term=term["term"],
                        weight=term["weight"],
                    )
                    st_stmt = st_stmt.on_conflict_do_update(
                        index_elements=[
                            search_terms.c.company_id,
                            search_terms.c.term,
                        ],
                        set_={"weight": st_stmt.excluded.weight},
                    )
                    conn.execute(st_stmt)


if __name__ == "__main__":
    main()
