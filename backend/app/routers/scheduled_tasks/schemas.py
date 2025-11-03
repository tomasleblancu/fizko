"""Pydantic schemas for scheduled tasks API."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ScheduledTaskCreate(BaseModel):
    """Request model for creating a new scheduled task."""

    name: str = Field(..., min_length=1, max_length=200, description="Unique task name")
    task: str = Field(..., description="Celery task name (e.g., 'sii.sync_documents')")
    schedule_type: Literal["interval", "crontab"] = Field(
        ..., description="Schedule type: interval or crontab"
    )

    # Interval schedule fields
    interval_every: Optional[int] = Field(None, gt=0, description="Interval count (e.g., 30)")
    interval_period: Optional[Literal["days", "hours", "minutes", "seconds"]] = Field(
        None, description="Interval period"
    )

    # Crontab schedule fields
    crontab_minute: Optional[str] = Field(None, description="Crontab minute (0-59, *, etc.)")
    crontab_hour: Optional[str] = Field(None, description="Crontab hour (0-23, *, etc.)")
    crontab_day_of_week: Optional[str] = Field(
        None, description="Crontab day of week (0-6, *, mon-fri, etc.)"
    )
    crontab_day_of_month: Optional[str] = Field(
        None, description="Crontab day of month (1-31, *, etc.)"
    )
    crontab_month_of_year: Optional[str] = Field(
        None, description="Crontab month (1-12, *, jan-jun, etc.)"
    )
    crontab_timezone: Optional[str] = Field(
        "America/Santiago", description="Timezone for crontab schedule"
    )

    # Task arguments
    args: List[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")

    # Queue routing
    queue: Optional[str] = Field(None, description="Queue name (high, default, low)")
    priority: Optional[int] = Field(None, ge=0, le=10, description="Task priority (0-10)")

    # Execution control
    enabled: bool = Field(True, description="Whether task is enabled")
    one_off: bool = Field(False, description="Run once and disable automatically")
    run_now: bool = Field(False, description="Execute immediately on creation (not stored in DB)")
    expires: Optional[datetime] = Field(None, description="Task expiration datetime")

    # Task limits
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum retry attempts")
    soft_time_limit: Optional[int] = Field(None, gt=0, description="Soft time limit (seconds)")
    hard_time_limit: Optional[int] = Field(None, gt=0, description="Hard time limit (seconds)")

    # Metadata
    description: Optional[str] = Field(None, description="Human-readable description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name doesn't contain special characters."""
        if not v.replace("-", "").replace("_", "").replace(" ", "").isalnum():
            raise ValueError("Name can only contain letters, numbers, hyphens, and underscores")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate schedule configuration after initialization."""
        if self.schedule_type == "interval":
            if not self.interval_every or not self.interval_period:
                raise ValueError("interval_every and interval_period required for interval schedule")
        elif self.schedule_type == "crontab":
            # Defaults are fine, but at least minute and hour should be set
            if self.crontab_minute is None:
                self.crontab_minute = "*"
            if self.crontab_hour is None:
                self.crontab_hour = "*"


class ScheduledTaskUpdate(BaseModel):
    """Request model for updating an existing scheduled task."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    enabled: Optional[bool] = None
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None
    queue: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    one_off: Optional[bool] = None
    expires: Optional[datetime] = None
    max_retries: Optional[int] = Field(None, ge=0)
    soft_time_limit: Optional[int] = Field(None, gt=0)
    hard_time_limit: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None

    # Schedule update fields (optional)
    # Interval schedule fields
    interval_every: Optional[int] = Field(None, gt=0, description="Interval count (e.g., 30)")
    interval_period: Optional[Literal["days", "hours", "minutes", "seconds"]] = Field(
        None, description="Interval period"
    )

    # Crontab schedule fields
    crontab_minute: Optional[str] = Field(None, description="Crontab minute (0-59, *, etc.)")
    crontab_hour: Optional[str] = Field(None, description="Crontab hour (0-23, *, etc.)")
    crontab_day_of_week: Optional[str] = Field(
        None, description="Crontab day of week (0-6, *, mon-fri, etc.)"
    )
    crontab_day_of_month: Optional[str] = Field(
        None, description="Crontab day of month (1-31, *, etc.)"
    )
    crontab_month_of_year: Optional[str] = Field(
        None, description="Crontab month (1-12, *, jan-jun, etc.)"
    )
    crontab_timezone: Optional[str] = Field(
        None, description="Timezone for crontab schedule"
    )


class IntervalSchedule(BaseModel):
    """Interval schedule details."""
    every: int
    period: str


class CrontabSchedule(BaseModel):
    """Crontab schedule details."""
    minute: str
    hour: str
    day_of_week: str
    day_of_month: str
    month_of_year: str
    timezone: str


class ScheduledTaskResponse(BaseModel):
    """Response model for scheduled task details."""

    id: int
    name: str
    task: str
    schedule_type: str
    schedule_display: str

    # Schedule details (mutually exclusive - one will be None)
    interval: Optional[IntervalSchedule] = None
    crontab: Optional[CrontabSchedule] = None

    args: List[Any]
    kwargs: Dict[str, Any]
    queue: Optional[str]
    priority: Optional[int]
    enabled: bool
    one_off: bool
    expires: Optional[datetime]
    max_retries: Optional[int]
    soft_time_limit: Optional[int]
    hard_time_limit: Optional[int]
    description: Optional[str]
    date_changed: datetime
    last_run_at: Optional[datetime]
    total_run_count: int

    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    """Response model for task execution history."""

    id: int
    task_id: str
    task_name: Optional[str]
    status: str
    worker: Optional[str]
    result: Optional[Dict[str, Any]]
    traceback: Optional[str]
    date_created: datetime
    date_done: Optional[datetime]

    class Config:
        from_attributes = True
