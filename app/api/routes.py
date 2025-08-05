import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.schemas.repo_models import GenerateRepoRequest
from app.services.gitlab_service import get_user_groups
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


@router.get("/groups")
async def groups(access_token: str) -> JSONResponse:
    """Returns the groups the user has access to."""
    try:
        groups = await get_user_groups(access_token)
        if groups is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized or invalid access token."},
            )
        return JSONResponse(content={"groups": groups})
    except httpx.RequestError as exc:
        logger.error(f"HTTPX error during group fetch: {exc}")
        return JSONResponse(
            status_code=502, content={"error": "Failed to contact GitLab for groups."}
        )
    except Exception as e:
        logger.error(f"Unexpected error during group fetch: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error while fetching groups."},
        )


@router.post("/generate-repo")
async def generate_repo(repo_data: GenerateRepoRequest) -> JSONResponse:
    """Generates a new repository in GitLab with the specified configuration."""
    try:
        # Validate project type specific requirements
        if (
            repo_data.repo.project_type in ["library", "microservice"]
            and not repo_data.repo.stack
        ):
            raise HTTPException(
                status_code=400,
                detail=f"{repo_data.repo.project_type} requires a stack to be specified",
            )

        if (
            repo_data.repo.project_type in ["monorepo", "delivery"]
            and not repo_data.repo.deployment_clusters
        ):
            raise HTTPException(
                status_code=400,
                detail=f"{repo_data.repo.project_type} requires at least one cluster configuration",
            )

        project_creator = ProjectCreator()

        repo_dict = repo_data.repo.dict()
        repo_dict["access_token"] = repo_data.access_token

        result = await project_creator.create_project(repo_data=repo_dict)

        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "repo_url": result["repo_url"],
                "project_id": result["project_id"],
                "files_created": result["files_created"],
                "message": "Project created and initialized successfully",
            },
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during project creation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while creating project: {str(e)}",
        )
