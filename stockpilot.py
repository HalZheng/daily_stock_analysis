#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
StockPilot CLI - Personal Investment Analysis Tool
===================================

Usage:
    python stockpilot.py [--config CONFIG_PATH] [--output OUTPUT_PATH]

Design Philosophy:
- Algorithmic rigor belongs to scripts: MA, MACD, divergence, support levels
- Fuzzy reasoning belongs to AI: portfolio context, news sentiment, market trends
- Scripts handle certainty (calculation, statistics, feature extraction)
- AI handles uncertainty (strategy combination, position sizing, style matching)
"""

import argparse
import logging
import sys
from pathlib import Path

from src.core.stockpilot_engine import StockPilotEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("StockPilot")


def main():
    parser = argparse.ArgumentParser(
        description="StockPilot - Personal Investment Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python stockpilot.py
    python stockpilot.py --config my_portfolio.yaml
    python stockpilot.py --output analysis_prompt.md
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to StockPilot config file (default: stockpilot_config.yaml)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="last_stockpilot_prompt.md",
        help="Output file path for generated prompt (default: last_stockpilot_prompt.md)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 60)
    print("  StockPilot - Personal Investment Analysis Engine")
    print("  Design: Scripts handle certainty, AI handles uncertainty")
    print("=" * 60)
    print()

    try:
        engine = StockPilotEngine(config_path=args.config)
        prompt = engine.run_and_save_prompt(output_path=args.output)

        if prompt:
            print()
            print("=" * 60)
            print("  Analysis Complete!")
            print(f"  Prompt saved to: {args.output}")
            print("=" * 60)
            return 0
        else:
            logger.error("Failed to generate analysis prompt")
            return 1

    except Exception as e:
        logger.error(f"StockPilot failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
