from typing import List
import math
import pandas as pd
import pandas_ta as ta
import akshare as ak
from .base import DataCollector
from core.constants import Constants
from datetime import datetime, timedelta
import math


class AkshareDataCollector(DataCollector):
    market_spot:pd.DataFrame=None
    def slope_to_degrees(self, slope):
        return math.degrees(math.atan(slope))

    def __fetch_data__(self, symbol: str, start_date: str = None, end_date: str = None, adjust: str = ""):
        start_date = (datetime.now() - timedelta(days=250)
                      ).strftime('%Y%m%d') if not start_date else start_date
        end_date = datetime.now().strftime('%Y%m%d') if not end_date else end_date
        # 日期    开盘    收盘    最高    最低     成交量           成交额    振幅   涨跌幅   涨跌额   换手率
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol, start_date=start_date, end_date=end_date, adjust='')
        except Exception as e:
            print(f'ak.stock_zh_a_hist调用出错。{e}')

        return df
    def __fetch_stock_changes_em__(self, symbol: str):
        """提取今日异动的股票信息。

        Args:
            event (str, optional): 指定的事件类型，默认为"大笔买入"。支持的时间类型如下：
            '火箭发射', '快速反弹', '大笔买入', '封涨停板', '打开跌停板', '有大买盘', '竞价上涨', 
            '高开5日线', '向上缺口', '60日新高', '60日大幅上涨', '加速下跌', '高台跳水', '大笔卖出', 
            '封跌停板', '打开涨停板', '有大卖盘', '竞价下跌', '低开5日线', '向下缺口', '60日新低', '60日大幅下跌'

        Returns:
            _type_: _description_
        """
        df = ak.stock_changes_em(symbol=symbol)
        return df
    def __fetch_stock_hot_rank_em__(self):
        df = ak.stock_hot_rank_em() #当前排名  代码   股票名称   最新价  涨跌幅
        df=df[["当前排名","代码","股票名称","最新价","涨跌幅"]]
        df.rename(columns={"当前排名":"rank","代码":"code","股票名称":"name","最新价":"price","涨跌幅":"pct"},inplace=True)        
        return df
    def get_stock_hot_rank(self)->pd.DataFrame:
        """
        获取特定事件（如大笔买入）的股票热度排名数据。
        Returns:
            pd.DataFrame: 返回一个pandas DataFrame对象，包含了指定事件的股票热度排名数据。
        """
        df = self.__fetch_stock_hot_rank_em__()        
        df =df[~(df['code'].apply(str).str.startswith('8')) & 
            ~(df['code'].apply(str).str.startswith('4')) &
            ~(df['name'].apply(str).str.startswith('ST')) & 
            ~(df['name'].apply(str).str.startswith('*'))  & 
            ~(df['name'].apply(str).str.startswith('N')) & 
            ~(df['name'].apply(str).str.startswith('C'))       
            ]
        return df
    def get_jingjia_rise_event(self)->pd.DataFrame:
        """
        获取特定事件（如快速反弹）的股票变动数据。        
        Returns:
            pd.DataFrame: 返回一个pandas DataFrame对象，包含了指定事件的股票变动数据。
        """
        df = self.__fetch_stock_changes_em__(symbol="竞价上涨") 
        df=df[["时间","代码","名称","相关信息"]]
        df.rename(columns={"时间":"time","代码":"code","名称":"name","相关信息":"info"},inplace=True)
        df =df[~(df['code'].apply(str).str.startswith('8')) & 
            ~(df['code'].apply(str).str.startswith('4')) &
            ~(df['name'].apply(str).str.startswith('ST')) & 
            ~(df['name'].apply(str).str.startswith('*'))  & 
            ~(df['name'].apply(str).str.startswith('N')) & 
            ~(df['name'].apply(str).str.startswith('C'))       
            ]
        df[['volume','price','diff']] =df['info'].astype(str).str.split(",",expand=True).astype(float)
        df['diff']=df['diff'].astype(float).abs()
        df = df.query('diff > 0.02 and price > 3 ')  
        # df.drop(columns=['volume'], inplace=True)
        return df
    def get_rapit_rise_event(self)->pd.DataFrame:
        """
        获取特定事件（如快速反弹）的股票变动数据。        
        Returns:
            pd.DataFrame: 返回一个pandas DataFrame对象，包含了指定事件的股票变动数据。
        """
        df = self.__fetch_stock_changes_em__(symbol="火箭发射") 
        df=df[["时间","代码","名称","相关信息"]]
        df.rename(columns={"时间":"time","代码":"code","名称":"name","相关信息":"info"},inplace=True)
        df =df[~(df['code'].apply(str).str.startswith('8')) & 
            ~(df['code'].apply(str).str.startswith('4')) &
            ~(df['name'].apply(str).str.startswith('ST')) & 
            ~(df['name'].apply(str).str.startswith('*'))  & 
            ~(df['name'].apply(str).str.startswith('N')) & 
            ~(df['name'].apply(str).str.startswith('C'))       
            ]
        df[['volume','price','diff']] =df['info'].astype(str).str.split(",",expand=True).astype(float)
        df['diff']=df['diff'].astype(float).abs()
        df = df.query('diff > 0.02 and price > 3 ')       
        # df.drop(columns=['volume'], inplace=True)
        return df
    def get_large_buy_event(self)->pd.DataFrame:
        """
        获取特定事件（如大笔买入）的股票变动数据。
        Returns:
            pd.DataFrame: 返回一个pandas DataFrame对象，包含了指定事件的股票变动数据。
        """
        df = self.__fetch_stock_changes_em__(symbol="大笔买入") 
        df=df[["时间","代码","名称","相关信息"]]
        df.rename(columns={"时间":"time","代码":"code","名称":"name","相关信息":"info"},inplace=True)
        df =df[~(df['code'].apply(str).str.startswith('8')) & 
            ~(df['code'].apply(str).str.startswith('4')) &
            ~(df['name'].apply(str).str.startswith('ST')) & 
            ~(df['name'].apply(str).str.startswith('*'))  & 
            ~(df['name'].apply(str).str.startswith('N')) & 
            ~(df['name'].apply(str).str.startswith('C'))       
            ]
        df[['volume','price','diff']] =df['info'].astype(str).str.split(",",expand=True).astype(float)
        df = df.query('diff > 0.02 and (volume / 500000) > 1 and price > 3 ') 
        # df.drop(columns=['volume'], inplace=True)      
        return df
    def get_data(self, symbol: str, start_date: str = None, end_date: str = None, adjust: str = "") -> pd.DataFrame:
        df = self.__fetch_data__(symbol, start_date, end_date)
        df = df.drop(['股票代码'], axis=1)
        df = df.drop(['涨跌额'], axis=1)
        # print(df.columns)
        df.columns = list(Constants.BAR_DAY_COLUMNS)
        df['close_yestday'] = df['close'].shift(1)
        df['pct_yestday'] = df['pct'].shift(1)
        df['volume_yestday'] = df['volume'].shift(1)
        df['amount_yestday'] = df['amount'].shift(1)
        df['turnover_yestday'] = df['turnover'].shift(1)
        df['volume_5_with_today'] = df['volume'].rolling(window=5).mean()
        df['volume_5'] = df['volume_5_with_today'].shift(1)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date', drop=False)
        return df

    def get_data_with_indictores(self, symbol: str, start_date: str = None, end_date: str = None, adjust: str = "") -> pd.DataFrame:
        df = self.get_data(
            symbol=symbol, start_date=start_date, end_date=end_date)

        for length in Constants.TA_INDIECT_LENTHES:
            df[f'slope_{length}'] = ta.slope(open=df.open, high=df.high, low=df.low,
                                             close=df.close, volume=df.volume, length=length)
            df[f'cmf_{length}'] = ta.cmf(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'obv_{length}'] = ta.obv(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'roc_{length}'] = ta.roc(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'sma_{length}'] = ta.sma(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'ema_{length}'] = ta.ema(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'rsi_{length}'] = ta.ema(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=length)
            df[f'cci_{length}'] = ta.cci(open=df.open, high=df.high, low=df.low,
                                         close=df.close, volume=df.volume, length=14)
        df['cci_88'] = ta.cci(open=df.open, high=df.high, low=df.low,
                              close=df.close, volume=df.volume, length=88)
        return df

    def get_stock_zh_a_spot_em(self):
        df = ak.stock_zh_a_spot_em()
        df.drop(columns=['序号'], inplace=True)
        df.drop(columns=['涨跌额'], inplace=True)
        df.drop(columns=['涨速'], inplace=True)
        df.columns = list(Constants.SPOT_EM_COLUMNS)
        return df

    def fetch_intraday_data(self, symbol, start_time, end_time):
        # Akshare may not support intraday data fetching directly
        raise NotImplementedError(
            "Intraday data fetching is not supported by Akshare")
