from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


def test_upload_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={
                "file": (
                    "guide.md",
                    b"# Guide\n\nSimple RAG project.",
                    "text/markdown",
                )
            },
        )

    assert response.status_code == 201

    document = response.json()
    assert document["filename"] == "guide.md"
    assert document["status"] == "pending"
    assert document["chunk_count"] == 0
    assert document["error_message"] is None

    saved_files = list((tmp_path / "uploads").iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"# Guide\n\nSimple RAG project."


def test_duplicate_filename_creates_new_document(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))
    content = b"# Same file"

    with TestClient(app) as client:
        first = client.post(
            "/api/documents",
            files={"file": ("same.md", content, "text/markdown")},
        )
        second = client.post(
            "/api/documents",
            files={"file": ("same.md", content, "text/markdown")},
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert len(list((tmp_path / "uploads").iterdir())) == 2


def test_upload_rejects_unsupported_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("guide.pdf", b"%PDF", "application/pdf")},
        )

    assert response.status_code == 400


def test_upload_rejects_empty_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("empty.txt", b"", "text/plain")},
        )

    assert response.status_code == 400
    assert list((tmp_path / "uploads").iterdir()) == []


def test_upload_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={
                "file": (
                    "large.txt",
                    b"x" * (main_module.MAX_FILE_SIZE + 1),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 413
    assert list((tmp_path / "uploads").iterdir()) == []


def test_database_failure_removes_saved_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    def fail_to_create_document(**_):
        raise RuntimeError("database failure")

    monkeypatch.setattr(
        main_module,
        "create_document",
        fail_to_create_document,
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("guide.md", b"# Guide", "text/markdown")},
        )

    assert response.status_code == 500
    assert list((tmp_path / "uploads").iterdir()) == []