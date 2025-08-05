from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, validator


class Stack(Enum):
    MAVEN = "maven"
    NODE = "node"
    PYTHON = "python"
    DOTNET = "dotnet"


class ClusterConfig(BaseModel):
    name: str
    environment: str


class RepoRequest(BaseModel):
    project_name: str
    group_id: str
    project_type: Literal["library", "microservice", "monorepo", "delivery"]
    stack: Optional[Stack] = None
    clusters: Optional[List[ClusterConfig]] = None
    
    @validator('project_name')
    def sanitize_project_name(cls, v):
        # Convert to lowercase, replace spaces with hyphens, remove invalid chars
        sanitized = v.lower().replace(' ', '-')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '-_')
        # Remove consecutive hyphens and trim
        sanitized = '-'.join(filter(None, sanitized.split('-')))
        if not sanitized:
            raise ValueError("Project name must contain at least one alphanumeric character")
        return sanitized
    
    def validate_requirements(self):
        if self.project_type in ["library", "microservice"] and not self.stack:
            raise ValueError(f"{self.project_type} requires a stack")
        if self.project_type in ["monorepo", "delivery"] and not self.clusters:
            raise ValueError(f"{self.project_type} requires clusters")
