"""Settings schemas."""

from typing import List, Optional

from pydantic import BaseModel


class BatchWindow(BaseModel):
    """Batch processing time window."""

    start: str  # "09:00"
    end: str  # "09:30"


class SettingsBase(BaseModel):
    """Base settings schema."""

    auto_send_enabled: bool = False
    batch_windows: List[BatchWindow] = []
    calendly_link: Optional[str] = None
    default_nda_url: Optional[str] = None
    llm_model: Optional[str] = None


class SettingsUpdate(SettingsBase):
    """Settings update schema (all fields optional)."""

    auto_send_enabled: Optional[bool] = None
    batch_windows: Optional[List[BatchWindow]] = None


class SettingsResponse(SettingsBase):
    """Settings response schema."""

    id: int
    broker_id: str

    class Config:
        from_attributes = True
