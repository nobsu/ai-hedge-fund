from graph.state import AgentState
from utils.progress import progress
from tools.api import CryptoAPI
import numpy as np

def calculate_volatility(df):
    """计算价格波动率"""
    returns = np.log(df['close'] / df['close'].shift(1))
    return returns.std() * np.sqrt(252)  # 年化波动率

def calculate_position_limit(portfolio_value: float, volatility: float, base_risk: float) -> float:
    """根据波动率计算仓位限制"""
    # 根据波动率调整风险系数
    risk_adjusted = base_risk / (volatility + 0.0001)  # 避免除以零
    return portfolio_value * risk_adjusted

def calculate_stop_loss(current_price: float, volatility: float) -> float:
    """计算止损价格"""
    # 使用波动率的1.5倍作为止损点，并确保止损价格为正数
    stop_loss = current_price * (1 - min(volatility * 1.5, 0.5))  # 最大止损50%
    return max(stop_loss, current_price * 0.5)  # 确保止损不低于当前价格的50%

def calculate_take_profit(current_price: float, volatility: float) -> float:
    """计算止盈价格"""
    return current_price * (1 + volatility * 2)  # 用波动率的2倍作为止盈点

def crypto_risk_manager(state: AgentState):
    """加密货币风险管理代理"""
    portfolio = state["data"]["portfolio"]
    symbols = state["data"]["symbols"]
    risk_analysis = {}
    crypto_api = CryptoAPI()
    
    for symbol in symbols:
        progress.update_status("crypto_risk_manager", symbol, "分析风险")
        
        # 获取历史价格数据用于计算波动率
        df = crypto_api.get_crypto_prices(
            symbol,
            state["data"]["start_date"],
            state["data"]["end_date"]
        )
        
        if df.empty:
            continue
            
        # 获取当前市场数据
        market_data = crypto_api.get_market_data(symbol)
        
        # 计算波动率
        volatility = calculate_volatility(df)
        
        # 计算总投资组合价值
        total_value = portfolio["cash"]
        for pos in portfolio["positions"].values():
            total_value += pos["amount"] * pos["avg_price"]
        
        # 根据波动率调整仓位限制
        position_limit = calculate_position_limit(
            portfolio_value=total_value,
            volatility=volatility,
            base_risk=0.02  # 基础风险系数
        )
        
        # 设置止损止盈
        stop_loss = calculate_stop_loss(
            current_price=market_data["weighted_avg_price"],
            volatility=volatility
        )
        
        take_profit = calculate_take_profit(
            current_price=market_data["weighted_avg_price"],
            volatility=volatility
        )
        
        risk_analysis[symbol] = {
            "position_limit": position_limit,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "volatility": volatility,
            "market_data": market_data,
            "current_price": market_data["weighted_avg_price"]
        }
    
    return {
        "messages": state["messages"],
        "data": {
            **state["data"],
            "analyst_signals": {
                **state["data"].get("analyst_signals", {}),
                "crypto_risk_manager": risk_analysis
            }
        }
    } 