import logging
from typing import Dict, List

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.repo_models import ClusterConfig, RepoRequest
from app.services.gitlab_service import GitLabService
from app.services.template_processor import TemplateProcessor

logger = logging.getLogger(__name__)


class ProjectCreator:
    def __init__(self):
        self.gitlab_service = GitLabService()
        self.template_processor = TemplateProcessor(
            settings.s3_bucket, settings.s3_region
        )

    async def create_project(self, token: str, repo_request: RepoRequest) -> Dict:
        # Validate requirements
        try:
            repo_request.validate_requirements()
        except ValueError as e:
            raise HTTPException(400, str(e))

        try:
            # Generate template files
            files = await self.template_processor.get_project_files(
                project_type=repo_request.project_type,
                repo_name=repo_request.sanitized_name,
                stack=repo_request.stack,
            )

            # Create repository
            repo_url, project_id = await self.gitlab_service.create_repository(
                token, repo_request.dict()
            )

            # Initialize with files
            await self.gitlab_service.add_files(token, project_id, files)

            # Set cluster variables if needed
            variables_created = []
            if self._should_create_cluster_variables(repo_request):
                cluster_variables = self._create_cluster_variables(
                    repo_request.clusters
                )
                await self.gitlab_service.set_project_variables(
                    token, project_id, cluster_variables
                )
                variables_created = list(cluster_variables.keys())

            return {
                "status": "success",
                "repo_url": repo_url,
                "project_id": project_id,
                "files_created": list(files.keys()),
                "variables_created": variables_created,
                "message": "Project created successfully",
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Project creation failed: {str(e)}")

    def _should_create_cluster_variables(self, repo_request: RepoRequest) -> bool:
        return (
            repo_request.project_type in ["monorepo", "delivery"]
            and repo_request.clusters
        )

    def _create_cluster_variables(
        self, clusters: List[ClusterConfig]
    ) -> Dict[str, str]:
        variables = {}
        for cluster in clusters:
            env_prefix = cluster.environment.upper()
            variables[f"{env_prefix}_CLUSTER_NAME"] = cluster.name
            variables[f"{env_prefix}_ENVIRONMENT"] = cluster.environment
        return variables
