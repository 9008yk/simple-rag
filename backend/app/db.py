import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'processing', 'ready', 'failed')
    ),
    chunk_count INTEGER NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

DOCUMENTS_INDEX_SQL = (
    """
    CREATE INDEX IF NOT EXISTS idx_documents_created_at
    ON documents (created_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_documents_status
    ON documents (status)
    """,
)


# 定义数据目录,默认使用D:\vue3-program\simple-rag\data
def get_data_dir() -> Path:
    return Path(os.getenv("SIMPLE_RAG_DATA_DIR", PROJECT_ROOT / "data"))


# 定义上传文件目录为data/uploads/
def get_upload_dir() -> Path:
    return get_data_dir() / "uploads"


# 定义数据库连接上下文管理器
@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    get_data_dir().mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(get_data_dir() / "app.db")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# 初始化数据库,创建documents表
def init_db() -> None:
    with get_connection() as connection:
        connection.execute(DOCUMENTS_TABLE_SQL)

        for index_sql in DOCUMENTS_INDEX_SQL:
            connection.execute(index_sql)


def migrate_documents_constraints() -> bool:
    """Upgrade the pre-constraint documents table without losing rows."""
    with get_connection() as connection:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'documents'
            """
        ).fetchone()

        if table is None:
            connection.execute(DOCUMENTS_TABLE_SQL)
            for index_sql in DOCUMENTS_INDEX_SQL:
                connection.execute(index_sql)
            return True

        if "UNIQUE" in table["sql"] and "CHECK" in table["sql"]:
            return False

        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(documents)")
        }
        required_columns = {
            "id",
            "filename",
            "file_path",
            "status",
            "chunk_count",
            "error_message",
            "created_at",
            "updated_at",
        }
        if not required_columns.issubset(existing_columns):
            raise RuntimeError("documents table cannot be migrated safely.")

        legacy_table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'documents_legacy'
            """
        ).fetchone()
        if legacy_table is not None:
            raise RuntimeError("documents_legacy already exists.")

        connection.execute("ALTER TABLE documents RENAME TO documents_legacy")
        connection.execute(DOCUMENTS_TABLE_SQL)
        connection.execute(
            """
            INSERT INTO documents (
                id,
                filename,
                file_path,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            )
            SELECT
                id,
                filename,
                file_path,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            FROM documents_legacy
            """
        )
        connection.execute("DROP TABLE documents_legacy")

        for index_sql in DOCUMENTS_INDEX_SQL:
            connection.execute(index_sql)

    return True


# 创建文档记录
def create_document(*, document_id: str, filename: str, file_path: str, created_at: str):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, filename, file_path, status, chunk_count,
                error_message, created_at, updated_at
            )
            VALUES (?, ?, ?, 'pending', 0, NULL, ?, ?)
            """,
            (document_id, filename, file_path, created_at, created_at),
        )

    return {
        "id": document_id,
        "filename": filename,
        "status": "pending",
        "chunk_count": 0,
        "error_message": None,
        "created_at": created_at,
        "updated_at": created_at,
    }


# 查询所有文档记录
def list_documents() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, status, chunk_count, error_message,
                   created_at, updated_at
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def list_ready_document_ids() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id
            FROM documents
            WHERE status = 'ready'
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [str(row["id"]) for row in rows]


def get_document(document_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                filename,
                file_path,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

    return dict(row) if row else None


def mark_document_processing(document_id: str) -> None:
    _update_document_status(
        document_id,
        status="processing",
        chunk_count=0,
        error_message=None,
    )


def mark_document_ready(document_id: str, *, chunk_count: int) -> None:
    _update_document_status(
        document_id,
        status="ready",
        chunk_count=chunk_count,
        error_message=None,
    )


def mark_document_failed(document_id: str, *, error_message: str) -> None:
    _update_document_status(
        document_id,
        status="failed",
        chunk_count=0,
        error_message=error_message,
    )


def recover_interrupted_documents() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE documents
            SET status = 'failed',
                error_message = 'Processing was interrupted by a service restart.',
                updated_at = ?
            WHERE status = 'processing'
            """,
            (timestamp,),
        )

    return cursor.rowcount


def _update_document_status(
    document_id: str,
    *,
    status: str,
    chunk_count: int,
    error_message: str | None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE documents
            SET status = ?,
                chunk_count = ?,
                error_message = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                chunk_count,
                error_message,
                datetime.now(timezone.utc).isoformat(),
                document_id,
            ),
        )
