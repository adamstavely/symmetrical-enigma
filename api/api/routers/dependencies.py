"""Dependencies endpoint."""
from fastapi import APIRouter, Query

router = APIRouter()


def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.get("/dependencies/{node_id}", response_model=dict)
async def get_dependencies(
    node_id: str,
    direction: str = Query("both", pattern="^(upstream|downstream|both)$"),
    depth: int = Query(1, ge=1, le=5),
):
    """Get dependency graph for a node (upstream, downstream, or both)."""
    vault = _vault()
    return await vault.get_dependencies(node_id=node_id, direction=direction, depth=depth)
