"""POST /analyze and WebSocket /ws/analysis for progress."""
import asyncio
import json
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from api.models.schemas import AnalyzeRequest

router = APIRouter()

# WebSocket connections for progress broadcast (optional)
_ws_connections: set[WebSocket] = set()

# Ensure scribe and vault are importable (e.g. PYTHONPATH=/app in Docker)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _clone_repo(path_or_url: str) -> Path | None:
    """Clone repo to temp dir if URL; else return path. Returns None on failure."""
    path_or_url = path_or_url.strip()
    if path_or_url.startswith("http://") or path_or_url.startswith("https://") or path_or_url.startswith("git@"):
        try:
            import git
        except ImportError:
            return None
        clone_dir = Path(os.environ.get("SCRIBE_CLONE_DIR", "/tmp/repos"))
        clone_dir.mkdir(parents=True, exist_ok=True)
        name = path_or_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = clone_dir / name
        if dest.exists():
            return dest
        try:
            git.Repo.clone_from(path_or_url, dest, depth=1)
            return dest
        except Exception:
            return None
    p = Path(path_or_url).resolve()
    return p if p.is_dir() else None


@router.post("/analyze", response_model=dict)
async def analyze_repository(request: AnalyzeRequest):
    """
    Run SCRIBE analysis on the given repository URL (or path).
    Clones if URL; stores result in VAULT. Uses mock LLM if USE_MOCK_LLM=true.
    """
    try:
        from scribe.analyzer import RepositoryAnalyzer
        from vault.repository import ArchitectureRepository
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"SCRIBE/VAULT not available: {e}")

    await _broadcast_progress("clone", "Cloning repository...")
    repo_path = _clone_repo(request.repository_url)
    if not repo_path:
        await _broadcast_progress("error", "Clone failed")
        raise HTTPException(status_code=400, detail="Invalid repository URL or path or clone failed")
    await _broadcast_progress("clone", "Clone done", path=str(repo_path))

    await _broadcast_progress("analyze", "Running SCRIBE analysis...")
    analyzer = RepositoryAnalyzer()
    model = await analyzer.analyze_repository(repo_path)
    await _broadcast_progress("analyze", "Analysis done", system_id=model.system.get("id"))

    await _broadcast_progress("store", "Storing in VAULT...")
    vault = ArchitectureRepository()
    try:
        await vault.store_architecture(model.to_vault_dict())
    finally:
        await vault.close()
    await _broadcast_progress("store", "Stored", system_id=model.system.get("id"))

    return {
        "status": "ok",
        "system_id": model.system.get("id"),
        "system_name": model.system.get("name"),
        "containers": len(model.containers),
        "relationships": len(model.relationships),
    }


async def _broadcast_progress(stage: str, message: str, **extra: object) -> None:
    """Send progress to all connected WebSocket clients."""
    msg = {"event": "progress", "stage": stage, "message": message, **extra}
    dead = set()
    for ws in _ws_connections:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _ws_connections.discard(ws)


@router.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """
    Optional WebSocket for analysis progress. Connect here; then trigger POST /analyze.
    Server will push messages: { "event": "progress", "stage": "clone|analyze|store", "message": "..." }.
    """
    await websocket.accept()
    _ws_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                obj = json.loads(data)
                if obj.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.discard(websocket)
