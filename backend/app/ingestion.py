from app.chunking import chunk_document
from app.db import (
    get_data_dir,
    get_document,
    mark_document_failed,
    mark_document_processing,
    mark_document_ready,
)
from app.embedding import embed_texts
from app.vector_store import delete_document_chunks, replace_document_chunks


def process_document(document_id: str) -> None:
    document = get_document(document_id)
    if document is None or document["status"] != "pending":
        return

    try:
        mark_document_processing(document_id)

        file_path = get_data_dir() / str(document["file_path"])
        text = file_path.read_text(encoding="utf-8-sig")
        chunks = chunk_document(
            document_id=document_id,
            source=str(document["filename"]),
            text=text,
            suffix=file_path.suffix,
        )

        if not chunks:
            raise ValueError("The document does not contain indexable text.")

        embeddings = embed_texts([chunk.text for chunk in chunks])
        replace_document_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )
        mark_document_ready(document_id, chunk_count=len(chunks))
    except Exception as error:
        try:
            delete_document_chunks(document_id)
        except Exception:
            pass

        message = str(error).strip() or error.__class__.__name__
        mark_document_failed(document_id, error_message=message[:1000])
