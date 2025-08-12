import logging
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from jinja2 import BaseLoader, Environment

from app.core.config import settings
from app.schemas.repo_models import Stack

logger = logging.getLogger(__name__)


class TemplateProcessor:
    STACK_CONFIGS = {
        "maven": "settings.xml",
        "node": ".npmrc",
        "python": "pip.ini",
        "dotnet": "nuget.config",
    }

    def __init__(self, s3_bucket: str, s3_region: str):
        self.bucket = s3_bucket

        # Configure S3 client for private instance
        s3_config = {
            "region_name": s3_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }

        # Add custom endpoint if specified
        if hasattr(settings, "s3_endpoint_url") and settings.s3_endpoint_url:
            s3_config["endpoint_url"] = settings.s3_endpoint_url

        self.s3_client = boto3.client("s3", **s3_config)
        self.jinja_env = Environment(
            loader=BaseLoader(),
            variable_start_string="{%",
            variable_end_string="%}",
            block_start_string="{#",
            block_end_string="#}",
        )

    async def get_project_files(
        self, project_type: str, repo_name: str, stack: Optional[Stack] = None
    ) -> Dict[str, str]:
        files = {}
        stack_name = stack.value if stack else ""

        # CI file
        files[".gitlab-ci.yml"] = await self._process_template(
            f"templates/{project_type}/{stack_name}.gitlab-ci.yml.j2",
            {"repo_name": repo_name, "stack": stack_name},
        )

        # Stack-specific files
        if stack:
            config_file = self.STACK_CONFIGS[stack.value]
            files[config_file] = await self._get_template(
                f"templates/common/configs/{config_file}"
            )

            if project_type != "library":
                files["build/Dockerfile"] = await self._get_template(
                    f"templates/common/build/Dockerfiles/{stack.value}.Dockerfile"
                )
                files["build/.dockerignore"] = await self._get_template(
                    "templates/common/build/.dockerignore"
                )

        # Gitignore
        gitignore_path = (
            f"templates/common/gitignore/{stack_name}.gitignore"
            if stack
            else "templates/common/gitignore/.gitignore"
        )
        files[".gitignore"] = await self._get_template(gitignore_path)

        # Helm files for deployment projects
        if project_type in ["monorepo", "delivery"]:
            for helm_file in ["Chart.yaml", "values.yaml"]:
                content = await self._process_template(
                    f"templates/{project_type}/helm/{helm_file}.j2",
                    {"repo_name": repo_name},
                )
                files[f"helm/{helm_file}"] = content

            # Add .helmignore (no processing needed)
            files["helm/.helmignore"] = await self._get_template(
                "templates/common/.helmignore"
            )

        # README
        files["README.md"] = await self._process_template(
            "templates/common/README.md.j2",
            {"repo_name": repo_name, "stack": stack_name, "project_type": project_type},
        )

        return files

    async def _process_template(self, s3_key: str, variables: Dict) -> str:
        raw_template = await self._get_template(s3_key)
        template = self.jinja_env.from_string(raw_template)
        return template.render(**variables)

    async def _get_template(self, s3_key: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                raise HTTPException(404, f"Template not found: {s3_key}")
            raise HTTPException(500, f"S3 error: {error_code}")
