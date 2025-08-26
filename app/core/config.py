from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    gitlab_url: str = "https://gitlab.com/api/v4"
    s3_bucket: str = "your-bucket"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""  # Set to your private S3 endpoint
    aws_access_key_id: str = "123"
    aws_secret_access_key: str = "123"
    log_level: str = "INFO"
    port: int = 8000
    gitlab_client_id: str = ""
    gitlab_client_secret: str = ""
    gitlab_redirect_uri: str = ""
    gitlab_token_url: str = "https://gitlab.com/oauth/token"

    class Config:
        env_file = ".env"


settings = Settings()