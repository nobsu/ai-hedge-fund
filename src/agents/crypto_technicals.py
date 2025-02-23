from graph.state import AgentState
import pandas as pd
import numpy as np
import talib
from utils.progress import progress
from tools.api import CryptoAPI

def crypto_technical_agent(state: AgentState):
    """加密货币技术分析代理"""
    data = state["data"]
    symbols = data["symbols"]
    technical_analysis = {}
    crypto_api = CryptoAPI()
    
    # 设置分析周期
    timeframes = {
        "1h": "1 hour",
        "4h": "4 hours",
        "1d": "1 day"
    }
    primary_timeframe = "1h"  # 主要分析周期
    
    for symbol in symbols:
        progress.update_status("crypto_technical_agent", symbol, "分析价格数据")
        
        signals = {}
        # 获取不同时间周期的数据
        for timeframe, description in timeframes.items():
            df = crypto_api.get_crypto_prices(
                symbol, 
                data["start_date"],
                data["end_date"],
                interval=timeframe
            )
            
            if df.empty:
                continue
                
            # 计算技术指标
            signals[timeframe] = calculate_crypto_signals(df)
        
        # 生成综合交易信号
        signal = generate_trading_signal(signals, primary_timeframe)
        signal["timeframes"] = list(signals.keys())  # 添加分析的时间周期
        
        technical_analysis[symbol] = signal
    
    return {
        "messages": state["messages"],
        "data": {
            **state["data"],
            "analyst_signals": {
                "crypto_technical_agent": technical_analysis
            }
        }
    }

def calculate_crypto_signals(df: pd.DataFrame) -> dict:
    """计算加密货币技术指标"""
    signals = {}
    
    # RSI
    signals['rsi'] = talib.RSI(df['close'])
    
    # MACD
    macd, signal, hist = talib.MACD(df['close'])
    signals['macd'] = macd
    signals['macd_signal'] = signal
    signals['macd_hist'] = hist
    
    # Bollinger Bands
    upper, middle, lower = talib.BBANDS(df['close'])
    signals['bb_upper'] = upper
    signals['bb_middle'] = middle
    signals['bb_lower'] = lower
    
    # 成交量分析
    signals['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
    
    # 额外的加密货币特定指标
    signals['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)  # 平均真实范围
    signals['obv'] = talib.OBV(df['close'], df['volume'])  # 能量潮指标
    signals['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)  # 趋向指标
    
    return signals

def generate_trading_signal(signals: dict, primary_tf: str) -> dict:
    """根据多个时间周期的技术指标生成交易信号"""
    # 获取主要时间周期的指标
    primary_signals = signals[primary_tf]
    
    # 计算各个时间周期的信号
    timeframe_analysis = {}
    for tf, tf_signals in signals.items():
        current_rsi = tf_signals['rsi'].iloc[-1]
        current_macd = tf_signals['macd'].iloc[-1]
        current_macd_signal = tf_signals['macd_signal'].iloc[-1]
        current_price = tf_signals['bb_middle'].iloc[-1]
        current_bb_upper = tf_signals['bb_upper'].iloc[-1]
        current_bb_lower = tf_signals['bb_lower'].iloc[-1]
        current_adx = tf_signals['adx'].iloc[-1]
        
        timeframe_analysis[tf] = {
            "rsi": current_rsi,
            "macd": "Bullish" if current_macd > current_macd_signal else "Bearish",
            "bb_position": "Oversold" if current_price < current_bb_lower else "Overbought" if current_price > current_bb_upper else "Normal",
            "trend_strength": "Strong" if current_adx > 25 else "Weak",
            "adx": current_adx
        }
    
    # 使用主要时间周期的信号作为基础
    primary_analysis = timeframe_analysis[primary_tf]
    
    # 生成详细的分析理由
    reasoning = []
    for tf, analysis in timeframe_analysis.items():
        reasoning.append(
            f"[{tf.upper()}] RSI: {analysis['rsi']:.2f}, "
            f"MACD: {analysis['macd']}, "
            f"BB: {analysis['bb_position']}, "
            f"Trend: {analysis['trend_strength']} (ADX: {analysis['adx']:.2f})"
        )
    
    # 计算综合信号
    bullish_signals = 0
    bearish_signals = 0
    total_weight = 0
    
    for tf, analysis in timeframe_analysis.items():
        # 根据时间周期分配权重
        weight = 1.0 if tf == primary_tf else 0.5
        total_weight += weight
        
        if analysis['rsi'] < 30:
            bullish_signals += weight
        elif analysis['rsi'] > 70:
            bearish_signals += weight
            
        if analysis['macd'] == "Bullish":
            bullish_signals += weight
        else:
            bearish_signals += weight
            
        if analysis['bb_position'] == "Oversold":
            bullish_signals += weight
        elif analysis['bb_position'] == "Overbought":
            bearish_signals += weight
    
    # 归一化信号强度
    signal_strength = (bullish_signals - bearish_signals) / total_weight
    
    # 生成最终信号
    if signal_strength > 0.2:
        action = "bullish"
        confidence = min(100, (signal_strength * 50 + 50))
    elif signal_strength < -0.2:
        action = "bearish"
        confidence = min(100, (-signal_strength * 50 + 50))
    else:
        action = "neutral"
        confidence = 50
    
    return {
        "signal": action,
        "confidence": confidence,
        "reasoning": " | ".join(reasoning)
    } 