from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root() -> dict[str, str]:
    """Root health-check endpoint (used when frontend is not bundled)."""
    return {"message": "Welcome to ConceptCast Council"}
