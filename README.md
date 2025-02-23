# AI Hedge Fund

An AI-powered trading system that leverages large language models and technical analysis to make cryptocurrency trading decisions.

## Features

- **Multi-Timeframe Analysis**: Analyzes crypto markets across multiple timeframes (1h, 4h, 1d)
- **Technical Indicators**: 
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - ADX (Average Directional Index)
  - Volume Analysis
  - ATR (Average True Range)
  - OBV (On-Balance Volume)

- **Risk Management**:
  - Position sizing based on volatility
  - Dynamic stop-loss levels
  - Take-profit targets
  - Portfolio allocation limits
  - Volatility-adjusted position sizing

- **LLM Integration**:
  - Supports multiple LLM providers (Groq, OpenAI, etc.)
  - Intelligent trade reasoning
  - Market context analysis
  - Risk-aware decision making

## Getting Started

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your:
- LLM API keys (GROQ_API_KEY, OPENAI_API_KEY)
- Binance API credentials (BINANCE_API_KEY, BINANCE_API_SECRET)

3. Run the trading system:
```bash
poetry run python src/main.py --symbols BTCUSDT,ETHUSDT
```

## Configuration

- `symbols`: List of cryptocurrency trading pairs (e.g., BTCUSDT, ETHUSDT)
- `timeframes`: Trading timeframes to analyze (1h, 4h, 1d)
- `risk_level`: Portfolio risk tolerance (0.0-1.0)
- `model`: LLM model to use (e.g., groq/deepseek-r1-70b)

## Output

The system provides:
- Technical analysis across multiple timeframes
- Risk assessment and position sizing
- Trading decisions with confidence levels
- Stop-loss and take-profit levels
- Portfolio allocation suggestions
- Detailed reasoning for each trade

## Logging

- Detailed LLM interactions are logged to `logs/llm_calls_*.log`
- Trading decisions and analysis are displayed in the terminal
- Portfolio performance metrics are tracked and displayed

## Architecture

The system uses a multi-agent architecture:
1. Technical Analysis Agent: Analyzes market data and generates signals
2. Risk Management Agent: Evaluates risk and sets position limits
3. Portfolio Management Agent: Makes final trading decisions
4. LLM Coordinator: Integrates analysis and generates reasoning

## Safety Features

- Position limits based on volatility
- Stop-loss protection
- Maximum allocation limits
- Error handling and fallback strategies
- Detailed logging for audit trails

## Disclaimer

This is an experimental trading system. Always do your own research and never trade with money you cannot afford to lose.

## License

MIT
