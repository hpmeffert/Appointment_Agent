from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .enums import ErrorCategory


class ProviderError(BaseModel):
    provider: str
    provider_operation: str
    error_code: Optional[str] = None
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    message: str
    retryable: bool = False
    raw_reference: Optional[str] = None


class SharedError(BaseModel):
    error_id: str
    error_type: str
    error_category: ErrorCategory
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False
    provider: Optional[str] = None
    provider_operation: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    journey_id: Optional[str] = None
    timestamp_utc: Optional[str] = None
