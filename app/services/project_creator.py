from typing import Dict

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.repo_models import RepoRequest
from app.services.gitlab_service import GitLabService
from app.services.template_processor import TemplateProcessor


class ProjectCreator:
    def __init__(self):
        self.gitlab = GitLabService()
        self.template_processor = TemplateProcessor(settings.s3_bucket, settings.s3_region)
    
    async def create_project(self, token: str, repo_data: RepoRequest) -> Dict:
        # Validate requirements
        repo_data.validate_requirements()
        
        project_id = None
        try:
            # Get template files
            files = await self.template_processor.get_project_files(
                project_type=repo_data.project_type,
                repo_name=repo_data.project_name,
                stack=repo_data.stack
            )
            
            # Create repository
            repo_url, project_id = await self.gitlab.create_repository(
                token, repo_data.dict()
            )
            
            # Add files to repository
            await self.gitlab.add_files(token, project_id, files)
            
            # Set cluster variables for monorepo/delivery projects
            if repo_data.project_type in ["monorepo", "delivery"] and repo_data.clusters:
                cluster_vars = self._create_cluster_variables(repo_data.clusters)
                await self.gitlab.set_project_variables(token, project_id, cluster_vars)
            
            return {
                "status": "success",
                "repo_url": repo_url,
                "project_id": project_id,
                "files_created": list(files.keys()),
                "variables_created": list(cluster_vars.keys()) if repo_data.clusters else [],
                "message": "Project created successfully"
            }
            
        except Exception as e:
            # If repo was created but file initialization failed, we should ideally delete it
            # For now, we'll just raise the error
            if project_id:
                # TODO: Add cleanup logic to delete the repository
                pass
            raise HTTPException(500, f"Project creation failed: {str(e)}")
    
    def _create_cluster_variables(self, clusters) -> Dict[str, str]:
        """Create GitLab CI variables from cluster configurations"""
        variables = {}
        for cluster in clusters:
            # Create variables like: DEV_CLUSTER_NAME, DEV_ENVIRONMENT
            prefix = cluster.environment.upper()
            variables[f"{prefix}_CLUSTER_NAME"] = cluster.name
            variables[f"{prefix}_ENVIRONMENT"] = cluster.environment
        return variables