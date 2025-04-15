# Alpaca Markets Integration

This document explains how to use the Alpaca Markets integration in the Trading Agent system to execute trades automatically based on agent recommendations.

## Overview

The system has been enhanced to not only provide trading recommendations but also to execute trades automatically through the Alpaca Markets API. The integration maintains the existing recommendation functionality while adding the ability to:

1. Execute trades based on agent recommendations
2. View current positions
3. Close positions manually
4. Track trade history and performance
5. Toggle between recommendation-only and auto-execution modes

## Setup

### 1. Alpaca Account

First, you need to create an Alpaca Markets account:

1. Go to [https://app.alpaca.markets/signup](https://app.alpaca.markets/signup) to sign up
2. Choose between a real money account or a paper trading account
3. Generate API keys from your dashboard (API Keys section)

### 2. Configuration

Update your `.env` file with the following Alpaca-specific settings:

```
# Alpaca Markets API credentials
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_API_SECRET=your_alpaca_api_secret_here
# Use this URL for paper trading (practice)
ALPACA_API_URL=https://paper-api.alpaca.markets
# Use this URL for live trading (CAUTION: real money)
# ALPACA_API_URL=https://api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# Execution settings
# Set to true to enable automatic execution of trades via Alpaca
EXECUTE_TRADES=false
```

By default, `EXECUTE_TRADES` is set to `false`, which means the system will only provide recommendations without executing trades. Set it to `true` to enable automatic trade execution.

### 3. Dependencies

Make sure to install the required Python packages:

```bash
pip install -r requirements.txt
```

The Alpaca integration requires the `alpaca-trade-api` package, which should be included in the requirements.

## Using Alpaca Trading Features

### Trade Execution

When `EXECUTE_TRADES` is set to `true`, the system will:

1. Analyze trading pairs as usual
2. Generate position recommendations
3. Automatically execute trades based on those recommendations
4. Apply appropriate stop loss and take profit levels
5. Track and display open positions

You can toggle this setting in the menu system without editing the .env file.

### Alpaca Trading Menu

The system includes a dedicated Alpaca Trading Menu accessible from the main menu:

1. **View Current Positions**: Display all currently open positions, including entry prices and profit/loss
2. **Close a Position**: Select and close a specific position
3. **Close All Positions**: Close all open positions at once
4. **Toggle Trade Execution**: Enable or disable automatic trade execution
5. **Run Analysis with Current Settings**: Run the trading agent with current execution settings

### Risk Management

The system calculates position sizes based on:

- Account equity
- Maximum risk per trade setting
- Distance between entry and stop loss

This ensures proper risk management regardless of the instrument being traded.

## Implementation Details

The Alpaca integration consists of the following components:

1. **AlpacaClient**: Base client for communicating with the Alpaca API
2. **AlpacaOrderExecutor**: Handles trade execution and position modification
3. **AlpacaPositionManager**: Tracks and manages open positions
4. **AlpacaDataFetcher**: Fetches market data from Alpaca (alternative to YFinance)

The main ForexTradingAgent has been extended to optionally execute trades via Alpaca while maintaining its recommendation functionality.

## Troubleshooting

### Common Issues

1. **API Connection Errors**:

   - Ensure your API keys are entered correctly in the .env file
   - Check that your Alpaca account is active and not restricted

2. **Symbol Not Found Errors**:

   - Alpaca markets supports US stocks and a limited set of forex pairs
   - The system will automatically convert symbols to Alpaca's format (e.g., EUR/USD → EUR-USD)

3. **Order Execution Failures**:
   - Check account balance and buying power
   - Verify that the symbol is available for trading on Alpaca
   - Ensure that your account has the right permissions for the asset type

### Logs

The system logs all trade activity in the console and keeps a trade history in the `data/trade_history.json` file for reference.

## Disclaimer

Trading financial instruments involves risk. This system is provided for educational and research purposes only. Always verify trades and manage risk appropriately. Paper trading is recommended before using real funds.

When using the live trading API endpoint, you will be trading with real money. Use caution and start with small position sizes until you are comfortable with the system.
