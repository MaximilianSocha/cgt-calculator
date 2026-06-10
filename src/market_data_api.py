import math
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import requests
import os

SPLITS_URL = "https://www.alphavantage.co/query?function=SPLITS"
OVERVIEW_URL = "https://www.alphavantage.co/query?function=OVERVIEW"

TICKER_CHANGES_DF = pd.read_csv(Path(__file__).parent / "ticker_change_data.csv")
TICKER_CHANGES_DF["date"] = pd.to_datetime(TICKER_CHANGES_DF["date"], dayfirst=True)

def get_alpha_vantage_api_key():
    load_dotenv()
    return os.getenv("ALPHAVANTAGE_API_KEY")

def get_splits_api_url(symbol):
    return f"{SPLITS_URL}&symbol={symbol}&apikey={get_alpha_vantage_api_key()}"

def get_company_overview_api_url(symbol):
    return f"{OVERVIEW_URL}&symbol={symbol}&apikey={get_alpha_vantage_api_key()}"


def apply_ticker_changes(trades_df, symbol, earliest_trade_date):
    # Only consider changes that happened on or after the symbol was active
    relevant = TICKER_CHANGES_DF[
        TICKER_CHANGES_DF["date"] >= earliest_trade_date
    ].sort_values("date")

    new_ticker = symbol
    while True:
        match = relevant[relevant["old_ticker"] == new_ticker]
        if match.empty:
            break
        # Follow the earliest rename that applies
        row = match.iloc[0]
        new_ticker = row["new_ticker"]
    
        if new_ticker != symbol:
            # This is checking if in the trade history there is a sell order
            # which occurs after the ticker change date which is for the new ticker.
            # This is not full-proof, however, it stops replacing symbols in the trade history
            # when it is not necessary by only doing so if there is a corresponding sell action
            # for the new symbol.
            change_applies = not trades_df[
                (trades_df["symbol"] == new_ticker)
                & (trades_df["trade_date"] > row["date"])
                & (trades_df["side"] == "SELL")
            ].empty

            if change_applies:
                old_symbol_df = trades_df[trades_df["symbol"] == symbol]
                for index in old_symbol_df.index:
                    trades_df.loc[index, "symbol"] = new_ticker

        # Now only look for renames after this change occurred
        relevant = relevant[relevant["date"] >= row["date"]]


def apply_stock_splits(trades_df, symbol, sorted_trade_dates):

    response = requests.get(get_splits_api_url(symbol))
    response_object = response.json()

    if response_object and "data" in response_object:
        splits = response_object["data"]
        earliest_split = len(splits) - 1
        trade_date_index = 0
        while trade_date_index < len(sorted_trade_dates):
            trade_date = sorted_trade_dates[trade_date_index]

            if earliest_split < 0:
                break

            effective_date = datetime.fromisoformat(splits[earliest_split]["effective_date"])
            if effective_date < trade_date:
                earliest_split -= 1
            else:
                split_factor = 1
                for i in range(earliest_split, -1, -1):
                    split_factor *= float(splits[i]["split_factor"])

                row_index = trades_df[
                    (trades_df["trade_date"] == trade_date)
                    & (trades_df["symbol"] == symbol)
                ].index[0]
                # multiply the quantity to reflect all splits which occurred after trade date
                trades_df.loc[row_index, "quantity"] *= split_factor
                # assume partial shares are rounded up to ensure solution exists
                trades_df.loc[row_index, "quantity"] = math.ceil(trades_df.loc[row_index, "quantity"])
                trade_date_index += 1


def handle_splits_and_ticker_changes(trades_df, nabtrade=False):

    symbols = trades_df["symbol"].unique()
    for symbol in symbols:
        symbol_df = trades_df[trades_df["symbol"] == symbol]
        trade_dates = sorted(symbol_df["trade_date"].to_list())

        if not nabtrade:
            apply_ticker_changes(trades_df, symbol, trade_dates[0])
        # Stock symbols are not guaranteed to be unique across exchanges.
        # This means that there is a small possibility that splits will
        # be applied to wrong stocks, with the current API this cannot be changed.
        # In future a different finance service would have to be used and exchange
        # codes would be kept for each symbol.
        apply_stock_splits(trades_df, symbol, trade_dates)
