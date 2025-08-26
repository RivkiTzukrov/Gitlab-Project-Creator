from functools import lru_cache

from app.services.gitlab_service import GitLabService
from app.services.project_creator import ProjectCreator


@lru_cache()
def get_gitlab_service() -> GitLabService:
    return GitLabService()


@lru_cache()
def get_project_creator() -> ProjectCreator:
    return ProjectCreator()