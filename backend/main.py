"""
FastAPI Application - LOGUS Backend
Main entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LOGUS API",
    description="Ecossistema de Inovação - Grupo Lisboa",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "LOGUS API",
        "version": "0.1.0",
        "projects": ["VerifiK"]
    }

@app.get("/api/health")
async def health():
    """API health status"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
