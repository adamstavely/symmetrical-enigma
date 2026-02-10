"""
SCRIBE - Pydantic models for architecture analysis output.
Single source of truth for the shape stored in VAULT.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Container(BaseModel):
    id: str
    name: str
    description: str = ""
    technology: str = ""
    type: Literal["service", "database", "queue", "cache", "storage", "cdn"] = "service"
    port: Optional[int] = None
    repository_path: Optional[str] = None


class Component(BaseModel):
    id: str
    name: str
    description: str = ""
    responsibility: str = ""
    file_path: str = ""
    language: str = ""


class Relationship(BaseModel):
    from_id: str
    to_id: str
    type: Literal[
        "calls_api",
        "reads_from",
        "writes_to",
        "publishes_to",
        "subscribes_to",
        "authenticates_with",
    ] = "calls_api"
    protocol: Optional[str] = None
    description: str = ""


class ExternalDependency(BaseModel):
    id: str
    name: str
    vendor: str = ""
    type: Literal["saas", "cloud", "partner_api", "legacy_system"] = "saas"


class ArchitectureModel(BaseModel):
    """Full C4 architecture output from SCRIBE analysis."""

    system: dict  # id, name, description, team, group, repository_url
    containers: list[Container] = []
    components: list[Component] = []
    relationships: list[Relationship] = []
    external_dependencies: list[ExternalDependency] = []
    analyzed_at: datetime = Field(default_factory=datetime.now)

    def to_vault_dict(self) -> dict:
        """Serialize for VAULT store_architecture (dict shape)."""
        return {
            "system": self.system,
            "containers": [c.model_dump() for c in self.containers],
            "components": [c.model_dump() for c in self.components],
            "relationships": [r.model_dump() for r in self.relationships],
            "external_dependencies": [e.model_dump() for e in self.external_dependencies],
        }
