import os

from app.db import list_ready_document_ids
from app.embedding import embed_texts
from app.vector_store import RetrievedChunk, query_chunks

DEFAULT_TOP_K = 4


def get_retrieval_top_k() -> int:
    top_k = int(os.getenv("RETRIEVAL_TOP_K", str(DEFAULT_TOP_K)))
    if top_k <= 0:
        raise ValueError("RETRIEVAL_TOP_K must be greater than 0.")
    return top_k


def retrieve_chunks(question: str) -> list[RetrievedChunk]:
    question = question.strip()
    if not question:
        return []

    ready_document_ids = list_ready_document_ids()
    if not ready_document_ids:
        return []

    query_embedding = embed_texts([question])[0]
    return query_chunks(
        query_embedding=query_embedding,
        top_k=get_retrieval_top_k(),
        document_ids=ready_document_ids,
    )
