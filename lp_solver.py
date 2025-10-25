import numpy as np
from scipy.optimize import linprog
import pandas as pd


def is_long_term(buy_date, sell_date):
    # ATO requires >12 months: exclude both acquisition day and CGT event day.
    # Practical test: strictly more than 365 days between dates (approx; leap years aside).
    return (sell_date - buy_date).days > 365


def minimise_tax_for_symbol_year(buys, sells, symbol):
    """
    buys: DataFrame with columns [id, trade_date, qty_avail, unit_price] for parcels with buy_date <= latest sell
    sells: DataFrame with columns [id, trade_date, quantity, unit_price]
    Returns dict with optimal taxable gain and breakdown, plus parcel assignments.
    """

    if sells.empty:
        return dict(
            short_term=0.0,
            long_term=0.0,
            loss=0.0,
            taxable=0.0,
            x=pd.DataFrame(columns=["buy_id", "sell_id", "quantity"]),
        )

    # Build edge list (eligible matches)
    edges = []
    for _, sell_row in sells.iterrows():
        for _, buy_row in buys.iterrows():
            if (
                buy_row["trade_date"] <= sell_row["trade_date"]
                and buy_row["qty_avail"] > 0
                and sell_row["quantity"] > 0
            ):
                gain = (
                    sell_row["unit_price"] - buy_row["unit_price"]
                )  # per-share raw gain
                long_term = is_long_term(buy_row["trade_date"], sell_row["trade_date"])
                edges.append((buy_row["id"], sell_row["id"], gain, long_term))

    # Index mapping
    buy_ids = list(buys["id"])
    sell_ids = list(sells["id"])

    # Variable order: x_e for each edge e, then A_prime, R, B_prime
    num_edges = len(edges)
    Ap_idx, Lp_idx, Bp_idx = num_edges, num_edges + 1, num_edges + 2
    c = np.zeros(num_edges + 3)
    c[Ap_idx] = 1.0
    c[Bp_idx] = 0.5  # minimise A' + 0.5 B'

    bounds = [(0, None)] * (num_edges + 3)  # x_e >=0; A',R,B' >=0

    # Equality constraints: for each sell, sum x_e = qty
    # Ensures that the sum of buy units linked to a sell equals the sell quantity
    A_eq = []
    b_eq = []
    for sell_id_1 in sell_ids:
        row = np.zeros(num_edges + 3)
        for k, (_, sell_id_2, _, _) in enumerate(edges):
            if sell_id_2 == sell_id_1:
                row[k] = 1.0
        A_eq.append(row)
        quantity = float(sells.loc[sells["id"] == sell_id_1, "quantity"].values[0])
        b_eq.append(quantity)

    # Inequalities:
    A_ub = []
    b_ub = []

    # (1) Buy capacities: sum_j x_ij <= qty_i
    # Ensures that the sum of sell units linked to a buy doesn't exceed the buy quantity
    for buy_id_1 in buy_ids:
        row = np.zeros(num_edges + 3)
        for k, (buy_id_2, _, _, _) in enumerate(edges):
            if buy_id_2 == buy_id_1:
                row[k] = 1.0
        cap = float(buys.loc[buys["id"] == buy_id_1, "qty_avail"].values[0])
        A_ub.append(row)
        b_ub.append(cap)

    # Helper to build linear forms for A, B, L
    # A: sum over ST & g>0 of g*x
    # B: sum over LT & g>0 of g*x
    # L: sum over g<=0 of (-g)*x
    A_row = np.zeros(num_edges + 3)
    B_row = np.zeros(num_edges + 3)
    L_row = np.zeros(num_edges + 3)
    for k, (_, _, gain, long_term) in enumerate(edges):
        if gain > 0:
            if long_term:
                B_row[k] = gain
            else:
                A_row[k] = gain
        else:
            L_row[k] = -gain  # positive number

    # Must be nagetive because upper bound cannot be infinity
    A_ub.append(-A_row)
    b_ub.append(0.0)
    A_ub.append(-B_row)
    b_ub.append(0.0)
    A_ub.append(-L_row)
    b_ub.append(0.0)

    # Rows which contain solution variables
    A_prime_row = np.zeros(num_edges + 3)
    A_prime_row[Ap_idx] = 1
    B_prime_row = np.zeros(num_edges + 3)
    B_prime_row[Bp_idx] = 1
    L_prime_row = np.zeros(num_edges + 3)
    L_prime_row[Lp_idx] = 1

    # Enforcing that the result is stored in the solution variable
    A_eq.append(A_prime_row - A_row)
    b_eq.append(0)

    A_eq.append(B_prime_row - B_row)
    b_eq.append(0)

    A_eq.append(L_prime_row - L_row)
    b_eq.append(0)

    A_ub = np.vstack(A_ub) if A_ub else None
    b_ub = np.array(b_ub) if b_ub else None

    A_eq = np.vstack(A_eq) if A_eq else None
    b_eq = np.array(b_eq) if b_eq else None

    # minimise c @ x
    # A_ub @ x <= b_ub
    # A_eq @ x == b_eq
    res = linprog(
        c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs"
    )
    if res.status != 0:
        raise RuntimeError(
            f"LP did not solve successfully for symbol: {symbol}\n"
            f"Error Message: {res.message}"
        ) 

    xsol = res.x[:num_edges]
    A_prime = res.x[Ap_idx]
    B_prime = res.x[Bp_idx]
    L_prime = res.x[Lp_idx]

    # Build assignment DataFrame
    rows = []
    for k, (buy_id, sell_id, gain, long_term) in enumerate(edges):
        quantity = xsol[k]
        if quantity > 1e-9:
            rows.append(
                dict(
                    buy_id=buy_id,
                    sell_id=sell_id,
                    quantity=quantity,
                    per_unit_gain=gain,
                    long_term=bool(long_term),
                )
            )
    x_df = pd.DataFrame(rows)

    taxable = A_prime + 0.5 * B_prime - L_prime
    return dict(
        short_term=A_prime,  # gain from short term
        long_term=B_prime,  # gain from long term
        loss=L_prime,
        taxable=taxable,
        x=x_df,
    )
