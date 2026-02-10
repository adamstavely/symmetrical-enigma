"""Manual override endpoints: toggle or edit so SCRIBE does not overwrite."""
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _vault():
    from vault.repository import ArchitectureRepository
    return ArchitectureRepository()


@router.patch("/systems/{system_id}/nodes/{node_id}/override")
async def set_node_override(
    system_id: str,
    node_id: str,
    override: bool = Query(True, description="Set manual override on this node"),
    node_type: str = Query("container", pattern="^(system|container|component)$"),
):
    """Set manual_override on a system, container, or component. SCRIBE will not overwrite when true."""
    vault = _vault()
    ok = await vault.set_manual_override(node_type=node_type, node_id=node_id, override=override, system_id=system_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node_id": node_id, "node_type": node_type, "manual_override": override}


@router.patch("/relationships/override")
async def set_relationship_override(
    from_id: str = Query(..., description="Source node id"),
    to_id: str = Query(..., description="Target node id"),
    override: bool = Query(True),
):
    """Set manual_override on a DEPENDS_ON relationship."""
    vault = _vault()
    ok = await vault.set_relationship_override(from_id=from_id, to_id=to_id, override=override)
    if not ok:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"from_id": from_id, "to_id": to_id, "manual_override": override}
