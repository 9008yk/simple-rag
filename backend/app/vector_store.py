from dataclasses import dataclass

from app.chunking import TextChunk
from app.db import get_data_dir

COLLECTION_NAME = "document_chunks"


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    chunk_id: str
    source: str
    chunk_index: int
    text: str
    score: float


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


def query_chunks(
    *,
    query_embedding: list[float],
    top_k: int,
    document_ids: list[str],
) -> list[RetrievedChunk]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")
    if not document_ids:
        return []

    result = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": {"$in": document_ids}},
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for index, chunk_id in enumerate(ids):
        metadata = metadatas[index] or {}
        text = documents[index] or ""
        distance = float(distances[index])

        chunks.append(
            RetrievedChunk(
                document_id=str(metadata["document_id"]),
                chunk_id=str(metadata.get("chunk_id", chunk_id)),
                source=str(metadata["source"]),
                chunk_index=int(metadata["chunk_index"]),
                text=str(text),
                score=1.0 - distance,
            )
        )

    return chunks
