"""create core tables

Revision ID: 0001
Revises: 
Create Date: 2024-08-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("exchange", sa.String()),
        sa.Column("country", sa.String()),
        sa.Column("sector", sa.String()),
        sa.Column("aliases", postgresql.JSONB(), nullable=True),
        sa.Column("popularity", sa.Float(), server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_companies_name_trgm",
        "companies",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_companies_aliases_gin",
        "companies",
        ["aliases"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_companies_ticker",
        "companies",
        ["ticker"],
        unique=True,
    )

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False
        ),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_watchlists_company_id",
        "watchlists",
        ["company_id"],
    )

    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metrics_company_id", "metrics", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_metrics_company_id", table_name="metrics")
    op.drop_table("metrics")
    op.drop_index("ix_watchlists_company_id", table_name="watchlists")
    op.drop_table("watchlists")
    op.drop_index("ix_companies_aliases_gin", table_name="companies")
    op.drop_index("ix_companies_name_trgm", table_name="companies")
    op.drop_index("ix_companies_ticker", table_name="companies")
    op.drop_table("companies")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
