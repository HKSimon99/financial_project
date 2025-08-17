"""metric aggregates materialized view

Revision ID: 0002
Revises: 0001
Create Date: 2024-08-20
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW metric_aggregates AS
        SELECT DISTINCT ON (company_id, name)
            id,
            company_id,
            name,
            value,
            as_of
        FROM metrics
        ORDER BY company_id, name, as_of DESC;
        """
    )
    op.create_index(
        "ix_metric_aggregates_company_id",
        "metric_aggregates",
        ["company_id"],
    )
    op.create_index(
        "ix_metric_aggregates_name",
        "metric_aggregates",
        ["name"],
    )


def downgrade() -> None:
    op.drop_index("ix_metric_aggregates_name", table_name="metric_aggregates")
    op.drop_index("ix_metric_aggregates_company_id", table_name="metric_aggregates")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS metric_aggregates")
