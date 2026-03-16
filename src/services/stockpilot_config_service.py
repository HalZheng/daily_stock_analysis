# -*- coding: utf-8 -*-
"""StockPilot configuration service for YAML-based investment profile management."""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from src.core.stockpilot_config import (
    Assets,
    DataFetchConfig,
    GlobalConfig,
    IndexConfig,
    InvestmentStyle,
    MacroContext,
    Position,
    ResponsePreference,
    Security,
    StockPilotConfig,
    UserProfile,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "stockpilot_config.yaml"


class StockPilotValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, issues: List[Dict[str, Any]]):
        super().__init__("StockPilot configuration validation failed")
        self.issues = issues


class StockPilotConflictError(Exception):
    """Raised when config_version is stale."""

    def __init__(self, current_version: str):
        super().__init__("Configuration version conflict")
        self.current_version = current_version


class StockPilotConfigService:
    """Service layer for StockPilot YAML configuration management."""

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = self._resolve_config_path(config_path)
        self._config: Optional[StockPilotConfig] = None
        self._config_version: Optional[str] = None
        self._updated_at: Optional[str] = None

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve the configuration file path."""
        if config_path:
            return Path(config_path)

        env_path = os.getenv("STOCKPILOT_CONFIG", DEFAULT_CONFIG_PATH)
        path = Path(env_path)
        if not path.is_absolute():
            path = Path(__file__).parent.parent.parent / env_path
        return path

    def _compute_version(self, content: str) -> str:
        """Compute a version hash from file content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _load_raw(self) -> Tuple[Dict[str, Any], str]:
        """Load raw YAML content and compute version."""
        if not self._config_path.exists():
            return {}, ""

        with open(self._config_path, "r", encoding="utf-8") as f:
            content = f.read()

        version = self._compute_version(content)
        data = yaml.safe_load(content) or {}
        return data, version

    def _save_raw(self, data: Dict[str, Any]) -> str:
        """Save data to YAML file and return new version."""
        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        version = self._compute_version(content)

        with open(self._config_path, "w", encoding="utf-8") as f:
            f.write(content)

        return version

    def get_config(self) -> Dict[str, Any]:
        """Load and return the full configuration."""
        data, version = self._load_raw()
        self._config_version = version
        self._updated_at = datetime.now().isoformat()

        if not data:
            config = StockPilotConfig()
        else:
            config = self._parse_config(data)

        self._config = config

        return {
            "config_version": version,
            "config": config.to_dict(),
            "updated_at": self._updated_at,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the configuration for dashboard display."""
        data = self.get_config()
        config_dict = data["config"]
        config = self._config or StockPilotConfig()

        active_profile = config.get_active_profile()
        profile_brief = None
        if active_profile:
            holdings = active_profile.get_holdings()
            profile_brief = {
                "profile_id": active_profile.profile_id,
                "profile_name": active_profile.profile_name,
                "is_active": active_profile.is_active,
                "security_count": len(active_profile.security_pool),
                "holding_count": len(holdings),
            }

        total_securities = sum(len(p.security_pool) for p in config.profiles)
        total_holdings = sum(len(p.get_holdings()) for p in config.profiles)

        total_capital = 0.0
        available_cash = 0.0
        if active_profile:
            total_capital = active_profile.assets.total_capital
            available_cash = active_profile.assets.available_cash

        return {
            "config_version": data["config_version"],
            "active_profile": profile_brief,
            "total_profiles": len(config.profiles),
            "total_securities": total_securities,
            "total_holdings": total_holdings,
            "total_capital": total_capital,
            "available_cash": available_cash,
        }

    def update_config(self, config_version: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and update the full configuration."""
        current_version = self._config_version
        if current_version is None:
            _, current_version = self._load_raw()

        if current_version != config_version:
            raise StockPilotConflictError(current_version=current_version)

        issues = self._validate_config(config_data)
        errors = [i for i in issues if i["severity"] == "error"]
        if errors:
            raise StockPilotValidationError(issues=errors)

        new_version = self._save_raw(config_data)
        self._config_version = new_version
        self._config = self._parse_config(config_data)
        self._updated_at = datetime.now().isoformat()

        return {
            "success": True,
            "config_version": new_version,
            "updated_at": self._updated_at,
        }

    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration without saving."""
        issues = self._validate_config(config_data)
        valid = not any(i["severity"] == "error" for i in issues)
        return {
            "valid": valid,
            "issues": issues,
        }

    def export_yaml(self) -> Dict[str, Any]:
        """Export configuration as YAML string."""
        data, version = self._load_raw()
        if not data:
            config = StockPilotConfig()
            data = config.to_dict()

        yaml_content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        filename = f"stockpilot_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"

        return {
            "yaml_content": yaml_content,
            "config_version": version,
            "filename": filename,
        }

    def import_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Import and validate YAML configuration."""
        issues: List[Dict[str, Any]] = []

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return {
                "success": False,
                "config": None,
                "issues": [
                    {
                        "path": "",
                        "code": "yaml_parse_error",
                        "message": f"Invalid YAML syntax: {str(e)}",
                        "severity": "error",
                    }
                ],
                "message": "Failed to parse YAML content",
            }

        if not isinstance(data, dict):
            return {
                "success": False,
                "config": None,
                "issues": [
                    {
                        "path": "",
                        "code": "invalid_format",
                        "message": "YAML content must be a dictionary",
                        "severity": "error",
                    }
                ],
                "message": "Invalid configuration format",
            }

        issues = self._validate_config(data)
        errors = [i for i in issues if i["severity"] == "error"]

        if errors:
            return {
                "success": False,
                "config": None,
                "issues": issues,
                "message": "Configuration validation failed",
            }

        config = self._parse_config(data)

        return {
            "success": True,
            "config": config.to_dict(),
            "issues": issues,
            "message": "Configuration imported successfully",
        }

    def _validate_config(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate configuration structure and values."""
        issues: List[Dict[str, Any]] = []

        global_config = data.get("global_config", {})
        issues.extend(self._validate_global_config(global_config))

        profiles = data.get("profiles", [])
        if not isinstance(profiles, list):
            issues.append({
                "path": "profiles",
                "code": "invalid_type",
                "message": "profiles must be a list",
                "severity": "error",
            })
        else:
            active_count = 0
            profile_ids = set()
            for idx, profile in enumerate(profiles):
                path_prefix = f"profiles[{idx}]"
                issues.extend(self._validate_profile(profile, path_prefix))

                if profile.get("is_active", False):
                    active_count += 1

                profile_id = profile.get("profile_id", "")
                if profile_id in profile_ids:
                    issues.append({
                        "path": f"{path_prefix}.profile_id",
                        "code": "duplicate_id",
                        "message": f"Duplicate profile_id: {profile_id}",
                        "severity": "error",
                    })
                profile_ids.add(profile_id)

            if active_count > 1:
                issues.append({
                    "path": "profiles",
                    "code": "multiple_active",
                    "message": "Only one profile can be active at a time",
                    "severity": "warning",
                })

        return issues

    def _validate_global_config(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate global configuration section."""
        issues: List[Dict[str, Any]] = []

        version = data.get("version", "")
        if not isinstance(version, str):
            issues.append({
                "path": "global_config.version",
                "code": "invalid_type",
                "message": "version must be a string",
                "severity": "error",
            })

        retry_count = data.get("akshare_retry_count", 3)
        if not isinstance(retry_count, int) or retry_count < 0 or retry_count > 10:
            issues.append({
                "path": "global_config.akshare_retry_count",
                "code": "out_of_range",
                "message": "akshare_retry_count must be an integer between 0 and 10",
                "severity": "error",
            })

        market_monitor = data.get("market_monitor", {})
        indices = market_monitor.get("indices", [])
        if not isinstance(indices, list):
            issues.append({
                "path": "global_config.market_monitor.indices",
                "code": "invalid_type",
                "message": "indices must be a list",
                "severity": "error",
            })
        else:
            seen_codes = set()
            for idx, index in enumerate(indices):
                path_prefix = f"global_config.market_monitor.indices[{idx}]"
                code = index.get("code", "")
                if code in seen_codes:
                    issues.append({
                        "path": f"{path_prefix}.code",
                        "code": "duplicate_code",
                        "message": f"Duplicate index code: {code}",
                        "severity": "warning",
                    })
                seen_codes.add(code)

                if not index.get("code"):
                    issues.append({
                        "path": f"{path_prefix}.code",
                        "code": "required",
                        "message": "Index code is required",
                        "severity": "error",
                    })
                if not index.get("name"):
                    issues.append({
                        "path": f"{path_prefix}.name",
                        "code": "required",
                        "message": "Index name is required",
                        "severity": "error",
                    })

        return issues

    def _validate_profile(self, data: Dict[str, Any], path_prefix: str) -> List[Dict[str, Any]]:
        """Validate a user profile."""
        issues: List[Dict[str, Any]] = []

        if not data.get("profile_id"):
            issues.append({
                "path": f"{path_prefix}.profile_id",
                "code": "required",
                "message": "profile_id is required",
                "severity": "error",
            })

        if not data.get("profile_name"):
            issues.append({
                "path": f"{path_prefix}.profile_name",
                "code": "required",
                "message": "profile_name is required",
                "severity": "error",
            })

        assets = data.get("assets", {})
        if not isinstance(assets, dict):
            issues.append({
                "path": f"{path_prefix}.assets",
                "code": "invalid_type",
                "message": "assets must be a dictionary",
                "severity": "error",
            })
        else:
            total_capital = assets.get("total_capital", 0)
            if not isinstance(total_capital, (int, float)) or total_capital < 0:
                issues.append({
                    "path": f"{path_prefix}.assets.total_capital",
                    "code": "invalid_value",
                    "message": "total_capital must be a non-negative number",
                    "severity": "error",
                })

            available_cash = assets.get("available_cash", 0)
            if not isinstance(available_cash, (int, float)) or available_cash < 0:
                issues.append({
                    "path": f"{path_prefix}.assets.available_cash",
                    "code": "invalid_value",
                    "message": "available_cash must be a non-negative number",
                    "severity": "error",
                })

        security_pool = data.get("security_pool", [])
        if not isinstance(security_pool, list):
            issues.append({
                "path": f"{path_prefix}.security_pool",
                "code": "invalid_type",
                "message": "security_pool must be a list",
                "severity": "error",
            })
        else:
            seen_codes = set()
            for idx, security in enumerate(security_pool):
                sec_path = f"{path_prefix}.security_pool[{idx}]"
                issues.extend(self._validate_security(security, sec_path))

                code = security.get("code", "")
                if code in seen_codes:
                    issues.append({
                        "path": f"{sec_path}.code",
                        "code": "duplicate_code",
                        "message": f"Duplicate security code: {code}",
                        "severity": "warning",
                    })
                seen_codes.add(code)

        return issues

    def _validate_security(self, data: Dict[str, Any], path_prefix: str) -> List[Dict[str, Any]]:
        """Validate a security entry."""
        issues: List[Dict[str, Any]] = []

        if not data.get("code"):
            issues.append({
                "path": f"{path_prefix}.code",
                "code": "required",
                "message": "Security code is required",
                "severity": "error",
            })

        if not data.get("name"):
            issues.append({
                "path": f"{path_prefix}.name",
                "code": "required",
                "message": "Security name is required",
                "severity": "error",
            })

        asset_type = data.get("asset_type", "Stock")
        valid_types = {"Stock", "ETF", "Fund", "Bond", "Other"}
        if asset_type not in valid_types:
            issues.append({
                "path": f"{path_prefix}.asset_type",
                "code": "invalid_enum",
                "message": f"asset_type must be one of: {', '.join(valid_types)}",
                "severity": "error",
            })

        position = data.get("position")
        if position is not None:
            if not isinstance(position, dict):
                issues.append({
                    "path": f"{path_prefix}.position",
                    "code": "invalid_type",
                    "message": "position must be a dictionary",
                    "severity": "error",
                })
            else:
                shares = position.get("shares", 0)
                if not isinstance(shares, int) or shares < 0:
                    issues.append({
                        "path": f"{path_prefix}.position.shares",
                        "code": "invalid_value",
                        "message": "shares must be a non-negative integer",
                        "severity": "error",
                    })

                cost = position.get("cost", 0)
                if not isinstance(cost, (int, float)) or cost < 0:
                    issues.append({
                        "path": f"{path_prefix}.position.cost",
                        "code": "invalid_value",
                        "message": "cost must be a non-negative number",
                        "severity": "error",
                    })

        return issues

    def _parse_config(self, data: Dict[str, Any]) -> StockPilotConfig:
        """Parse dictionary into StockPilotConfig object."""
        from src.core.stockpilot_config import (
            _parse_global_config,
            _parse_user_profile,
        )

        global_config = _parse_global_config(data.get("global_config", {}))
        profiles = [_parse_user_profile(p) for p in data.get("profiles", [])]

        return StockPilotConfig(
            global_config=global_config,
            profiles=profiles,
        )


_stockpilot_config_service: Optional[StockPilotConfigService] = None


def get_stockpilot_config_service() -> StockPilotConfigService:
    """Get or create StockPilotConfigService instance."""
    global _stockpilot_config_service
    if _stockpilot_config_service is None:
        _stockpilot_config_service = StockPilotConfigService()
    return _stockpilot_config_service
