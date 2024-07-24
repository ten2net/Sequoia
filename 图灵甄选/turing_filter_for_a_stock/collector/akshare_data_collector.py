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

    def get_data(self, symbol: str, start_date: str = None, end_date: str = None, adjust: str = "") -> pd.DataFrame:
        df = self.__fetch_data__(symbol, start_date, end_date)
        df = df.drop(['涨跌额'], axis=1)
        df.columns = list(Constants.BAR_DAY_COLUMNS)
        df['close_yestday'] = df['close'].shift(1)
        df['pct_yestday'] = df['pct'].shift(1)
        df['volume_yestday'] = df['volume'].shift(1)
        df['amount_yestday'] = df['amount'].shift(1)
        df['turnover_yestday'] = df['turnover'].shift(1)
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
        df['volume_5'] = df['volume'].rolling(window=5).mean()
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
