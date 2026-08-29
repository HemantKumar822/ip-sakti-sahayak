from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Backend API for the IP-SAKTI Sahayak RAG system",
    version="0.1.0"
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
