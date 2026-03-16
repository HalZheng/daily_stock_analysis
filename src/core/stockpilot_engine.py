# -*- coding: utf-8 -*-
"""
===================================
StockPilot - Personal Investment Analysis Engine
===================================

Design Philosophy:
- Algorithmic rigor belongs to scripts: MA, MACD, divergence, support levels
- Fuzzy reasoning belongs to AI: portfolio context, news sentiment, market trends
- Scripts handle certainty (calculation, statistics, feature extraction)
- AI handles uncertainty (strategy combination, position sizing, style matching)

This module provides:
1. Market environment analysis (indices, market stage)
2. Security pool analysis with technical indicators
3. Compressed data summary for AI interpretation
4. Personalized prompt generation based on user profile
"""

import datetime
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pytz

from data_provider.base import DataFetcherManager
from src.core.stockpilot_config import (
    Assets,
    DataFetchConfig,
    Security,
    UserProfile,
    get_stockpilot_config,
)
from src.core.stockpilot_indicators import DataCompressor, TechnicalSummary

logger = logging.getLogger(__name__)


class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy data types"""

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)


@dataclass
class MarketStage:
    """Market trading stage"""
    stage: str
    today_str: str
    current_time: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "date": self.today_str,
            "time": self.current_time,
        }


class MarketTimer:
    """Market time and stage detector"""

    def __init__(self, tz_name: str = "Asia/Shanghai"):
        self.tz = pytz.timezone(tz_name)
        self.now = datetime.datetime.now(self.tz)
        self.today_str = self.now.strftime("%Y-%m-%d")
        self.current_time = self.now.strftime("%H:%M:%S")

    def get_market_stage(self) -> MarketStage:
        """Determine current market stage"""
        current_time = self.now.time()

        if self.now.weekday() >= 5:
            stage = "休市(周末)"
        else:
            t = lambda h, m: datetime.time(h, m)
            if current_time < t(9, 15):
                stage = "盘前"
            elif t(9, 15) <= current_time < t(9, 30):
                stage = "集合竞价"
            elif t(9, 30) <= current_time < t(11, 30):
                stage = "早盘交易中"
            elif t(11, 30) <= current_time < t(13, 0):
                stage = "午间休市"
            elif t(13, 0) <= current_time < t(15, 0):
                stage = "午盘交易中"
            else:
                stage = "盘后"

        return MarketStage(
            stage=stage,
            today_str=self.today_str,
            current_time=self.current_time,
        )


@dataclass
class SecurityAnalysis:
    """Complete analysis result for a security"""

    code: str
    name: str
    asset_type: str
    groups: List[str]
    tags: List[str]

    technical: TechnicalSummary
    weekly_trend: str
    strategy_note: str

    position: Optional[Dict[str, Any]] = None
    capital_flow_3d: Optional[str] = None
    recent_news: List[str] = field(default_factory=list)
    valuation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "name": self.name,
            "asset_type": self.asset_type,
            "groups": self.groups,
            "tags": self.tags,
            "technical": self.technical.to_dict(),
            "weekly_trend": self.weekly_trend,
            "strategy_note": self.strategy_note,
        }

        if self.position:
            result["position"] = self.position
        if self.capital_flow_3d:
            result["capital_flow_3d"] = self.capital_flow_3d
        if self.recent_news:
            result["recent_news"] = self.recent_news
        if self.valuation:
            result["valuation"] = self.valuation

        return result


@dataclass
class MarketSummary:
    """Market indices summary"""

    name: str
    code: str
    price: float
    change_pct: float
    trend: str
    technical: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "price": self.price,
            "change_pct": self.change_pct,
            "trend": self.trend,
            "technical": self.technical,
        }


class StockPilotEngine:
    """
    StockPilot Analysis Engine

    Integrates:
    1. User profile configuration
    2. Market data fetching
    3. Technical indicator calculation
    4. Data compression for AI
    5. Personalized prompt generation
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = get_stockpilot_config()
        self.timer = MarketTimer()
        self.data_manager = DataFetcherManager()
        self.index_data_cache: Dict[str, pd.DataFrame] = {}

    def _load_index_data(self) -> None:
        """Pre-load index data for RS calculation"""
        for idx_config in self.config.global_config.indices:
            if not idx_config.enabled:
                continue
            try:
                code = self._clean_index_code(idx_config.code)
                df, _ = self.data_manager.get_daily_data(code, days=120)
                if df is not None and not df.empty:
                    self.index_data_cache[idx_config.code] = df
            except Exception as e:
                logger.debug(f"Failed to load index {idx_config.code}: {e}")

    def _get_index_df_for_stock(self, stock_code: str) -> Optional[pd.DataFrame]:
        """Get appropriate index DataFrame for RS calculation"""
        if "SH" in stock_code.upper() or stock_code.startswith("6"):
            index_code = "000001.SH"
        else:
            index_code = "399001.SZ"

        return self.index_data_cache.get(index_code)

    def run(self) -> Dict[str, Any]:
        """
        Run complete analysis and return prompt payload

        Returns:
            Dict containing all analysis data for AI prompt
        """
        logger.info(f"StockPilot starting... [{self.timer.today_str}]")

        active_profile = self.config.get_active_profile()
        if not active_profile:
            logger.error("No active user profile found in configuration")
            return {}

        self._load_index_data()

        market_summary = self._analyze_market()
        holdings_summary, watchlist_summary = self._analyze_securities(active_profile)

        prompt_payload = {
            "user_profile": {
                "name": active_profile.profile_name,
                "style": active_profile.get_active_styles(),
                "preferences": active_profile.get_active_preferences(),
                "cash": (
                    active_profile.assets.available_cash
                    if active_profile.assets.include_cash_in_prompt
                    else "Hidden"
                ),
                "total_capital": (
                    active_profile.assets.total_capital
                    if active_profile.assets.include_cash_in_prompt
                    else "Hidden"
                ),
            },
            "market_context": {
                "stage": self.timer.get_market_stage().to_dict(),
                "indices": {s.name: s.to_dict() for s in market_summary},
            },
            "portfolio": [h.to_dict() for h in holdings_summary],
            "watchlist": [w.to_dict() for w in watchlist_summary],
        }

        return prompt_payload

    def _analyze_market(self) -> List[MarketSummary]:
        """Analyze market indices"""
        logger.info("Analyzing market indices...")

        summaries = []

        for idx_config in self.config.global_config.indices:
            if not idx_config.enabled:
                continue

            logger.info(f"Fetching {idx_config.name} data...")

            try:
                code = idx_config.code
                clean_code = self._clean_index_code(code)

                df, _ = self.data_manager.get_daily_data(clean_code, days=60)

                if df is not None and not df.empty:
                    compressor = DataCompressor(df)
                    tech_summary = compressor.get_summary()

                    summary = MarketSummary(
                        name=idx_config.name,
                        code=idx_config.code,
                        price=tech_summary.price,
                        change_pct=tech_summary.change_pct,
                        trend=tech_summary.trend,
                        technical={
                            "kdj_signal": tech_summary.kdj_signal,
                            "boll_signal": tech_summary.boll_signal,
                            "macd_signal": tech_summary.macd_signal,
                        },
                    )
                    summaries.append(summary)

            except Exception as e:
                logger.warning(f"Failed to analyze {idx_config.name}: {e}")

        return summaries

    def _analyze_securities(
        self, profile: UserProfile
    ) -> tuple[List[SecurityAnalysis], List[SecurityAnalysis]]:
        """Analyze securities in the pool"""
        logger.info("Analyzing security pool...")

        holdings = []
        watchlist = []

        scope = profile.data_fetch_config.consult_scope
        fetch_flow = profile.data_fetch_config.fetch_main_money_flow
        fetch_news = profile.data_fetch_config.fetch_news_sentiment

        for sec in profile.security_pool:
            if not any(grp in scope for grp in sec.groups):
                continue

            logger.info(f"Processing: {sec.name} ({sec.code})...")

            try:
                df = self._get_security_data(sec)
                if df is None:
                    continue

                index_df = self._get_index_df_for_stock(sec.code)
                compressor = DataCompressor(df, index_df)
                tech_summary = compressor.get_summary()

                analysis = SecurityAnalysis(
                    code=sec.code,
                    name=sec.name,
                    asset_type=sec.asset_type,
                    groups=sec.groups,
                    tags=sec.tags,
                    technical=tech_summary,
                    weekly_trend=compressor.get_weekly_trend(),
                    strategy_note=sec.strategy_note,
                )

                if sec.is_holding and sec.position:
                    cost = sec.position.cost
                    curr = tech_summary.price
                    profit_pct = (curr - cost) / cost * 100 if cost > 0 else 0

                    analysis.position = {
                        "shares": sec.position.shares,
                        "cost": cost,
                        "current_value": curr * sec.position.shares,
                        "profit_pct": f"{profit_pct:.2f}%",
                    }

                if fetch_flow and sec.asset_type == "Stock":
                    flow = self._get_capital_flow(sec)
                    if flow:
                        analysis.capital_flow_3d = flow

                if fetch_news:
                    news = self._get_recent_news(sec)
                    if news:
                        analysis.recent_news = news

                if "当前持仓" in sec.groups:
                    holdings.append(analysis)
                else:
                    watchlist.append(analysis)

            except Exception as e:
                logger.warning(f"Failed to analyze {sec.name}: {e}")

        return holdings, watchlist

    def _get_security_data(self, sec: Security) -> Optional[pd.DataFrame]:
        """Get historical data for a security"""
        code = self._clean_stock_code(sec.code)

        try:
            df, _ = self.data_manager.get_daily_data(code, days=120)
            return df
        except Exception as e:
            logger.warning(f"Failed to get data for {sec.code}: {e}")
            return None

    def _clean_stock_code(self, code: str) -> str:
        """Clean stock code format"""
        return "".join(filter(str.isdigit, code))

    def _clean_index_code(self, code: str) -> str:
        """Clean index code format for data fetcher"""
        clean = code.lower().replace(".", "")
        if clean.endswith("sh"):
            clean = "sh" + clean[:-2]
        elif clean.endswith("sz"):
            clean = "sz" + clean[:-2]
        return clean

    def _get_capital_flow(self, sec: Security) -> Optional[str]:
        """Get 3-day capital flow summary using akshare"""
        try:
            import akshare as ak

            code = self._clean_stock_code(sec.code)
            market = "sh" if "SH" in sec.code else "sz"

            flow_df = ak.stock_individual_fund_flow(stock=code, market=market)

            if flow_df is not None and not flow_df.empty:
                net_inflow = flow_df.tail(3)["主力净流入-净额"].sum()
                return f"{net_inflow / 10000:.1f}万"

        except Exception as e:
            logger.debug(f"Failed to get capital flow for {sec.code}: {e}")

        return None

    def _get_recent_news(self, sec: Security) -> List[str]:
        """Get recent news headlines using akshare"""
        try:
            import akshare as ak

            code = self._clean_stock_code(sec.code)
            news_df = ak.stock_news_em(symbol=code)

            if news_df is not None and not news_df.empty:
                return news_df.head(2)["新闻标题"].tolist()

        except Exception as e:
            logger.debug(f"Failed to get news for {sec.code}: {e}")

        return []

    def generate_prompt(self, payload: Dict[str, Any]) -> str:
        """
        Generate AI prompt from analysis payload

        Args:
            payload: Analysis data dictionary

        Returns:
            Formatted prompt string for AI
        """
        json_str = json.dumps(payload, ensure_ascii=False, indent=2, cls=NpEncoder)

        user_styles = payload.get("user_profile", {}).get("style", [])
        user_prefs = payload.get("user_profile", {}).get("preferences", [])

        style_text = "\n".join([f"  - {s}" for s in user_styles]) if user_styles else "  - 无特别设定"
        pref_text = "\n".join([f"  - {p}" for p in user_prefs]) if user_prefs else "  - 无特别要求"

        prompt = f"""# 角色：StockPilot 智能投研专家

# 任务
你是一位专业的投资顾问。请分析以下包含市场环境、持仓状态和自选股技术指标的 JSON 数据，并给出操作建议。

# 用户画像
## 投资风格
{style_text}

## 回答偏好
{pref_text}

# 数据 (JSON)
{json_str}

# 指标解读指南

## 指标趋势描述 (indicator_trend)
- `kdj_trend`: KDJ 三线方向描述，如"K线向上，多头排列"
- `kdj_cross_days`: 金叉/死叉发生天数，1表示刚发生
- `kdj_cross_type`: "金叉"或"死叉"或空
- `macd_hist_trend`: MACD柱子变化趋势，如"红柱放大中"、"绿柱缩短"
- `macd_hist_days`: 红绿柱持续天数
- `rsi_trend`: RSI方向和超买超卖状态
- `volume_price_signal`: 量价配合描述，如"放量上涨，买盘积极"

## 周线指标 (weekly_indicators)
- 周线KDJ和MACD信号，用于确认日线趋势
- `macd_turning_signal`: 周线MACD拐头信号，如"绿柱缩短，即将拐头"、"二次翻绿，底部信号"

## 相对强弱 (rs_strength)
- `vs_index`: 相对大盘的强度，>1.1 表示强于大盘
- `signal`: 如"强于大盘5%"
- `trend`: 相对强度变化趋势

## 背离检测 (divergence)
- `macd_divergence`: "顶背离"或"底背离"或"none"
- 顶背离：股价新高但指标未创新高，注意回调风险
- 底背离：股价新低但指标未创新低，可能反弹

## 波动率 (volatility)
- `atr_pct`: ATR占股价百分比
- `signal`: "高波动"(>3%)、"中等波动"(2-3%)、"低波动"(<2%)

## 连涨连跌 (consecutive_days)
- 连续上涨/下跌天数统计
- 连续5日以上注意反转可能

# 指令
1. **市场大盘分析**：根据 `market_context` 中的指数情况，简要评估当前市场情绪（多头/空头/震荡）。

2. **持仓诊断 (Portfolio)**：
    - 针对 `portfolio` 中的标的，结合技术信号 (KDJ, BOLL, MACD) 和用户的 `strategy_note`，给出【持有】、【加仓】或【减仓/卖出】的建议。
    - 特别关注 `profit_pct` (盈亏比例) 和用户的止损线设定。
    - **重点参考 `indicator_trend` 中的趋势描述**，判断金叉死叉时机。
    - **参考 `weekly_indicators` 确认周线级别趋势**，日线与周线共振更可靠。
    - **关注 `divergence` 背离信号**，顶背离提示风险，底背离提示机会。
    - **参考 `rs_strength` 判断个股强弱**，强于大盘的标的优先关注。

3. **机会发掘 (Watchlist)**：
    - 检查 `watchlist` 中的标的，寻找买入信号（如 KDJ 金叉, BOLL 支撑位反弹, MACD 翻红）。
    - 如果满足条件，建议具体的买入价格区间。
    - **优先推荐 `rs_strength.vs_index > 1.1` 且无顶背离的标的**。
    - **关注 `consecutive_days` 连续下跌后的反弹机会**。

4. **约束条件**：
    - 观点要明确果断。
    - 尽可能提到具体的价格点位。
    - 如果某个标的信号恶劣（例如：死叉 + 空头趋势 + 顶背离），明确建议规避。
    - 如果 `capital_flow_3d` (3日主力资金) 为大幅负值，请在买入建议中提示风险。
    - 如果 `volatility.signal` 为"高波动"，提示风险并建议缩小仓位。

# 输出格式
请使用清晰的 Markdown 格式输出分析报告。
"""
        return prompt

    def run_and_save_prompt(self, output_path: Optional[str] = None) -> str:
        """
        Run analysis and save prompt to prompts folder

        Args:
            output_path: Output file path (optional, auto-generated if None)

        Returns:
            Generated prompt string
        """
        from pathlib import Path

        payload = self.run()

        if not payload:
            logger.error("No analysis data generated")
            return ""

        prompt = self.generate_prompt(payload)

        prompts_dir = Path("prompts")
        prompts_dir.mkdir(exist_ok=True)

        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(prompts_dir / f"{timestamp}_stockpilot_analysis.txt")

        print("\n" + "=" * 50)
        print("StockPilot Prompt Generated")
        print("=" * 50)
        print(prompt)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# StockPilot 智能投研分析\n")
            f.write(f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(prompt)

        print(f"\n[OK] Prompt saved to '{output_path}'")

        return prompt


def run_stockpilot(config_path: Optional[str] = None) -> str:
    """
    Convenience function to run StockPilot analysis

    Args:
        config_path: Optional path to config file

    Returns:
        Generated prompt string
    """
    engine = StockPilotEngine(config_path)
    return engine.run_and_save_prompt()
