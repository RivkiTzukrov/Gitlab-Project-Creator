import base64
import logging
from typing import Dict, List, Tuple

import httpx

from app.core.config import settings
from app.core.exceptions import AuthenticationError, GitLabAPIError

logger = logging.getLogger(__name__)


class GitLabService:
    def __init__(self):
        self.base_url = settings.gitlab_url
        self.timeout = 30.0

    def _get_headers(self, token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def get_user_groups(self, token: str) -> List[Dict[str, str]]:
        all_groups = []
        page = 1

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                response = await client.get(
                    f"{self.base_url}/groups",
                    headers=self._get_headers(token),
                    params={"page": page, "per_page": 100},
                )

                if response.status_code == 401:
                    raise AuthenticationError("Invalid access token")
                if response.status_code != 200:
                    raise GitLabAPIError("Failed to fetch user groups", response.status_code)

                groups_data = response.json()
                if not groups_data:
                    break

                all_groups.extend(
                    [{"id": g["id"], "group": g["full_path"]} for g in groups_data]
                )

                if len(groups_data) < 100:
                    break

                page += 1



        return all_groups

    async def create_repository(self, token: str, repo_data: Dict) -> Tuple[str, int]:
        payload = {
            "name": repo_data["project_name"],
            "namespace_id": repo_data["group_id"],
            "visibility": "private",
            "initialize_with_readme": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/projects",
                headers=self._get_headers(token),
                json=payload,
            )

        if response.status_code == 401:
            raise AuthenticationError("Invalid access token")
        if response.status_code != 201:
            error_details = {"gitlab_response": response.json() if response.content else {}}
            raise GitLabAPIError("Repository creation failed", response.status_code, error_details)

        repo_data = response.json()
        return repo_data["http_url_to_repo"], repo_data["id"]

    async def add_files(
        self, token: str, project_id: int, files: Dict[str, str]
    ) -> None:
        actions = []
        for file_path, content in files.items():
            encoded_content = base64.b64encode(content.encode()).decode()
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
            "commit_message": "Initial project setup",
            "actions": actions,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/projects/{project_id}/repository/commits",
                headers=self._get_headers(token),
                json=payload,
            )

        if response.status_code == 401:
            raise AuthenticationError("Invalid access token")
        if response.status_code != 201:
            error_details = {"gitlab_response": response.json() if response.content else {}}
            raise GitLabAPIError("Failed to initialize repository", response.status_code, error_details)

    async def set_project_variables(
        self, token: str, project_id: int, variables: Dict[str, str]
    ) -> None:
        for key, value in variables.items():
            payload = {"key": key, "value": value, "protected": False, "masked": False}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/projects/{project_id}/variables",
                    headers=self._get_headers(token),
                    json=payload,
                )

            if response.status_code not in [201, 400]:  # 400 = already exists
                logger.warning(f"Failed to set variable {key}")
