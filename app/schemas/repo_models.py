from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator


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
    

    
    @property
    def sanitized_name(self) -> str:
        """Get sanitized version for templates and file names"""
        sanitized = self.project_name.lower().replace(' ', '-')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '-_')
        return '-'.join(filter(None, sanitized.split('-')))
    
    def validate_requirements(self):
        if self.project_type in ["library", "microservice"] and not self.stack:
            raise ValueError(f"{self.project_type} requires a stack")
        if self.project_type in ["monorepo", "delivery"] and not self.clusters:
            raise ValueError(f"{self.project_type} requires clusters")
