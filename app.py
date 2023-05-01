# import io
import numpy as np
import pandas as pd
import requests
import streamlit as st

columns = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "qav",
    "num_trades",
    "taker_base_vol",
    "taker_quote_vol",
    "ignore",
]


def get_atr(currency_pair, days):
    if days == 7:
        url = f"https://api.binance.com/api/v3/klines?symbol={currency_pair}&limit=168&interval=30m"
    elif days == 30:
        url = f"https://api.binance.com/api/v3/klines?symbol={currency_pair}&limit=360&interval=1h"
    elif days == 180:
        url = f"https://api.binance.com/api/v3/klines?symbol={currency_pair}&limit=1080&interval=2h"
    else:
        ValueError("days must be 7, 30 or 180")
    resp = requests.get(url).json()
    data = pd.DataFrame(resp, columns=columns, dtype=np.float64)
    data.index = [pd.to_datetime(x, unit="ms").strftime("%Y-%m-%d %H:%M:%S") for x in data.open_time]
    usecols = ["open", "high", "low", "close", "volume", "qav", "num_trades", "taker_base_vol", "taker_quote_vol"]
    data = data[usecols]
    arr = np.array(
        [data["high"] - data["low"], data["high"] - data["close"].shift(1), data["close"].shift(1) - data["low"]]
    )
    return pd.Series(arr[:, 1:].max(axis=0)).rolling(window=14).mean()[-days:]


def main():
    st.set_page_config(page_icon="₿", page_title="Binance grid calculator Streamlit")

    st.title("Binance grid calculator Streamlit")

    st.write("This is a web application that calculates the grid of Binance.")

    st.markdown(
        """
Key Takeaways:
 - Grid trading is a strategic tool that automates buying and selling futures contracts at preset intervals around a present price range.

 - It can help traders profit from small price fluctuations, especially in raging markets. 

 - The auto parameters function allows anyone to create a grid trading strategy with just one click.
        """
    )

    # col 3
    col11, col12, col13 = st.columns([1, 1, 1])

    # Currency pair selection from BTCUSDT, ETHUSDT etc
    currency_pair = col11.selectbox("Select a currency pair", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ZECUSDT", "XRPUSDT"])

    # Days 7, 30, 180
    days = col12.selectbox("Select a days", [7, 30, 180])

    # Neutral or Long or Short
    grid_direction = col13.selectbox("Select a grid direction", ["Neutral", "Long", "Short"])

    col21, col22, col23 = st.columns([1, 1, 1])

    # Amount
    amount = col21.number_input("Enter an amount", min_value=0.0, max_value=1000000.0, value=1000.0, step=1.0)

    # Leverage
    leverage = col22.slider("Select a leverage", min_value=1, max_value=100)

    # Arithmetic or Geometric
    grid_type = col23.selectbox("Select a grid type", ["Arithmetic", "Geometric"])

    # Current price
    current_price = float(
        requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={currency_pair}").json()["price"]
    )
    st.text(f"Current price: {current_price}")

    # Button for calculating the grid
    if st.button("Calculate the grid", key="calculate_grid"):
        url = f"https://api.binance.com/api/v3/klines?symbol={currency_pair}&limit={20 + days}&interval=1d"
        resp = requests.get(url).json()
        data = pd.DataFrame(resp, columns=columns, dtype=np.float64)
        data.index = [pd.to_datetime(x, unit="ms").strftime("%Y-%m-%d %H:%M:%S") for x in data.open_time]
        usecols = ["open", "high", "low", "close", "volume", "qav", "num_trades", "taker_base_vol", "taker_quote_vol"]
        data = data[usecols]
        sma = data["close"].rolling(window=20).mean()[-days:]
        std = data["close"].rolling(window=20).std()[-days:]

        grid_upper = np.ceil(sma + 2 * std).values[-1]
        grid_lower = np.floor(sma - 2 * std).values[-1]

        atr = get_atr(currency_pair, days).values[-1]

        grid_num = int((1 + 0.2) * (grid_upper - grid_lower) / atr)

        st.markdown(
            f"""
Grid Num: {grid_num}
====

            """
        )

        aum = amount * leverage

        if grid_type == "Arithmetic":
            ladder = np.linspace(grid_upper, grid_lower, grid_num)
        elif grid_type == "Geometric":
            ladder = np.geomspace(grid_upper, grid_lower, grid_num)
        else:
            ValueError("grid_type must be Arithmetic or Geometric")

        grid = []
        for p in ladder:
            direction = "Short" if p > current_price else "Long"
            grid += [
                {
                    "price": p,
                    "lot": aum / grid_num / p,
                    "direction": direction
                    if grid_direction == "Neutral"
                    else ("Long" if grid_direction == "Long" else "Short"),
                }
            ]

        df = pd.DataFrame.from_records(grid)

        st.write(df)


if __name__ == "__main__":
    main()
