from app.chunking import TextChunk
from app.db import get_data_dir

COLLECTION_NAME = "document_chunks"


def get_collection():
    import chromadb

    chroma_dir = get_data_dir() / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def replace_document_chunks(
    *,
    document_id: str,
    chunks: list[TextChunk],
    embeddings: list[list[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match.")

    collection = get_collection()
    collection.delete(where={"document_id": document_id})

    if not chunks:
        return

    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )


def delete_document_chunks(document_id: str) -> None:
    get_collection().delete(where={"document_id": document_id})
