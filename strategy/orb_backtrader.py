import backtrader as bt
from backtrader.indicators import ATR
import akshare as ak
import pandas as pd


def get_stock_market(stock_code):
    """
    根据A股股票代码判断其所属的市场。

    参数:
    stock_code -- 股票代码，字符串类型

    返回:
    市场名称，若无法识别则返回 "Unknown"
    """
    if stock_code.startswith(('60', '68')):
        return "SH"
    elif stock_code.startswith(('0', '3')):
        return "SZ"
    elif stock_code.startswith(('4', '8')):
        return "BJ"
    else:
        return "Unknown"
# 定义获取沪深A股数据的函数
# def get_stock_data(ticker):
#     df = ak.stock_zh_a_daily(symbol=ticker)
#     return df


def get_stock_data(stock_code):
    venue = get_stock_market(stock_code)
    symbol = f"{venue.lower()}{stock_code}"
    stock_zh_a_minute_df = ak.stock_zh_a_minute(
        symbol=symbol, period='5', adjust='hfq')

    print(symbol, stock_zh_a_minute_df)
    stock_zh_a_minute_df[['open', 'high', 'low', 'close']] = stock_zh_a_minute_df[[
        'open', 'high', 'low', 'close']].round(3)
    return stock_zh_a_minute_df


def get_stock_data_from_local(stock_code):
    data_dir = "/opt/wangf/nautilustrader-research/nautilus_trader/wangf/bars_5_minute_hfq_from_akshare-5547"
    venue = get_stock_market(stock_code)
    symbol = f"{venue}{stock_code}"
    df = pd.read_csv(f"{data_dir}/{symbol}.csv")
    mask=(df['day'] >= '2024-03-18')
    df = df.loc[mask]
    df[['open', 'high', 'low', 'close']] = df[[
        'open', 'high', 'low', 'close']].round(3)
    # df.rename(columns={'day': 'date'}, inplace=True)
    df['ts_code'] = symbol
    df['openinterest'] = 0
    # df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'openinterest']]
    # df.sort_values(by='date', ascending=True, inplace=True)  # 逆序排序
    df['day'] = pd.to_datetime(df['day'])
    df.set_index('day', inplace=True)
    # df = df.drop(['day'], axis=1)
    return df

# 定义ORB策略

class FiveMinStockDataFeed(bt.feeds.PandasData):
    def __init__(self, dataname, **kwargs):
        # 调用父类构造函数，并传递数据源
        super(FiveMinStockDataFeed, self).__init__(dataname, **kwargs)
        
class ORBStrategy(bt.Strategy):
    # 定义参数
    params = (
        ('atr_length', 14),  # ATR周期
        ('stop_loss_factor', 1.5),  # 止损因子
    )  
    def __init__(self):
        # self.dataclose = self.datas[0].close
        # print(self.datas[0])
        self.atr = bt.indicators.ATR(period=self.params.atr_length)
        print("----",self.atr)
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        dt = dt or self.datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def next(self):
        # 检查是否在交易时间
        if self.datetime.time().hour == 9 and self.datetime.time().minute < 35:
            return

        # 计算ATR
        atr = self.atr # self.atr(self.data, period=self.params.atr_length)[0]
        # print("self.data", self.data)
        # 定义开盘区间
        open_range_high = self.data.high[0]
        open_range_low = self.data.low[0]
        # print("OR:",(open_range_low,open_range_high))
        # 检查是否突破开盘区间
        print("CH:",(self.data.close[0] , open_range_high))
        if self.data.close[0] > open_range_high:
            print("突破开盘")
            self.buy(size=100)  # 买入100股
            self.stop_loss = self.data.close[0] - atr * self.p.stop_loss_factor  # 计算止损
        elif self.data.close[0] < open_range_low:
            self.sell(size=100)  # 卖出100股
            self.stop_loss = self.data.close[0] + atr * self.p.stop_loss_factor

        # 检查止损
        if self.position.size > 0 and self.data.close[0] <= self.stop_loss:
            self.sell(size=self.position.size)  # 止损卖出
            self.stop_loss = None

    # 计算ATR
    # @bt.indicator
    def atr(self, dataseries, period):
        high = dataseries.high
        low = dataseries.low
        close = dataseries.close
        # close = dataseries.close.shift(1)
        diff = bt.indicator.Max(high, period) - bt.indicator.Min(low, period)
        diff2 = bt.indicator.Max(high, period) - close
        diff3 = bt.indicator.Max(close, period) - low
        true_range = bt.indicator.Max([diff, diff2, diff3], period)
        return true_range.mean(period)


def main():
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 获取股票数据
    ticker = '600519'  # 以贵州茅台为例
    df = get_stock_data_from_local(ticker)
    print(df)
    fromdate = '2024-03-18'
    enddate = '2024-05-20'
    
    # data = FiveMinStockDataFeed(dataname = df, timeframe=bt.TimeFrame.Minutes(5))
    # data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=enddate)
    # data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=enddate)
    data = bt.feeds.PandasData(dataname=df, datetime=None,
                           open=0, high=1, low=2, close=3, volume=4, openinterest=-1)    

    # 添加数据到Cerebro
    cerebro.adddata(data)

    # 添加ORB策略
    cerebro.addstrategy(ORBStrategy)

    # 设定初始资金
    cerebro.broker.setcash(100000)

    # 设定交易佣金
    cerebro.broker.setcommission(commission=0.002)

    # 运行回测
    cerebro.run()

    # 打印结果
    print(f'最终净值: {cerebro.broker.getvalue():,.2f}')


if __name__ == '__main__':
    main()
