"""PostgreSQL 连接池与建表逻辑。"""
import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resume_analyses (
    id BIGSERIAL PRIMARY KEY,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    total_score NUMERIC(5, 2),
    category_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    analysis_text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resume_analyses_resume_id
    ON resume_analyses (resume_id, created_at DESC);

CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    job_title TEXT NOT NULL,
    questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interview_answers (
    id BIGSERIAL PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    question_index INTEGER,
    question TEXT,
    answer_text TEXT NOT NULL,
    score NUMERIC(5, 2),
    feedback TEXT,
    suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE interview_answers
    ADD COLUMN IF NOT EXISTS suggestions JSONB NOT NULL DEFAULT '[]'::jsonb;
"""

_pool = None


def init_db(retries: int = 10, delay: float = 1.5) -> None:
    """建立连接池并确保表结构存在，启动阶段调用。"""
    global _pool
    if _pool is not None:
        return
    if not DATABASE_URL:
        raise RuntimeError("未配置 DATABASE_URL，无法连接 PostgreSQL")

    last_error = None
    for attempt in range(retries):
        try:
            _pool = pool.ThreadedConnectionPool(1, 10, dsn=DATABASE_URL)
            with get_cursor() as cur:
                cur.execute(SCHEMA_SQL)
            return
        except psycopg2.OperationalError as exc:
            last_error = exc
            if _pool is not None:
                _pool.closeall()
                _pool = None
            if attempt < retries - 1:
                time.sleep(delay)

    raise RuntimeError(f"连接 PostgreSQL 失败: {last_error}")


def close_db() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_cursor(commit: bool = True):
    if _pool is None:
        raise RuntimeError("数据库连接池尚未初始化")
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
