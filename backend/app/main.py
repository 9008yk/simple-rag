# from fastapi import FastAPI

# app = FastAPI(title="Simple RAG API")


# @app.get("/health")
# async def health() -> dict[str, str]:
#     return {"status": "ok"}
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.db import create_document, get_upload_dir, init_db

ALLOWED_SUFFIXES = {".txt", ".md", ".markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Simple RAG API", lifespan=lifespan)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunk_count: int
    error_message: str | None
    created_at: str
    updated_at: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()

    if not original_name or suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt, .md and .markdown files are supported.",
        )

    document_id = uuid4().hex
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{document_id}{suffix}"
    bytes_written = 0

    try:
        with stored_path.open("wb") as stored_file:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                bytes_written += len(chunk)

                if bytes_written > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="The uploaded file exceeds the 10 MiB size limit.",
                    )

                stored_file.write(chunk)

        if bytes_written == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty.",
            )

        document = create_document(
            document_id=document_id,
            filename=original_name,
            file_path=stored_path.relative_to(upload_dir.parent).as_posix(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    except OSError as error:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=507,
            detail="File storage is unavailable.",
        ) from error
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return DocumentResponse(**document)


