"""Groups endpoint."""
from fastapi import APIRouter

router = APIRouter()


def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.get("/groups", response_model=dict)
async def list_groups():
    """List all groups (ODIN, HEIMDALL, etc.)."""
    vault = _vault()
    groups = await vault.get_all_groups()
    return {"groups": groups}
