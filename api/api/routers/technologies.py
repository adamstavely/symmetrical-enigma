"""Technologies and technology inventory endpoints."""
from fastapi import APIRouter, Query
from typing import Any

router = APIRouter()


def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.get("/technologies", response_model=dict)
async def list_technologies(
    inventory: bool = Query(False, description="Include system_ids per technology"),
) -> dict[str, Any]:
    """List distinct container technologies. Optionally include inventory (technology -> system_ids)."""
    vault = _vault()
    if inventory:
        inv = await vault.get_technology_inventory()
        technologies = [x["technology"] for x in inv]
        return {"technologies": technologies, "inventory": inv}
    technologies = await vault.get_all_technologies()
    return {"technologies": technologies}
