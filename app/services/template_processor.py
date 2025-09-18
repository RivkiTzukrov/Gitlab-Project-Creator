from typing import Dict, Optional
from boto3 import client as boto3_client
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from jinja2 import BaseLoader, Environment
from app.core.config import settings
from app.core.exceptions import TemplateProcessingError
from app.schemas.repo_models import Stack


class TemplateProcessor:
    def __init__(self, s3_bucket: str, s3_region: str):
        self.bucket = s3_bucket
        
        s3_config = {
            "region_name": s3_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        if settings.s3_endpoint_url:
            s3_config["endpoint_url"] = settings.s3_endpoint_url
            
        self.s3_client = boto3_client("s3", **s3_config)
        self.jinja_env = Environment(
            loader=BaseLoader(),
            variable_start_string="{%",
            variable_end_string="%}",
            block_start_string="{#",
            block_end_string="#}"
        )

    async def get_project_files(self, project_type: str, repo_name: str, stack: Optional[Stack] = None) -> Dict[str, str]:
        variables = {
            "repo_name": repo_name, 
            "repo_title": repo_name.replace('-', ' ').title(),
            "stack": stack.value if stack else "", 
            "project_type": project_type
        }
        files = {}
        
        if stack:
            files.update(await self._get_template_directory(f"templates/stacks/{stack.value}/", variables))
        
        ci_path = f"templates/project-types/{project_type}/{stack.value if stack else ''}.gitlab-ci.yml.j2"
        files[".gitlab-ci.yml"] = await self._process_template(ci_path, variables)
        
        if project_type in ["microservice", "monorepo"] and stack:
            files["build/Dockerfile"] = await self._get_template(f"templates/docker/{stack.value}.Dockerfile")
            files["build/.dockerignore"] = await self._get_template("templates/docker/.dockerignore")
        
        if project_type in ["monorepo", "delivery"]:
            files.update(await self._get_template_directory("templates/common/helm/", variables, "helm/"))
        
        files["README.md"] = await self._process_template("templates/common/README.md.j2", variables)

        return files

    async def _get_template_directory(self, prefix: str, variables: Dict, target_prefix: str = "") -> Dict[str, str]:
        files = {}
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            if 'Contents' not in response:
                return files
                
            for obj in response['Contents']:
                s3_key = obj['Key']
                if s3_key == prefix:
                    continue
                    
                relative_path = s3_key[len(prefix):]
                actual_path = f"{target_prefix}{relative_path}"
                
                if s3_key.endswith('.j2'):
                    actual_path = actual_path[:-3]
                    files[actual_path] = await self._process_template(s3_key, variables)
                else:
                    files[actual_path] = await self._get_template(s3_key)
                    
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code != "NoSuchKey":  # Ignore missing directories
                raise TemplateProcessingError(f"Failed to list templates in {prefix}: {error_code}", 500, {"prefix": prefix})
            
        return files

    async def _process_template(self, s3_key: str, variables: Dict) -> str:
        try:
            raw_template = await self._get_template(s3_key)
            template = self.jinja_env.from_string(raw_template)
            return template.render(**variables)
        except TemplateProcessingError:
            raise
        except (EndpointConnectionError, NoCredentialsError) as e:
            details = {"template": s3_key, "variables": list(variables.keys())}
            raise TemplateProcessingError("S3 connection failed - check configuration", 500, details)
        except Exception as e:
            details = {"template": s3_key, "variables": list(variables.keys()), "error": str(e)}
            raise TemplateProcessingError(f"Template processing failed: {s3_key}", 500, details)

    async def _get_template(self, s3_key: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            details = {"error_code": error_code}
            if error_code == "NoSuchKey":
                raise TemplateProcessingError(f"Template not found: {s3_key}", 404, details)
            raise TemplateProcessingError(f"S3 error: {error_code}", 500, details)
        except (EndpointConnectionError, NoCredentialsError):
            raise TemplateProcessingError("S3 connection failed - check configuration", 500, {})
        except Exception as e:
            raise TemplateProcessingError(f"Failed to load template: {s3_key}", 500, {"error": str(e)})