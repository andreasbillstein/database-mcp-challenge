import unittest
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa

from db_mcp_server.backends.sqlalchemy import SQLAlchemyBackend


@pytest.fixture
def database(tmp_path: Path) -> Iterator[str]:
    url = f"sqlite:///{tmp_path}/test.db"
    setup_engine = sa.create_engine(url)
    try:
        metadata = sa.MetaData()

        sa.Table(
            "users",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Index("ix_users_name", "name"),
        )

        sa.Table(
            "orders",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("users.id", name="fk_orders_user_id"),
                nullable=False,
            ),
            sa.Column("amount_cents", sa.Integer, nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Index("ix_orders_user_id", "user_id"),
        )

        metadata.create_all(setup_engine)
        yield url
    finally:
        setup_engine.dispose()


USERS_ROWS = [
    {"id": 1, "email": "alice@example.com", "name": "Alice"},
    {"id": 2, "email": "bob@example.com", "name": "Bob"},
]

ORDERS_ROWS = [
    {"id": 1, "user_id": 1, "amount_cents": 500, "status": "paid"},
    {"id": 2, "user_id": 1, "amount_cents": 1500, "status": "pending"},
    {"id": 3, "user_id": 2, "amount_cents": 2000, "status": "paid"},
]


@pytest.fixture
def sample_rows(database: str) -> dict[str, list[dict]]:
    setup_engine = sa.create_engine(database)
    md = sa.MetaData()
    md.reflect(bind=setup_engine)
    with setup_engine.begin() as conn:
        conn.execute(md.tables["users"].insert(), USERS_ROWS)
        conn.execute(md.tables["orders"].insert(), ORDERS_ROWS)
    setup_engine.dispose()
    return {"users": USERS_ROWS, "orders": ORDERS_ROWS}


def test_sqlalchemy_backend_execute_query(database: str, sample_rows: dict[str, list[dict]]):
    backend = SQLAlchemyBackend(engine=sa.create_engine(database))
    unittest.TestCase().assertCountEqual(
        backend.execute_query("SELECT * FROM users ORDER BY id"), sample_rows["users"]
    )


def test_sqlalchemy_backend_list_tables(database: str):
    backend = SQLAlchemyBackend(engine=sa.create_engine(database))
    unittest.TestCase().assertCountEqual(backend.list_tables(), ["users", "orders"])
