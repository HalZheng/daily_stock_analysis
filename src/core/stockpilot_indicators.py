# -*- coding: utf-8 -*-
"""
===================================
StockPilot - Technical Indicators Calculator
===================================

Design Philosophy:
- Algorithmic rigor belongs to scripts: MA, MACD, divergence, support levels
- Scripts handle certainty (calculation, statistics, feature extraction)
- This module provides precise technical indicator calculations

Indicators included:
1. Moving Averages (MA5, MA10, MA20, MA60)
2. KDJ (Stochastic Oscillator)
3. BOLL (Bollinger Bands)
4. MACD (Moving Average Convergence Divergence)
5. RSI (Relative Strength Index)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class IndicatorTrend:
    """Trend description for indicators (giving 'soul' to dead numbers)"""
    kdj_trend: str = "unknown"
    kdj_cross_days: int = 0
    kdj_cross_type: str = ""
    macd_hist_trend: str = "unknown"
    macd_hist_days: int = 0
    rsi_trend: str = "unknown"
    volume_price_signal: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kdj_trend": self.kdj_trend,
            "kdj_cross_days": self.kdj_cross_days,
            "kdj_cross_type": self.kdj_cross_type,
            "macd_hist_trend": self.macd_hist_trend,
            "macd_hist_days": self.macd_hist_days,
            "rsi_trend": self.rsi_trend,
            "volume_price_signal": self.volume_price_signal,
        }


@dataclass
class WeeklyIndicators:
    """Weekly-level detailed indicators"""
    kdj_k: float = 50.0
    kdj_d: float = 50.0
    kdj_j: float = 50.0
    kdj_signal: str = "unknown"
    macd_dif: float = 0.0
    macd_dea: float = 0.0
    macd_hist: float = 0.0
    macd_hist_trend: str = "unknown"
    macd_turning_signal: str = "unknown"
    trend: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kdj": {
                "K": round(self.kdj_k, 1),
                "D": round(self.kdj_d, 1),
                "J": round(self.kdj_j, 1),
                "signal": self.kdj_signal,
            },
            "macd": {
                "DIF": round(self.macd_dif, 3),
                "DEA": round(self.macd_dea, 3),
                "HIST": round(self.macd_hist, 3),
                "hist_trend": self.macd_hist_trend,
                "turning_signal": self.macd_turning_signal,
            },
            "trend": self.trend,
        }


@dataclass
class RSStrength:
    """Relative Strength indicator"""
    vs_index: float = 1.0
    signal: str = "neutral"
    trend: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vs_index": round(self.vs_index, 2),
            "signal": self.signal,
            "trend": self.trend,
        }


@dataclass
class DivergenceSignal:
    """Divergence detection result"""
    macd_divergence: str = "none"
    macd_divergence_type: str = ""
    kdj_divergence: str = "none"
    kdj_divergence_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "macd_divergence": self.macd_divergence,
            "macd_divergence_type": self.macd_divergence_type,
            "kdj_divergence": self.kdj_divergence,
            "kdj_divergence_type": self.kdj_divergence_type,
        }


@dataclass
class VolatilityInfo:
    """Volatility metrics"""
    atr: float = 0.0
    atr_pct: float = 0.0
    signal: str = "normal"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atr": round(self.atr, 2),
            "atr_pct": f"{self.atr_pct:.2f}%",
            "signal": self.signal,
        }


@dataclass
class ConsecutiveDays:
    """Consecutive up/down days"""
    up_days: int = 0
    down_days: int = 0
    signal: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "up_days": self.up_days,
            "down_days": self.down_days,
            "signal": self.signal,
        }


@dataclass
class TechnicalSummary:
    """Compressed technical indicator summary for AI analysis"""

    price: float = 0.0
    change_pct: float = 0.0
    volume_ratio: float = 0.0

    trend: str = "unknown"
    trend_strength: int = 50

    kdj_k: float = 0.0
    kdj_d: float = 0.0
    kdj_j: float = 0.0
    kdj_signal: str = "neutral"

    boll_upper: float = 0.0
    boll_mid: float = 0.0
    boll_lower: float = 0.0
    boll_position: float = 0.5
    boll_signal: str = "normal"
    boll_width: float = 0.0

    macd_dif: float = 0.0
    macd_dea: float = 0.0
    macd_hist: float = 0.0
    macd_signal: str = "neutral"

    rsi_6: float = 50.0
    rsi_12: float = 50.0
    rsi_24: float = 50.0
    rsi_signal: str = "neutral"

    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0

    bias_ma5: float = 0.0
    bias_ma10: float = 0.0
    bias_ma20: float = 0.0

    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)

    weekly_trend: str = "unknown"

    indicator_trend: Optional[IndicatorTrend] = None
    weekly_indicators: Optional[WeeklyIndicators] = None
    rs_strength: Optional[RSStrength] = None
    divergence: Optional[DivergenceSignal] = None
    volatility: Optional[VolatilityInfo] = None
    consecutive_days: Optional[ConsecutiveDays] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "price": self.price,
            "change_pct": self.change_pct,
            "volume_ratio": self.volume_ratio,
            "trend": self.trend,
            "trend_strength": self.trend_strength,
            "kdj": {
                "K": round(self.kdj_k, 1),
                "D": round(self.kdj_d, 1),
                "J": round(self.kdj_j, 1),
                "signal": self.kdj_signal,
            },
            "boll": {
                "upper": round(self.boll_upper, 2),
                "mid": round(self.boll_mid, 2),
                "lower": round(self.boll_lower, 2),
                "position": f"{self.boll_position:.0%}",
                "signal": self.boll_signal,
            },
            "macd": {
                "DIF": round(self.macd_dif, 3),
                "DEA": round(self.macd_dea, 3),
                "HIST": round(self.macd_hist, 3),
                "signal": self.macd_signal,
            },
            "rsi": {
                "RSI6": round(self.rsi_6, 1),
                "RSI12": round(self.rsi_12, 1),
                "RSI24": round(self.rsi_24, 1),
                "signal": self.rsi_signal,
            },
            "ma": {
                "MA5": round(self.ma5, 2),
                "MA10": round(self.ma10, 2),
                "MA20": round(self.ma20, 2),
                "MA60": round(self.ma60, 2),
            },
            "bias": {
                "bias_ma5": f"{self.bias_ma5:.2f}%",
                "bias_ma10": f"{self.bias_ma10:.2f}%",
                "bias_ma20": f"{self.bias_ma20:.2f}%",
            },
            "support_levels": [round(s, 2) for s in self.support_levels[:3]],
            "resistance_levels": [round(r, 2) for r in self.resistance_levels[:3]],
            "weekly_trend": self.weekly_trend,
        }

        if self.indicator_trend:
            result["indicator_trend"] = self.indicator_trend.to_dict()
        if self.weekly_indicators:
            result["weekly_indicators"] = self.weekly_indicators.to_dict()
        if self.rs_strength:
            result["rs_strength"] = self.rs_strength.to_dict()
        if self.divergence:
            result["divergence"] = self.divergence.to_dict()
        if self.volatility:
            result["volatility"] = self.volatility.to_dict()
        if self.consecutive_days:
            result["consecutive_days"] = self.consecutive_days.to_dict()

        return result


class IndicatorCalculator:
    """
    Technical Indicator Calculator

    Provides precise calculations for:
    - Moving Averages (MA)
    - KDJ (Stochastic Oscillator)
    - BOLL (Bollinger Bands)
    - MACD (Moving Average Convergence Divergence)
    - RSI (Relative Strength Index)
    """

    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names to Chinese standard"""
        df = df.copy()

        col_map = {
            "date": "日期",
            "open": "开盘",
            "close": "收盘",
            "high": "最高",
            "low": "最低",
            "volume": "成交量",
            "amount": "成交额",
        }

        for eng, chn in col_map.items():
            if eng in df.columns and chn not in df.columns:
                df.rename(columns={eng: chn}, inplace=True)

        return df

    @staticmethod
    def add_ma(df: pd.DataFrame, windows: List[int] = None) -> pd.DataFrame:
        """
        Add Moving Averages

        Args:
            df: DataFrame with '收盘' column
            windows: MA windows, default [5, 10, 20, 60]

        Returns:
            DataFrame with MA columns added
        """
        if windows is None:
            windows = [5, 10, 20, 60]

        df = df.copy()

        for window in windows:
            df[f"MA{window}"] = df["收盘"].rolling(window=window).mean()

        return df

    @staticmethod
    def add_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        Add KDJ Indicator

        Formula:
        RSV = (Close - LowN) / (HighN - LowN) * 100
        K = SMA(RSV, M1)
        D = SMA(K, M2)
        J = 3K - 2D

        Args:
            df: DataFrame with '收盘', '最高', '最低' columns
            n: RSV period (default 9)
            m1: K smoothing period (default 3)
            m2: D smoothing period (default 3)

        Returns:
            DataFrame with K, D, J columns added
        """
        df = df.copy()

        low_n = df["最低"].rolling(window=n).min()
        high_n = df["最高"].rolling(window=n).max()

        rsv = (df["收盘"] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)

        df["K"] = rsv.ewm(com=m1 - 1, adjust=False).mean()
        df["D"] = df["K"].ewm(com=m2 - 1, adjust=False).mean()
        df["J"] = 3 * df["K"] - 2 * df["D"]

        return df

    @staticmethod
    def add_boll(df: pd.DataFrame, n: int = 20, k: int = 2) -> pd.DataFrame:
        """
        Add Bollinger Bands

        Formula:
        MID = MA(Close, N)
        UPPER = MID + K * STD(Close, N)
        LOWER = MID - K * STD(Close, N)
        WIDTH = (UPPER - LOWER) / MID

        Args:
            df: DataFrame with '收盘' column
            n: Period (default 20)
            k: Standard deviation multiplier (default 2)

        Returns:
            DataFrame with BOLL_MID, BOLL_UP, BOLL_LOW, BOLL_WIDTH columns
        """
        df = df.copy()

        df["BOLL_MID"] = df["收盘"].rolling(window=n).mean()
        std = df["收盘"].rolling(window=n).std()

        df["BOLL_UP"] = df["BOLL_MID"] + k * std
        df["BOLL_LOW"] = df["BOLL_MID"] - k * std
        df["BOLL_WIDTH"] = (df["BOLL_UP"] - df["BOLL_LOW"]) / df["BOLL_MID"]

        return df

    @staticmethod
    def add_macd(
        df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """
        Add MACD Indicator

        Formula:
        DIF = EMA(Close, Fast) - EMA(Close, Slow)
        DEA = EMA(DIF, Signal)
        MACD = (DIF - DEA) * 2

        Args:
            df: DataFrame with '收盘' column
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)

        Returns:
            DataFrame with MACD_DIF, MACD_DEA, MACD_HIST columns
        """
        df = df.copy()

        ema_fast = df["收盘"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["收盘"].ewm(span=slow, adjust=False).mean()

        df["MACD_DIF"] = ema_fast - ema_slow
        df["MACD_DEA"] = df["MACD_DIF"].ewm(span=signal, adjust=False).mean()
        df["MACD_HIST"] = (df["MACD_DIF"] - df["MACD_DEA"]) * 2

        return df

    @staticmethod
    def add_rsi(
        df: pd.DataFrame, periods: List[int] = None
    ) -> pd.DataFrame:
        """
        Add RSI Indicator

        Formula:
        RS = AvgGain / AvgLoss
        RSI = 100 - (100 / (1 + RS))

        Args:
            df: DataFrame with '收盘' column
            periods: RSI periods, default [6, 12, 24]

        Returns:
            DataFrame with RSI_N columns
        """
        if periods is None:
            periods = [6, 12, 24]

        df = df.copy()

        delta = df["收盘"].diff()

        for period in periods:
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.fillna(50)

            df[f"RSI_{period}"] = rsi

        return df

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with all indicators added
        """
        if df is None or df.empty:
            return df

        df = IndicatorCalculator.normalize_columns(df)

        df = IndicatorCalculator.add_ma(df)
        df = IndicatorCalculator.add_kdj(df)
        df = IndicatorCalculator.add_boll(df)
        df = IndicatorCalculator.add_macd(df)
        df = IndicatorCalculator.add_rsi(df)

        return df


class TechnicalAnalyzer:
    """
    Technical Analysis Engine

    Analyzes technical indicators and generates human-readable signals
    for AI to interpret.
    """

    @staticmethod
    def analyze_kdj(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze KDJ indicator and generate signal

        Signals:
        - 金叉 (Golden Cross): K crosses above D from below
        - 死叉 (Death Cross): K crosses below D from above
        - 超买 (Overbought): J > 100
        - 超卖 (Oversold): J < 0
        - 多头 (Bullish): K > D and both rising
        - 空头 (Bearish): K < D and both falling
        """
        if len(df) < 2:
            return {"signal": "数据不足", "K": 0, "D": 0, "J": 0}

        last = df.iloc[-1]
        prev = df.iloc[-2]

        k, d, j = last["K"], last["D"], last["J"]
        prev_k, prev_d = prev["K"], prev["D"]

        signal = "中性"

        if k > d and prev_k <= prev_d:
            signal = "金叉"
        elif k < d and prev_k >= prev_d:
            signal = "死叉"
        elif j > 100:
            signal = "超买"
        elif j < 0:
            signal = "超卖"
        elif k > d and k > prev_k:
            signal = "多头"
        elif k < d and k < prev_k:
            signal = "空头"

        return {
            "K": round(k, 1),
            "D": round(d, 1),
            "J": round(j, 1),
            "signal": signal,
        }

    @staticmethod
    def analyze_boll(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Bollinger Bands and generate signal

        Signals:
        - 突破上轨 (Break above upper): Price > UPPER
        - 跌破下轨 (Break below lower): Price < LOWER
        - 收敛变盘前夕 (Squeeze): Width narrowing significantly
        - 正常 (Normal): Price within bands
        """
        if len(df) < 20:
            return {"signal": "数据不足", "position": 0.5}

        last = df.iloc[-1]
        close = last["收盘"]
        upper = last["BOLL_UP"]
        mid = last["BOLL_MID"]
        lower = last["BOLL_LOW"]
        width = last["BOLL_WIDTH"]

        if upper != lower:
            position = (close - lower) / (upper - lower)
        else:
            position = 0.5

        signal = "正常"

        if close > upper:
            signal = "突破上轨"
        elif close < lower:
            signal = "跌破下轨"
        elif width < df["BOLL_WIDTH"].tail(20).mean() * 0.7:
            signal = "收敛变盘前夕"

        return {
            "upper": round(upper, 2),
            "mid": round(mid, 2),
            "lower": round(lower, 2),
            "position": position,
            "signal": signal,
        }

    @staticmethod
    def analyze_macd(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze MACD indicator and generate signal

        Signals:
        - 零轴上金叉 (Golden cross above zero): DIF crosses DEA above 0
        - 金叉 (Golden cross): DIF crosses DEA from below
        - 死叉 (Death cross): DIF crosses DEA from above
        - 多头 (Bullish): DIF > DEA > 0
        - 空头 (Bearish): DIF < DEA < 0
        - 红柱放大 (Red bar expanding): HIST > 0 and increasing
        - 绿柱放大 (Green bar expanding): HIST < 0 and decreasing
        """
        if len(df) < 2:
            return {"signal": "数据不足", "DIF": 0, "DEA": 0, "HIST": 0}

        last = df.iloc[-1]
        prev = df.iloc[-2]

        dif, dea, hist = last["MACD_DIF"], last["MACD_DEA"], last["MACD_HIST"]
        prev_dif, prev_dea, prev_hist = prev["MACD_DIF"], prev["MACD_DEA"], prev["MACD_HIST"]

        signal = "中性"

        if dif > dea and prev_dif <= prev_dea:
            if dif > 0:
                signal = "零轴上金叉"
            else:
                signal = "金叉"
        elif dif < dea and prev_dif >= prev_dea:
            signal = "死叉"
        elif dif > dea > 0:
            if hist > prev_hist:
                signal = "多头增强"
            else:
                signal = "多头"
        elif dif < dea < 0:
            if hist < prev_hist:
                signal = "空头增强"
            else:
                signal = "空头"
        elif hist > 0:
            signal = "红柱"
        else:
            signal = "绿柱"

        return {
            "DIF": round(dif, 3),
            "DEA": round(dea, 3),
            "HIST": round(hist, 3),
            "signal": signal,
        }

    @staticmethod
    def analyze_rsi(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze RSI indicator and generate signal

        Signals:
        - 超买 (Overbought): RSI > 70
        - 超卖 (Oversold): RSI < 30
        - 强势 (Strong): 50 < RSI < 70
        - 弱势 (Weak): 30 < RSI < 50
        - 中性 (Neutral): RSI around 50
        """
        if "RSI_6" not in df.columns:
            return {"signal": "数据不足", "RSI6": 50, "RSI12": 50, "RSI24": 50}

        last = df.iloc[-1]
        rsi6 = last.get("RSI_6", 50)
        rsi12 = last.get("RSI_12", 50)
        rsi24 = last.get("RSI_24", 50)

        avg_rsi = (rsi6 + rsi12 + rsi24) / 3

        if avg_rsi > 70:
            signal = "超买"
        elif avg_rsi < 30:
            signal = "超卖"
        elif avg_rsi > 50:
            signal = "强势"
        elif avg_rsi < 50:
            signal = "弱势"
        else:
            signal = "中性"

        return {
            "RSI6": round(rsi6, 1),
            "RSI12": round(rsi12, 1),
            "RSI24": round(rsi24, 1),
            "signal": signal,
        }

    @staticmethod
    def analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze trend based on MA alignment

        Trend status:
        - 强势多头 (Strong Bull): MA5 > MA10 > MA20, spreading
        - 多头排列 (Bull): MA5 > MA10 > MA20
        - 弱势多头 (Weak Bull): MA5 > MA10, MA10 < MA20
        - 盘整 (Consolidation): MAs intertwined
        - 弱势空头 (Weak Bear): MA5 < MA10, MA10 > MA20
        - 空头排列 (Bear): MA5 < MA10 < MA20
        - 强势空头 (Strong Bear): MA5 < MA10 < MA20, spreading
        """
        if len(df) < 20:
            return {"trend": "数据不足", "strength": 50}

        last = df.iloc[-1]
        ma5 = last.get("MA5", 0)
        ma10 = last.get("MA10", 0)
        ma20 = last.get("MA20", 0)
        ma60 = last.get("MA60", 0)

        if ma5 > ma10 > ma20:
            spread = (ma5 - ma20) / ma20 * 100 if ma20 > 0 else 0
            if spread > 5:
                trend = "强势多头"
                strength = 90
            else:
                trend = "多头排列"
                strength = 75
        elif ma5 > ma10 and ma10 <= ma20:
            trend = "弱势多头"
            strength = 55
        elif ma5 < ma10 < ma20:
            spread = (ma20 - ma5) / ma5 * 100 if ma5 > 0 else 0
            if spread > 5:
                trend = "强势空头"
                strength = 10
            else:
                trend = "空头排列"
                strength = 25
        elif ma5 < ma10 and ma10 >= ma20:
            trend = "弱势空头"
            strength = 40
        else:
            trend = "盘整"
            strength = 50

        return {
            "trend": trend,
            "strength": strength,
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
        }

    @staticmethod
    def calculate_bias(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate bias (deviation from MA)

        Bias = (Close - MA) / MA * 100%
        """
        if len(df) < 20:
            return {"bias_ma5": 0, "bias_ma10": 0, "bias_ma20": 0}

        last = df.iloc[-1]
        close = last["收盘"]
        ma5 = last.get("MA5", close)
        ma10 = last.get("MA10", close)
        ma20 = last.get("MA20", close)

        bias_ma5 = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
        bias_ma10 = (close - ma10) / ma10 * 100 if ma10 > 0 else 0
        bias_ma20 = (close - ma20) / ma20 * 100 if ma20 > 0 else 0

        return {
            "bias_ma5": round(bias_ma5, 2),
            "bias_ma10": round(bias_ma10, 2),
            "bias_ma20": round(bias_ma20, 2),
        }

    @staticmethod
    def find_support_resistance(df: pd.DataFrame) -> Dict[str, List[float]]:
        """
        Find support and resistance levels

        Support: MA5, MA10, MA20, recent lows
        Resistance: Recent highs
        """
        if len(df) < 20:
            return {"support": [], "resistance": []}

        last = df.iloc[-1]
        close = last["收盘"]
        ma5 = last.get("MA5", 0)
        ma10 = last.get("MA10", 0)
        ma20 = last.get("MA20", 0)

        support = []
        resistance = []

        tolerance = 0.02

        for ma in [ma5, ma10, ma20]:
            if ma > 0 and ma < close:
                distance = abs(close - ma) / ma
                if distance <= tolerance * 2:
                    support.append(ma)

        recent_low = df["最低"].tail(20).min()
        if recent_low < close:
            support.append(recent_low)

        recent_high = df["最高"].tail(20).max()
        if recent_high > close:
            resistance.append(recent_high)

        support = sorted(list(set(support)), reverse=True)[:3]
        resistance = sorted(list(set(resistance)))[:3]

        return {
            "support": [round(s, 2) for s in support],
            "resistance": [round(r, 2) for r in resistance],
        }

    @staticmethod
    def get_weekly_trend(df: pd.DataFrame) -> str:
        """
        Resample to weekly and check trend

        Returns:
            "多头趋势" or "空头趋势" or "未知"
        """
        if df is None or len(df) < 20:
            return "未知"

        df_w = df.copy()

        if "日期" in df_w.columns:
            df_w["日期"] = pd.to_datetime(df_w["日期"])
            df_w.set_index("日期", inplace=True)
        elif df_w.index.name != "日期":
            df_w.index = pd.to_datetime(df_w.index)

        try:
            df_w = df_w.resample("W").agg({"收盘": "last"})
            df_w["MA20"] = df_w["收盘"].rolling(20).mean()

            if len(df_w) < 2:
                return "未知"

            last = df_w.iloc[-1]
            if last["收盘"] > last["MA20"]:
                return "多头趋势"
            else:
                return "空头趋势"
        except Exception:
            return "未知"

    @staticmethod
    def analyze_indicator_trend(df: pd.DataFrame) -> IndicatorTrend:
        """
        Analyze indicator trends and cross timing (giving 'soul' to dead numbers)

        Returns:
            IndicatorTrend: Trend descriptions for KDJ, MACD, RSI, volume-price
        """
        trend = IndicatorTrend()

        if df is None or len(df) < 10:
            return trend

        last = df.iloc[-1]

        k, d, j = last.get("K", 50), last.get("D", 50), last.get("J", 50)
        prev_k = df.iloc[-2].get("K", 50)
        prev_d = df.iloc[-2].get("D", 50)

        if k > d:
            if prev_k <= prev_d:
                trend.kdj_cross_type = "金叉"
                for i in range(2, min(10, len(df))):
                    if df.iloc[-i]["K"] <= df.iloc[-i]["D"]:
                        trend.kdj_cross_days = i - 1
                        break
                else:
                    trend.kdj_cross_days = 1
            trend.kdj_trend = "K线向上，多头排列" if k > prev_k else "K线走平，多头减弱"
        elif k < d:
            if prev_k >= prev_d:
                trend.kdj_cross_type = "死叉"
                for i in range(2, min(10, len(df))):
                    if df.iloc[-i]["K"] >= df.iloc[-i]["D"]:
                        trend.kdj_cross_days = i - 1
                        break
                else:
                    trend.kdj_cross_days = 1
            trend.kdj_trend = "K线向下，空头排列" if k < prev_k else "K线走平，空头减弱"
        else:
            trend.kdj_trend = "KDJ走平，方向不明"

        hist = last.get("MACD_HIST", 0)
        prev_hist = df.iloc[-2].get("MACD_HIST", 0)

        if hist > 0:
            if prev_hist <= 0:
                trend.macd_hist_trend = "红柱刚出现"
                trend.macd_hist_days = 1
            elif hist > prev_hist:
                trend.macd_hist_trend = "红柱放大中"
                for i in range(1, min(10, len(df))):
                    if df.iloc[-(i + 1)].get("MACD_HIST", 0) <= 0:
                        trend.macd_hist_days = i
                        break
            else:
                trend.macd_hist_trend = "红柱缩短"
        else:
            if prev_hist >= 0:
                trend.macd_hist_trend = "绿柱刚出现"
                trend.macd_hist_days = 1
            elif hist < prev_hist:
                trend.macd_hist_trend = "绿柱放大中"
                for i in range(1, min(10, len(df))):
                    if df.iloc[-(i + 1)].get("MACD_HIST", 0) >= 0:
                        trend.macd_hist_days = i
                        break
            else:
                trend.macd_hist_trend = "绿柱缩短"

        rsi6 = last.get("RSI_6", 50)
        prev_rsi6 = df.iloc[-2].get("RSI_6", 50)

        if rsi6 > 70:
            trend.rsi_trend = "超买区域，注意回调风险"
        elif rsi6 < 30:
            trend.rsi_trend = "超卖区域，可能反弹"
        elif rsi6 > prev_rsi6:
            trend.rsi_trend = "RSI向上，动能增强"
        elif rsi6 < prev_rsi6:
            trend.rsi_trend = "RSI向下，动能减弱"
        else:
            trend.rsi_trend = "RSI走平"

        close = last["收盘"]
        prev_close = df.iloc[-2]["收盘"]
        volume = last.get("成交量", 0)
        prev_volume = df.iloc[-2].get("成交量", 0)

        vol_change = (volume / prev_volume - 1) * 100 if prev_volume > 0 else 0
        price_change = (close / prev_close - 1) * 100 if prev_close > 0 else 0

        if price_change > 0 and vol_change > 10:
            trend.volume_price_signal = "放量上涨，买盘积极"
        elif price_change > 0 and vol_change < -10:
            trend.volume_price_signal = "缩量上涨，上涨乏力"
        elif price_change < 0 and vol_change > 10:
            trend.volume_price_signal = "放量下跌，抛压较重"
        elif price_change < 0 and vol_change < -10:
            trend.volume_price_signal = "缩量下跌，卖盘枯竭"
        else:
            trend.volume_price_signal = "量价正常"

        return trend

    @staticmethod
    def analyze_weekly_indicators(df: pd.DataFrame) -> WeeklyIndicators:
        """
        Analyze weekly-level detailed indicators

        Returns:
            WeeklyIndicators: Weekly KDJ, MACD with turning signals
        """
        weekly = WeeklyIndicators()

        if df is None or len(df) < 60:
            return weekly

        df_w = df.copy()

        if "日期" in df_w.columns:
            df_w["日期"] = pd.to_datetime(df_w["日期"])
            df_w.set_index("日期", inplace=True)
        elif df_w.index.name != "日期":
            df_w.index = pd.to_datetime(df_w.index)

        try:
            df_w = df_w.resample("W").agg({
                "开盘": "first",
                "收盘": "last",
                "最高": "max",
                "最低": "min",
                "成交量": "sum"
            })

            if len(df_w) < 10:
                return weekly

            df_w = IndicatorCalculator.add_kdj(df_w)
            df_w = IndicatorCalculator.add_macd(df_w)
            df_w["MA20"] = df_w["收盘"].rolling(20).mean()

            last = df_w.iloc[-1]
            prev = df_w.iloc[-2] if len(df_w) > 1 else last

            weekly.kdj_k = last.get("K", 50)
            weekly.kdj_d = last.get("D", 50)
            weekly.kdj_j = last.get("J", 50)

            k, d = weekly.kdj_k, weekly.kdj_d
            prev_k, prev_d = prev.get("K", 50), prev.get("D", 50)

            if k > d and prev_k <= prev_d:
                weekly.kdj_signal = "周线金叉"
            elif k < d and prev_k >= prev_d:
                weekly.kdj_signal = "周线死叉"
            elif k > d:
                weekly.kdj_signal = "周线多头"
            else:
                weekly.kdj_signal = "周线空头"

            weekly.macd_dif = last.get("MACD_DIF", 0)
            weekly.macd_dea = last.get("MACD_DEA", 0)
            weekly.macd_hist = last.get("MACD_HIST", 0)

            hist = weekly.macd_hist
            prev_hist = prev.get("MACD_HIST", 0)

            if hist > 0:
                weekly.macd_hist_trend = "红柱"
                if hist > prev_hist:
                    weekly.macd_hist_trend = "红柱放大"
                else:
                    weekly.macd_hist_trend = "红柱缩短"
            else:
                weekly.macd_hist_trend = "绿柱"
                if hist < prev_hist:
                    weekly.macd_hist_trend = "绿柱放大"
                else:
                    weekly.macd_hist_trend = "绿柱缩短"

            if hist > 0 and prev_hist <= 0:
                weekly.macd_turning_signal = "刚翻红，趋势转强"
            elif hist < 0 and prev_hist >= 0:
                weekly.macd_turning_signal = "刚翻绿，趋势转弱"
            elif hist > 0 and hist < prev_hist and prev_hist > 0:
                weekly.macd_turning_signal = "红柱缩短，动能减弱"
            elif hist < 0 and hist > prev_hist and prev_hist < 0:
                weekly.macd_turning_signal = "绿柱缩短，即将拐头"
            elif hist < 0 and hist > prev_hist and len(df_w) >= 3:
                prev2_hist = df_w.iloc[-3].get("MACD_HIST", 0)
                if prev2_hist < prev_hist < hist:
                    weekly.macd_turning_signal = "二次翻绿，底部信号"
            else:
                weekly.macd_turning_signal = "趋势延续"

            close = last["收盘"]
            ma20 = last.get("MA20", close)

            if close > ma20:
                weekly.trend = "周线多头趋势"
            else:
                weekly.trend = "周线空头趋势"

        except Exception as e:
            logger.debug(f"Weekly indicator calculation failed: {e}")

        return weekly

    @staticmethod
    def calculate_rs_strength(df: pd.DataFrame, index_df: pd.DataFrame = None) -> RSStrength:
        """
        Calculate Relative Strength vs index

        RS = Stock Performance / Index Performance

        Args:
            df: Stock DataFrame
            index_df: Index DataFrame (optional, defaults to equal performance)

        Returns:
            RSStrength: Relative strength metrics
        """
        rs = RSStrength()

        if df is None or len(df) < 20:
            return rs

        try:
            stock_change = (df.iloc[-1]["收盘"] / df.iloc[-20]["收盘"] - 1) * 100

            if index_df is not None and len(index_df) >= 20:
                index_change = (index_df.iloc[-1]["收盘"] / index_df.iloc[-20]["收盘"] - 1) * 100
                if index_change != 0:
                    rs.vs_index = stock_change / index_change
                else:
                    rs.vs_index = 1.0
            else:
                rs.vs_index = 1.0 + stock_change / 100

            if rs.vs_index > 1.1:
                rs.signal = f"强于大盘{(rs.vs_index - 1) * 100:.0f}%"
            elif rs.vs_index < 0.9:
                rs.signal = f"弱于大盘{(1 - rs.vs_index) * 100:.0f}%"
            else:
                rs.signal = "与大盘同步"

            if len(df) >= 40:
                prev_rs = (df.iloc[-20]["收盘"] / df.iloc[-40]["收盘"] - 1) * 100
                if stock_change > prev_rs:
                    rs.trend = "相对强度上升中"
                elif stock_change < prev_rs:
                    rs.trend = "相对强度下降中"
                else:
                    rs.trend = "相对强度稳定"

        except Exception as e:
            logger.debug(f"RS calculation failed: {e}")

        return rs

    @staticmethod
    def detect_divergence(df: pd.DataFrame) -> DivergenceSignal:
        """
        Detect MACD and KDJ divergence

        Divergence types:
        - Top divergence (顶背离): Price makes higher high, indicator makes lower high
        - Bottom divergence (底背离): Price makes lower low, indicator makes higher low

        Args:
            df: DataFrame with price and indicator data

        Returns:
            DivergenceSignal: Detected divergence signals
        """
        div = DivergenceSignal()

        if df is None or len(df) < 30:
            return div

        try:
            close = df["收盘"].values
            macd_hist = df["MACD_HIST"].values if "MACD_HIST" in df.columns else None
            kdj_j = df["J"].values if "J" in df.columns else None

            if macd_hist is not None:
                lookback = min(20, len(df) - 1)

                recent_high_idx = np.argmax(close[-lookback:])
                recent_low_idx = np.argmin(close[-lookback:])

                if recent_high_idx > lookback // 2:
                    prev_high_idx = np.argmax(close[-lookback:-recent_high_idx - 1]) if recent_high_idx < lookback - 1 else -1
                    if prev_high_idx >= 0:
                        actual_prev_idx = -(lookback - prev_high_idx)
                        actual_recent_idx = -(lookback - recent_high_idx)

                        if (close[actual_recent_idx] > close[actual_prev_idx] and
                            macd_hist[actual_recent_idx] < macd_hist[actual_prev_idx]):
                            div.macd_divergence = "顶背离"
                            div.macd_divergence_type = f"股价新高但MACD未创新高，注意回调风险"

                if recent_low_idx > lookback // 2:
                    prev_low_idx = np.argmin(close[-lookback:-recent_low_idx - 1]) if recent_low_idx < lookback - 1 else -1
                    if prev_low_idx >= 0:
                        actual_prev_idx = -(lookback - prev_low_idx)
                        actual_recent_idx = -(lookback - recent_low_idx)

                        if (close[actual_recent_idx] < close[actual_prev_idx] and
                            macd_hist[actual_recent_idx] > macd_hist[actual_prev_idx]):
                            div.macd_divergence = "底背离"
                            div.macd_divergence_type = f"股价新低但MACD未创新低，可能反弹"

            if kdj_j is not None:
                lookback = min(15, len(df) - 1)

                recent_high_idx = np.argmax(close[-lookback:])
                recent_low_idx = np.argmin(close[-lookback:])

                if recent_high_idx > lookback // 2:
                    prev_high_idx = np.argmax(close[-lookback:-recent_high_idx - 1]) if recent_high_idx < lookback - 1 else -1
                    if prev_high_idx >= 0:
                        actual_prev_idx = -(lookback - prev_high_idx)
                        actual_recent_idx = -(lookback - recent_high_idx)

                        if (close[actual_recent_idx] > close[actual_prev_idx] and
                            kdj_j[actual_recent_idx] < kdj_j[actual_prev_idx] and
                            kdj_j[actual_recent_idx] > 80):
                            div.kdj_divergence = "顶背离"
                            div.kdj_divergence_type = f"KDJ顶背离，超买区注意风险"

                if recent_low_idx > lookback // 2:
                    prev_low_idx = np.argmin(close[-lookback:-recent_low_idx - 1]) if recent_low_idx < lookback - 1 else -1
                    if prev_low_idx >= 0:
                        actual_prev_idx = -(lookback - prev_low_idx)
                        actual_recent_idx = -(lookback - recent_low_idx)

                        if (close[actual_recent_idx] < close[actual_prev_idx] and
                            kdj_j[actual_recent_idx] > kdj_j[actual_prev_idx] and
                            kdj_j[actual_recent_idx] < 20):
                            div.kdj_divergence = "底背离"
                            div.kdj_divergence_type = f"KDJ底背离，超卖区可能反弹"

        except Exception as e:
            logger.debug(f"Divergence detection failed: {e}")

        return div

    @staticmethod
    def calculate_volatility(df: pd.DataFrame, period: int = 14) -> VolatilityInfo:
        """
        Calculate ATR (Average True Range) for volatility measurement

        ATR = SMA(True Range, N)
        True Range = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))

        Args:
            df: DataFrame with OHLC data
            period: ATR period (default 14)

        Returns:
            VolatilityInfo: Volatility metrics
        """
        vol = VolatilityInfo()

        if df is None or len(df) < period + 1:
            return vol

        try:
            high = df["最高"].values
            low = df["最低"].values
            close = df["收盘"].values

            tr = np.zeros(len(df))
            tr[0] = high[0] - low[0]

            for i in range(1, len(df)):
                tr[i] = max(
                    high[i] - low[i],
                    abs(high[i] - close[i - 1]),
                    abs(low[i] - close[i - 1])
                )

            atr = np.mean(tr[-period:])
            vol.atr = atr

            current_price = close[-1]
            vol.atr_pct = (atr / current_price) * 100 if current_price > 0 else 0

            if vol.atr_pct > 3:
                vol.signal = "高波动"
            elif vol.atr_pct > 2:
                vol.signal = "中等波动"
            else:
                vol.signal = "低波动"

        except Exception as e:
            logger.debug(f"Volatility calculation failed: {e}")

        return vol

    @staticmethod
    def calculate_consecutive_days(df: pd.DataFrame) -> ConsecutiveDays:
        """
        Calculate consecutive up/down days

        Args:
            df: DataFrame with close prices

        Returns:
            ConsecutiveDays: Up/down day counts
        """
        cons = ConsecutiveDays()

        if df is None or len(df) < 2:
            return cons

        try:
            close = df["收盘"].values
            changes = np.diff(close)

            last_change = changes[-1]

            if last_change > 0:
                for i in range(len(changes) - 1, -1, -1):
                    if changes[i] > 0:
                        cons.up_days += 1
                    else:
                        break

                if cons.up_days >= 5:
                    cons.signal = f"连续上涨{cons.up_days}日，注意回调"
                elif cons.up_days >= 3:
                    cons.signal = f"连续上涨{cons.up_days}日"
                else:
                    cons.signal = "上涨趋势"

            elif last_change < 0:
                for i in range(len(changes) - 1, -1, -1):
                    if changes[i] < 0:
                        cons.down_days += 1
                    else:
                        break

                if cons.down_days >= 5:
                    cons.signal = f"连续下跌{cons.down_days}日，可能反弹"
                elif cons.down_days >= 3:
                    cons.signal = f"连续下跌{cons.down_days}日"
                else:
                    cons.signal = "下跌趋势"
            else:
                cons.signal = "平盘"

        except Exception as e:
            logger.debug(f"Consecutive days calculation failed: {e}")

        return cons


class DataCompressor:
    """
    Compress rich DataFrame data into AI-readable JSON summary

    Design Philosophy:
    - Give indicator values without context is meaningless
    - Provide trend descriptions and signals for LLM to interpret
    - Scripts handle certainty, AI handles uncertainty
    """

    def __init__(self, df: pd.DataFrame, index_df: pd.DataFrame = None):
        self.df = IndicatorCalculator.add_all_indicators(df)
        self.index_df = index_df

    def get_summary(self) -> TechnicalSummary:
        """
        Generate compressed technical summary

        Returns:
            TechnicalSummary: Compressed summary for AI analysis
        """
        if self.df is None or len(self.df) < 20:
            return TechnicalSummary(trend="数据不足")

        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]

        summary = TechnicalSummary()

        summary.price = float(last["收盘"])
        summary.change_pct = round(
            ((last["收盘"] - prev["收盘"]) / prev["收盘"]) * 100, 2
        )

        vol_5d_avg = self.df["成交量"].iloc[-6:-1].mean()
        if vol_5d_avg > 0:
            summary.volume_ratio = round(float(last["成交量"]) / vol_5d_avg, 2)

        trend_info = TechnicalAnalyzer.analyze_trend(self.df)
        summary.trend = trend_info["trend"]
        summary.trend_strength = trend_info["strength"]
        summary.ma5 = trend_info["ma5"]
        summary.ma10 = trend_info["ma10"]
        summary.ma20 = trend_info["ma20"]
        summary.ma60 = trend_info["ma60"]

        kdj_info = TechnicalAnalyzer.analyze_kdj(self.df)
        summary.kdj_k = kdj_info["K"]
        summary.kdj_d = kdj_info["D"]
        summary.kdj_j = kdj_info["J"]
        summary.kdj_signal = kdj_info["signal"]

        boll_info = TechnicalAnalyzer.analyze_boll(self.df)
        summary.boll_upper = boll_info["upper"]
        summary.boll_mid = boll_info["mid"]
        summary.boll_lower = boll_info["lower"]
        summary.boll_position = boll_info["position"]
        summary.boll_signal = boll_info["signal"]

        macd_info = TechnicalAnalyzer.analyze_macd(self.df)
        summary.macd_dif = macd_info["DIF"]
        summary.macd_dea = macd_info["DEA"]
        summary.macd_hist = macd_info["HIST"]
        summary.macd_signal = macd_info["signal"]

        rsi_info = TechnicalAnalyzer.analyze_rsi(self.df)
        summary.rsi_6 = rsi_info["RSI6"]
        summary.rsi_12 = rsi_info["RSI12"]
        summary.rsi_24 = rsi_info["RSI24"]
        summary.rsi_signal = rsi_info["signal"]

        bias_info = TechnicalAnalyzer.calculate_bias(self.df)
        summary.bias_ma5 = bias_info["bias_ma5"]
        summary.bias_ma10 = bias_info["bias_ma10"]
        summary.bias_ma20 = bias_info["bias_ma20"]

        levels = TechnicalAnalyzer.find_support_resistance(self.df)
        summary.support_levels = levels["support"]
        summary.resistance_levels = levels["resistance"]

        summary.weekly_trend = TechnicalAnalyzer.get_weekly_trend(self.df)

        summary.indicator_trend = TechnicalAnalyzer.analyze_indicator_trend(self.df)
        summary.weekly_indicators = TechnicalAnalyzer.analyze_weekly_indicators(self.df)
        summary.rs_strength = TechnicalAnalyzer.calculate_rs_strength(self.df, self.index_df)
        summary.divergence = TechnicalAnalyzer.detect_divergence(self.df)
        summary.volatility = TechnicalAnalyzer.calculate_volatility(self.df)
        summary.consecutive_days = TechnicalAnalyzer.calculate_consecutive_days(self.df)

        return summary

    def get_weekly_trend(self) -> str:
        """Get weekly trend analysis"""
        return TechnicalAnalyzer.get_weekly_trend(self.df)
