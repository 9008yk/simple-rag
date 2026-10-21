import os
from dataclasses import dataclass

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
MARKDOWN_HEADERS = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]
SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    document_id: str
    source: str
    chunk_index: int


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def get_chunk_config() -> tuple[int, int]:
    chunk_size = int(os.getenv("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
    chunk_overlap = int(
        os.getenv("CHUNK_OVERLAP", str(DEFAULT_CHUNK_OVERLAP))
    )

    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be greater than 0.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be between 0 and CHUNK_SIZE.")

    return chunk_size, chunk_overlap


def _split_plain_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=SEPARATORS,
        keep_separator=True,
    )
    return splitter.split_text(text)


def _build_chunk(
    *,
    document_id: str,
    source: str,
    chunk_index: int,
    text: str,
) -> TextChunk:
    return TextChunk(
        chunk_id=f"{document_id}:{chunk_index}",
        text=text,
        document_id=document_id,
        source=source,
        chunk_index=chunk_index,
    )


def chunk_document(
    *,
    document_id: str,
    source: str,
    text: str,
    suffix: str,
) -> list[TextChunk]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    chunk_size, chunk_overlap = get_chunk_config()
    chunks: list[TextChunk] = []

    if suffix.lower() in {".md", ".markdown"}:
        sections = MarkdownHeaderTextSplitter(
            headers_to_split_on=MARKDOWN_HEADERS,
            strip_headers=True,
        ).split_text(normalized)

        for section in sections:
            heading_path = " > ".join(
                section.metadata[key]
                for _, key in MARKDOWN_HEADERS
                if section.metadata.get(key)
            )
            prefix = f"{heading_path}\n\n" if heading_path else ""
            body_limit = max(200, chunk_size - len(prefix))
            body_overlap = min(chunk_overlap, body_limit // 2)

            for body in _split_plain_text(
                section.page_content,
                chunk_size=body_limit,
                overlap=body_overlap,
            ):
                content = f"{prefix}{body.strip()}".strip()
                if content:
                    chunks.append(
                        _build_chunk(
                            document_id=document_id,
                            source=source,
                            chunk_index=len(chunks),
                            text=content,
                        )
                    )
    else:
        for body in _split_plain_text(
            normalized,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        ):
            content = body.strip()
            if content:
                chunks.append(
                    _build_chunk(
                        document_id=document_id,
                        source=source,
                        chunk_index=len(chunks),
                        text=content,
                    )
                )

    return chunks
