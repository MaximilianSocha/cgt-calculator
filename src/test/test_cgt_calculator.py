from pathlib import Path

import numpy as np
from pandas import Timestamp
import pytest

from test.mock_cgt_calculator import MockCGTCalculator


@pytest.fixture
def path_to_csv():
    return Path(__file__).parent / "trade_history_test.csv"


def test_cgt_calculator(path_to_csv):
    """
    Test that the output dictionary is as expected.
    Run with: pytest src/test/test_cgt_calculator.py
    """

    results_per_fy = MockCGTCalculator(str(path_to_csv)).execute(
        allow_short_selling=True
    )
    assert results_per_fy == TEST_RESULT


TEST_RESULT = {
    np.int64(2019): {
        "buy_and_sell_pairs": {},
        "short_term": 0.0,
        "long_term": 0.0,
        "total_capital_gain": 0.0,
        "capital_gain_discount": 0.0,
        "loss": 0.0,
        "short_sell_gain": 0,
        "taxable_capital_gain": 0.0,
    },
    np.int64(2020): {
        "buy_and_sell_pairs": {
            "FLT": [
                (
                    None,
                    Timestamp("2020-06-25 00:00:00"),
                    np.float64(196.0),
                    11.832849162011172,
                ),
                (
                    Timestamp("2020-03-19 00:00:00"),
                    Timestamp("2020-06-25 00:00:00"),
                    341,
                    -2.2109924802175662,
                ),
            ],
            "NAB": [
                (
                    None,
                    Timestamp("2020-06-29 00:00:00"),
                    np.float64(176.0),
                    17.87271028037383,
                ),
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2020-06-29 00:00:00"),
                    359,
                    3.7171392497331617,
                ),
            ],
            "NVDA": [
                (
                    Timestamp("2019-05-30 00:00:00"),
                    Timestamp("2020-01-21 00:00:00"),
                    1920,
                    3.9032864583333344,
                )
            ],
            "QAN": [
                (
                    Timestamp("2020-04-21 00:00:00"),
                    Timestamp("2020-04-21 00:00:00"),
                    1329,
                    -0.15249811888638076,
                )
            ],
            "TSLA": [
                (
                    Timestamp("2019-05-30 00:00:00"),
                    Timestamp("2019-10-28 00:00:00"),
                    1065,
                    13.46892018779343,
                )
            ],
            "WEB": [
                (None, Timestamp("2020-04-14 00:00:00"), 1400.0, 2.6693214285714286),
                (
                    None,
                    Timestamp("2020-04-15 00:00:00"),
                    np.float64(1145.0),
                    2.767100436681223,
                ),
                (
                    Timestamp("2020-03-18 00:00:00"),
                    Timestamp("2020-06-25 00:00:00"),
                    2545,
                    -0.4756777996070727,
                ),
            ],
        },
        "short_term": np.float64(35543.378435754195),
        "long_term": np.float64(0.0),
        "total_capital_gain": np.float64(35543.378435754195),
        "capital_gain_discount": np.float64(0.0),
        "loss": np.float64(2167.21843575419),
        "short_sell_gain": np.float64(12370.215445099984),
        "taxable_capital_gain": np.float64(33376.16),
    },
    np.int64(2021): {
        "buy_and_sell_pairs": {
            "CCL": [
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2020-10-29 00:00:00"),
                    380,
                    -1.7070000000000007,
                )
            ],
            "SYD": [
                (
                    Timestamp("2020-03-19 00:00:00"),
                    Timestamp("2020-08-05 00:00:00"),
                    1017,
                    0.29568338249754245,
                )
            ],
        },
        "short_term": np.float64(300.71000000000066),
        "long_term": np.float64(0.0),
        "total_capital_gain": np.float64(300.71000000000066),
        "capital_gain_discount": 0.0,
        "loss": np.float64(648.6600000000003),
        "short_sell_gain": 0,
        "taxable_capital_gain": np.float64(-347.94999999999965),
    },
    np.int64(2022): {
        "buy_and_sell_pairs": {
            "AAPL": [
                (
                    Timestamp("2021-01-19 00:00:00"),
                    Timestamp("2022-06-01 00:00:00"),
                    49,
                    37.947551020408184,
                )
            ],
            "AIR": [
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2022-06-01 00:00:00"),
                    46,
                    56.719999999999985,
                )
            ],
            "AIZ": [
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2021-08-20 00:00:00"),
                    5796,
                    0.49897860593512755,
                )
            ],
            "BRBY": [
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2022-06-01 00:00:00"),
                    450,
                    7.679777777777776,
                )
            ],
            "GOOGL": [
                (
                    Timestamp("2020-08-05 00:00:00"),
                    Timestamp("2022-06-01 00:00:00"),
                    4,
                    1088.5,
                )
            ],
            "IMAX": [
                (
                    Timestamp("2020-03-31 00:00:00"),
                    Timestamp("2022-06-02 00:00:00"),
                    329,
                    9.238206686930093,
                )
            ],
            "MGM": [
                (
                    Timestamp("2020-03-31 00:00:00"),
                    Timestamp("2022-06-01 00:00:00"),
                    355,
                    28.53307042253521,
                )
            ],
            "QQQ": [
                (
                    Timestamp("2022-01-25 00:00:00"),
                    Timestamp("2022-06-02 00:00:00"),
                    10,
                    -73.02842857142855,
                ),
                (
                    Timestamp("2021-09-29 00:00:00"),
                    Timestamp("2022-06-02 00:00:00"),
                    20,
                    -88.49442857142856,
                ),
                (
                    Timestamp("2020-08-05 00:00:00"),
                    Timestamp("2022-06-02 00:00:00"),
                    5,
                    40.598571428571404,
                ),
            ],
        },
        "short_term": np.float64(0.0),
        "long_term": np.float64(28542.132857142857),
        "total_capital_gain": np.float64(28542.132857142857),
        "capital_gain_discount": np.float64(13020.98),
        "loss": np.float64(2500.1728571428566),
        "short_sell_gain": 0,
        "taxable_capital_gain": np.float64(13020.98),
    },
    np.int64(2023): {
        "buy_and_sell_pairs": {
            "GOOG": [
                (
                    Timestamp("2020-04-15 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    60,
                    33.02956666666665,
                ),
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    40,
                    40.77489999999999,
                ),
                (
                    Timestamp("2022-06-13 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    60,
                    -21.996499999999997,
                ),
                (
                    Timestamp("2020-03-23 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    40,
                    40.944,
                ),
            ],
            "META": [
                (
                    Timestamp("2022-04-06 00:00:00"),
                    Timestamp("2023-02-22 00:00:00"),
                    33,
                    -55.33757575757579,
                )
            ],
            "NCLH": [
                (
                    Timestamp("2020-03-18 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    295,
                    7.593898305084746,
                )
            ],
            "NVDA": [
                (
                    Timestamp("2020-11-10 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    280,
                    11.254357142857138,
                )
            ],
            "QQQ": [
                (
                    Timestamp("2022-06-06 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    50,
                    -6.099900000000048,
                ),
                (
                    Timestamp("2020-08-05 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    6,
                    47.754899999999964,
                ),
                (
                    Timestamp("2020-04-15 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    44,
                    91.9689909090909,
                ),
                (
                    Timestamp("2022-10-11 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    39,
                    0.07791666666668107,
                ),
                (
                    Timestamp("2022-07-05 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    35,
                    10.417726190476174,
                ),
                (
                    Timestamp("2022-06-13 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    30,
                    20.351249999999936,
                ),
                (
                    Timestamp("2020-08-05 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    14,
                    47.66458333333327,
                ),
                (
                    Timestamp("2020-04-07 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    2,
                    97.26870098039211,
                ),
            ],
            "RCL": [
                (
                    Timestamp("2020-03-18 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    108,
                    59.67805555555556,
                )
            ],
            "TEAM": [
                (
                    Timestamp("2020-04-03 00:00:00"),
                    Timestamp("2023-02-21 00:00:00"),
                    33,
                    20.671212121212136,
                )
            ],
        },
        "short_term": np.float64(978.1966666666647),
        "long_term": np.float64(22964.33656862745),
        "total_capital_gain": np.float64(23942.53323529411),
        "capital_gain_discount": np.float64(10245.804117647054),
        "loss": np.float64(3450.925000000004),
        "short_sell_gain": 0,
        "taxable_capital_gain": np.float64(10245.804117647054),
    },
    np.int64(2024): {
        "buy_and_sell_pairs": {
            "TQQQ": [
                (
                    Timestamp("2022-06-13 00:00:00"),
                    Timestamp("2024-01-29 00:00:00"),
                    55,
                    48.45238666666666,
                ),
                (
                    Timestamp("2022-06-06 00:00:00"),
                    Timestamp("2024-01-29 00:00:00"),
                    200,
                    36.76092,
                ),
                (
                    Timestamp("2022-04-05 00:00:00"),
                    Timestamp("2024-01-29 00:00:00"),
                    245,
                    3.333924081632645,
                ),
            ]
        },
        "short_term": np.float64(0.0),
        "long_term": np.float64(10833.876666666665),
        "total_capital_gain": np.float64(10833.876666666665),
        "capital_gain_discount": np.float64(5416.938333333333),
        "loss": np.float64(0.0),
        "short_sell_gain": 0,
        "taxable_capital_gain": np.float64(5416.938333333333),
    },
    np.int64(2025): {
        "buy_and_sell_pairs": {
            "AMZN": [
                (
                    Timestamp("2020-11-09 00:00:00"),
                    Timestamp("2025-06-17 00:00:00"),
                    40,
                    106.38550000000001,
                )
            ],
            "HOOD": [
                (
                    Timestamp("2021-08-20 00:00:00"),
                    Timestamp("2025-06-17 00:00:00"),
                    80,
                    51.786125,
                )
            ],
            "MSFT": [
                (
                    Timestamp("2021-09-30 00:00:00"),
                    Timestamp("2025-06-17 00:00:00"),
                    12,
                    321.9716666666667,
                )
            ],
            "PLTR": [
                (
                    Timestamp("2020-11-09 00:00:00"),
                    Timestamp("2024-12-17 00:00:00"),
                    500,
                    95.67854,
                )
            ],
        },
        "short_term": np.float64(0.0),
        "long_term": np.float64(60101.24),
        "total_capital_gain": np.float64(60101.24),
        "capital_gain_discount": np.float64(30050.62),
        "loss": np.float64(0.0),
        "short_sell_gain": 0,
        "taxable_capital_gain": np.float64(30050.62),
    },
}
