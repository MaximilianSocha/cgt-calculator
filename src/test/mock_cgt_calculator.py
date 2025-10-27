from datetime import datetime
import pandas as pd
from cgt_calculator import CGTCalculator

TEST_STOCK_SPLITS = {
    "AMZN": {"data":
        [
            {"effective_date": "2022-06-06", "split_factor": "20.0000"},
            {"effective_date": "1999-09-02", "split_factor": "2.0000"},
            {"effective_date": "1999-01-05", "split_factor": "3.0000"},
        ]
    },
    "TQQQ": {"data":
        [
            {'effective_date': '2022-01-13', 'split_factor': '2.0000'},
            {'effective_date': '2021-01-21', 'split_factor': '2.0000'},
            {'effective_date': '2018-05-24', 'split_factor': '3.0000'},
            {'effective_date': '2017-01-12', 'split_factor': '2.0000'},
            {'effective_date': '2014-01-24', 'split_factor': '2.0000'},
            {'effective_date': '2012-05-11', 'split_factor': '2.0000'},
            {'effective_date': '2011-02-25', 'split_factor': '2.0000'}]
},
    "GOOG": {"data":
        [
            {'effective_date': '2022-07-18', 'split_factor': '20.0000'}]
},
    "NVDA": {"data":
        [
            {'effective_date': '2024-06-10', 'split_factor': '10.0000'},
            {'effective_date': '2021-07-20', 'split_factor': '4.0000'},
            {'effective_date': '2007-09-11', 'split_factor': '1.5000'},
            {'effective_date': '2006-04-07', 'split_factor': '2.0000'},
            {'effective_date': '2001-09-17', 'split_factor': '2.0000'},
            {'effective_date': '2000-06-27', 'split_factor': '2.0000'}
        ]
},
    "TSLA": {"data":
        [
            {'effective_date': '2022-08-25', 'split_factor': '3.0000'},
            {'effective_date': '2020-08-31', 'split_factor': '5.0000'}
        ]
    }
}


def apply_stock_splits(trades_df, symbol, trade_dates):

    if symbol in TEST_STOCK_SPLITS:
        response = TEST_STOCK_SPLITS[symbol]
        
        if response and "data" in response:
            splits = response["data"]
            earliest_split = len(splits) - 1
            trade_date_index = 0
            while trade_date_index < len(trade_dates):
                trade_date = trade_dates[trade_date_index]

                if earliest_split < 0:
                    break

                effective_date = datetime.fromisoformat(
                    splits[earliest_split]["effective_date"]
                )
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
                    trades_df.loc[row_index, "quantity"] *= int(split_factor)
                    trade_date_index += 1


def mock_handle_splits_and_ticker_changes(trades_df):
    symbols = trades_df["symbol"].unique()
    for symbol in symbols:
        symbol_df = trades_df[trades_df["symbol"] == symbol]
        trade_dates = sorted(symbol_df["trade_date"].to_list())

        # apply_ticker_changes(trades_df, symbols, symbol, trade_dates[-1])
        apply_stock_splits(trades_df, symbol, trade_dates)

class MockCGTCalculator(CGTCalculator):

    def __init__(self, trade_history_csv_path):

        # Initialise the trades data frame
        self.trades_df = pd.read_csv(trade_history_csv_path)
        self._initialise_trades_df()
        mock_handle_splits_and_ticker_changes(self.trades_df)