from cgt_calculator import CGTCalculator
from test.test_helpers import mock_handle_splits_and_ticker_changes

class MockCGTCalculator(CGTCalculator):

    def __init__(self, trade_history_csv_path):

        # Initialise the trades data frame
        self.trades_df = self._parse_trade_history_file(trade_history_csv_path)
        self._initialise_trades_df()
        mock_handle_splits_and_ticker_changes(self.trades_df)