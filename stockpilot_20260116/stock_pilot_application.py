import yaml
import json
import time
import datetime
import pytz
import logging
import pandas as pd
import numpy as np
import akshare as ak
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# ==========================================
# 1. 配置与日志设置 (Configuration & Logging)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("StockPilot")

class NpEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，用于处理 NumPy 数据类型"""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)

def load_config(file_path='config.yaml') -> Dict:
    """加载 YAML 配置文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"成功加载配置，版本: {config['global_config']['version']}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

# ==========================================
# 2. 市场环境与时间判断 (Market Environment)
# ==========================================
class MarketTimer:
    def __init__(self, tz_name="Asia/Shanghai"):
        self.tz = pytz.timezone(tz_name)
        self.now = datetime.datetime.now(self.tz)
        self.today_str = self.now.strftime("%Y-%m-%d")

    def get_market_stage(self) -> str:
        """判断当前市场阶段"""
        current_time = self.now.time()
        
        # 简单判断是否为周末 (更严谨的做法是调用交易日历接口)
        if self.now.weekday() >= 5: 
            return "休市(周末)"

        t = lambda h, m: datetime.time(h, m)
        if current_time < t(9, 15): return "盘前"
        if t(9, 15) <= current_time < t(9, 30): return "集合竞价"
        if t(9, 30) <= current_time < t(11, 30): return "早盘交易中"
        if t(11, 30) <= current_time < t(13, 0): return "午间休市"
        if t(13, 0) <= current_time < t(15, 0): return "午盘交易中"
        return "盘后"

# ==========================================
# 3. 数据获取器 (AkShare Wrapper)
# ==========================================
class DataFetcher:
    """处理所有 AkShare API 调用，包含重试机制"""
    
    @staticmethod
    def fetch_with_retry(func, *args, retries=3, **kwargs):
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == retries - 1:
                    logger.warning(f"重试 {retries} 次后失败: {e}")
                    return None
                time.sleep(1)

    @staticmethod
    def get_index_daily(symbol: str) -> pd.DataFrame:
        # 代码清洗： "000001.SH" -> "sh000001"
        clean_symbol = symbol.lower().replace('.', '')
        if clean_symbol.endswith('sh'): clean_symbol = 'sh' + clean_symbol[:-2]
        elif clean_symbol.endswith('sz'): clean_symbol = 'sz' + clean_symbol[:-2]
        
        return DataFetcher.fetch_with_retry(ak.stock_zh_index_daily_em, symbol=clean_symbol)

    @staticmethod
    def get_stock_daily(code: str) -> pd.DataFrame:
        # 提取数字代码： "600519.SH" -> "600519"
        symbol = ''.join(filter(str.isdigit, code))
        return DataFetcher.fetch_with_retry(ak.stock_zh_a_hist, symbol=symbol, period="daily", adjust="qfq")

    @staticmethod
    def get_etf_daily(code: str) -> pd.DataFrame:
        symbol = ''.join(filter(str.isdigit, code))
        return DataFetcher.fetch_with_retry(ak.fund_etf_hist_em, symbol=symbol, period="daily", adjust="qfq")
    
    @staticmethod
    def get_stock_news(code: str) -> pd.DataFrame:
        symbol = ''.join(filter(str.isdigit, code))
        return DataFetcher.fetch_with_retry(ak.stock_news_em, symbol=symbol)

    @staticmethod
    def get_money_flow(code: str, market: str) -> pd.DataFrame:
        # market 参数: "sh" 或 "sz"
        symbol = ''.join(filter(str.isdigit, code))
        return DataFetcher.fetch_with_retry(ak.stock_individual_fund_flow, stock=symbol, market=market)

# ==========================================
# 4. 技术分析核心 (Technical Analysis)
# ==========================================
class IndicatorCalculator:
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty: return df
        df = df.copy()
        
        # 标准化列名
        col_map = {'date': '日期', 'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低', 'volume': '成交量'}
        df.rename(columns=col_map, inplace=True)
        
        # 移动平均线 (MA)
        for window in [5, 10, 20, 60]:
            df[f'MA{window}'] = df['收盘'].rolling(window).mean()
            
        # KDJ (9,3,3)
        low_list = df['最低'].rolling(9).min()
        high_list = df['最高'].rolling(9).max()
        rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
        df['K'] = rsv.ewm(com=2, adjust=False).mean()
        df['D'] = df['K'].ewm(com=2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        # BOLL (20, 2)
        df['BOLL_MID'] = df['收盘'].rolling(20).mean()
        std = df['收盘'].rolling(20).std()
        df['BOLL_UP'] = df['BOLL_MID'] + 2 * std
        df['BOLL_LOW'] = df['BOLL_MID'] - 2 * std
        df['BOLL_WIDTH'] = (df['BOLL_UP'] - df['BOLL_LOW']) / df['BOLL_MID']
        
        # MACD (12, 26, 9)
        exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
        exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
        df['MACD_DIF'] = exp1 - exp2
        df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
        df['MACD_HIST'] = (df['MACD_DIF'] - df['MACD_DEA']) * 2
        
        return df

class DataCompressor:
    """将丰富的数据帧压缩为 AI 可读的 JSON 摘要"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = IndicatorCalculator.add_all_indicators(df)
        
    def get_summary(self) -> Dict:
        if self.df is None or len(self.df) < 20:
            return {"status": "数据不足"}
            
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # KDJ 信号判断
        kdj_sig = "中性"
        if last['K'] > last['D'] and prev['K'] <= prev['D']: kdj_sig = "金叉"
        elif last['K'] < last['D'] and prev['K'] >= prev['D']: kdj_sig = "死叉"
        elif last['J'] > 100: kdj_sig = "超买"
        elif last['J'] < 0: kdj_sig = "超卖"
        
        # BOLL 信号判断
        # 计算当前价格在布林带中的百分比位置
        if (last['BOLL_UP'] - last['BOLL_LOW']) != 0:
            boll_pos_val = (last['收盘'] - last['BOLL_LOW']) / (last['BOLL_UP'] - last['BOLL_LOW'])
        else:
            boll_pos_val = 0.5

        boll_sig = "正常"
        if last['收盘'] > last['BOLL_UP']: boll_sig = "突破上轨"
        elif last['收盘'] < last['BOLL_LOW']: boll_sig = "跌破下轨"
        # 简单判断开口收敛 (如果当前宽度小于过去20天平均宽度的70%)
        elif last['BOLL_WIDTH'] < self.df['BOLL_WIDTH'].tail(20).mean() * 0.7: boll_sig = "收敛变盘前夕"
        
        # 趋势判断
        trend = "多头" if last['MA5'] > last['MA20'] else "空头"
        
        return {
            "price": round(last['收盘'], 2),
            "change_pct": round(((last['收盘'] - prev['收盘']) / prev['收盘']) * 100, 2),
            "technical": {
                "trend": trend,
                "kdj": f"K:{last['K']:.1f}/J:{last['J']:.1f} ({kdj_sig})",
                "boll": f"位置:{boll_pos_val:.0%} ({boll_sig})",
                "macd": "红柱" if last['MACD_HIST'] > 0 else "绿柱"
            }
        }
        
    def get_weekly_trend(self) -> str:
        """重采样为周线并检查简单趋势"""
        df_w = self.df.copy()
        df_w['日期'] = pd.to_datetime(df_w['日期'])
        df_w.set_index('日期', inplace=True)
        try:
            # 简化重采样逻辑
            df_w = df_w.resample('W').agg({'收盘': 'last'})
            df_w['MA20'] = df_w['收盘'].rolling(20).mean()
            if len(df_w) < 2: return "未知"
            return "多头趋势" if df_w.iloc[-1]['收盘'] > df_w.iloc[-1]['MA20'] else "空头趋势"
        except:
            return "未知"

# ==========================================
# 5. 主程序逻辑 (Main Application)
# ==========================================
class StockPilotApp:
    def __init__(self):
        self.config = load_config()
        self.timer = MarketTimer()
        
    def run(self):
        print(f"🚀 StockPilot 启动... [{self.timer.today_str} | {self.timer.get_market_stage()}]")
        
        # 1. 获取激活的用户配置
        active_profile = next((p for p in self.config['profiles'] if p.get('is_active')), None)
        if not active_profile:
            logger.error("在配置中未找到激活的用户 Profile。")
            return

        # 2. 分析市场 (指数)
        market_summary = self._analyze_market()
        
        # 3. 分析证券 (个股/ETF)
        holdings_summary, watchlist_summary = self._analyze_securities(active_profile)
        
        # 4. 构建 Prompt 数据包
        prompt_payload = {
            "user_profile": {
                "name": active_profile['profile_name'],
                "style": [s['content'] for s in active_profile['investment_style'] if s['enabled']],
                "cash": active_profile['assets']['available_cash'] if active_profile['assets'].get('include_cash_in_prompt') else "Hidden"
            },
            "market_context": {
                "stage": self.timer.get_market_stage(),
                "indices": market_summary
            },
            "portfolio": holdings_summary,
            "watchlist": watchlist_summary
        }
        
        # 5. 生成并保存最终的 Prompt 文本
        self._generate_and_save_prompt(prompt_payload)

    def _analyze_market(self):
        """获取并压缩市场指数数据"""
        logger.info("正在分析大盘指数...")
        indices = self.config['global_config']['market_monitor']['indices']
        summary = {}
        
        for idx in indices:
            if not idx['enabled']: continue
            logger.info(f"获取 {idx['name']} 数据...")
            df = DataFetcher.get_index_daily(idx['code'])
            if df is not None:
                comp = DataCompressor(df)
                summary[idx['name']] = comp.get_summary()
        return summary

    def _analyze_securities(self, profile):
        """获取并压缩个股数据"""
        logger.info("正在分析证券池...")
        holdings = []
        watchlist = []
        
        scope = profile['data_fetch_config'].get('consult_scope', [])
        fetch_flow = profile['data_fetch_config'].get('fetch_main_money_flow', False)
        fetch_news = profile['data_fetch_config'].get('fetch_news_sentiment', False)

        for sec in profile['security_pool']:
            # 检查该股票是否在咨询范围内
            if not any(grp in scope for grp in sec['groups']):
                continue
                
            logger.info(f"处理中: {sec['name']} ({sec['code']})...")
            
            # 获取价格数据
            if sec['asset_type'] == 'Stock':
                df = DataFetcher.get_stock_daily(sec['code'])
            else:
                df = DataFetcher.get_etf_daily(sec['code'])
                
            if df is None: continue

            # 数据压缩与指标计算
            comp = DataCompressor(df)
            data_packet = comp.get_summary()
            data_packet['name'] = sec['name']
            data_packet['code'] = sec['code']
            data_packet['weekly_trend'] = comp.get_weekly_trend()
            data_packet['strategy_note'] = sec.get('strategy_note', '')
            
            # 可选：主力资金流 (仅个股)
            if fetch_flow and sec['asset_type'] == 'Stock':
                market_code = "sh" if "SH" in sec['code'] else "sz"
                flow_df = DataFetcher.get_money_flow(sec['code'], market_code)
                if flow_df is not None and not flow_df.empty:
                    # 计算最近3日主力净流入总和
                    net_inflow = flow_df.tail(3)['主力净流入-净额'].sum()
                    data_packet['capital_flow_3d'] = f"{net_inflow/10000:.1f}万"

            # 可选：获取新闻头条
            if fetch_news:
                news_df = DataFetcher.get_stock_news(sec['code'])
                if news_df is not None and not news_df.empty:
                    # 获取最近2条新闻标题
                    data_packet['recent_news'] = news_df.head(2)['新闻标题'].tolist()

            # 分类：持仓 vs 观察
            if "当前持仓" in sec['groups']:
                pos = sec.get('position', {})
                if pos:
                    cost = pos.get('cost', 1)
                    curr = data_packet['price']
                    profit_pct = (curr - cost) / cost * 100
                    data_packet['holding_info'] = {
                        "shares": pos.get('shares'),
                        "cost": cost,
                        "profit_pct": f"{profit_pct:.2f}%"
                    }
                holdings.append(data_packet)
            else:
                watchlist.append(data_packet)
                
        return holdings, watchlist

    def _generate_and_save_prompt(self, payload):
        """将最终生成的 Prompt 输出到控制台和文件"""
        
        json_str = json.dumps(payload, ensure_ascii=False, indent=2, cls=NpEncoder)
        
        final_prompt = f"""
# 角色：StockPilot 智能投研专家

# 任务
你是一位专业的投资顾问。请分析以下包含市场环境、持仓状态和自选股技术指标的 JSON 数据，并给出操作建议。

# 数据 (JSON)
{json_str}

# 指令
1. **市场大盘分析**：根据 `market_context` 中的指数情况，简要评估当前市场情绪（多头/空头/震荡）。
2. **持仓诊断 (Portfolio)**：
    - 针对 `portfolio` 中的标的，结合技术信号 (KDJ, BOLL) 和用户的 `strategy_note`，给出【持有】、【加仓】或【减仓/卖出】的建议。
    - 特别关注 `profit_pct` (盈亏比例) 和用户的止损线（用户设定严格止损线为 8%）。
3. **机会发掘 (Watchlist)**：
    - 检查 `watchlist` 中的标的，寻找买入信号（如 KDJ 金叉, BOLL 支撑位反弹, MACD 翻红）。
    - 如果满足条件，建议具体的买入价格区间。
4. **约束条件**：
    - 观点要明确果断。
    - 尽可能提到具体的价格点位。
    - 如果某个标的信号恶劣（例如：死叉 + 空头趋势），明确建议规避。
    - 如果 `capital_flow_3d` (3日主力资金) 为大幅负值，请在买入建议中提示风险。

# 输出格式
请使用清晰的 Markdown 格式输出分析报告。
"""
        print("\n" + "="*40)
        print("已生成 Prompt (请复制以下内容发送给大模型)")
        print("="*40)
        print(final_prompt)
        
        # 保存到文件
        with open("last_generated_prompt.md", "w", encoding="utf-8") as f:
            f.write(final_prompt)
        print("\n[✔] Prompt 已保存至 'last_generated_prompt.md'")

if __name__ == "__main__":
    app = StockPilotApp()
    app.run()