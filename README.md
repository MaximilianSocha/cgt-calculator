# Overview

This is a tool designed to calculate the minimum capital gains tax a person can pay in Australia.
It is not intended to handle capital gains from real estate or physical asset, but gains made from trading/investing in stocks and ETFs.
The final product is intended to be a webpage where a user inputs a `.csv` file with all their trade history and they recieve a `.xlsx` file with a summary of their taxable capital gain.

# Input

# Handling stock splits, ticker changes, short selling, and delisted stocks/ETFs

# LP Solver

# Output


# NOTES
Unapplied Net Capital Losses Caried Forward:
From previous years if too much tax was paid it would go here
This is also used when the calculated net capital gain for a financial year is negative.

CGT exemption, rollover or additional discount:
Not applicable for this program as it is only working off of trade orders from brokerage website.
There will be no info on company splits, mergers, or demergers.

Remembers this all applies for CGT events after September 21, 1999

Stocks which went bankrupt and lost all value can be added to losses (this could be added to the script)
Check if company has been delisted and add warning about this to the user.
Add info about this in the instructions, no need to calculate it because very simple
for the user to add but hard for the program to do. Just inform the user about it.

After calculating dialog will either say:
- Failed to calculate because of incorrectly formatted input, refer to instructions
- Failed to calculate for symbol: ... , refer to instructions
- Success! You're total capital gains for this FY are:
    - (If applicable, highlighted yellow) Short selling detected on symbols: ...
      Refer to short selling in instructions for info.
    - (If applicable, highlighted yellow) Companies under following symbols delisted: ...
      Refer to deslited companies in instructions for info.
    - Continue to results?