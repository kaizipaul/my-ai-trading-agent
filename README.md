# AI Trading Agent

A sophisticated trading analysis and position recommendation system that uses artificial intelligence to analyze financial markets and provide trading recommendations.

## Features

- **Multi-Agent System** - Risk management, trading analysis, technical analysis, and news sentiment agents
- **Automated Trading** - Optional execution of trades via Alpaca API
- **Backtesting Tools** - Test strategies against historical data
- **Strategy Optimization** - Fine-tune trading strategies
- **Monte Carlo Simulation** - Assess risk and probability distributions

## Getting Started

### Prerequisites

- Python 3.7+
- Alpaca API key for live trading
- Internet connection for market data

### Installation

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/my-ai-trading-agent.git
   cd my-ai-trading-agent
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   Create a `.env` file with the following (see `.env.example` for the full list):
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_API_SECRET=your_api_secret
   ALPACA_API_URL=https://paper-api.alpaca.markets
   EXECUTE_TRADES=false
   ```

### Usage

Run the main application:

```bash
python src/main.py
```

For command line options:

```bash
python src/main.py --help
```

## Configuration

Edit `src/config.py` to change:

- Trading pairs/symbols
- Risk parameters
- Technical indicators
- Backtesting settings

At startup, `validate_config()` checks the configuration and refuses to run
if `EXECUTE_TRADES=true` is set without valid Alpaca credentials, or if
`ALPACA_API_URL` points at the live (real-money) endpoint without an
explicit `ALLOW_LIVE_TRADING=true` opt-in.

## Testing

Install dependencies (includes `pytest`) and run the test suite:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests run against a mocked Alpaca client - no real API calls or credentials
are needed. A couple of pre-existing tests do make live calls to Yahoo
Finance for market data, so you'll need an internet connection to run the
full suite.

## Testing with an Alpaca Paper (Demo) Account

Paper trading lets you run the full system - signal generation, risk
checks, order placement, position tracking - against a real (simulated)
brokerage account with no real money at risk. This is the recommended way
to validate the system end-to-end before ever considering live trading.

1. **Create a paper account**: sign up at
   [alpaca.markets](https://app.alpaca.markets/signup) and generate API
   keys from the dashboard - paper accounts are created automatically
   alongside a live account and use separate keys.

2. **Configure `.env`** with your paper keys and leave the paper endpoint in
   place:
   ```
   ALPACA_API_KEY=your_paper_key
   ALPACA_API_SECRET=your_paper_secret
   ALPACA_API_URL=https://paper-api.alpaca.markets
   EXECUTE_TRADES=true
   ```

3. **Start small and watch the logs**. Run a single symbol first:
   ```bash
   python src/main.py --run AAPL
   ```
   Every connection attempt, order, fill, close, and error is written to
   `logs/forex_trader_<date>.log` in addition to the console - check there
   for a full audit trail, especially after leaving the system running
   unattended.

4. **Verify the risk gate is doing its job**: the risk agent pulls live
   equity, open positions, and today's realized + unrealized P/L from your
   Alpaca paper account on every trade decision, and blocks new trades once
   `MAX_DAILY_LOSS` or `MAX_OPEN_POSITIONS` is hit. You can watch this in
   the Alpaca paper dashboard alongside the console output.

5. **Never point `ALPACA_API_URL` at the live endpoint** for testing.
   `validate_config()` will refuse to start against the live endpoint
   unless you explicitly set `ALLOW_LIVE_TRADING=true` - that guard exists
   specifically to prevent an accidental switch from paper to real money.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. Trading financial instruments involves significant risk and can result in loss of capital.
