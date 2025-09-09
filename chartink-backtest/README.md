# Chartink Backtest Tool

This tool allows you to backtest stock trades using stop loss and target percentages on flexible timeframes. It uses Streamlit for the UI and Yahoo Finance for historical data.

## Features
- Upload a CSV file with `date` and `symbol` columns
- Set stop loss and target percentages
- Choose capital per trade
- Select timeframe (5 min, 15 min, 30 min, 1 hour, 1 day)
- Option to start balance as capital × number of trades
- Calculates equity curve, max drawdown, Sharpe and Sortino ratios
- Visualizes results and equity curves
- Download results as CSV
- View individual stock charts with entry/exit markers

## How to Use
1. Run the script with Streamlit:
   ```sh
   streamlit run chartink-backtest.py
   ```
2. Upload your CSV file containing `date` and `symbol` columns.
3. Set your desired parameters (SL %, Target %, Capital, Timeframe).
4. Click "Process" to run the backtest.
5. Review results, download CSV, and visualize trades.

## CSV Format
Your CSV should have at least these columns:
```
date,symbol
2023-01-01,RELIANCE
2023-01-02,TCS
...etc
```

## Requirements
- Python 3.8+
- Install dependencies:
  ```sh
  pip install streamlit pandas yfinance matplotlib numpy
  ```

## Notes
- The tool tries to fetch data from NSE (.NS), BSE (.BO), and fallback to raw symbol.
- All calculations and charts are for educational purposes only.

## License
See main repo LICENSE file.
