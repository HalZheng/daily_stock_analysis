# -*- coding: utf-8 -*-
"""StockPilot configuration API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PositionSchema(BaseModel):
    """Holding position information."""

    shares: int = Field(default=0, ge=0)
    cost: float = Field(default=0.0, ge=0)
    current_value: float = Field(default=0.0, ge=0)


class SecuritySchema(BaseModel):
    """Security in the pool."""

    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    asset_type: Literal["Stock", "ETF", "Fund", "Bond", "Other"] = Field(default="Stock")
    groups: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    position: Optional[PositionSchema] = None
    strategy_note: str = Field(default="")
    private_note: str = Field(default="")
    linked_ref: str = Field(default="")


class DataFetchConfigSchema(BaseModel):
    """Data fetch preferences."""

    fetch_full_realtime: bool = Field(default=False)
    fetch_main_money_flow: bool = Field(default=True)
    fetch_valuation_metrics: bool = Field(default=True)
    fetch_announcements: bool = Field(default=True)
    fetch_news_sentiment: bool = Field(default=True)
    consult_scope: List[str] = Field(default_factory=lambda: ["当前持仓", "重点观察"])


class AssetsSchema(BaseModel):
    """User assets and position information."""

    total_capital: float = Field(default=100000.0, ge=0)
    available_cash: float = Field(default=15000.0, ge=0)
    include_cash_in_prompt: bool = Field(default=True)


class MacroContextSchema(BaseModel):
    """Macro market context entry."""

    date: str = Field(default="")
    summary: str = Field(default="")


class ResponsePreferenceSchema(BaseModel):
    """AI response preference."""

    content: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)


class InvestmentStyleSchema(BaseModel):
    """Investment style entry."""

    content: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)


class UserProfileSchema(BaseModel):
    """User profile with investment preferences."""

    profile_id: str = Field(..., min_length=1)
    profile_name: str = Field(..., min_length=1)
    is_active: bool = Field(default=True)
    investment_style: List[InvestmentStyleSchema] = Field(default_factory=list)
    current_macro_context: List[MacroContextSchema] = Field(default_factory=list)
    assets: AssetsSchema = Field(default_factory=AssetsSchema)
    data_fetch_config: DataFetchConfigSchema = Field(default_factory=DataFetchConfigSchema)
    response_preference: List[ResponsePreferenceSchema] = Field(default_factory=list)
    security_pool: List[SecuritySchema] = Field(default_factory=list)


class IndexConfigSchema(BaseModel):
    """Market index configuration."""

    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)


class GlobalConfigSchema(BaseModel):
    """Global configuration."""

    version: str = Field(default="1.0.0")
    akshare_retry_count: int = Field(default=3, ge=0, le=10)
    indices: List[IndexConfigSchema] = Field(default_factory=list)


class StockPilotConfigSchema(BaseModel):
    """Complete StockPilot configuration."""

    global_config: GlobalConfigSchema = Field(default_factory=GlobalConfigSchema)
    profiles: List[UserProfileSchema] = Field(default_factory=list)


class StockPilotConfigResponse(BaseModel):
    """Response for StockPilot configuration."""

    config_version: str
    config: StockPilotConfigSchema
    updated_at: Optional[str] = None


class StockPilotConfigUpdateRequest(BaseModel):
    """Request to update StockPilot configuration."""

    config_version: str
    config: StockPilotConfigSchema


class StockPilotValidationIssue(BaseModel):
    """Validation issue details."""

    path: str = Field(..., description="JSON path to the field with issue")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable message")
    severity: Literal["error", "warning"] = Field(default="error")


class StockPilotValidateResponse(BaseModel):
    """Validation result for StockPilot config."""

    valid: bool
    issues: List[StockPilotValidationIssue] = Field(default_factory=list)


class StockPilotValidationErrorResponse(BaseModel):
    """Error response for validation failure."""

    error: str = Field(default="validation_failed")
    message: str
    issues: List[StockPilotValidationIssue]


class StockPilotConflictResponse(BaseModel):
    """Error response for version conflict."""

    error: str = Field(default="config_version_conflict")
    message: str
    current_config_version: str


class StockPilotExportResponse(BaseModel):
    """Response for YAML export."""

    yaml_content: str
    config_version: str
    filename: str


class StockPilotImportRequest(BaseModel):
    """Request to import YAML configuration."""

    yaml_content: str = Field(..., min_length=1)

    @field_validator("yaml_content")
    @classmethod
    def validate_yaml_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("YAML content cannot be empty")
        return v


class StockPilotImportResponse(BaseModel):
    """Response for YAML import."""

    success: bool
    config: Optional[StockPilotConfigSchema] = None
    issues: List[StockPilotValidationIssue] = Field(default_factory=list)
    message: str = ""


class SecurityBrief(BaseModel):
    """Brief security info for list display."""

    code: str
    name: str
    asset_type: str
    groups: List[str]
    tags: List[str]
    is_holding: bool
    shares: int = 0
    cost: float = 0.0


class ProfileBrief(BaseModel):
    """Brief profile info for list display."""

    profile_id: str
    profile_name: str
    is_active: bool
    security_count: int
    holding_count: int


class StockPilotSummaryResponse(BaseModel):
    """Summary response for dashboard."""

    config_version: str
    active_profile: Optional[ProfileBrief] = None
    total_profiles: int
    total_securities: int
    total_holdings: int
    total_capital: float
    available_cash: float
