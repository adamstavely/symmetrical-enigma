"""Pydantic schemas for API request/response (DRY, single source)."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    group: Optional[str] = None
    technology: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = Field(default_factory=SearchFilters)


class AnalyzeRequest(BaseModel):
    """Trigger SCRIBE analysis for a repository; result stored in VAULT."""
    repository_url: str


class ManualOverrideRequest(BaseModel):
    """Set manual override flag on a node or relationship (SCRIBE will not overwrite)."""
    override: bool = True
