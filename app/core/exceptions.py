from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """Base exception for all API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "internal_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(message)


class GitLabAPIError(BaseAPIException):
    """GitLab API related errors"""
    
    def __init__(self, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, "gitlab_api_error", details)


class TemplateProcessingError(BaseAPIException):
    """Template processing and S3 related errors"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, "template_processing_error", details)


class ValidationError(BaseAPIException):
    """Request validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "validation_error", details)


class AuthenticationError(BaseAPIException):
    """Authentication related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, "authentication_error", details)