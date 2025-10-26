import xlsxwriter


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
            ("Capital Gains Discount", fy_data.get("capital_gain_discount", 0)),
            ("Net Capital Gain", fy_data.get("taxable_capital_gain", 0)),
        ]

        for label, value in summary_items:
            worksheet.write(current_row, 0, label, summary_label_format)
            worksheet.merge_range(
                current_row, 1, current_row, 3, value, summary_value_format
            )
            current_row += 1

    workbook.close()
    print(f"Excel file '{filename}' created successfully!")
