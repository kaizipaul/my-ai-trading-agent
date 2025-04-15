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
   Create a `.env` file with the following:
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. Trading financial instruments involves significant risk and can result in loss of capital.
