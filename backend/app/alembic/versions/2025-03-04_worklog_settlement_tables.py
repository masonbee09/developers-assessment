"""Worklog settlement tables

Revision ID: 20250304a001
Revises: 1a31ce608336
Create Date: 2025-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20250304a001"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "remittance",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_remittance_user_id"), "remittance", ["user_id"])
    op.create_index(op.f("ix_remittance_status"), "remittance", ["status"])
    op.create_index(op.f("ix_remittance_created_at"), "remittance", ["created_at"])

    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("remittance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["remittance_id"], ["remittance.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_user_id"), "worklog", ["user_id"])
    op.create_index(op.f("ix_worklog_remittance_id"), "worklog", ["remittance_id"])
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"])

    op.create_table(
        "time_segment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_time_segment_worklog_id"), "time_segment", ["worklog_id"])
    op.create_index(op.f("ix_time_segment_created_at"), "time_segment", ["created_at"])

    op.create_table(
        "adjustment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_adjustment_worklog_id"), "adjustment", ["worklog_id"])
    op.create_index(op.f("ix_adjustment_created_at"), "adjustment", ["created_at"])


def downgrade():
    op.drop_index(op.f("ix_adjustment_created_at"), table_name="adjustment")
    op.drop_index(op.f("ix_adjustment_worklog_id"), table_name="adjustment")
    op.drop_table("adjustment")
    op.drop_index(op.f("ix_time_segment_created_at"), table_name="time_segment")
    op.drop_index(op.f("ix_time_segment_worklog_id"), table_name="time_segment")
    op.drop_table("time_segment")
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_remittance_id"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_user_id"), table_name="worklog")
    op.drop_table("worklog")
    op.drop_index(op.f("ix_remittance_created_at"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_status"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_user_id"), table_name="remittance")
    op.drop_table("remittance")
