from fastapi.testclient import TestClient

from app.main import app


def test_health(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIMPLE_RAG_DATA_DIR", str(tmp_path))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
