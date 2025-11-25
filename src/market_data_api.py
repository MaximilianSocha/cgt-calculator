from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import requests
import os

SPLITS_URL = "https://www.alphavantage.co/query?function=SPLITS"
OVERVIEW_URL = "https://www.alphavantage.co/query?function=OVERVIEW"

TICKER_CHANGES_DF = pd.read_csv(Path(__file__).parent / "ticker_change_data.csv")

def get_alpha_vantage_api_key():
    load_dotenv()
    return os.getenv("ALPHAVANTAGE_API_KEY")

def get_splits_api_url(symbol):
    return f"{SPLITS_URL}&symbol={symbol}&apikey={get_alpha_vantage_api_key()}"

def get_company_overview_api_url(symbol):
    return f"{OVERVIEW_URL}&symbol={symbol}&apikey={get_alpha_vantage_api_key()}"


def apply_ticker_changes(trades_df, symbol):
    old_ticker_row = TICKER_CHANGES_DF[TICKER_CHANGES_DF["old_ticker"] == symbol]
    new_ticker = ""
    while not old_ticker_row.empty:
        new_ticker = TICKER_CHANGES_DF.loc[old_ticker_row.index[0], "new_ticker"]
        old_ticker_row = TICKER_CHANGES_DF[
            TICKER_CHANGES_DF["old_ticker"] == new_ticker
        ]
    
    if new_ticker:
        old_symbol_df = trades_df[trades_df["symbol"] == symbol]
        for index in old_symbol_df.index:
            trades_df.loc[index, "symbol"] = new_ticker


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
                trade_date_index += 1


def handle_splits_and_ticker_changes(trades_df):

    symbols = trades_df["symbol"].unique()
    for symbol in symbols:
        symbol_df = trades_df[trades_df["symbol"] == symbol]
        trade_dates = sorted(symbol_df["trade_date"].to_list())

        # Download ticker change data from here https://stockanalysis.com/actions/changes/2022/
        # and if needed from https://www.asx.com.au/markets/market-resources/asx-codes-and-descriptors/asx-code-changes
        # It will only have to be updated once a year around June/July, so no need for API
        #apply_ticker_changes(trades_df, symbol)
        #apply_stock_splits(trades_df, symbol, trade_dates)
