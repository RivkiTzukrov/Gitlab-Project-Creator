import logging
from typing import Dict, List

from httpx import AsyncClient, RequestError
from json import JSONDecodeError
from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.dependencies import get_gitlab_service, get_project_creator
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
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Access token is required")
    return credentials.credentials


def _build_oauth_url() -> str:
    return (
        "https://gitlab.com/oauth/authorize"
        f"?client_id={settings.gitlab_client_id}"
        f"&redirect_uri={settings.gitlab_redirect_uri}"
        f"&response_type=code"
        f"&scope=api read_user read_repository write_repository"
    )


@router.get("/login", response_class=RedirectResponse)
def get_oauth_login_url() -> RedirectResponse:
    return RedirectResponse(url=_build_oauth_url())


@router.get("/login-url")
def get_oauth_url() -> Dict[str, str]:
    return {"login_url": _build_oauth_url()}


@router.get("/callback")
async def handle_oauth_callback(request: Request) -> JSONResponse:
    code = request.query_params.get("code")
    if not code:
        raise AuthenticationError("Authorization code missing")

    try:
        async with AsyncClient(timeout=10.0) as client:
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
            try:
                error_details = {"gitlab_response": response.json() if response.content else {}}
            except JSONDecodeError:
                error_details = {"gitlab_response": "Invalid JSON response"}
            raise GitLabAPIError("Token exchange failed", response.status_code, error_details)

        try:
            token_data = response.json()
        except JSONDecodeError:
            raise GitLabAPIError("Invalid JSON response from GitLab", response.status_code)
        
        return JSONResponse(content=token_data)

    except RequestError as e:
        raise GitLabAPIError("Unable to contact GitLab", 502, {"error": str(e)})


@router.get("/groups")
async def get_user_groups(
    token: str = Depends(get_access_token),
    gitlab_service: GitLabService = Depends(get_gitlab_service),
) -> Dict[str, List[Dict]]:
    groups = await gitlab_service.get_user_groups(token)
    return {"groups": groups}


@router.post("/generate-repo")
async def create_repository(
    repo_request: RepoRequest, 
    token: str = Depends(get_access_token),
    project_creator: ProjectCreator = Depends(get_project_creator)
) -> Dict:
    return await project_creator.create_project(token, repo_request)
