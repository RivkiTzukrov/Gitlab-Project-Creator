from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model"""
    
    status_code: int
    error: str
    message: str
    details: Dict[str, Any] = {}
    timestamp: str
    
    @classmethod
    def from_exception(cls, exc: Exception, status_code: int = 500, error_type: str = "internal_error") -> "ErrorResponse":
        """Create error response from exception"""
        details = getattr(exc, 'details', {})
        return cls(
            status_code=status_code,
            error=error_type,
            message=str(exc),
            details=details,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )