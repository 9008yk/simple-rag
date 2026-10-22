from pathlib import Path

import pytest

import app.retrieval as retrieval_module
from app.chunking import TextChunk
from app.db import (
    create_document,
    init_db,
    mark_document_processing,
    mark_document_ready,
)
from app.retrieval import retrieve_chunks
from app.vector_store import replace_document_chunks


def _query_embedding() -> list[float]:
    return [1.0] + [0.0] * 511


def _add_document_chunk(
    *,
    document_id: str,
    filename: str,
    text: str,
    status: str,
) -> None:
    create_document(
        document_id=document_id,
        filename=filename,
        file_path=f"uploads/{document_id}{Path(filename).suffix}",
        created_at="2026-10-21T00:00:00+00:00",
    )

    if status == "ready":
        mark_document_ready(document_id, chunk_count=1)
    else:
        mark_document_processing(document_id)

    replace_document_chunks(
        document_id=document_id,
        chunks=[
            TextChunk(
                chunk_id=f"{document_id}:0",
                text=text,
                document_id=document_id,
                source=filename,
                chunk_index=0,
            )
        ],
        embeddings=[_query_embedding()],
    )


def test_retrieval_returns_empty_without_ready_documents(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    init_db()

    def unexpected_embedding(_: list[str]) -> list[list[float]]:
        raise AssertionError("Embedding should not be called without ready documents.")

    monkeypatch.setattr(retrieval_module, "embed_texts", unexpected_embedding)

    assert retrieve_chunks("项目目标是什么？") == []


def test_retrieval_filters_non_ready_documents(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    init_db()
    monkeypatch.setattr(
        retrieval_module,
        "embed_texts",
        lambda _: [_query_embedding()],
    )
    _add_document_chunk(
        document_id="ready-doc",
        filename="ready.md",
        text="Ready document content.",
        status="ready",
    )
    _add_document_chunk(
        document_id="processing-doc",
        filename="processing.md",
        text="Processing document content.",
        status="processing",
    )

    results = retrieve_chunks("文档内容是什么？")

    assert len(results) == 1
    assert results[0].document_id == "ready-doc"
    assert results[0].chunk_id == "ready-doc:0"
    assert results[0].source == "ready.md"
    assert results[0].chunk_index == 0
    assert results[0].text == "Ready document content."
    assert results[0].score == pytest.approx(1.0)


def test_retrieval_respects_configured_top_k(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RETRIEVAL_TOP_K", "2")
    init_db()
    monkeypatch.setattr(
        retrieval_module,
        "embed_texts",
        lambda _: [_query_embedding()],
    )

    for index in range(5):
        document_id = f"doc-{index}"
        _add_document_chunk(
            document_id=document_id,
            filename=f"{document_id}.md",
            text=f"Document {index}.",
            status="ready",
        )

    results = retrieve_chunks("document")

    assert len(results) == 2
