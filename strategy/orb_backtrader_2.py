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
    mask = (df['day'] >= '2024-03-18')
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


class ORBStrategy(bt.Strategy):
    params = (
        ('atr_length', 14),  # ATR周期
        ('risk_per_trade', 1),  # 每笔交易的风险比例
    )

    def __init__(self):  
        # self.position = None  # 初始化仓位     
        self.atr = bt.indicators.ATR(period=self.params.atr_length)  # 初始化ATR指标

    def log(self, txt, dt=None):
        dt = dt or self.datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order:bt.order.BuyOrder):
        # print(type(order))
        
        # print([order.Submitted, 
        #        order.Accepted,
        #        order.Expired,
        #        order.Margin,
        #        order.Rejected,
        #        ])
        
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return

        # 检查一个交易是否完成。
        # 如果钱不够，交易会被拒绝。
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '执行买入, 价格: %.2f, 成本: %.2f, 手续费 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(
                    '执行卖出, 价格: %.2f, 成本: %.2f, 手续费 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(order.status)
            self.log('交易取消/被拒绝。')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('操作收益%.2f, 成本%.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.datetime.time().hour == 9 and self.datetime.time().minute < 35:
            return

        # print(self.datetime.date(),self.datetime.time(),self.data.open[0],self.data.high[0],self.data.low[0],self.data.close[0])
        # 计算止损价格
        stop_price = self.data.close - self.atr * self.params.risk_per_trade

        # self.log('持仓 %.2f' % self.position.size)
        # 检查是否已有头寸
        if self.position.size > 0:
            # 如果价格触及止损，关闭头寸
            if self.data.close <= stop_price:
                self.close()

        # 定义开盘区间高点和低点
        open_range_high = self.data.high[-1]
        open_range_low = self.data.low[-1]
        
        
        # 检查买入信号
        if self.position.size == 0 and self.data.close > open_range_high:
            # print((self.data.close[0] , open_range_high))
            self.buy(size=100)  # 买入逻辑
            self.last_trade_date = self.datetime.date()  # 更新最后交易日期
            # self.stop = stop_price  # 设置止损价格

        # 检查卖出信号
        elif self.position.size > 0 and self.data.close < open_range_low:
            if self.datetime.date() > self.last_trade_date:
                self.sell(size=100)  # 卖出逻辑
                self.last_trade_date = None  # 重置最后交易日期
                # self.stop = stop_price  # 设置止损价格


def main():
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 获取股票数据
    ticker = '000001'  # 以贵州茅台为例

    df = get_stock_data_from_local(ticker)
    # print(df)
    fromdate = '2024-03-18'
    enddate = '2024-05-20'

    # data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=enddate)
    # data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=enddate)
    data = bt.feeds.PandasData(dataname=df, datetime=None,
                               open=0, high=1, low=2, close=3, volume=4, openinterest=-1)

    # 添加数据到Cerebro
    cerebro.adddata(data)

    # 添加ORB策略
    cerebro.addstrategy(ORBStrategy)

    # 设定初始资金
    cerebro.broker.setcash(1000000000)

    # 设定交易佣金
    cerebro.broker.setcommission(commission=0.002)

    # 运行回测
    cerebro.run()

    # 打印结果
    # print(f'最终净值: {cerebro.broker.getvalue():,.2f}')
    
    
    cash = cerebro.broker.get_cash()
    print(f'现金余额: {cash}')    
    
    print(f'最终净值: {cerebro.broker.getvalue():,.2f}')
    
    # docker run -d -p 18501:8501 -p 18080:8080 -it --name quantlab registry.cn-shenzhen.aliyuncs.com/quantlab/quantlab:4.2.1
    
    positions = cerebro.broker.positions
    
    for p in positions:
        print(p,p[0],p[-1])

    # for data, position in positions.items():
    #     print(f'股票代码: {data._name}, 持仓量: {position.size}, 平均买入价格: {position.price}, 预留市值: {position.value()}')

if __name__ == '__main__':
    main()
