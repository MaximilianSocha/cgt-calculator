# CGT Calculator

## Overview

This Capital Gains Tax (CGT) Calculator helps you accurately calculate your minimum tax obligations from investing in assets like stocks or crypto. Simply upload your transaction data and receive a comprehensive breakdown of your capital gains, losses, and tax discounts for each financial year.

The calculator uses a linear solver which attempts to optimally determine buy-sell pairs minimize your capital gains tax liability, potentially saving you hundreds of dollars in taxes.

## How to Use

1. **Prepare Your Trade History**
   - Download your complete trade history from your broker (NabTrade, CommSec, or any other service)
   - Ensure the date range includes **all** trades you have ever executed
   - The file should be in CSV or Excel (.xlsx) format

2. **Upload Your File**
   - Import your trade history file using the upload button on the website
   - The calculator will automatically process your transactions and optimize your capital gains tax

3. **Complete Payment**
   - After successful calculation, you'll be directed to a secure payment portal ($19.99 AUD)
   - Upon payment completion, an Excel file will be downloaded containing your optimized CGT results

4. **Review Your Results**
   - The Excel file contains separate sheets for each financial year you traded
   - At the bottom of each sheet, you'll find:
     - **Total Capital Gain**: Your total gains for the year
     - **Loss**: Your total losses for the year
     - **Capital Gains Discount**: Your eligible tax discount
     - **Taxable Capital Gain**: The final amount subject to tax
   - These are the exact fields needed for your tax return

## Supported Brokers

### NabTrade
- Go to "Statements and Reports" → "Transaction report"
- Select the full date range of all your trading history
- Export as Excel and save as a `.xlsx` file

### CommSec
- Navigate to "Accounts" → "Transactions"
- Select the full date range covering all trades
- Download as CSV
- Multiple accounts can be combined into a single CSV file

### Other Brokers
For other trading platforms, create a file with the following format:

| transaction_date | symbol | transaction_type | quantity | transaction_amount |
|-----------------|--------|------------------|----------|-------------------|
| DD/MM/YYYY      | AAPL   | BUY             | 100      | 15000.00          |
| DD/MM/YYYY      | AAPL   | SELL            | 50       | 8500.00           |

**Important Notes:**
- Column names must match exactly as shown
- `transaction_amount` should **include** any trading fees
- Dates should be in DD/MM/YYYY format
- Save as `.csv` or `.xlsx` file

## Tax Filing

Once you receive your results:

1. Use the totals at the bottom of each year's sheet to fill out your tax return
2. If you've overpaid CGT in previous years, add the overpaid amount to "Unapplied Net Capital Losses Carried Forward"
3. If your losses exceed your gains, also report this in the "Unapplied Net Capital Losses Carried Forward" section

## Limitations

While this calculator is designed to provide accurate and optimal capital gains tax calculations, users should be aware of the following limitations:

### Ticker Symbol Changes
- The calculator maintains a comprehensive but **not exhaustive** history of ticker symbol changes
- Some historical ticker changes may not be included in the database
- Users may need to manually update ticker symbols in their trade history if a change is not recognized

### Delisted Companies
- If a company has been delisted, historical information about stock splits or ticker changes during its active period may no longer be available
- This can affect the accuracy of calculations for trades involving delisted securities

### Cross-Exchange Ticker Overlap
- Ticker symbols can overlap across different stock exchanges (e.g., the same ticker might exist on both ASX and NYSE)
- If you have obtained stock with the same ticker symbol from different exchanges, the calculator may return inaccurate results
- Users should verify their results if they trade across multiple exchanges with overlapping tickers

### Short Selling Detection
- The calculator may flag potential short selling when stock is awarded without an explicit buy transaction
- Users should review any short selling warnings to ensure they are legitimate and not caused by missed symbol changes or stock splits

## Disclaimer

This tool is provided for informational purposes only. Users must evaluate the output themselves and verify its accuracy before making any financial decisions or filing tax returns based on its results. It is recommended to consult with a qualified tax professional for specific advice regarding your tax obligations.

---

**© 2025 CGT Calculator** - Optimizing your capital gains tax, one trade at a time.