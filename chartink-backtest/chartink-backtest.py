import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

st.title("Stock SL/Target Backtester (Flexible Timeframe), Developed specifically for chartink backtest CSV")

# --- Inputs ---
csv_file = st.file_uploader("Upload CSV with 'date' and 'symbol' columns", type=["csv"])
sl_pct = st.number_input("Stop Loss %", min_value=0.1, max_value=100.0, value=5.0, step=0.1)
target_pct = st.number_input("Target %", min_value=0.1, max_value=500.0, value=10.0, step=0.1)
capital_per_trade = st.number_input("Capital per trade", min_value=100.0, max_value=1_000_000.0, value=10000.0, step=100.0)
sequential_start = st.checkbox("Start balance = Capital × # of trades", value=False)

# Timeframe selection
interval_map = {"1 hour": "1h", "1 day": "1d"}
selected_interval_label = st.selectbox("Select Timeframe", list(interval_map.keys()))
selected_interval = interval_map[selected_interval_label]


# --- Helper functions ---
def get_history(symbol, start_date, end_date, interval):
    """Fetch stock history with given interval. Try NSE (.NS), BSE (.BO), fallback raw."""
    for suffix in [".NS", ".BO", ""]:
        try:
            ticker = yf.Ticker(symbol + suffix)
            hist = ticker.history(interval=interval, start=start_date, end=end_date + timedelta(days=1))
            if not hist.empty:
                return hist, symbol + suffix
        except Exception:
            continue
    return None, None


def calculate_max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for x in equity_curve:
        if x > peak:
            peak = x
        dd = (peak - x) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    if len(returns) < 2:
        return 0.0
    excess_returns = np.array(returns) - risk_free_rate
    mean_return = np.mean(excess_returns)
    std_dev = np.std(excess_returns, ddof=1)
    if std_dev == 0:
        return 0.0
    return round(mean_return / std_dev, 2)


def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    if len(returns) < 2:
        return 0.0
    excess_returns = np.array(returns) - risk_free_rate
    mean_return = np.mean(excess_returns)
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0:
        return float("inf")
    downside_std = np.std(downside_returns, ddof=1)
    if downside_std == 0:
        return 0.0
    return round(mean_return / downside_std, 2)


# --- Process trades ---
if csv_file:
    df = pd.read_csv(csv_file)

    if "symbol" not in df.columns or "date" not in df.columns:
        st.error("CSV must contain 'symbol' and 'date' columns")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True).dt.date
        print(df["date"])
        today = datetime.today().date()

        if st.button("Process"):
            results = []
            equity_curve = []
            absolute_curve = []
            trade_returns = []

            total_trades = len(df)
            equity = capital_per_trade * total_trades if sequential_start else 0.0

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, row in df.iterrows():
                sym = row["symbol"]
                purchase_date = row["date"]

                # Fetch history
                hist, used_symbol = get_history(sym, purchase_date, today, selected_interval)
                if hist is None or hist.empty:
                    st.warning(f"No data for {sym}")
                    continue

                # Fix timezone
                hist.index = hist.index.tz_localize(None)

                # Filter from purchase date onwards
                hist = hist[hist.index >= pd.to_datetime(purchase_date)]
                if hist.empty:
                    continue

                purchase_price = hist.iloc[0]["Close"]
                target_price = purchase_price * (1 + target_pct / 100)
                sl_price = purchase_price * (1 - sl_pct / 100)

                today_close = hist["Close"].iloc[-1]
                sl_target_hit, hit_time = "None", None
                exit_price = today_close  # default exit = today's close

                for ts, r in hist.iterrows():
                    close_price = r["Close"]
                    if close_price >= target_price:
                        sl_target_hit, hit_time, exit_price = "Target", ts, close_price
                        break
                    elif close_price <= sl_price:
                        sl_target_hit, hit_time, exit_price = "SL", ts, close_price
                        break

                trade_return_pct = ((exit_price - purchase_price) / purchase_price) * 100
                shares = capital_per_trade / purchase_price
                profit_loss = shares * (exit_price - purchase_price)

                equity += profit_loss
                equity_curve.append(
                    equity / (capital_per_trade * total_trades) * 100 if total_trades > 0 else 100
                )
                absolute_curve.append(equity)
                trade_returns.append(trade_return_pct)

                results.append({
                    "Symbol": sym,
                    "Yahoo Symbol": used_symbol,
                    "Purchase Date": purchase_date,
                    "Purchase Price": round(purchase_price, 2),
                    "Target Price": round(target_price, 2),
                    "SL Price": round(sl_price, 2),
                    "Today's Close": round(today_close, 2),
                    "Hit Result": sl_target_hit,
                    "Hit Time": hit_time,
                    "Exit Price": round(exit_price, 2),
                    "Return %": round(trade_return_pct, 2),
                    "Shares": int(shares),
                    "P&L": round(profit_loss, 2),
                    "Equity After Trade": round(equity, 2),
                })

                progress = int((i + 1) / len(df) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Processing {i+1}/{len(df)} stocks...")

            progress_bar.empty()
            status_text.text("✅ Processing complete!")

            result_df = pd.DataFrame(results)

            # Save in session_state so charts don't clear
            st.session_state["result_df"] = result_df
            st.session_state["equity_curve"] = equity_curve
            st.session_state["absolute_curve"] = absolute_curve
            st.session_state["trade_returns"] = trade_returns
            st.session_state["final_equity"] = equity
            st.session_state["capital_per_trade"] = capital_per_trade
            st.session_state["total_trades"] = total_trades


# --- Show results if available ---
if "result_df" in st.session_state:
    result_df = st.session_state["result_df"]

    st.subheader("Results Table")
    def highlight_hit(val):
        if val["Hit Result"] == "Target":
            return ["background-color: lightgreen; color: black;"] * len(val)
        elif val["Hit Result"] == "SL":
            return ["background-color: lightcoral; color: white;"] * len(val)
        elif val["Hit Result"] == "None":
            return ["background-color: lightblue; color: black;"] * len(val)
        return ""
    st.dataframe(result_df.style.apply(highlight_hit, axis=1))

    # Summary
    won_trades = result_df["Hit Result"].value_counts().get("Target", 0)
    lost_trades = result_df["Hit Result"].value_counts().get("SL", 0)
    pending_trades = result_df["Hit Result"].value_counts().get("None", 0)
    win_rate = round(won_trades / (won_trades + lost_trades) * 100, 2) if (won_trades + lost_trades) > 0 else 0
    max_drawdown = calculate_max_drawdown(st.session_state["equity_curve"])
    sharpe_ratio = calculate_sharpe_ratio(st.session_state["trade_returns"])
    sortino_ratio = calculate_sortino_ratio(st.session_state["trade_returns"])
    total_pnl = result_df["P&L"].sum()

    st.markdown(f"**Summary:**")
    st.markdown(f"- Total trades: {st.session_state['total_trades']}")
    st.markdown(f"- Won trades (Target hit): {won_trades}")
    st.markdown(f"- Lost trades (SL hit): {lost_trades}")
    st.markdown(f"- Pending (None hit): {pending_trades}")
    st.markdown(f"- Winning rate: {win_rate} %")
    st.markdown(f"- Final Equity: {round(st.session_state['final_equity'], 2)}")
    st.markdown(f"- Total P&L: {round(total_pnl, 2)}")
    st.markdown(f"- Max Drawdown: {max_drawdown} %")
    st.markdown(f"- Sharpe Ratio: {sharpe_ratio}")
    st.markdown(f"- Sortino Ratio: {sortino_ratio}")

    # Equity curves
    st.subheader("Equity Curve (%) and Absolute Balance")
    fig, ax = plt.subplots()
    ax.plot(st.session_state["equity_curve"], marker="o", label="Equity % (relative)")
    ax.plot(st.session_state["absolute_curve"], marker="x", label="Equity (absolute)")
    ax.set_title("Equity Curves")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Equity")
    ax.legend()
    st.pyplot(fig)

    # Distribution of returns
    st.subheader("Distribution of Trade Returns (%)")
    fig, ax = plt.subplots()
    ax.hist(result_df["Return %"], bins=20, color="skyblue", edgecolor="black")
    ax.set_title("Trade Return Distribution")
    ax.set_xlabel("Return %")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    # Download results
    csv_export = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Results as CSV", csv_export, "results.csv", "text/csv")

    # Stock chart with markers
    st.subheader("Stock Chart with Entry & Exit Markers")
    stock_choice = st.selectbox("Select stock for chart", result_df["Symbol"].unique())
    if stock_choice:
        trade_row = result_df[result_df["Symbol"] == stock_choice].iloc[0]
        purchase_date = trade_row["Purchase Date"]
        today = datetime.today().date()
        hist, used_symbol = get_history(stock_choice, purchase_date, today, selected_interval)
        if hist is not None and not hist.empty:
            hist.index = hist.index.tz_localize(None)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(hist.index, hist["Close"], label="Close Price", color="blue")

            # Entry marker
            ax.scatter(purchase_date, trade_row["Purchase Price"], color="orange", s=100, marker="^", label="Entry")

            # Exit marker
            if trade_row["Hit Result"] in ["SL", "Target"]:
                color = "green" if trade_row["Hit Result"] == "Target" else "red"
                ax.scatter(trade_row["Hit Time"], hist.loc[trade_row["Hit Time"]]["Close"], color=color, s=100, marker="v", label=trade_row["Hit Result"])

            ax.set_title(f"{stock_choice} Price Chart")
            ax.set_xlabel("Date")
            ax.set_ylabel("Close Price")
            ax.legend()
            st.pyplot(fig)
