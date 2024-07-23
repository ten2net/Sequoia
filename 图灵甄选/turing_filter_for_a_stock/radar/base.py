from abc import ABC, abstractmethod

class StockRadar(ABC):
    @abstractmethod
    def startup(self):
        pass
