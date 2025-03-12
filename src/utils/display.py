from colorama import Fore, Style
from tabulate import tabulate
from .analysts import ANALYST_ORDER
import os
from rich.console import Console
from rich.table import Table
import logging
from datetime import datetime

# 创建rich console实例
console = Console()

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
    # import json
    # print(json.dumps(result, ensure_ascii=False))
    """打印交易系统的输出结果"""
    if not result or "decisions" not in result or "analyst_signals" not in result:
        print("No results to display")
        return

    decisions = result["decisions"]
    analyst_signals = result["analyst_signals"]
    portfolio = result.get("data", {}).get("portfolio", {})

    # 创建详细日志
    log_detailed_analysis(decisions, analyst_signals, portfolio)
    
    # 在终端显示简洁的结果表格
    table = Table(title="Crypto Trading Summary")
    
    # 添加表格列
    table.add_column("Symbol", style="cyan")
    table.add_column("Price ($)", style="blue")
    table.add_column("Signal", style="yellow")
    table.add_column("Action", style="green")
    table.add_column("Amount", style="blue")
    table.add_column("Value ($)", style="magenta")
    table.add_column("Risk Level", style="red")
    table.add_column("Stop Loss", style="yellow")
    table.add_column("Take Profit", style="green")

    # 添加每个交易对的数据
    for symbol in decisions.keys():
        tech_signal = analyst_signals.get("crypto_technical_agent", {}).get(symbol, {})
        risk_data = analyst_signals.get("crypto_risk_manager", {}).get(symbol, {})
        decision = decisions[symbol]
        
        # 准备数据
        current_price = risk_data.get('current_price', 0)
        signal = tech_signal.get('signal', 'UNKNOWN').upper()
        action = decision.get('action', 'HOLD').upper()
        quantity = float(decision.get('quantity', 0))
        value = quantity * current_price
        risk_level = f"{risk_data.get('volatility', 0) * 100:.1f}%"
        stop_loss = f"${risk_data.get('stop_loss', 0):,.2f}"
        take_profit = f"${risk_data.get('take_profit', 0):,.2f}"
        
        table.add_row(
            symbol,
            f"${current_price:,.2f}",
            signal,
            action,
            f"{quantity:.8f}",
            f"${value:,.2f}",
            risk_level,
            stop_loss,
            take_profit
        )

    # 添加投资组合摘要
    if portfolio:
        cash = portfolio.get('cash', 0)
        total_position_value = sum(
            pos['amount'] * analyst_signals.get('crypto_risk_manager', {}).get(sym, {}).get('current_price', 0)
            for sym, pos in portfolio.get('positions', {}).items()
        )
        total_value = cash + total_position_value
        
        table.add_section()
        table.add_row(
            "PORTFOLIO",
            "",
            "",
            "CASH",
            "",
            f"${cash:,.2f}",
            "",
            "Total Value:",
            f"${total_value:,.2f}"
        )

    # 打印表格
    console.print(table)

def log_detailed_analysis(decisions, analyst_signals, portfolio):
    """将详细分析记录到日志文件"""
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # 设置日志文件
    log_filename = f"logs/trading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    
    logger = logging.getLogger('trading_analysis')
    
    # 记录详细分析
    logger.info("=" * 50)
    logger.info("DETAILED TRADING ANALYSIS")
    logger.info("=" * 50)
    
    for symbol in decisions.keys():
        logger.info(f"\nAnalysis for {symbol}")
        logger.info("-" * 30)
        
        # 记录技术分析
        tech_signal = analyst_signals.get("crypto_technical_agent", {}).get(symbol, {})
        if tech_signal:
            logger.info("Technical Analysis:")
            logger.info(f"Signal: {tech_signal.get('signal', 'UNKNOWN').upper()}")
            logger.info(f"Timeframes: {', '.join(tech_signal.get('timeframes', ['1h']))}")
            logger.info("Key Indicators:")
            for analysis in tech_signal.get('reasoning', '').split(' | '):
                logger.info(f"  • {analysis}")
        
        # 记录风险分析
        risk_data = analyst_signals.get("crypto_risk_manager", {}).get(symbol, {})
        if risk_data:
            logger.info("\nRisk Analysis:")
            logger.info(f"Risk Level: {risk_data.get('volatility', 0) * 100:.1f}%")
            logger.info(f"Position Limit: ${risk_data.get('position_limit', 0):,.2f}")
            logger.info(f"Stop Loss: ${risk_data.get('stop_loss', 0):,.2f}")
            logger.info(f"Take Profit: ${risk_data.get('take_profit', 0):,.2f}")
        
        # 记录交易决策
        decision = decisions[symbol]
        logger.info("\nTrading Decision:")
        logger.info(f"Action: {decision.get('action', 'HOLD').upper()}")
        logger.info(f"Quantity: {float(decision.get('quantity', 0)):.8f}")
        logger.info(f"Confidence: {decision.get('confidence', 0):.1f}%")
        logger.info(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
    
    # 记录投资组合信息
    if portfolio:
        logger.info("\n" + "=" * 50)
        logger.info("PORTFOLIO SUMMARY")
        logger.info("-" * 30)
        logger.info(f"Cash Balance: ${portfolio.get('cash', 0):,.2f}")
        
        total_position_value = sum(
            pos['amount'] * analyst_signals.get('crypto_risk_manager', {}).get(sym, {}).get('current_price', 0)
            for sym, pos in portfolio.get('positions', {}).items()
        )
        logger.info(f"Total Position Value: ${total_position_value:,.2f}")
        logger.info(f"Total Portfolio Value: ${(portfolio.get('cash', 0) + total_position_value):,.2f}")


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
