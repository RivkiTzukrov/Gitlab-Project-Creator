from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel

ClusterConfig = dict[str, str]


class StackType(Enum):
    MAVEN = "maven"
    NODE = "node"
    PYTHON = "python"
    DOTNET = "dotnet"


class RepoBase(BaseModel):
    project_name: str
    group_id: str
    project_type: Literal["library", "microservice", "monorepo", "delivery"]
    stack: Optional[StackType] = None
    deployment_clusters: List[ClusterConfig] | None = None


class GenerateRepoRequest(BaseModel):
    access_token: str
    repo: RepoBase
