from typing import Dict

import boto3
from fastapi import HTTPException
from jinja2 import BaseLoader, Environment

from app.schemas.repo_models import Stack


class TemplateProcessor:
    STACK_CONFIGS = {
        "maven": "settings.xml",
        "node": ".npmrc", 
        "python": "pip.ini",
        "dotnet": "nuget.config",
    }
    
    def __init__(self, s3_bucket: str, s3_region: str):
        self.s3 = boto3.client("s3", region_name=s3_region)
        self.bucket = s3_bucket
        self.jinja_env = Environment(loader=BaseLoader())

    async def get_project_files(self, project_type: str, repo_name: str, stack: Stack = None) -> Dict[str, str]:
        files = {}
        stack_name = stack.value if stack else ""
        
        # CI file
        ci_template = f"templates/{project_type}/{stack_name}.gitlab-ci.yml"
        files[".gitlab-ci.yml"] = await self._process_template(
            ci_template, {"repo_name": repo_name, "stack": stack_name}
        )
        
        # Stack-specific files
        if stack:
            config_file = self.STACK_CONFIGS[stack.value]
            files[config_file] = await self._get_template(f"templates/common/configs/{config_file}")
            
            if project_type != "library":
                files["build/Dockerfile"] = await self._get_template(
                    f"templates/common/build/Dockerfiles/{stack.value}.Dockerfile"
                )
                files["build/.dockerignore"] = await self._get_template(
                    "templates/common/build/.dockerignore"
                )
        
        # Gitignore
        gitignore_path = (
            f"templates/common/gitignore/{stack_name}.gitignore" if stack 
            else "templates/common/gitignore/.gitignore"
        )
        files[".gitignore"] = await self._get_template(gitignore_path)
        
        # Helm files for monorepo/delivery
        if project_type in ["monorepo", "delivery"]:
            for helm_file in ["Chart.yaml", "values.yaml"]:
                content = await self._process_template(
                    f"templates/{project_type}/helm/{helm_file}", 
                    {"repo_name": repo_name}
                )
                files[f"helm/{helm_file}"] = content
        
        # README
        files["README.md"] = await self._process_template(
            "templates/common/README.md.j2",
            {"repo_name": repo_name, "stack": stack_name, "project_type": project_type}
        )
        
        return files

    async def _process_template(self, s3_key: str, replacements: Dict) -> str:
        """Get and process a template with replacements"""
        raw = await self._get_template(s3_key)
        template = self.jinja_env.from_string(raw)
        return template.render(**replacements)

    async def _get_template(self, s3_key: str) -> str:
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read().decode("utf-8")
        except Exception as e:
            raise HTTPException(500, f"Template not found: {s3_key}")
