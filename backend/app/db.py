import logging
import time
from collections.abc import Generator
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Depends
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Parse port and scheme from the database URL
_parsed_url = urlsplit(settings.DATABASE_URL)
if "sqlite" in settings.sync_database_url:
    _connect_args: dict = {"check_same_thread": False, "timeout": 10}
else:
    _connect_args: dict = {"connect_timeout": 10}
    # Port 6543 is Supabase's transaction pooler (PgBouncer/Supavisor transaction mode).
    # In transaction mode, server-side prepared statements are unsupported and cause errors.
    # In psycopg 3, setting prepare_threshold=None disables prepared statements.
    if _parsed_url.port == 6543 or ":6543" in settings.DATABASE_URL:
        _connect_args["prepare_threshold"] = None

# Create SQLModel engine ONCE at startup with connection pooling and quick connect timeout
_engine_kwargs: dict = {
    "echo": (settings.ENVIRONMENT == "development"),
    "pool_pre_ping": True,
    "connect_args": _connect_args,
}

# QueuePool parameters (PostgreSQL / Supabase)
if "sqlite" not in settings.sync_database_url:
    _engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 1800,
    })

engine = create_engine(
    settings.sync_database_url,
    **_engine_kwargs,
)


# Log slow queries taking longer than 300 ms
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_time = getattr(context, "_query_start_time", None)
    if start_time is not None:
        duration_ms = (time.perf_counter() - start_time) * 1000
        if duration_ms > 300:
            logger.warning(
                "SLOW QUERY (%.2f ms): %s",
                duration_ms,
                statement.strip().replace("\n", " ")[:200],
            )


def init_db() -> None:
    """Create all SQLModel tables in the database and ensure latest columns exist."""
    SQLModel.metadata.create_all(engine)
    if "sqlite" not in str(engine.url).lower():
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE job_openings ADD COLUMN IF NOT EXISTS pass_mark integer DEFAULT 80;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS review_status varchar(50) DEFAULT 'pending';"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS review_decision_at timestamptz;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS offer_letter_draft json;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS offer_letter_status varchar(50);"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS offer_letter_sent_at timestamptz;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS auto_reply_sent boolean NOT NULL DEFAULT false;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS auto_reply_status varchar(50);"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS auto_reply_error text;"))
            conn.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS auto_reply_sent_at timestamptz;"))
            conn.execute(text("ALTER TABLE google_accounts ADD COLUMN IF NOT EXISTS auto_reply_enabled boolean NOT NULL DEFAULT false;"))
            conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS channel varchar(30) DEFAULT 'email';"))
            conn.execute(text("ALTER TABLE scheduling_links ADD COLUMN IF NOT EXISTS round_type varchar(64) DEFAULT 'initial';"))
            conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS round_type varchar(64) DEFAULT 'initial';"))
            conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS result_status varchar(32);"))
            conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS feedback text;"))
            conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS result_recorded_at timestamptz;"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_settings (
                    id uuid PRIMARY KEY,
                    user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    is_paused boolean NOT NULL DEFAULT false,
                    paused_at timestamptz,
                    paused_reason text,
                    daily_send_limit integer NOT NULL DEFAULT 50,
                    notify_email varchar(320),
                    notify_on_booking boolean NOT NULL DEFAULT true,
                    notify_on_reply boolean NOT NULL DEFAULT true,
                    notify_on_failure boolean NOT NULL DEFAULT true,
                    daily_summary_enabled boolean NOT NULL DEFAULT true,
                    daily_summary_time varchar(10) NOT NULL DEFAULT '09:00',
                    last_daily_summary_sent_at timestamptz,
                    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))
            # Performance optimization indexes (Task 3: candidate_id, user_id, status, created_at, updated_at, stage)
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_candidate_user_created ON messages (candidate_id, user_id, created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_user_created ON messages (user_id, created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_user_created ON candidates (user_id, created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_user_updated ON candidates (user_id, updated_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_user_stage ON candidates (user_id, stage);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_user_review_status ON candidates (user_id, review_status);"))
            conn.commit()


def get_session() -> Generator[Session, None, None]:
    """Yield a database session per request."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
