import logging
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.schemas.repo_models import RepoRequest
from app.services.gitlab_service import GitLabService
from app.services.project_creator import ProjectCreator

logger = logging.getLogger("gitlab_repo_sculptor")
router = APIRouter()


@router.get("/login", response_class=RedirectResponse)
def login() -> RedirectResponse:
    """Redirects user to GitLab OAuth login."""
    url = (
        "https://gitlab.com/oauth/authorize"
        f"?client_id={settings.gitlab_client_id}"
        f"&redirect_uri={settings.gitlab_redirect_uri}"
        f"&response_type=code"
        f"&scope=api read_user read_repository write_repository"
    )
    return RedirectResponse(url=url)


@router.get("/callback")
async def callback(request: Request) -> JSONResponse:
    """Handles GitLab redirect and returns access token."""
    code = request.query_params.get("code")
    if not code:
        return JSONResponse(
            status_code=400, content={"error": "Missing code in callback"}
        )

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                settings.gitlab_token_url,
                data={
                    "client_id": settings.gitlab_client_id,
                    "client_secret": settings.gitlab_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.gitlab_redirect_uri,
                },
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
    except httpx.RequestError as exc:
        logger.error(f"HTTPX error during token exchange: {exc}")
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to contact GitLab for token exchange."},
        )
    except Exception as exc:
        logger.error(f"Unexpected error during token exchange: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error during token exchange."},
        )

    if token_response.status_code != 200:
        try:
            error_json = token_response.json()
        except Exception:
            error_json = {"error": "Unknown error from GitLab."}
        return JSONResponse(status_code=token_response.status_code, content=error_json)

    return JSONResponse(content=token_response.json())


bearer_scheme = HTTPBearer()

def get_current_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    return credentials.credentials

@router.get("/groups")
async def get_groups(token: str = Depends(get_current_token)) -> Dict[str, List[Dict]]:
    """Returns the groups the user has access to."""
    gitlab = GitLabService()
    groups = await gitlab.get_user_groups(token)
    return {"groups": groups}


@router.post("/generate-repo")
async def create_repo(
    repo_data: RepoRequest, 
    token: str = Depends(get_current_token)
) -> Dict:
    """Creates and initializes a new GitLab repository."""
    creator = ProjectCreator()
    result = await creator.create_project(token, repo_data)
    return result
