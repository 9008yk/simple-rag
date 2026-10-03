from fastapi import FastAPI

app = FastAPI(title="Simple RAG API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
