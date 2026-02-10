"""Systems and containers endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Optional

router = APIRouter()

# Repository is created on first use (lazy) so we don't need async startup for Neo4j
def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.get("/enterprise", response_model=dict)
async def get_enterprise_view() -> dict[str, Any]:
    """All systems and edges for the top-level C4 view."""
    vault = _vault()
    return await vault.get_enterprise_view()


@router.get("/systems", response_model=dict)
async def list_systems(
    group: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
) -> dict[str, Any]:
    """List all systems with optional group filter and pagination."""
    vault = _vault()
    systems = await vault.get_all_systems(group=group, skip=skip, limit=limit)
    return {"systems": systems, "total": len(systems)}


@router.get("/systems/{system_id}", response_model=dict)
async def get_system(
    system_id: str,
    version: Optional[str] = Query(None, description="Version id for point-in-time view"),
) -> dict[str, Any]:
    """Get system detail with containers and relationships. Optional ?version=<id> for history."""
    vault = _vault()
    system = await vault.get_system_detail(system_id, version_id=version)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


@router.get("/systems/{system_id}/versions", response_model=dict)
async def list_system_versions(
    system_id: str,
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List architecture versions for a system (newest first)."""
    vault = _vault()
    versions = await vault.get_system_versions(system_id, limit=limit)
    return {"system_id": system_id, "versions": versions}


@router.get("/systems/{system_id}/containers/{container_id}", response_model=dict)
async def get_container(system_id: str, container_id: str) -> dict[str, Any]:
    """Get container detail with components and dependencies."""
    vault = _vault()
    container = await vault.get_container_detail(system_id, container_id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container
