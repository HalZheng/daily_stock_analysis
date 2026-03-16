# -*- coding: utf-8 -*-
"""
===================================
StockPilot - Personal Investment Profile Configuration
===================================

Design Philosophy:
- Algorithmic rigor belongs to scripts: MA, MACD, divergence, support levels
- Fuzzy reasoning belongs to AI: portfolio context, news sentiment, market trends
- Scripts handle certainty (calculation, statistics, feature extraction)
- AI handles uncertainty (strategy combination, position sizing, style matching)

This module provides:
1. User profile management with investment style and risk preferences
2. Security pool with positions, tags, and strategy notes
3. Data fetch preferences for technical indicators
4. AI response preferences for personalized advice
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "stockpilot_config.yaml"


@dataclass
class Position:
    """Holding position information"""
    shares: int = 0
    cost: float = 0.0
    current_value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shares": self.shares,
            "cost": self.cost,
            "current_value": self.current_value,
        }


@dataclass
class Security:
    """Security in the pool"""
    code: str
    name: str
    asset_type: str = "Stock"
    groups: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    position: Optional[Position] = None
    strategy_note: str = ""
    private_note: str = ""
    linked_ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "asset_type": self.asset_type,
            "groups": self.groups,
            "tags": self.tags,
            "position": self.position.to_dict() if self.position else None,
            "strategy_note": self.strategy_note,
            "private_note": self.private_note,
            "linked_ref": self.linked_ref,
        }

    @property
    def is_holding(self) -> bool:
        """Check if this security is currently held"""
        return self.position is not None and self.position.shares > 0


@dataclass
class DataFetchConfig:
    """Data fetch preferences"""
    fetch_full_realtime: bool = False
    fetch_main_money_flow: bool = True
    fetch_valuation_metrics: bool = True
    fetch_announcements: bool = True
    fetch_news_sentiment: bool = True
    consult_scope: List[str] = field(default_factory=lambda: ["当前持仓", "重点观察"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fetch_full_realtime": self.fetch_full_realtime,
            "fetch_main_money_flow": self.fetch_main_money_flow,
            "fetch_valuation_metrics": self.fetch_valuation_metrics,
            "fetch_announcements": self.fetch_announcements,
            "fetch_news_sentiment": self.fetch_news_sentiment,
            "consult_scope": self.consult_scope,
        }


@dataclass
class Assets:
    """User assets and position information"""
    total_capital: float = 100000.0
    available_cash: float = 15000.0
    include_cash_in_prompt: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_capital": self.total_capital,
            "available_cash": self.available_cash,
            "include_cash_in_prompt": self.include_cash_in_prompt,
        }


@dataclass
class MacroContext:
    """Macro market context entry"""
    date: str
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "summary": self.summary,
        }


@dataclass
class ResponsePreference:
    """AI response preference"""
    content: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "enabled": self.enabled,
        }


@dataclass
class InvestmentStyle:
    """Investment style entry"""
    content: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "enabled": self.enabled,
        }


@dataclass
class UserProfile:
    """User profile with investment preferences"""
    profile_id: str
    profile_name: str
    is_active: bool = True
    investment_style: List[InvestmentStyle] = field(default_factory=list)
    current_macro_context: List[MacroContext] = field(default_factory=list)
    assets: Assets = field(default_factory=Assets)
    data_fetch_config: DataFetchConfig = field(default_factory=DataFetchConfig)
    response_preference: List[ResponsePreference] = field(default_factory=list)
    security_pool: List[Security] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "is_active": self.is_active,
            "investment_style": [s.to_dict() for s in self.investment_style],
            "current_macro_context": [c.to_dict() for c in self.current_macro_context],
            "assets": self.assets.to_dict(),
            "data_fetch_config": self.data_fetch_config.to_dict(),
            "response_preference": [p.to_dict() for p in self.response_preference],
            "security_pool": [s.to_dict() for s in self.security_pool],
        }

    def get_active_styles(self) -> List[str]:
        """Get list of enabled investment style descriptions"""
        return [s.content for s in self.investment_style if s.enabled]

    def get_active_preferences(self) -> List[str]:
        """Get list of enabled response preferences"""
        return [p.content for p in self.response_preference if p.enabled]

    def get_securities_by_group(self, group: str) -> List[Security]:
        """Get securities filtered by group"""
        return [s for s in self.security_pool if group in s.groups]

    def get_holdings(self) -> List[Security]:
        """Get all securities currently held"""
        return [s for s in self.security_pool if s.is_holding]

    def get_watchlist(self) -> List[Security]:
        """Get all securities in watchlist (not held)"""
        return [s for s in self.security_pool if not s.is_holding]


@dataclass
class IndexConfig:
    """Market index configuration"""
    code: str
    name: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "enabled": self.enabled,
        }


@dataclass
class GlobalConfig:
    """Global configuration"""
    version: str = "1.0.0"
    akshare_retry_count: int = 3
    indices: List[IndexConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "akshare_retry_count": self.akshare_retry_count,
            "indices": [i.to_dict() for i in self.indices],
        }


@dataclass
class StockPilotConfig:
    """Complete StockPilot configuration"""
    global_config: GlobalConfig = field(default_factory=GlobalConfig)
    profiles: List[UserProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "global_config": self.global_config.to_dict(),
            "profiles": [p.to_dict() for p in self.profiles],
        }

    def get_active_profile(self) -> Optional[UserProfile]:
        """Get the currently active user profile"""
        for profile in self.profiles:
            if profile.is_active:
                return profile
        return None


def _parse_position(data: Optional[Dict]) -> Optional[Position]:
    """Parse position data from dict"""
    if data is None:
        return None
    return Position(
        shares=data.get("shares", 0),
        cost=data.get("cost", 0.0),
        current_value=data.get("current_value", 0.0),
    )


def _parse_security(data: Dict) -> Security:
    """Parse security data from dict"""
    return Security(
        code=data.get("code", ""),
        name=data.get("name", ""),
        asset_type=data.get("asset_type", "Stock"),
        groups=data.get("groups", []),
        tags=data.get("tags", []),
        position=_parse_position(data.get("position")),
        strategy_note=data.get("strategy_note", ""),
        private_note=data.get("private_note", ""),
        linked_ref=data.get("linked_ref", ""),
    )


def _parse_data_fetch_config(data: Dict) -> DataFetchConfig:
    """Parse data fetch config from dict"""
    return DataFetchConfig(
        fetch_full_realtime=data.get("fetch_full_realtime", False),
        fetch_main_money_flow=data.get("fetch_main_money_flow", True),
        fetch_valuation_metrics=data.get("fetch_valuation_metrics", True),
        fetch_announcements=data.get("fetch_announcements", True),
        fetch_news_sentiment=data.get("fetch_news_sentiment", True),
        consult_scope=data.get("consult_scope", ["当前持仓", "重点观察"]),
    )


def _parse_assets(data: Dict) -> Assets:
    """Parse assets from dict"""
    return Assets(
        total_capital=data.get("total_capital", 100000.0),
        available_cash=data.get("available_cash", 15000.0),
        include_cash_in_prompt=data.get("include_cash_in_prompt", True),
    )


def _parse_user_profile(data: Dict) -> UserProfile:
    """Parse user profile from dict"""
    investment_style = [
        InvestmentStyle(content=s.get("content", ""), enabled=s.get("enabled", True))
        for s in data.get("investment_style", [])
    ]

    macro_context = [
        MacroContext(date=c.get("date", ""), summary=c.get("summary", ""))
        for c in data.get("current_macro_context", [])
    ]

    response_preference = [
        ResponsePreference(content=p.get("content", ""), enabled=p.get("enabled", True))
        for p in data.get("response_preference", [])
    ]

    security_pool = [_parse_security(s) for s in data.get("security_pool", [])]

    return UserProfile(
        profile_id=data.get("profile_id", ""),
        profile_name=data.get("profile_name", ""),
        is_active=data.get("is_active", True),
        investment_style=investment_style,
        current_macro_context=macro_context,
        assets=_parse_assets(data.get("assets", {})),
        data_fetch_config=_parse_data_fetch_config(data.get("data_fetch_config", {})),
        response_preference=response_preference,
        security_pool=security_pool,
    )


def _parse_global_config(data: Dict) -> GlobalConfig:
    """Parse global config from dict"""
    market_monitor = data.get("market_monitor", {})
    indices_data = market_monitor.get("indices", [])
    indices = [
        IndexConfig(
            code=i.get("code", ""),
            name=i.get("name", ""),
            enabled=i.get("enabled", True),
        )
        for i in indices_data
    ]

    return GlobalConfig(
        version=data.get("version", "1.0.0"),
        akshare_retry_count=data.get("akshare_retry_count", 3),
        indices=indices,
    )


def load_stockpilot_config(config_path: Optional[str] = None) -> StockPilotConfig:
    """
    Load StockPilot configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        StockPilotConfig: Parsed configuration object
    """
    if config_path is None:
        config_path = os.getenv("STOCKPILOT_CONFIG", DEFAULT_CONFIG_PATH)

    config_file = Path(config_path)

    if not config_file.is_absolute():
        config_file = Path(__file__).parent.parent.parent / config_path

    if not config_file.exists():
        logger.warning(f"StockPilot config file not found: {config_file}")
        return StockPilotConfig()

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty StockPilot config file: {config_file}")
            return StockPilotConfig()

        global_config = _parse_global_config(data.get("global_config", {}))
        profiles = [_parse_user_profile(p) for p in data.get("profiles", [])]

        logger.info(f"Loaded StockPilot config: version={global_config.version}, profiles={len(profiles)}")

        return StockPilotConfig(
            global_config=global_config,
            profiles=profiles,
        )

    except Exception as e:
        logger.error(f"Failed to load StockPilot config: {e}")
        return StockPilotConfig()


_stockpilot_config_cache: Optional[StockPilotConfig] = None


def get_stockpilot_config(reload: bool = False) -> StockPilotConfig:
    """
    Get StockPilot configuration (cached).

    Args:
        reload: Force reload from file.

    Returns:
        StockPilotConfig: Configuration object
    """
    global _stockpilot_config_cache

    if _stockpilot_config_cache is None or reload:
        _stockpilot_config_cache = load_stockpilot_config()

    return _stockpilot_config_cache
