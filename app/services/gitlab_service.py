import base64
from typing import Dict, List, Optional

import httpx

from app.core.config import settings


async def get_user_groups(token: str) -> Optional[List[str]]:
    """
    Fetch groups the user has access to from GitLab.
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.gitlab_url}/groups", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return [{"id": group["id"], "group": group["full_path"]} for group in data]
        elif resp.status_code == 401:
            return None
        else:
            raise Exception(f"GitLab API error: {resp.status_code} - {resp.text}")


async def create_repository(token: str, repo_data: dict) -> str:
    """
    Create a new repository in GitLab using the provided token and data.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "name": repo_data["project_name"],
        "namespace_id": repo_data["group_id"],
        "visibility": "private",
        "initialize_with_readme": False,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.gitlab_url}/projects", headers=headers, json=payload
        )

        if resp.status_code == 201:
            data = resp.json()
            return data["http_url_to_repo"], data["id"]
        elif resp.status_code == 400:
            raise Exception(f"Bad request: {resp.text}")
        elif resp.status_code == 401:
            raise Exception("Unauthorized: invalid or expired token.")
        else:
            raise Exception(f"GitLab API error: {resp.status_code} - {resp.text}")


async def initialize_repository_with_files(
    token: str,
    project_id: int,
    files: Dict[str, str],
    commit_message: str = "Initial commit with template files",
) -> bool:
    """
    Initialize a GitLab repository with multiple files using a single commit.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    actions = []
    for file_path, content in files.items():
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        actions.append(
            {
                "action": "create",
                "file_path": file_path,
                "content": encoded_content,
                "encoding": "base64",
            }
        )

    payload = {
        "branch": "main",
        "commit_message": commit_message,
        "actions": actions,
    }

    # Increased timeout for large commits
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.gitlab_url}/projects/{project_id}/repository/commits",
            headers=headers,
            json=payload,
        )

        if resp.status_code == 201:
            return True
        elif resp.status_code == 400:
            raise Exception(f"Bad request: {resp.text}")
        elif resp.status_code == 401:
            raise Exception("Unauthorized: invalid or expired token.")
        elif resp.status_code == 403:
            raise Exception(
                "Forbidden: insufficient permissions to commit to repository."
            )
        else:
            raise Exception(f"GitLab API error: {resp.status_code} - {resp.text}")
