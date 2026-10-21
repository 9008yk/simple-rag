from pathlib import Path

from fastapi.testclient import TestClient

import app.ingestion as ingestion_module
import app.main as main_module
from app.chunking import chunk_document
from app.db import (
    create_document,
    get_connection,
    get_document,
    init_db,
    recover_interrupted_documents,
)
from app.main import app
from app.vector_store import get_collection


def _embedding_for(texts: list[str]) -> list[list[float]]:
    return [
        [1.0] + [0.0] * 511
        for _ in texts
    ]


def _create_file_document(
    *,
    data_dir: Path,
    document_id: str,
    filename: str,
    content: bytes,
) -> None:
    upload_dir = data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{document_id}{Path(filename).suffix}"
    stored_path.write_bytes(content)
    create_document(
        document_id=document_id,
        filename=filename,
        file_path=stored_path.relative_to(data_dir).as_posix(),
        created_at="2026-10-17T00:00:00+00:00",
    )


def test_markdown_chunks_preserve_heading_context():
    text = "# 项目说明\n\n## 技术栈\n\n" + "FastAPI 和 Vue。" * 120

    chunks = chunk_document(
        document_id="doc-1",
        source="guide.md",
        text=text,
        suffix=".md",
    )

    assert len(chunks) > 1
    assert all(chunk.chunk_id.startswith("doc-1:") for chunk in chunks)
    assert all("项目说明 > 技术栈" in chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= 800 for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_process_document_writes_chunks_and_marks_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(ingestion_module, "embed_texts", _embedding_for)
    init_db()
    _create_file_document(
        data_dir=tmp_path,
        document_id="doc-ready",
        filename="guide.md",
        content=b"# Guide\n\n" + ("Simple RAG content. " * 80).encode(),
    )

    ingestion_module.process_document("doc-ready")

    document = get_document("doc-ready")
    assert document is not None
    assert document["status"] == "ready"
    assert document["chunk_count"] > 0
    assert document["error_message"] is None

    stored = get_collection().get(where={"document_id": "doc-ready"})
    assert len(stored["ids"]) == document["chunk_count"]
    assert all(
        metadata["document_id"] == "doc-ready"
        for metadata in stored["metadatas"]
    )


def test_process_document_marks_invalid_encoding_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(ingestion_module, "embed_texts", _embedding_for)
    init_db()
    _create_file_document(
        data_dir=tmp_path,
        document_id="doc-invalid",
        filename="invalid.txt",
        content=b"\xff\xfe\xfa",
    )

    ingestion_module.process_document("doc-invalid")

    document = get_document("doc-invalid")
    assert document is not None
    assert document["status"] == "failed"
    assert document["chunk_count"] == 0
    assert document["error_message"]

    stored = get_collection().get(where={"document_id": "doc-invalid"})
    assert stored["ids"] == []


def test_recover_interrupted_documents_marks_processing_failed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    init_db()
    _create_file_document(
        data_dir=tmp_path,
        document_id="doc-interrupted",
        filename="guide.md",
        content=b"# Guide",
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE documents
            SET status = 'processing'
            WHERE id = 'doc-interrupted'
            """
        )

    assert recover_interrupted_documents() == 1

    document = get_document("doc-interrupted")
    assert document is not None
    assert document["status"] == "failed"
    assert "restart" in document["error_message"]


def test_upload_schedules_document_processing(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    processed: list[str] = []
    monkeypatch.setattr(
        main_module,
        "process_document",
        lambda document_id: processed.append(document_id),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("guide.md", b"# Guide", "text/markdown")},
        )

    assert response.status_code == 201
    assert processed == [response.json()["id"]]
