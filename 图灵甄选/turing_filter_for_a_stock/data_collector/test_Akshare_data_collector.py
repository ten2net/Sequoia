

import unittest
from unittest.mock import patch
from .akshare_data_collector import AkshareDataCollector

class TestAkshareDataCollector(unittest.TestCase):
    def setUp(self):
        self.collector = AkshareDataCollector()

    @patch('akshare.stock_zh_a_daily')
    def test_fetch_data(self, mock_fetch_data):
        # Arrange
        mock_data = {'symbol': '000001', 'data': 'mocked data'}
        mock_fetch_data.return_value = mock_data
        
        symbol = '000001'
        start_date = '2024-01-01'
        end_date = '2024-07-19'

        # Act
        result = self.collector.fetch_data(symbol, start_date, end_date)

        # Assert
        self.assertEqual(result, mock_data)
        mock_fetch_data.assert_called_once_with(symbol=symbol, start_date=start_date, end_date=end_date)

    def test_fetch_intraday_data(self):
        # Arrange
        symbol = '000001.SZ'
        start_time = '09:30'
        end_time = '15:00'

        # Act & Assert
        with self.assertRaises(NotImplementedError) as context:
            self.collector.fetch_intraday_data(symbol, start_time, end_time)

        self.assertTrue('Intraday data fetching is not supported by Akshare' in str(context.exception))

if __name__ == '__main__':
    unittest.main()