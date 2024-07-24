
from typing import List
from pool.base import StockPool
from favor.favor import StockFavorManagement
from collector.akshare_data_collector import AkshareDataCollector

class AmountStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,cloumn_name:str="amount",k:int=100):
    """
    获取股票符号列表，默认为按成交额排序的前100只股票
    
    Args:
        cloumn_name (str, optional): 用于排序的列名，默认为'amount'。
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.adc.get_stock_zh_a_spot_em()
    df.sort_values(by='amount', ascending=False, inplace=True)
    df = df.head(k).copy()
    symbols = df['code'].tolist()
    return symbols  

  
class FavorStockPool(StockPool):
  def __init__(self,groups:List[str]):
    self.groups = groups
    self.adc = AkshareDataCollector()
    self.sfm = StockFavorManagement()
  
  def get_symbols(self):
    """
    从所有分组中获取符号列表，并去重。
    
    Args:
        无参数。
    
    Returns:
        list: 包含去重后的符号的列表。
    
    """
    symbols=[]
    for group in self.groups:
      symbols += self.sfm.get_symbols(group_name=group)
    symbols = list(set(symbols))  
    # df[df['symbol'].isin(symbols)]    
    return symbols

    
