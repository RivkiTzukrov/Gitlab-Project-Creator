import logging
from typing import Dict, List

import httpx
from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import AuthenticationError, GitLabAPIError
from app.schemas.repo_models import RepoRequest
from app.services.gitlab_service import GitLabService
from app.services.project_creator import ProjectCreator

logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer()


def get_access_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    return credentials.credentials


@router.get("/login", response_class=RedirectResponse)
def get_oauth_login_url() -> RedirectResponse:
    oauth_url = (
        "https://gitlab.com/oauth/authorize"
        f"?client_id={settings.gitlab_client_id}"
        f"&redirect_uri={settings.gitlab_redirect_uri}"
        f"&response_type=code"
        f"&scope=api read_user read_repository write_repository"
    )
    return RedirectResponse(url=oauth_url)


@router.get("/login-url")
def get_oauth_url() -> Dict[str, str]:
    oauth_url = (
        "https://gitlab.com/oauth/authorize"
        f"?client_id={settings.gitlab_client_id}"
        f"&redirect_uri={settings.gitlab_redirect_uri}"
        f"&response_type=code"
        f"&scope=api read_user read_repository write_repository"
    )
    return {"login_url": oauth_url}


@router.get("/callback")
async def handle_oauth_callback(request: Request) -> JSONResponse:
    code = request.query_params.get("code")
    if not code:
        raise AuthenticationError("Authorization code missing")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.gitlab_token_url,
                data={
                    "client_id": settings.gitlab_client_id,
                    "client_secret": settings.gitlab_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.gitlab_redirect_uri,
                },
                headers={"Accept": "application/json"},
            )

        if response.status_code != 200:
            error_details = {"gitlab_response": response.json() if response.content else {}}
            raise GitLabAPIError("Token exchange failed", response.status_code, error_details)

        return JSONResponse(content=response.json())

    except httpx.RequestError as e:
        raise GitLabAPIError("Unable to contact GitLab", 502, {"error": str(e)})


@router.get("/groups")
async def get_user_groups(
    token: str = Depends(get_access_token),
) -> Dict[str, List[Dict]]:
    gitlab_service = GitLabService()
    groups = await gitlab_service.get_user_groups(token)
    return {"groups": groups}


@router.post("/generate-repo")
async def create_repository(
    repo_request: RepoRequest, token: str = Depends(get_access_token)
) -> Dict:
    project_creator = ProjectCreator()
    return await project_creator.create_project(token, repo_request)
