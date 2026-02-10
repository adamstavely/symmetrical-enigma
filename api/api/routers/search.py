"""Search endpoint."""
from fastapi import APIRouter
from api.models.schemas import SearchRequest

router = APIRouter()


def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.post("/search", response_model=dict)
async def search(request: SearchRequest):
    """Full-text search across systems, containers, components."""
    vault = _vault()
    filters = request.filters.model_dump() if request.filters else None
    results = await vault.search(query=request.query, filters=filters)
    return {"results": results}
