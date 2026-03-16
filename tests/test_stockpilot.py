# -*- coding: utf-8 -*-
"""
Tests for StockPilot modules
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.stockpilot_config import (
    UserProfile,
    Security,
    Position,
    Assets,
    DataFetchConfig,
    load_stockpilot_config,
    get_stockpilot_config,
)
from src.core.stockpilot_indicators import (
    IndicatorCalculator,
    TechnicalAnalyzer,
    DataCompressor,
    TechnicalSummary,
)
from src.core.stockpilot_engine import (
    MarketTimer,
    MarketStage,
    NpEncoder,
)


class TestStockPilotConfig:
    """Tests for StockPilot configuration"""

    def test_position_to_dict(self):
        pos = Position(shares=100, cost=50.0, current_value=5500.0)
        result = pos.to_dict()
        assert result["shares"] == 100
        assert result["cost"] == 50.0
        assert result["current_value"] == 5500.0

    def test_security_is_holding(self):
        sec_with_position = Security(
            code="600519.SH",
            name="贵州茅台",
            position=Position(shares=100, cost=1650.0),
        )
        assert sec_with_position.is_holding is True

        sec_without_position = Security(
            code="300750.SZ",
            name="宁德时代",
            position=None,
        )
        assert sec_without_position.is_holding is False

    def test_user_profile_get_active_styles(self):
        from src.core.stockpilot_config import InvestmentStyle

        profile = UserProfile(
            profile_id="test",
            profile_name="Test User",
            investment_style=[
                InvestmentStyle(content="Style 1", enabled=True),
                InvestmentStyle(content="Style 2", enabled=False),
                InvestmentStyle(content="Style 3", enabled=True),
            ],
        )

        styles = profile.get_active_styles()
        assert len(styles) == 2
        assert "Style 1" in styles
        assert "Style 3" in styles
        assert "Style 2" not in styles

    def test_data_fetch_config_defaults(self):
        config = DataFetchConfig()
        assert config.fetch_main_money_flow is True
        assert config.fetch_news_sentiment is True
        assert "当前持仓" in config.consult_scope


class TestIndicatorCalculator:
    """Tests for technical indicator calculations"""

    @pytest.fixture
    def sample_df(self):
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 2)
        high = close + np.abs(np.random.randn(100) * 3)
        low = close - np.abs(np.random.randn(100) * 3)
        open_price = close + np.random.randn(100) * 2
        volume = np.random.randint(1000000, 10000000, 100)

        df = pd.DataFrame({
            "date": dates,
            "收盘": close,
            "开盘": open_price,
            "最高": high,
            "最低": low,
            "成交量": volume,
        })
        return df

    def test_normalize_columns(self, sample_df):
        df = sample_df.rename(columns={"收盘": "close", "开盘": "open"})
        result = IndicatorCalculator.normalize_columns(df)
        assert "收盘" in result.columns
        assert "开盘" in result.columns

    def test_add_ma(self, sample_df):
        result = IndicatorCalculator.add_ma(sample_df)
        assert "MA5" in result.columns
        assert "MA10" in result.columns
        assert "MA20" in result.columns
        assert "MA60" in result.columns

    def test_add_kdj(self, sample_df):
        result = IndicatorCalculator.add_kdj(sample_df)
        assert "K" in result.columns
        assert "D" in result.columns
        assert "J" in result.columns

    def test_add_boll(self, sample_df):
        result = IndicatorCalculator.add_boll(sample_df)
        assert "BOLL_MID" in result.columns
        assert "BOLL_UP" in result.columns
        assert "BOLL_LOW" in result.columns
        assert "BOLL_WIDTH" in result.columns

    def test_add_macd(self, sample_df):
        result = IndicatorCalculator.add_macd(sample_df)
        assert "MACD_DIF" in result.columns
        assert "MACD_DEA" in result.columns
        assert "MACD_HIST" in result.columns

    def test_add_rsi(self, sample_df):
        result = IndicatorCalculator.add_rsi(sample_df)
        assert "RSI_6" in result.columns
        assert "RSI_12" in result.columns
        assert "RSI_24" in result.columns

    def test_add_all_indicators(self, sample_df):
        result = IndicatorCalculator.add_all_indicators(sample_df)
        assert "MA5" in result.columns
        assert "K" in result.columns
        assert "BOLL_MID" in result.columns
        assert "MACD_DIF" in result.columns
        assert "RSI_6" in result.columns


class TestTechnicalAnalyzer:
    """Tests for technical analysis"""

    @pytest.fixture
    def sample_df_with_indicators(self):
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 2)
        high = close + np.abs(np.random.randn(100) * 3)
        low = close - np.abs(np.random.randn(100) * 3)
        volume = np.random.randint(1000000, 10000000, 100)

        df = pd.DataFrame({
            "date": dates,
            "收盘": close,
            "开盘": close,
            "最高": high,
            "最低": low,
            "成交量": volume,
        })
        return IndicatorCalculator.add_all_indicators(df)

    def test_analyze_kdj(self, sample_df_with_indicators):
        result = TechnicalAnalyzer.analyze_kdj(sample_df_with_indicators)
        assert "signal" in result
        assert "K" in result
        assert "D" in result
        assert "J" in result

    def test_analyze_boll(self, sample_df_with_indicators):
        result = TechnicalAnalyzer.analyze_boll(sample_df_with_indicators)
        assert "signal" in result
        assert "position" in result

    def test_analyze_macd(self, sample_df_with_indicators):
        result = TechnicalAnalyzer.analyze_macd(sample_df_with_indicators)
        assert "signal" in result
        assert "DIF" in result
        assert "DEA" in result
        assert "HIST" in result

    def test_analyze_trend(self, sample_df_with_indicators):
        result = TechnicalAnalyzer.analyze_trend(sample_df_with_indicators)
        assert "trend" in result
        assert "strength" in result

    def test_find_support_resistance(self, sample_df_with_indicators):
        result = TechnicalAnalyzer.find_support_resistance(sample_df_with_indicators)
        assert "support" in result
        assert "resistance" in result


class TestDataCompressor:
    """Tests for data compression"""

    @pytest.fixture
    def sample_df(self):
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 2)
        high = close + np.abs(np.random.randn(100) * 3)
        low = close - np.abs(np.random.randn(100) * 3)
        volume = np.random.randint(1000000, 10000000, 100)

        df = pd.DataFrame({
            "date": dates,
            "收盘": close,
            "开盘": close,
            "最高": high,
            "最低": low,
            "成交量": volume,
        })
        return df

    def test_get_summary(self, sample_df):
        compressor = DataCompressor(sample_df)
        summary = compressor.get_summary()

        assert isinstance(summary, TechnicalSummary)
        assert summary.price > 0
        assert isinstance(summary.trend, str)
        assert isinstance(summary.kdj_signal, str)
        assert isinstance(summary.boll_signal, str)
        assert isinstance(summary.macd_signal, str)

    def test_get_summary_to_dict(self, sample_df):
        compressor = DataCompressor(sample_df)
        summary = compressor.get_summary()
        result = summary.to_dict()

        assert "price" in result
        assert "kdj" in result
        assert "boll" in result
        assert "macd" in result
        assert "trend" in result


class TestMarketTimer:
    """Tests for market timer"""

    def test_get_market_stage(self):
        timer = MarketTimer()
        stage = timer.get_market_stage()

        assert isinstance(stage, MarketStage)
        assert stage.today_str is not None
        assert stage.current_time is not None

    def test_market_stage_to_dict(self):
        stage = MarketStage(
            stage="盘前",
            today_str="2024-01-01",
            current_time="08:00:00",
        )
        result = stage.to_dict()

        assert result["stage"] == "盘前"
        assert result["date"] == "2024-01-01"
        assert result["time"] == "08:00:00"


class TestNpEncoder:
    """Tests for NumPy JSON encoder"""

    def test_encode_int(self):
        encoder = NpEncoder()
        result = encoder.default(np.int64(42))
        assert result == 42
        assert isinstance(result, int)

    def test_encode_float(self):
        encoder = NpEncoder()
        result = encoder.default(np.float64(3.14))
        assert result == 3.14
        assert isinstance(result, float)

    def test_encode_array(self):
        encoder = NpEncoder()
        result = encoder.default(np.array([1, 2, 3]))
        assert result == [1, 2, 3]
        assert isinstance(result, list)
