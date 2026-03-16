# -*- coding: utf-8 -*-
"""StockPilot configuration endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user_optional
from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.stockpilot_config import (
    StockPilotConfigResponse,
    StockPilotConfigUpdateRequest,
    StockPilotConfigSchema,
    StockPilotConflictResponse,
    StockPilotValidationErrorResponse,
    StockPilotValidateResponse,
    StockPilotExportResponse,
    StockPilotImportRequest,
    StockPilotImportResponse,
    StockPilotSummaryResponse,
)
from src.services.stockpilot_config_service import (
    StockPilotConflictError,
    StockPilotValidationError,
    StockPilotConfigService,
    get_stockpilot_config_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_service() -> StockPilotConfigService:
    return get_stockpilot_config_service()


@router.get(
    "/config",
    response_model=StockPilotConfigResponse,
    responses={
        200: {"description": "Configuration loaded"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get StockPilot configuration",
    description="Load and return the complete StockPilot investment profile configuration.",
)
def get_stockpilot_config(
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotConfigResponse:
    """Load and return StockPilot configuration."""
    try:
        payload = service.get_config()
        return StockPilotConfigResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to load StockPilot config: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to load StockPilot configuration",
            },
        )


@router.get(
    "/config/summary",
    response_model=StockPilotSummaryResponse,
    responses={
        200: {"description": "Summary loaded"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get StockPilot configuration summary",
    description="Return a summary of the configuration for dashboard display.",
)
def get_stockpilot_summary(
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotSummaryResponse:
    """Return configuration summary."""
    try:
        payload = service.get_summary()
        return StockPilotSummaryResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to load StockPilot summary: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to load StockPilot summary",
            },
        )


@router.put(
    "/config",
    response_model=StockPilotConfigResponse,
    responses={
        200: {"description": "Configuration updated"},
        400: {"description": "Validation failed", "model": StockPilotValidationErrorResponse},
        409: {"description": "Version conflict", "model": StockPilotConflictResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Update StockPilot configuration",
    description="Validate and persist the complete StockPilot configuration.",
)
def update_stockpilot_config(
    request: StockPilotConfigUpdateRequest,
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotConfigResponse:
    """Update StockPilot configuration."""
    try:
        service.update_config(
            config_version=request.config_version,
            config_data=request.config.model_dump(),
        )
        payload = service.get_config()
        return StockPilotConfigResponse.model_validate(payload)
    except StockPilotValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_failed",
                "message": "StockPilot configuration validation failed",
                "issues": exc.issues,
            },
        )
    except StockPilotConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "config_version_conflict",
                "message": "Configuration has changed, please reload and retry",
                "current_config_version": exc.current_version,
            },
        )
    except Exception as exc:
        logger.error("Failed to update StockPilot config: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to update StockPilot configuration",
            },
        )


@router.post(
    "/config/validate",
    response_model=StockPilotValidateResponse,
    responses={
        200: {"description": "Validation completed"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Validate StockPilot configuration",
    description="Validate configuration without saving.",
)
def validate_stockpilot_config(
    request: StockPilotConfigUpdateRequest,
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotValidateResponse:
    """Validate configuration without saving."""
    try:
        payload = service.validate_config(request.config.model_dump())
        return StockPilotValidateResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to validate StockPilot config: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to validate StockPilot configuration",
            },
        )


@router.get(
    "/config/export",
    response_model=StockPilotExportResponse,
    responses={
        200: {"description": "YAML exported"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Export StockPilot configuration as YAML",
    description="Export the current configuration as a YAML string for download.",
)
def export_stockpilot_config(
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotExportResponse:
    """Export configuration as YAML."""
    try:
        payload = service.export_yaml()
        return StockPilotExportResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to export StockPilot config: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to export StockPilot configuration",
            },
        )


@router.post(
    "/config/import",
    response_model=StockPilotImportResponse,
    responses={
        200: {"description": "YAML imported"},
        400: {"description": "Invalid YAML", "model": StockPilotValidationErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Import StockPilot configuration from YAML",
    description="Parse and validate YAML configuration content without saving.",
)
def import_stockpilot_config(
    request: StockPilotImportRequest,
    service: StockPilotConfigService = Depends(_get_service),
    _user: dict = Depends(get_current_user_optional),
) -> StockPilotImportResponse:
    """Import and validate YAML configuration."""
    try:
        payload = service.import_yaml(request.yaml_content)
        return StockPilotImportResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to import StockPilot config: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to import StockPilot configuration",
            },
        )
