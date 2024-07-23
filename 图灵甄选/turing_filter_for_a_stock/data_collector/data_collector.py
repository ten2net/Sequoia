from abc import ABC, abstractmethod

class DataCollector(ABC):
    @abstractmethod
    def get_data(self, symbol, start_date, end_date):
        """
        Fetch data from the source.
        :param symbol: The symbol of the stock.
        :param start_date: The start date for fetching data.
        :param end_date: The end date for fetching data.
        :return: Data fetched from the source.
        """
        pass

    @abstractmethod
    def fetch_intraday_data(self, symbol, start_time, end_time):
        """
        Fetch intraday data from the source.
        :param symbol: The symbol of the stock.
        :param start_time: The start time for fetching intraday data.
        :param end_time: The end time for fetching intraday data.
        :return: Intraday data fetched from the source.
        """
        pass