from pathlib import Path
import pandas as pd
from lp_solver import minimise_tax_for_symbol_year
from market_data_api import handle_splits_and_ticker_changes
from output_excel_writer import export_capital_gains_to_excel


def au_fin_year(transaction_date):
    # FY runs 1 Jul–30 Jun; FY label is the year ending (e.g., 30/06/2025 -> "2025")
    return (
        transaction_date.year + 1
        if transaction_date.month >= 7
        else transaction_date.year
    )


def create_trades_dataframe(trade_history_csv_path):
    trades_df = pd.read_csv(trade_history_csv_path)
    # Normalise columns
    trades_df.columns = [c.strip().lower() for c in trades_df.columns]
    required_cols = {"symbol", "side", "trade_date", "quantity", "transaction_amount"}
    missing_cols = required_cols - set(trades_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # parse and transform data
    trades_df["side"] = trades_df["side"].astype(str).str.upper()
    # remove appended exchange name (e.g .NYSE)
    trades_df["symbol"] = [str(s).split(".")[0].upper() for s in trades_df["symbol"]]
    trades_df["trade_date"] = pd.to_datetime(trades_df["trade_date"], dayfirst=True)
    trades_df["quantity"] = trades_df["quantity"].astype(float)
    trades_df["transaction_amount"] = trades_df["transaction_amount"].astype(float)
    trades_df["fy"] = trades_df["trade_date"].apply(au_fin_year).astype(int)
    trades_df["id"] = [i for i in range(len(trades_df["trade_date"]))]

    handle_splits_and_ticker_changes(trades_df)

    return trades_df


def calculate_short_sell_gain(sell_df, qty_difference, sell_buy_pairs_for_symbol):
    """
    Modify sell df to not include short selling on symbol and return gain from short selling.
    """
    sorted_sells_df = sell_df.sort_values(by="unit_price")
    short_sell_gain = 0
    for _, sell_trade in sorted_sells_df.iterrows():
        row_index = sell_df[sell_df["id"] == sell_trade["id"]].index[0]
        if sell_trade["quantity"] >= qty_difference:
            sell_df.loc[row_index, "quantity"] -= qty_difference
            short_sell_gain += qty_difference * sell_trade["unit_price"]

            # Add short sell to output
            sell_buy_pairs_for_symbol.append(
                (
                    None,
                    sell_trade["trade_date"],
                    qty_difference,
                    sell_trade["unit_price"],
                )
            )

            return short_sell_gain
        
        else:
            sell_df.loc[row_index, "quantity"] = 0
            qty_difference -= sell_trade["quantity"]
            short_sell_gain += sell_trade["quantity"] * sell_trade["unit_price"]

            # Add short sell to output
            sell_buy_pairs_for_symbol.append(
                (
                    None,
                    sell_trade["trade_date"],
                    sell_trade["quantity"],
                    sell_trade["unit_price"],
                )
            )

    return short_sell_gain


def extract_trades(trades_df, used_buy_trades={}):
    trades = []
    for _, trade in trades_df.iterrows():
        trade_id = trade["id"]
        trade_date = trade["trade_date"]
        unit_price = trade["transaction_amount"] / trade["quantity"]

        if trade_id in used_buy_trades:
            quantity = trade["quantity"] - used_buy_trades[trade_id]
        else:
            used_buy_trades[trade_id] = 0
            quantity = trade["quantity"]

        if quantity <= 0:
            continue

        trades.append([trade_id, trade_date, quantity, unit_price])

    return trades


def compute_min_tax_per_fy(trade_history_csv_path):
    """
    CSV columns (case-insensitive):
      symbol, side (BUY/SELL), trade_date (YYYY-MM-DD), quantity, transaction_amount,
    Returns: DataFrame of per-FY totals and dict of per-FY assignment details.
    """

    trades_df = create_trades_dataframe(trade_history_csv_path)

    used_buy_trades = {}  # key is id and value is quantity used
    results_per_fy = {}
    for fy in sorted(trades_df["fy"].unique()):
        results_per_fy[fy] = dict(
            # key: symbol, value: list of tuples
            buy_and_sell_pairs={},
            total_capital_gain=0,
            capital_gain_discount=0,
            loss=0,
            short_sell_gain=0,
            taxable_capital_gain=0,
        )

        for symbol in sorted(trades_df["symbol"].unique()):

            buy_trades_df = trades_df[
                (trades_df["symbol"] == symbol)
                & (trades_df["side"] == "BUY")
                & (trades_df["fy"] <= fy)
            ]
            sell_trades_df = trades_df[
                (trades_df["symbol"] == symbol)
                & (trades_df["side"] == "SELL")
                & (trades_df["fy"] == fy)
            ]

            buy_trades = extract_trades(buy_trades_df, used_buy_trades)
            sell_trades = extract_trades(sell_trades_df)

            # Build DataFrames for LP
            solver_buys_df = pd.DataFrame(
                buy_trades, columns=["id", "trade_date", "qty_avail", "unit_price"]
            )
            solver_sells_df = pd.DataFrame(
                sell_trades, columns=["id", "trade_date", "quantity", "unit_price"]
            )

            # Check if the user is short selling on the symbol
            short_sell_gain = 0
            total_sell_qty = solver_sells_df["quantity"].sum()
            total_buy_qty = solver_buys_df["qty_avail"].sum()
            if total_buy_qty < total_sell_qty:
                response = input(f"Short selling detected on symbol: {symbol}.\nDo you wish to proceed? (Y/N)")
                if response == "Y":
                    results_per_fy[fy]["buy_and_sell_pairs"][symbol] = []
                    short_sell_gain = calculate_short_sell_gain(
                        solver_sells_df,
                        total_sell_qty - total_buy_qty,
                        results_per_fy[fy]["buy_and_sell_pairs"][symbol],
                    )
                else:
                    return

            # Solve
            result = minimise_tax_for_symbol_year(
                solver_buys_df, solver_sells_df, symbol
            )

            solution_df = result["x"]
            for _, sol_row in solution_df.iterrows():
                # Mark as used so that units from this buy are not reused
                used_buy_trades[sol_row["buy_id"]] += sol_row["quantity"]

                # Extract data from trades df to populate result
                buy_date = trades_df[trades_df["id"] == sol_row["buy_id"]]["trade_date"].iloc[0]
                sell_date = trades_df[trades_df["id"] == sol_row["sell_id"]]["trade_date"].iloc[0]
                qty_sold = int(sol_row["quantity"])
                per_unit_gain = sol_row["per_unit_gain"]

                if symbol in results_per_fy[fy]["buy_and_sell_pairs"]:
                    results_per_fy[fy]["buy_and_sell_pairs"][symbol].append(
                        (buy_date, sell_date, qty_sold, per_unit_gain)
                    )
                else:
                    results_per_fy[fy]["buy_and_sell_pairs"][symbol] = [
                        (buy_date, sell_date, qty_sold, per_unit_gain)
                    ]

            results_per_fy[fy]["total_capital_gain"] += (
                result["short_term"] + result["long_term"]
            )
            results_per_fy[fy]["capital_gain_discount"] += 0.5 * result["long_term"]
            results_per_fy[fy]["loss"] += result["loss"]
            results_per_fy[fy]["short_sell_gain"] += short_sell_gain
            # Taxable gain includes raw gain, subtracted CGT discount, subtracted loss, and then short sell gain on top
            results_per_fy[fy]["taxable_capital_gain"] += (
                result["taxable"] + short_sell_gain
            )

    export_capital_gains_to_excel(results_per_fy)


if __name__ == "__main__":
    compute_min_tax_per_fy(Path(__file__).parent / "trade_history.csv")
