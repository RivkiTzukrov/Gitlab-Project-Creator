from typing import Dict

from fastapi import HTTPException

from app.core.config import settings
from app.services import gitlab_service
from app.services.template_processor import TemplateProcessor  # Fixed import


class ProjectCreator:
    def __init__(self):
        self.template_processor = TemplateProcessor(
            settings.s3_bucket, settings.s3_region
        )

    async def create_project(self, repo_data: Dict) -> Dict:
        """Orchestrate project creation with full initialization"""
        try:
            files = await self.template_processor.get_project_files(
                project_type=repo_data["project_type"],
                repo_name=repo_data["project_name"],
                stack=repo_data["stack"],
            )

            repo_url, project_id = await gitlab_service.create_repository(
                repo_data["access_token"], repo_data
            )

            await gitlab_service.initialize_repository_with_files(
                token=repo_data["access_token"],
                project_id=project_id,
                files=files,
                commit_message=f"Initial commit: {repo_data['project_type']} project setup",
            )

            return {
                "status": "success",
                "message": "Project created and initialized successfully",
                "repo_url": repo_url,
                "project_id": project_id,
                "files_created": list(files.keys()),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Project creation failed: {str(e)}"
            )
