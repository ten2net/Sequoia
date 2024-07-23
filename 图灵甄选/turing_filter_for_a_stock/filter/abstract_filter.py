from abc import ABC, abstractmethod

class StockFilter(ABC):
    @abstractmethod
    def filter(self, df):
        pass
