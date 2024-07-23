from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from tqdm import tqdm

class StockRadar(ABC):
    @abstractmethod
    def startup(self):
        pass
