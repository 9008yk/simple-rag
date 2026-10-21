import os
from threading import Lock

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_EMBEDDING_DIMENSION = 512

_model = None
_model_lock = Lock()


def get_embedding_model():
    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                model_name = os.getenv(
                    "EMBEDDING_MODEL",
                    DEFAULT_EMBEDDING_MODEL,
                )
                _model = SentenceTransformer(model_name)

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    embeddings = [vector.tolist() for vector in vectors]

    dimension = int(
        os.getenv(
            "EMBEDDING_DIMENSION",
            str(DEFAULT_EMBEDDING_DIMENSION),
        )
    )

    if any(len(vector) != dimension for vector in embeddings):
        raise ValueError(
            f"Embedding dimension must be {dimension}."
        )

    return embeddings
