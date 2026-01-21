from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ConceptCast API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["http://localhost:5173"],  # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint to verify API is running."""
    return {"status": "ok", "message": "Welcome to ConceptCast API"}

@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
