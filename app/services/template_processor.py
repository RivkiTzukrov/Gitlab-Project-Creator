from enum import Enum
from string import Template
from typing import Dict

import boto3
from fastapi import HTTPException
from jinja2 import BaseLoader, Environment

from app.schemas.repo_models import StackType

_SUPPORTED_STACKS = ["maven", "node", "python", "dotnet"]


class TemplateProcessor:
    def __init__(self, s3_bucket: str, s3_region: str):
        self.s3 = boto3.client("s3", region_name=s3_region)
        self.bucket = s3_bucket
        self.jinja_env = Environment(loader=BaseLoader())
        self.stack_config_map = {
            "maven": "settings.xml",
            "node": ".npmrc",
            "python": "pip.ini",
            "dotnet": "nuget.config",
        }

    async def get_project_files(
        self, project_type: str, repo_name: str, stack: StackType = None
    ) -> Dict[str, str]:
        """Get and process all required files for the project"""

        if stack and stack.value not in _SUPPORTED_STACKS:
            raise HTTPException(400, detail=f"Unsupported stack: {stack.value}")

        files: Dict[str, str] = {}

        # 1. Add CI file
        ci_content = (
            f"templates/{project_type}/{stack.value if stack else ''}.gitlab-ci.yml"
        )
        files[".gitlab-ci.yml"] = await self._process_template(
            ci_content, {"repo_name": repo_name, "stack": stack.value if stack else ""}
        )

        # 2. Add stack-specific files
        if stack:
            # Config file
            config_file = self.stack_config_map[stack.value]
            config_content = await self._get_template(
                f"templates/common/config/{config_file}"
            )
            files[config_file] = config_content

            # Dockerfile
            if project_type != "library":
                files["build/Dockerfile"] = await self._get_template(
                    f"templates/common/build/Dockerfiles/{stack.value}.Dockerfile"
                )
                files["build/.dockerignore"] = await self._get_template(
                    f"templates/common/build/.dockerignore_content"
                )

        # 3. Add appropriate .gitignore
        gitignore_source = (
            f"templates/common/gitignore/{stack.value}.gitignore"
            if stack
            else "templates/delivery/.gitignore"
        )
        files[".gitignore"] = await self._get_template(gitignore_source)

        # 4. Add helm files for monorepo/delivery
        if project_type in ["monorepo", "delivery"]:
            helm_files = ["Chart.yaml", "values.yaml"]
            for h_file in helm_files:
                content = await self._process_template(
                    f"templates/{project_type}/helm/{h_file}", {"repo_name": repo_name}
                )
                files[f"helm/{h_file}"] = content

        # 5. Add README
        readme_content = await self._process_template(
            f"templates/{project_type}/README.md",
            {"repo_name": repo_name, "stack": stack.value if stack else ""},
        )
        files["README.md"] = readme_content

        return files

    async def _process_template(self, s3_key: str, replacements: Dict) -> str:
        """Get and process a template with replacements"""
        raw = await self._get_template(s3_key)
        template = self.jinja_env.from_string(raw)
        return template.render(**replacements)

    async def _get_template(self, s3_key: str) -> str:
        """Get raw template content from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read().decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to load template {s3_key}: {str(e)}"
            )
