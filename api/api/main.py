"""
EDDA API - FastAPI app, CORS, and router wiring.
Auth: optional API key via EDDA_API_KEY env and X-API-Key header (see api.auth).
Extension point for SAML/LDAP + RBAC in production.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import systems, search, dependencies, groups, analyze, corrections

app = FastAPI(
    title="EDDA API",
    version="1.0.0",
    description="REST API for EDDA (Enterprise Documentation & Diagram Automation). "
                "Auth: set EDDA_API_KEY to require X-API-Key header; otherwise open for dev.",
)

origins = os.environ.get("CORS_ORIGINS", "http://localhost:4200,http://localhost:4201,http://localhost:3000").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(systems.router, prefix="/api/v1", tags=["systems"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(dependencies.router, prefix="/api/v1", tags=["dependencies"])
app.include_router(groups.router, prefix="/api/v1", tags=["groups"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(corrections.router, prefix="/api/v1", tags=["corrections"])


@app.get("/health")
def health():
    return {"status": "ok"}
