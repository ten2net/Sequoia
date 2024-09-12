
from typing import List
import pandas as pd
from pool.base import StockPool

from collector.akshare_data_collector import AkshareDataCollector
from user.user import User
from user.user_management import UserManagement

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
  
class ATPStockPool(StockPool):
  def __init__(self,k:int=100):
    self.adc = AkshareDataCollector()
    self.k = k
  def get_symbols(self) -> List[str]:
    """
    获取股票符号列表，默认为按成交额、换手率、涨跌幅综合排序的前K只股票
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    df = self.get_topN()
    symbols = df['code'].tolist()
    return symbols  
  def get_topN(self) -> pd.DataFrame:
    """
    获取股票符号列表，默认为按成交额、换手率、涨跌幅综合排序的前K只股票
    
    Returns:
        pd.DataFrame: 包含股票数据。
    
    """
    k= self.k
    stock_df = self.adc.get_stock_zh_a_spot_em()    
    stock_df['amount_rank'] = stock_df['amount'].rank(method='dense',ascending=False)
    stock_df['turnover_rank'] = stock_df['turnover'].rank(method='dense',ascending=False)
    stock_df['pct_rank'] = stock_df['pct'].rank(method='dense',ascending=False) 
    stock_df = stock_df[
        (stock_df['amount_rank'] <= k) &
        (stock_df['turnover_rank'] <= k) &
        (stock_df['pct_rank'] <= k)
    ]  
    # 定义权重
    w1 = 1.3  # amount_rank 的权重
    w2 = 1.2  # turnover_rank 的权重
    w3 = 0.5  # pct_rank 的权重
    stock_df['score'] = 3 * k - (w1 * stock_df['amount_rank'] + w2 * stock_df['turnover_rank'] + w3 * stock_df['pct_rank'])
    # print(stock_df.columns)
    stock_df = stock_df.sort_values(by="score",ascending=False)        
    stock_df.reset_index(drop=True)                
    stock_df=stock_df.head(k)    
    return stock_df.head(k)

class TurnoverStockPool(StockPool):
  def __init__(self):
    self.adc = AkshareDataCollector()
  def get_symbols(self,k:int=100) -> List[str]:
    """
    获取股票符号列表，默认为按成交额排序的前100只股票
    
    Args:
        cloumn_name (str, optional): 用于排序的列名，默认为'amount'。
        k (int, optional): 返回的股票数量，默认为100。
    
    Returns:
        list: 包含股票符号的列表。
    
    """
    cloumn_name:str="turnover"
    df = self.adc.get_stock_zh_a_spot_em()
    df.sort_values(by=cloumn_name, ascending=False, inplace=True)
    df = df.head(k).copy()
    symbols = df['code'].tolist()
    return symbols  
  
class FavorStockPool(StockPool):
  def __init__(self,groups:List[str],user:User=None):
    self.groups = groups
    if user is None:
      um = UserManagement()
      users = um.get_users()
      self.user = users[0]
    else:
      self.user = user
  
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
      symbols += self.user.favor.get_symbols(group_name=group)
    symbols = list(set(symbols))      
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
    symbols=[symbol[2:] for symbol in symbols ] 
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
