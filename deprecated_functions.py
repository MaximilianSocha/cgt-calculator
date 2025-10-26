from datetime import datetime
import nasdaqdatalink
import requests
from apiclient import APIClient
from src.market_data_api import get_company_overview_api_url


def apply_ticker_changes(trades_df, symbols, current_symbol, latest_trade_date):
    # EODHD api is a possible other candidate for getting stock splits and ticker change data - this is probably the best option
    # another way of potentially doing this is to download the ticker change data and store it in a database (would be 10000s rows at most) and then query that database, only need to updated once a year.
    # The above wouldn't be fool proof but it could be the best option
    response = requests.get(get_company_overview_api_url(current_symbol))
    response_object = response.json()

    if response_object and "data" in response_object:
        current_cik = response_object["CIK"]
        for symbol in symbols:
            r = requests.get(get_company_overview_api_url(symbol))
            cik = r.json()["data"]["CIK"]

            symbol_df = trades_df[trades_df["symbol"] == symbol]
            # if company identifier is the same and the trade is newer, then set all instances of past symbol to new symbol
            if (
                current_symbol != symbol
                and current_cik == cik
                and latest_trade_date < symbol_df["trade_date"].max()
            ):
                row_indices = trades_df[(trades_df["symbol"] == current_symbol)].index
                for index in row_indices:
                    trades_df.loc[index, "symbol"] = symbol

EODHD_TOKEN = ""  # get from .env

def eodhd():
    symbol = "AAPL.US"
    api = APIClient(EODHD_TOKEN)
    resp = api.symbol_change_history()
    print(resp)

    url = f"https://eodhd.com/api/div/{symbol}?from=2000-01-01&api_token={EODHD_TOKEN}&fmt=json"
    data = requests.get(url).json()
    print(data)

eodhd()


NASDAQ_LINK_API_KEY = "vxV5QWzBmbTi2XzeD9ca"
DATA_TABLE_CODES = ["NDAQ/RTAT10", "ZACKS/FC"]

def nasdaq_data_link():
    nasdaqdatalink.ApiConfig.api_key = NASDAQ_LINK_API_KEY
    df = nasdaqdatalink.get_table(
        datatable_code="WIKI/PRICES",
        api_key=NASDAQ_LINK_API_KEY,
        paginate=True,
        ticker="BHP",
        qopts={"columns": ["split_ratio"]},
    )
    print(df[df["split_ratio"] != 1])



POLYGON_API_KEY = "" # get from .env

# def polygon_io(trades_df):
#     client = RESTClient(POLYGON_API_KEY)

#     symbols = trades_df["symbol"].unique()
#     for symbol in symbols:
#         symbol_df = trades_df[trades_df["symbol"] == symbol]
#         trade_dates = sorted(symbol_df["trade_date"].to_list())

#         print(symbol)

#         apply_stock_splits(client, trades_df, symbol, trade_dates)
#         apply_ticker_changes(client, trades_df, symbol)


def apply_stock_splits(client, trades_df, symbol, trade_dates):
    splits = []
    for s in client.list_splits(
        ticker=symbol,
        order="asc",
        limit="1000",
        sort="execution_date",
    ):
        splits.append(s)

    earliest_split = 0
    for trade_date in trade_dates:
        if earliest_split >= len(splits):
            break

        execution_date = datetime.fromisoformat(splits[earliest_split].execution_date)
        if execution_date < trade_date:
            earliest_split += 1
        else:
            split_factor = 1
            for i in range(earliest_split, len(splits)):
                split_from = int(splits[i].split_from)
                split_to = int(splits[i].split_to)
                split_factor *= int(split_to / split_from)
            row_index = trades_df[trades_df["trade_date"] == trade_date].index[0]
            col_name = "quantity"
            # multiply the quantity to reflect all splits which occurred after trade date
            trades_df[row_index, col_name] *= split_factor

