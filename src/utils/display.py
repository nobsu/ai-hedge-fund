from colorama import Fore, Style
from tabulate import tabulate
from .analysts import ANALYST_ORDER
import os


def sort_analyst_signals(signals):
    """Sort analyst signals in a consistent order."""
    # 创建加密货币分析代理的顺序
    CRYPTO_ANALYST_ORDER = [
        ("Technical Analysis", "crypto_technical_agent"),
        ("Risk Management", "crypto_risk_manager"),
    ]
    
    # 创建顺序映射
    analyst_order = {display: idx for idx, (display, _) in enumerate(CRYPTO_ANALYST_ORDER)}
    
    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def print_trading_output(result):
    """打印交易系统的输出结果"""
    if not result or "decisions" not in result or "analyst_signals" not in result:
        print("No results to display")
        return

    decisions = result["decisions"]
    analyst_signals = result["analyst_signals"]
    portfolio = result.get("data", {}).get("portfolio", {})

    print(f"\n{Fore.CYAN}Crypto Trading Analysis{Style.RESET_ALL}")
    print("=" * 50)

    # 为每个交易对打印分析结果
    for symbol in analyst_signals.get("crypto_technical_agent", {}).keys():
        print(f"\n{Fore.YELLOW}{symbol}{Style.RESET_ALL}")
        print("-" * 30)
        
        tech_signal = analyst_signals.get("crypto_technical_agent", {}).get(symbol, {})
        risk_data = analyst_signals.get("crypto_risk_manager", {}).get(symbol, {})
        
        # 显示关键指标
        if tech_signal:
            signal = tech_signal.get('signal', 'UNKNOWN')
            signal_color = Fore.GREEN if signal == 'bullish' else Fore.RED if signal == 'bearish' else Fore.YELLOW
            print(f"Signal: {signal_color}{signal.upper()}{Style.RESET_ALL}")
            print(f"Timeframes Analyzed: {', '.join(tech_signal.get('timeframes', ['1h']))}")
            print(f"Key Indicators:")
            reasoning = tech_signal.get('reasoning', 'No analysis available')
            for analysis in reasoning.split(' | '):
                print(f"  • {analysis}")
        
        # 显示风险信息
        if risk_data:
            volatility = risk_data.get('volatility', 0) * 100
            volatility_color = Fore.RED if volatility > 40 else Fore.YELLOW if volatility > 20 else Fore.GREEN
            print(f"\nRisk Level: {volatility_color}{volatility:.1f}%{Style.RESET_ALL}")
        
        # 显示交易决策
        if decisions and symbol in decisions:
            decision = decisions[symbol]
            quantity = float(decision.get("quantity", 0))
            current_price = risk_data.get("current_price", 0)
            trade_value = quantity * current_price
            
            print(f"\n{Fore.WHITE}Trading Decision:{Style.RESET_ALL}")
            print(f"Action: {Fore.GREEN if decision['action'] == 'buy' else Fore.RED}{decision['action'].upper()}{Style.RESET_ALL}")
            print(f"Amount: {quantity:.8f} {symbol.replace('USDT', '')}")
            print(f"Value: ${trade_value:,.2f}")
            print(f"Confidence: {decision['confidence']:.1f}%")
            
            # 显示止损和止盈价格
            if risk_data:
                if risk_data.get('stop_loss', 0) > 0:
                    print(f"Stop Loss: ${risk_data['stop_loss']:,.2f}")
                if risk_data.get('take_profit', 0) > 0:
                    print(f"Take Profit: ${risk_data['take_profit']:,.2f}")
            
            # 显示投资组合分配
            if trade_value > 0 and portfolio.get('cash', 0) > 0:
                allocation_percentage = (trade_value / portfolio['cash']) * 100
                print(f"Portfolio Allocation: {allocation_percentage:.1f}%")
        
        print("-" * 30)

    # 显示投资组合信息
    if portfolio:
        print(f"\n{Fore.WHITE}Portfolio Summary:{Style.RESET_ALL}")
        print(f"Cash Balance: ${portfolio.get('cash', 0):,.2f}")
        
        # 计算总持仓价值和加权平均波动率
        total_position_value = 0
        weighted_volatility = 0
        for symbol, pos in portfolio.get('positions', {}).items():
            risk_data = analyst_signals.get('crypto_risk_manager', {}).get(symbol, {})
            current_price = risk_data.get('current_price', 0)
            position_value = pos['amount'] * current_price
            total_position_value += position_value
            
            if position_value > 0:
                weighted_volatility += risk_data.get('volatility', 0) * (position_value / total_position_value)
        
        print(f"Position Value: ${total_position_value:,.2f}")
        print(f"Total Value: ${(portfolio.get('cash', 0) + total_position_value):,.2f}")
        if weighted_volatility > 0:
            volatility_color = Fore.RED if weighted_volatility > 0.4 else Fore.YELLOW if weighted_volatility > 0.2 else Fore.GREEN
            print(f"Portfolio Risk Level: {volatility_color}{weighted_volatility*100:.1f}%{Style.RESET_ALL}")


def print_backtest_results(table_rows: list) -> None:
    """Print the backtest results in a nicely formatted table"""
    # Clear the screen
    os.system("cls" if os.name == "nt" else "clear")

    # Split rows into ticker rows and summary rows
    ticker_rows = []
    summary_rows = []

    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    
    # Display latest portfolio summary
    if summary_rows:
        latest_summary = summary_rows[-1]
        print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")

        # Extract values and remove commas before converting to float
        cash_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        position_str = latest_summary[6].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        total_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

        print(f"Cash Balance: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Position Value: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Value: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")
        print(f"Return: {latest_summary[9]}")
        
        # Display performance metrics if available
        if latest_summary[10]:  # Sharpe ratio
            print(f"Sharpe Ratio: {latest_summary[10]}")
        if latest_summary[11]:  # Sortino ratio
            print(f"Sortino Ratio: {latest_summary[11]}")
        if latest_summary[12]:  # Max drawdown
            print(f"Max Drawdown: {latest_summary[12]}")

    # Add vertical spacing
    print("\n" * 2)

    # Print the table with just ticker rows
    print(
        tabulate(
            ticker_rows,
            headers=[
                "Date",
                "Ticker",
                "Action",
                "Quantity",
                "Price",
                "Shares",
                "Position Value",
                "Bullish",
                "Bearish",
                "Neutral",
            ],
            tablefmt="grid",
            colalign=(
                "left",  # Date
                "left",  # Ticker
                "center",  # Action
                "right",  # Quantity
                "right",  # Price
                "right",  # Shares
                "right",  # Position Value
                "right",  # Bullish
                "right",  # Bearish
                "right",  # Neutral
            ),
        )
    )

    # Add vertical spacing
    print("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list[any]:
    """Format a row for the backtest results table"""
    # Color the action
    action_color = {
        "BUY": Fore.GREEN,
        "COVER": Fore.GREEN,
        "SELL": Fore.RED,
        "SHORT": Fore.RED,
        "HOLD": Fore.YELLOW,
    }.get(action.upper(), Fore.WHITE)

    if is_summary:
        return_color = Fore.GREEN if return_pct >= 0 else Fore.RED
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Shares
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{max_drawdown:.2f}%{Style.RESET_ALL}" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
            f"{action_color}{action.upper()}{Style.RESET_ALL}",
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{shares_owned:,.0f}{Style.RESET_ALL}",
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
            f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
            f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
            f"{Fore.BLUE}{neutral_count}{Style.RESET_ALL}",
        ]
