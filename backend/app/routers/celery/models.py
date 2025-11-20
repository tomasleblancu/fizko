"""
Pydantic models for Celery Tasks API.

Contains all request/response models and enums used by the Celery router.
"""
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class TaskType(str, Enum):
    """Available task types"""
    SYNC_DOCUMENTS = "sii.sync_documents"
    SYNC_DOCUMENTS_ALL = "sii.sync_documents_all_companies"
    SYNC_F29 = "sii.sync_f29"
    SYNC_F29_ALL = "sii.sync_f29_all_companies"
    SYNC_COMPANY_CALENDAR = "calendar.sync_company_calendar"


class TaskStatus(str, Enum):
    """Celery task states"""
    PENDING = "PENDING"      # Task is waiting to be executed
    STARTED = "STARTED"      # Task has been started
    SUCCESS = "SUCCESS"      # Task completed successfully
    FAILURE = "FAILURE"      # Task failed with an error
    RETRY = "RETRY"          # Task is being retried
    REVOKED = "REVOKED"      # Task was revoked/cancelled


# ============================================================================
# Task Parameter Models
# ============================================================================

class SyncDocumentsParams(BaseModel):
    """Parameters for sync_documents task"""
    company_id: str = Field(..., description="Company UUID")
    months: int = Field(1, ge=1, le=12, description="Number of months to sync")
    month_offset: int = Field(0, ge=0, description="Month offset (0=current, 1=last month)")


class SyncDocumentsAllParams(BaseModel):
    """Parameters for sync_documents_all_companies task"""
    months: int = Field(1, ge=1, le=12, description="Number of months to sync")
    month_offset: int = Field(0, ge=0, description="Month offset")


class SyncF29Params(BaseModel):
    """Parameters for sync_f29 task"""
    company_id: str = Field(..., description="Company UUID")
    year: Optional[str] = Field(None, description="Year to sync (YYYY format). Defaults to current year.")


class SyncF29AllParams(BaseModel):
    """Parameters for sync_f29_all_companies task"""
    year: Optional[str] = Field(None, description="Year to sync (YYYY format). Defaults to current year.")


class SyncCompanyCalendarParams(BaseModel):
    """Parameters for sync_company_calendar task"""
    company_id: str = Field(..., description="Company UUID")


# ============================================================================
# Request/Response Models
# ============================================================================

class TaskLaunchRequest(BaseModel):
    """Generic task launch request"""
    task_type: TaskType = Field(..., description="Type of task to launch")
    params: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")


class TaskLaunchResponse(BaseModel):
    """Response when launching a task"""
    success: bool = Field(True, description="Whether task was launched successfully")
    task_id: str = Field(..., description="Celery task ID")
    task_type: str = Field(..., description="Task type/name")
    status: str = Field(..., description="Initial task status (usually PENDING)")
    message: Optional[str] = Field(None, description="Human-readable message")


class TaskStatusResponse(BaseModel):
    """Response for task status query"""
    task_id: str = Field(..., description="Celery task ID")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[Any] = Field(None, description="Task result (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    traceback: Optional[str] = Field(None, description="Error traceback (if failed)")
    meta: Optional[Dict[str, Any]] = Field(None, description="Task metadata")


class AvailableTask(BaseModel):
    """Information about an available task"""
    task_type: str = Field(..., description="Task type identifier")
    name: str = Field(..., description="Task name in Celery")
    description: str = Field(..., description="Human-readable description")
    parameters: Dict[str, Any] = Field(..., description="Expected parameters schema")
