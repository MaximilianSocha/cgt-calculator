from pandas import Timestamp
import xlsxwriter
import numpy as np


def export_capital_gains_to_excel(data_dict, filename="capital_gains_report.xlsx"):
    """
    Export capital gains data to a multi-sheet Excel file.

    Args:
        data_dict: Dictionary with structure:
            { financial_year: {
                buy_and_sell_pairs: {
                    symbol: [(buy_date, sell_date, sold_quantity, per_unit_gain), ...]
                },
                total_capital_gain: float,
                losses: float,
                short_sell_gain: float,
                capital_gain_discount: float,
                taxable_capital_gain: float
            }}
        filename: Output Excel filename
    """

    workbook = xlsxwriter.Workbook(filename)

    # Define formats
    header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#4472C4",
            "font_color": "white",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )

    symbol_header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9E1F2",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "font_size": 11,
        }
    )

    data_format = workbook.add_format(
        {"border": 1, "align": "left", "valign": "vcenter"}
    )

    number_format = workbook.add_format(
        {"border": 1, "align": "right", "valign": "vcenter", "num_format": "#,##0.00"}
    )

    date_format = workbook.add_format(
        {
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "num_format": "dd/mm/yyyy",
        }
    )

    summary_label_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#F2F2F2",
            "border": 1,
            "align": "left",
            "valign": "vcenter",
        }
    )

    summary_value_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#F2F2F2",
            "border": 1,
            "align": "right",
            "valign": "vcenter",
            "num_format": "$#,##0.00",
        }
    )

    # Process each financial year
    for fy, fy_data in sorted(data_dict.items()):
        # Create worksheet for this financial year
        worksheet = workbook.add_worksheet(str(fy))

        # Set column widths
        worksheet.set_column("A:A", 18)  # Buy Date
        worksheet.set_column("B:B", 18)  # Sell Date
        worksheet.set_column("C:C", 18)  # Quantity
        worksheet.set_column("D:D", 18)  # Per Unit Gain

        current_row = 0

        # Process each symbol
        sell_and_buy_pairs = fy_data.get("buy_and_sell_pairs", {})

        for symbol in sorted(sell_and_buy_pairs.keys()):
            trades = sell_and_buy_pairs[symbol]

            # Symbol header
            worksheet.merge_range(
                current_row,
                0,
                current_row,
                3,
                f"Symbol: {symbol}",
                symbol_header_format,
            )
            current_row += 1

            # Column headers
            worksheet.write(current_row, 0, "Buy Date", header_format)
            worksheet.write(current_row, 1, "Sell Date", header_format)
            worksheet.write(current_row, 2, "Sold Quantity", header_format)
            worksheet.write(current_row, 3, "Per Unit Gain", header_format)
            current_row += 1

            # Trade data
            for trade in trades:
                buy_date, sell_date, sold_quantity, per_unit_gain = trade

                # Handle buy_date (can be None for short selling)
                if buy_date is None:
                    worksheet.write(current_row, 0, "Short Sell", data_format)
                else:
                    worksheet.write_datetime(current_row, 0, buy_date, date_format)

                # Sell date
                worksheet.write_datetime(current_row, 1, sell_date, date_format)

                # Quantity and gain
                worksheet.write(current_row, 2, sold_quantity, number_format)
                worksheet.write(current_row, 3, per_unit_gain, number_format)

                current_row += 1

            # Add spacing after each symbol
            current_row += 1

        # Add summary section at the bottom
        current_row += 1
        worksheet.merge_range(
            current_row,
            0,
            current_row,
            3,
            f"Financial Year {fy} Summary",
            symbol_header_format,
        )
        current_row += 1

        # Summary rows
        summary_items = [
            ("Total Capital Gain", fy_data.get("total_capital_gain", 0)),
            ("Loss", fy_data.get("loss", 0)),
            ("Short Sell Gain", fy_data.get("short_sell_gain", 0)),
            ("Capital Gains Discount", fy_data.get("capital_gain_discount", 0)),
            ("Taxable Capital Gain", fy_data.get("taxable_capital_gain", 0)),
        ]

        for label, value in summary_items:
            worksheet.write(current_row, 0, label, summary_label_format)
            worksheet.merge_range(
                current_row, 1, current_row, 3, value, summary_value_format
            )
            current_row += 1

    workbook.close()
    print(f"Excel file '{filename}' created successfully!")


# Example usage
if __name__ == "__main__":
    # Sample data
    sample_data = {
        np.int64(2019): {
            "buy_and_sell_pairs": {},
            "total_capital_gain": 0.0,
            "capital_gain_discount": 0.0,
            "losses": 0.0,
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
                        341.0,
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
                        359.0,
                        3.7171392497331617,
                    ),
                ],
                "NVDA": [
                    (
                        Timestamp("2019-05-30 00:00:00"),
                        Timestamp("2020-01-21 00:00:00"),
                        1920.0,
                        3.9032864583333344,
                    )
                ],
                "QAN": [
                    (
                        Timestamp("2020-04-21 00:00:00"),
                        Timestamp("2020-04-21 00:00:00"),
                        1329.0,
                        -0.15249811888638076,
                    )
                ],
                "TSLA": [
                    (
                        Timestamp("2019-05-30 00:00:00"),
                        Timestamp("2019-10-28 00:00:00"),
                        1065.0,
                        13.46892018779343,
                    )
                ],
                "WEB": [
                    (
                        None,
                        Timestamp("2020-04-14 00:00:00"),
                        1400.0,
                        2.6693214285714286,
                    ),
                    (
                        None,
                        Timestamp("2020-04-15 00:00:00"),
                        np.float64(1145.0),
                        2.767100436681223,
                    ),
                    (
                        Timestamp("2020-03-18 00:00:00"),
                        Timestamp("2020-06-25 00:00:00"),
                        2545.0,
                        -0.4756777996070727,
                    ),
                ],
            },
            "total_capital_gain": np.float64(23173.16299065421),
            "capital_gain_discount": np.float64(0.0),
            "losses": np.float64(2167.21843575419),
            "short_sell_gain": np.float64(12370.215445099984),
            "taxable_capital_gain": np.float64(33376.16),
        },
        np.int64(2021): {
            "buy_and_sell_pairs": {
                "CCL": [
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2020-10-29 00:00:00"),
                        380.0,
                        -1.7070000000000007,
                    )
                ],
                "SYD": [
                    (
                        Timestamp("2020-03-19 00:00:00"),
                        Timestamp("2020-08-05 00:00:00"),
                        1017.0,
                        0.29568338249754245,
                    )
                ],
            },
            "total_capital_gain": np.float64(300.71000000000066),
            "capital_gain_discount": np.float64(0.0),
            "losses": np.float64(648.6600000000003),
            "short_sell_gain": 0,
            "taxable_capital_gain": np.float64(-347.94999999999965),
        },
        np.int64(2022): {
            "buy_and_sell_pairs": {
                "AAPL": [
                    (
                        Timestamp("2021-01-19 00:00:00"),
                        Timestamp("2022-06-01 00:00:00"),
                        49.0,
                        37.947551020408184,
                    )
                ],
                "AIR": [
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2022-06-01 00:00:00"),
                        46.0,
                        56.719999999999985,
                    )
                ],
                "AIZ": [
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2021-08-20 00:00:00"),
                        5796.0,
                        0.49897860593512755,
                    )
                ],
                "BRBY": [
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2022-06-01 00:00:00"),
                        450.0,
                        7.679777777777776,
                    )
                ],
                "GOOGL": [
                    (
                        Timestamp("2020-08-05 00:00:00"),
                        Timestamp("2022-06-01 00:00:00"),
                        4.0,
                        1088.5,
                    )
                ],
                "IMAX": [
                    (
                        Timestamp("2020-03-31 00:00:00"),
                        Timestamp("2022-06-02 00:00:00"),
                        329.0,
                        9.238206686930093,
                    )
                ],
                "MGM": [
                    (
                        Timestamp("2020-03-31 00:00:00"),
                        Timestamp("2022-06-01 00:00:00"),
                        355.0,
                        28.53307042253521,
                    )
                ],
                "QQQ": [
                    (
                        Timestamp("2022-01-25 00:00:00"),
                        Timestamp("2022-06-02 00:00:00"),
                        10.0,
                        -73.02842857142855,
                    ),
                    (
                        Timestamp("2021-09-29 00:00:00"),
                        Timestamp("2022-06-02 00:00:00"),
                        20.0,
                        -88.49442857142856,
                    ),
                    (
                        Timestamp("2020-08-05 00:00:00"),
                        Timestamp("2022-06-02 00:00:00"),
                        5.0,
                        40.598571428571404,
                    ),
                ],
            },
            "total_capital_gain": np.float64(28542.132857142857),
            "capital_gain_discount": np.float64(14271.066428571428),
            "losses": np.float64(2500.1728571428566),
            "short_sell_gain": 0,
            "taxable_capital_gain": np.float64(11770.893571428573),
        },
        np.int64(2023): {
            "buy_and_sell_pairs": {
                "GOOG": [
                    (
                        Timestamp("2020-04-15 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        60.0,
                        33.02956666666665,
                    ),
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        40.0,
                        40.77489999999999,
                    ),
                    (
                        Timestamp("2022-06-13 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        60.0,
                        -21.996499999999997,
                    ),
                    (
                        Timestamp("2020-03-23 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        40.0,
                        40.944,
                    ),
                ],
                "META": [
                    (
                        Timestamp("2022-04-06 00:00:00"),
                        Timestamp("2023-02-22 00:00:00"),
                        33.0,
                        -55.33757575757579,
                    )
                ],
                "NCLH": [
                    (
                        Timestamp("2020-03-18 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        295.0,
                        7.593898305084746,
                    )
                ],
                "NVDA": [
                    (
                        Timestamp("2020-11-10 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        280.0,
                        11.254357142857138,
                    )
                ],
                "QQQ": [
                    (
                        Timestamp("2022-06-06 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        50.0,
                        -6.099900000000048,
                    ),
                    (
                        Timestamp("2020-08-05 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        6.0,
                        47.754899999999964,
                    ),
                    (
                        Timestamp("2020-04-15 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        44.0,
                        91.9689909090909,
                    ),
                    (
                        Timestamp("2022-10-11 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        39.0,
                        0.07791666666668107,
                    ),
                    (
                        Timestamp("2022-07-05 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        35.0,
                        10.417726190476174,
                    ),
                    (
                        Timestamp("2022-06-13 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        30.0,
                        20.351249999999936,
                    ),
                    (
                        Timestamp("2020-08-05 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        14.0,
                        47.66458333333327,
                    ),
                    (
                        Timestamp("2020-04-07 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        2.0,
                        97.26870098039211,
                    ),
                ],
                "RCL": [
                    (
                        Timestamp("2020-03-18 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        108.0,
                        59.67805555555556,
                    )
                ],
                "TEAM": [
                    (
                        Timestamp("2020-04-03 00:00:00"),
                        Timestamp("2023-02-21 00:00:00"),
                        33.0,
                        20.671212121212136,
                    )
                ],
            },
            "total_capital_gain": np.float64(23942.533235294115),
            "capital_gain_discount": np.float64(11482.168284313724),
            "losses": np.float64(3450.925000000004),
            "short_sell_gain": 0,
            "taxable_capital_gain": np.float64(9009.439950980384),
        },
        np.int64(2024): {
            "buy_and_sell_pairs": {
                "TQQQ": [
                    (
                        Timestamp("2022-06-13 00:00:00"),
                        Timestamp("2024-01-29 00:00:00"),
                        55.0,
                        48.45238666666666,
                    ),
                    (
                        Timestamp("2022-06-06 00:00:00"),
                        Timestamp("2024-01-29 00:00:00"),
                        200.0,
                        36.76092,
                    ),
                    (
                        Timestamp("2022-04-05 00:00:00"),
                        Timestamp("2024-01-29 00:00:00"),
                        245.0,
                        3.333924081632645,
                    ),
                ]
            },
            "total_capital_gain": np.float64(10833.876666666665),
            "capital_gain_discount": np.float64(5416.938333333333),
            "losses": np.float64(0.0),
            "short_sell_gain": 0,
            "taxable_capital_gain": np.float64(5416.938333333333),
        },
        np.int64(2025): {
            "buy_and_sell_pairs": {
                "AMZN": [
                    (
                        Timestamp("2020-11-09 00:00:00"),
                        Timestamp("2025-06-17 00:00:00"),
                        40.0,
                        106.38550000000001,
                    )
                ],
                "HOOD": [
                    (
                        Timestamp("2021-08-20 00:00:00"),
                        Timestamp("2025-06-17 00:00:00"),
                        80.0,
                        51.786125,
                    )
                ],
                "MSFT": [
                    (
                        Timestamp("2021-09-30 00:00:00"),
                        Timestamp("2025-06-17 00:00:00"),
                        12.0,
                        321.9716666666667,
                    )
                ],
                "PLTR": [
                    (
                        Timestamp("2020-11-09 00:00:00"),
                        Timestamp("2024-12-17 00:00:00"),
                        500.0,
                        95.67854,
                    )
                ],
            },
            "total_capital_gain": np.float64(60101.24),
            "capital_gain_discount": np.float64(30050.62),
            "losses": np.float64(0.0),
            "short_sell_gain": 0,
            "taxable_capital_gain": np.float64(30050.62),
        },
    }

    export_capital_gains_to_excel(sample_data)
