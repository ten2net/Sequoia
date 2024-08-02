
from typing import List
import pandas as pd
from pool.base import StockPool
from favor.favor import StockFavorManagement
from collector.akshare_data_collector import AkshareDataCollector

class AmountStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,cloumn_name:str="amount",k:int=100) -> List[str]:
    """
    获取股票符号列表，默认为按成交额排序的前100只股票
    
    Args:
        cloumn_name (str, optional): 用于排序的列名，默认为'amount'。
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.adc.get_stock_zh_a_spot_em()
    df.sort_values(by=cloumn_name, ascending=False, inplace=True)
    df = df.head(k).copy()
    symbols = df['code'].tolist()
    return symbols  
  
  def get_data_frame(self,cloumn_name:str="amount",k:int=100) -> pd.DataFrame:
    """
    获取股票符号列表，默认为按成交额排序的前100只股票
    
    Args:
        cloumn_name (str, optional): 用于排序的列名，默认为'amount'。
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        pd.DataFrame: 包含股票数据。
    
    """
    df = self.adc.get_stock_zh_a_spot_em()
    df.sort_values(by=cloumn_name, ascending=False, inplace=True)
    return df.head(k).copy()

  
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

class JingJiaRiseStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,k:int=100):
    """
    获取竞价上涨股票列表
    
    Args:
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.adc.get_jingjia_rise_event()
    df.sort_values(by='diff', ascending=False, inplace=True)
    df = df.reset_index(drop=True)
    symbols = df['code'].tolist()
    return symbols   
  
class LargeBuyStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,k:int=100):
    """
    获取大笔买入股票列表
    
    Args:
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df1 = self.adc.get_large_buy_event()
    df2 = self.adc.get_rapit_rise_event()
    df = pd.concat([df1, df2], axis=0, ignore_index=True)
    df.sort_values(by='diff', ascending=False, inplace=True)
    df = df.reset_index(drop=True)    
    symbols = list(set(df['code'].tolist()))
    return symbols   
    
class HotRankStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,k:int=100):
    """
    获取热度排名靠前的股票列表
    
    Args:
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.adc.get_stock_hot_rank()
    df.sort_values(by='rank', ascending=True, inplace=True)
    df = df.head(k).copy()
    symbols = df['code'].tolist()
    return symbols  
     
class HotSymbolStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,k:int=5)->List[str]:
    """
    获取8大热门行业靠前的股票列表
    
    Args:
        k (int, optional): 返回的股票数量，默认为5。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.adc.get_hot_symbols(k)
    if df is not None :
      symbols = df['code'].tolist()
      return symbols   
    else :
      return []  
