import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from colorama import Fore, Style

from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm


class PortfolioDecision(BaseModel):
    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    decisions: dict[str, PortfolioDecision] = Field(description="Dictionary of ticker to trading decisions")


##### Portfolio Management Agent #####
def portfolio_management_agent(state: AgentState):
    """Makes final trading decisions for crypto assets"""
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    symbols = state["data"]["symbols"]
    
    print(f"\n{Fore.YELLOW}Portfolio Management Agent Analysis:{Style.RESET_ALL}")
    print(f"Processing signals for: {', '.join(symbols)}")
    
    # 准备LLM输入数据
    signals_by_ticker = {}
    current_prices = {}
    max_shares = {}
    
    for symbol in symbols:
        technical_signal = analyst_signals.get("crypto_technical_agent", {}).get(symbol, {})
        risk_data = analyst_signals.get("crypto_risk_manager", {}).get(symbol, {})
        
        if technical_signal and risk_data:
            signals_by_ticker[symbol] = {
                "technical": technical_signal,
                "risk": risk_data
            }
            current_prices[symbol] = risk_data.get("current_price", 0)
            position_limit = risk_data.get("position_limit", 0)
            max_shares[symbol] = int(position_limit / current_prices[symbol]) if current_prices[symbol] > 0 else 0

    # 调用LLM生成交易决策
    result = generate_trading_decision(
        tickers=symbols,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        model_name=state["metadata"]["model_name"],
        model_provider=state["metadata"]["model_provider"]
    )
    
    # 将 Pydantic 模型转换为字典
    decisions_dict = {
        symbol: decision.model_dump()
        for symbol, decision in result.decisions.items()
    }
    
    print(f"\n{Fore.GREEN}Generated trading decisions:{Style.RESET_ALL}")
    print(json.dumps(decisions_dict, indent=2))
    
    # 创建最终消息
    message = HumanMessage(
        content=json.dumps(decisions_dict),
        name="portfolio_management",
    )
    
    return {
        "messages": [message],
        "data": {
            **state["data"],
            "decisions": decisions_dict  # 使用字典而不是 Pydantic 模型
        }
    }


def generate_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
    model_name: str,
    model_provider: str,
) -> PortfolioManagerOutput:
    """Attempts to get a decision from the LLM with retry logic"""
    # Create the prompt template
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a portfolio manager making final trading decisions based on multiple tickers.

            Trading Rules:
            - For long positions:
              * Only buy if you have available cash
              * Only sell if you currently hold long shares of that ticker
              * Sell quantity must be ≤ current long position shares
              * Buy quantity must be ≤ max_shares for that ticker
            
            - For short positions:
              * Only short if you have available margin (50% of position value required)
              * Only cover if you currently have short shares of that ticker
              * Cover quantity must be ≤ current short position shares
              * Short quantity must respect margin requirements
            
            - The max_shares values are pre-calculated to respect position limits
            - Consider both long and short opportunities based on signals
            - Maintain appropriate risk management with both long and short exposure

            Available Actions:
            - "buy": Open or add to long position
            - "sell": Close or reduce long position
            - "short": Open or add to short position
            - "cover": Close or reduce short position
            - "hold": No action
            """,
        ),
        (
            "human",
            """Based on the team's analysis, make your trading decisions for each ticker.

            Here are the signals by ticker:
            {signals_by_ticker}

            Current Prices:
            {current_prices}

            Maximum Shares Allowed For Purchases:
            {max_shares}

            Portfolio Cash: {portfolio_cash}
            Current Positions: {portfolio_positions}
            Current Margin Requirement: {margin_requirement}

            Output strictly in JSON with the following structure:
            {{
              "decisions": {{
                "TICKER1": {{
                  "action": "buy/sell/short/cover/hold",
                  "quantity": integer,
                  "confidence": float,
                  "reasoning": "string"
                }},
                "TICKER2": {{
                  ...
                }},
                ...
              }}
            }}
            """,
        ),
    ])

    # Generate the prompt
    prompt = template.invoke({
        "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
        "current_prices": json.dumps(current_prices, indent=2),
        "max_shares": json.dumps(max_shares, indent=2),
        "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
        "portfolio_positions": json.dumps(portfolio.get('positions', {}), indent=2),
        "margin_requirement": f"{portfolio.get('margin_requirement', 0):.2f}",
    })

    # Create default factory for PortfolioManagerOutput
    def create_default_portfolio_output():
        return PortfolioManagerOutput(decisions={
            ticker: PortfolioDecision(
                action="hold",
                quantity=0,
                confidence=0.0,
                reasoning="Error in portfolio management, defaulting to hold"
            ) for ticker in tickers
        })

    # 调用LLM
    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=PortfolioManagerOutput,
        agent_name="Portfolio Manager",
        default_factory=create_default_portfolio_output
    )
