import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
        connection.execute(
            """
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
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_created_at
            ON documents (created_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_status
            ON documents (status)
            """
        )


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
