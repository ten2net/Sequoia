import argparse
import os
from typing import Tuple, Union
import akshare as ak
import concurrent.futures
from dotenv import load_dotenv
import schedule
import time
import pandas as pd
from threading import local, Lock

from collector.akshare_data_collector import AkshareDataCollector
from core.constants import Constants
from core.topic import TradeSignalTopic
from filter.filter_chain import FilterChain
from filter.fund.fund_filter import NameFilter, SymbolFilter, TotalCapitalFilter
from notification.wecom import WeCom, WeComNotification
from pool.pool import AmountStockPool, FavorStockPool, HotSymbolStockPool
from strategy.fib import FibonacciRetracement, FibonacciTradingSignal, VWAPCalculator
from trader.base import OrderMessage
from trader.trader_management import SimTraderManagement
from user.user_management import UserManagement
from termcolor import colored
from pubsub import pub
from datetime import datetime, timedelta


# 定义股票池
stock_pool = ["000001", "000002", "300031"]  # 替换为实际的股票代码列表
stock_pool = ["600686"]  # 替换为实际的股票代码列表
# stock_pool = ["001379"]  # 替换为实际的股票代码列表
stock_pool = ["002829"]  # 替换为实际的股票代码列表
# stock_pool = ["603336"]  # 替换为实际的股票代码列表
# stock_pool = ["600817"]  # 替换为实际的股票代码列表
# stock_pool = ["600326"]  # 替换为实际的股票代码列表
# stock_pool = ["001379","300494"]  # 替换为实际的股票代码列表
stock_pool = ["00200"]  # 替换为实际的股票代码列表
stock_pool = ["002370"]  # 替换为实际的股票代码列表
stock_pool = ["300410"]  # 替换为实际的股票代码列表

# 使用 threading.local 来创建线程局部变量
thread_data = local()

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
      
def get_stock_data(stock_code,daily=False):
    stock_df = None
    if daily==False:
        dt=datetime.now()
        if dt.hour < 9 or (dt.hour == 9 and dt.minute < 25 ):
           dt = datetime.now() - timedelta(days=1)
        today=dt.strftime("%Y-%m-%d")
        stock_df =  ak.stock_zh_a_hist_min_em(symbol=stock_code, period="1",  start_date=f"{today} 09:25:00", adjust="")
        #stock_df =  ak.stock_zh_a_hist_pre_min_em(symbol=stock_code, start_time="09:25:00")
        # print(stock_df.columns)
        stock_df.rename(
            columns={"时间":"time","开盘":"open","最高":"high","最低":"low","收盘":"close","成交量":"volume","成交额":"amount"},inplace=True)    
    else:
        start_date = datetime.now() - timedelta(days=60)
        start_date = start_date.strftime("%Y%m%d")
        stock_df =  ak.stock_zh_a_hist(symbol=stock_code, period="daily",  start_date=start_date, adjust="")
        stock_df.rename(
            columns={"日期":"time","开盘":"open","最高":"high","最低":"low","收盘":"close","成交量":"volume","成交额":"amount"},inplace=True)
    stock_df['open'] = stock_df['open'].astype(float)
    stock_df['high'] = stock_df['high'].astype(float)
    stock_df['low'] = stock_df['low'].astype(float)
    stock_df['close'] = stock_df['close'].astype(float)
    stock_df['volume'] = stock_df['volume'].astype(int)
    stock_df=stock_df[stock_df['volume']> 0]
    return stock_df  
def get_stock_high_and_low(stock_code,date:str,length:int=10) -> Tuple[float,float]:
    start_date = datetime.strptime(date, "%Y%m%d") - timedelta(days=length)
    start_date = start_date.strftime("%Y%m%d")
    stock_df =  ak.stock_zh_a_hist(symbol=stock_code, period="daily",  start_date=start_date, end_date=date, adjust="")
    stock_df.rename(
        columns={"日期":"time","开盘":"open","最高":"high","最低":"low","收盘":"close","成交量":"volume","成交额":"amount"},inplace=True)
    stock_df['open'] = stock_df['open'].astype(float)
    stock_df['high'] = stock_df['high'].astype(float)
    stock_df['low'] = stock_df['low'].astype(float)
    stock_df['close'] = stock_df['close'].astype(float)
    stock_df['volume'] = stock_df['volume'].astype(int)
    return stock_df['high'].max(),stock_df['low'].min()

def generate_data_chunks(df, period=2):
    import time
    index = 0
    while index < len(df):
        yield df.head(index+1)
        time.sleep(period)
        index += 1    

def compute_market_sentiment_index() -> float:
    stockPool = AmountStockPool()
    df =stockPool.get_data_frame(cloumn_name="amount", k=300)       

    # 定义涨跌幅区间和权重
    bins = [-float('inf'), -0.1, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.1, float('inf')]
    weights = [-16, -8, -4, -2, -1, 1, 2, 4, 8, 16]

    df['segment'] = pd.cut(df['pct'] / 100, bins=bins, labels=weights, right=True)

    df['weighted_amount'] = df['amount'] * df['segment'].astype(float)
    # 计算实际加权因子
    actual_weighted_factor = df['weighted_amount'].sum()
  
    # 计算最大可能的加权因子
    max_weighted_factor = df['amount'].sum() * max(weights)

    # 计算强弱指数
    strength_index = round(actual_weighted_factor / max_weighted_factor,3)
    return strength_index

def draw(df_signal,symbol,name):
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    import numpy as np
   
    df=df_signal.copy()
    # print(df.columns)
    df["time"] =pd.to_datetime(df["time"])
    df.set_index('time', inplace=True)

    buy_signals = df[df['signal'] == "B"]
    sell_signals = df[df['signal'] == "S"] 
    # fig = plt.figure(figsize=(16, 12))
    df['R1W'] = df['R1'].rolling(window=5).mean()
    df['S1W'] = df['S1'].rolling(window=5).mean()           
    apds = [
        mpf.make_addplot(df['R1W'], color='blue', linestyle='-',width=0.4, label='R1'),
        mpf.make_addplot(df['S1W'], color='red', linestyle='-',width=0.4, label='S1')
        ]
    # 初始化买卖信号的序列
    buy_signal_plot = pd.Series(index=df.index, data=np.nan)
    sell_signal_plot = pd.Series(index=df.index, data=np.nan)

    # 将买卖信号的价格填充到相应的位置
    buy_signal_plot[df['signal'] == "B"] = df[df['signal'] == "B"]['close']
    sell_signal_plot[df['signal'] == "S"] = df[df['signal'] == "S"]['close']
    # 为买入信号添加散点图
    if not buy_signals.empty:
        apds.append(mpf.make_addplot(buy_signal_plot, type='scatter', markersize=60, marker='^', color='red', label='Buy'))
    # 为卖出信号添加散点图
    if not sell_signals.empty:
        apds.append(mpf.make_addplot(sell_signal_plot, type='scatter', markersize=60, marker='v', color='green', label='Sell'))

    try:
        # 自定义市场颜色，上涨为红色，下跌为绿色
        market_colors = mpf.make_marketcolors(up='r', down='g', edge='i', wick='i', volume='i')
        custom_style = mpf.make_mpf_style(marketcolors=market_colors)

        mpf.plot(df, type='candle', style=custom_style, addplot=apds, volume=True, figsize=(12, 6), title='{} {}'.format(symbol, name))
        if not buy_signals.empty or not sell_signals.empty:
            save_path = "{}_{}.png".format(symbol, name)
            plt.savefig(save_path)
            time.sleep(0.5)
            plt.close()
            print(f"Chart saved as {save_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        plt.close()
    
# 定义处理单只股票的函数
def process_stock_data(stock):
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true',
                        help='Set dev mode to true')
    parser.add_argument('--daily', action='store_true',
                        help='Set k line is daily true')
    args = parser.parse_args()  
    stock_symbol=stock["code"]
    stock_name=stock["name"]
    global thread_data
    global ganzhou_index
    thread_data.high = {}
    thread_data.low = {}
    thread_data.vwap_calculator = {}
    thread_data.fibonacciTradingSignal = {}
    thread_data.short_ma = {}
    thread_data.long_ma = {}    
    # 初始化股票特定的变量
    if stock_symbol not in thread_data.high:
        # with Lock():
          thread_data.high[stock_symbol] = float('-inf')
          thread_data.low[stock_symbol] = float('inf')
          thread_data.vwap_calculator[stock_symbol] = VWAPCalculator()
        #   thread_data.fibonacciTradingSignal[stock_symbol] = FibonacciTradingSignal(float('-inf'),float('-inf'))
          thread_data.short_ma[stock_symbol] = 0
          thread_data.long_ma[stock_symbol] = 0
    try:
        # 获取股票的分时数据
        all_data = get_stock_data(stock_symbol,args.daily)
        all_data['signal'] = ""
        all_data['R1']=0.0
        all_data['S1']=0.0
        # generator = generate_data_chunks(all_data, period=0.2)
        generator = generate_data_chunks(all_data, period=0.1)
        stock_tick_df=None
        while stock_tick_df is None or len(stock_tick_df) < len(all_data): 
          if args.dev:                     
            stock_tick_df = next(generator)
          else:
            stock_tick_df = all_data
          stock_tick_df=stock_tick_df.copy()
          # 更新最高价和最低价
        #   high = stock_tick_df['high'].max()
        #   low = stock_tick_df['low'].min()  
          dt = stock_tick_df.iloc[-1]['time'] if args.daily else datetime.strptime(stock_tick_df.iloc[-1]['time'], "%Y-%m-%d %H:%M:%S") 
          dt = dt.strftime("%Y%m%d")
          high,low = get_stock_high_and_low(stock_symbol,dt,length=1)           
       
        #   print(stock_name,stock_tick_df.iloc[-1]["time"],stock_tick_df.iloc[-1]["close"],high,low)
          volume = stock_tick_df['volume'].sum()        
          amount = stock_tick_df['amount'].sum()        
          thread_data.high[stock_symbol] = high
          thread_data.low[stock_symbol] = low
          thread_data.fibonacciTradingSignal[stock_symbol] = FibonacciTradingSignal(high=thread_data.high[stock_symbol],low=thread_data.low[stock_symbol])
          # 计算移动平均
          stock_tick_df['short_ma'] = round(stock_tick_df['close'].rolling(window=5).mean(),2)
          stock_tick_df['long_ma'] = round(stock_tick_df['close'].rolling(window=20).mean(),2)
          short_ma = stock_tick_df.iloc[-1]['short_ma']
          long_ma = stock_tick_df.iloc[-1]['long_ma']
          thread_data.short_ma[stock_symbol] = short_ma
          thread_data.long_ma[stock_symbol] = long_ma
          latest_data = stock_tick_df.iloc[-1].to_dict()
          # 更新VWAP
          thread_data.vwap_calculator[stock_symbol].update(latest_data['close'], latest_data['volume'])
          vwap = thread_data.vwap_calculator[stock_symbol].calculate()
          
          if not args.dev: 
            for index, row in stock_tick_df.iterrows():
                signal,resistances, supports = thread_data.fibonacciTradingSignal[stock_symbol].generate_signal(currentPrice = row['close'],threshold=0.02)
                all_data.loc[index,'R1']= resistances[0]   
                all_data.loc[index,'S1']= supports[0]
          
          # # 生成斐波那契回撤信号并用VWAP加强
          try:
            signal,resistances, supports = thread_data.fibonacciTradingSignal[stock_symbol].generate_signal(currentPrice = latest_data['close'],threshold=0.02)
          except Exception as e:
              continue
          if signal == 'buy' and latest_data['close'] < vwap:
              strong_signal = 'strong_buy'
          elif signal == 'sell' and latest_data['close'] > vwap:
              strong_signal = 'strong_sell'
          else:
              strong_signal = 'hold'
        #   print(thread_data.fibonacciTradingSignal[stock_symbol].fib_levels)
        #   print(stock_name,high,low,latest_data['close'], signal,resistances, supports,strong_signal)

          # 使用均线交叉进一步处理信号
          ma_cross_up = short_ma > long_ma  # and latest_data['close'] > short_ma
          ma_cross_down = short_ma <= long_ma # and latest_data['close'] < short_ma
          if ma_cross_up and strong_signal == 'strong_buy':
              final_signal = 'strong_buy'
          elif ma_cross_down and strong_signal == 'strong_sell':
              final_signal = 'strong_sell'
          else:
              final_signal = 'hold'
          latest_data['vwap'] = vwap
          latest_data['signal'] = signal
          latest_data['strong_signal'] = strong_signal
          latest_data['final_signal'] = final_signal 
          
          ind=stock_tick_df.index[-1]
        #   print(ind, stock_name,latest_data['close'],high,low, resistances, supports,signal,strong_signal,final_signal)
          all_data.loc[ind,'R1']= resistances[0]   
          all_data.loc[ind,'S1']= supports[0] 
        #   all_data.loc[ind,'R1']=resistances[1] if len(resistances)>1 else resistances[0]   
        #   all_data.loc[ind,'S1']=supports[1] if len(supports)>1 else supports[0]   

        #   if latest_data['final_signal'] != 'hold':
          latest_data['final_signal'] = strong_signal
          if latest_data['final_signal'] != 'hold':
            strategyName = "大笔买入"            
            # date_object = datetime.strptime(latest_data['time'], "%Y-%m-%d %H:%M:%S")
            date_object = latest_data['time'] if args.daily else datetime.strptime(latest_data['time'], "%Y-%m-%d %H:%M:%S")
            pct =round(100* (latest_data['close'] - stock["close_yesterday"]) /stock["close_yesterday"] ,2)
            turnover =round(100 * volume / (stock["circulating_capital"] / stock["close"]) ,2)
            print(f"{date_object.strftime('%H:%M')} 情绪指数:{ganzhou_index} ☞ {latest_data['final_signal']} {stock_symbol} {stock_name} {latest_data['close']}")
            traderMessage = {**stock,
                            "strategyName":strategyName, 
                            "resistances":"  ".join(map(str,resistances)),
                            "supports":"  ".join(map(str,supports)),
                            "close":latest_data['close'],
                            "high":high,
                            "low":low,
                            "pct":pct,
                            "turnover":turnover,
                            "amount":amount,
                            "price":latest_data['close'],
                            "index":ganzhou_index,
                            "date":date_object.strftime("%Y-%m-%d"),
                            "time":date_object.strftime("%H:%M")                            
                            }

            if latest_data['final_signal'] == "strong_buy":
              all_data.loc[ind,'signal']='B'
              traderMessage["price"] = round(supports[0] + 0.01,2)  # 在第一支撑位之上挂单
              pub.sendMessage(str(TradeSignalTopic.BUY), message=traderMessage)  
            elif latest_data['final_signal'] == "strong_sell":
              all_data.loc[ind,'signal']='S'
              traderMessage["price"] = round(resistances[0] - 0.01,2) # 在第一阻力位位之下挂单
              pub.sendMessage(str(TradeSignalTopic.SELL),message=traderMessage)          
          else:
            pass
        # print(f"{stock_name}",all_data[["time","close","R1","S1","signal"]].head(50))
        if (all_data['signal'] == "B").any() or (all_data['signal'] == "S").any():
            draw(all_data, stock_symbol, stock_name)
    except Exception as e:
        print(f"处理股票 {stock_symbol} 时发生错误: {e}")

# 使用ThreadPoolExecutor来并行处理股票池中的股票
def job():
    global ganzhou_index
    # 计算情绪指数
    ganzhou_index =compute_market_sentiment_index()

    # with concurrent.futures.ThreadPoolExecutor() as executor:
        # 1 准备市场行情快照，获取股票代码、名称、总市值、PE、PB等指标，用于筛选股票
    try:
        akshareDataCollector = AkshareDataCollector()
        market_spot_df = akshareDataCollector.get_stock_zh_a_spot_em()
        # market_spot_df = akshareDataCollector.get_fund_etf_spot_em()
        market_spot_df = market_spot_df[Constants.SPOT_EM_COLUMNS]
    except Exception as e:
        print(f'Akshare接口调用异常{e}')
        return
    # 2、准备主股票池和其他附加股票池        
    # favorStockPool =FavorStockPool(["自选股","仓","大笔买全榜","热股强全榜"])
    favorStockPool =FavorStockPool(["大笔买全榜","热股强全榜"])
    # favorStockPool =FavorStockPool(["ETF"])
    stockPools = [favorStockPool]
    symbols = []
    for stockPool in stockPools:
        symbols += stockPool.get_symbols()
    # 3、先对symbols进行基本面过滤,以便减少后续计算量
    symbols_spot_df = market_spot_df[market_spot_df['code'].isin(symbols)]
    fand_filter_list = [SymbolFilter(),
                        NameFilter(),
                        TotalCapitalFilter(min_threshold=20, max_threshold=1200),  # 总市值过滤
                        ]
    fand_filter_chain = FilterChain(fand_filter_list)
    symbols_spot_df = fand_filter_chain.apply(symbols_spot_df)
    # print(symbols_spot_df)
    # symbols = symbols_spot_df[['code',"name","open","high","low","pct","amount","volume_ratio","turnover","5_minute_change"]].values.tolist()
    # symbols = symbols_spot_df[['code',"name","open","high","low","pct","amount","volume_ratio","turnover","5_minute_change"]].to_dict('records')
    # symbols = symbols_spot_df.tail(1).to_dict('records')
    symbols = symbols_spot_df.to_dict('records')
    # executor.map(process_stock_data, symbols)
    for symbol in symbols:
        # if symbol['code'] == '300438':
        process_stock_data(symbol)
        
def is_trading_time(now):
    """
    检查当前时间是否在交易时段内。
    交易时段为每个交易日的9:26到15:00。
    """
    start_hour_9 = 9
    start_minute = 26
    
    end_hour_11 = 11
    start_hour_13 = 13
    end_hour_15 = 15
    # 构建交易开始和结束的时间
    start_1 = datetime(now.year, now.month, now.day, start_hour_9, start_minute)
    end_1 = datetime(now.year, now.month, now.day, end_hour_11, 30)
    
    start_2 = datetime(now.year, now.month, now.day, start_hour_13, 0)
    end_2 = datetime(now.year, now.month, now.day, end_hour_15, 0)
    
    return now.weekday() < 5 and ((start_1 <= now <= end_1) or (start_2 <= now <= end_2))
# 设置定时任务
def timed_job(): 
    now = datetime.now()
    if is_trading_time(now):
        job()
    else:
        print(f"当前时间 {now.hour}:{now.minute} 不在交易时段")    
    
def main():
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true',
                        help='Set dev mode to true')
    parser.add_argument('--daily', action='store_true',
                        help='Set k line is daily true')    
    args = parser.parse_args()     
    # load_dotenv()  # Load environment variables from .env file
    os.environ.pop("EM_APPKEY")
    os.environ.pop("EM_HEADER")
    os.environ.pop("USER_CONFIG_LIST")
    os.environ.pop("ACCOUNT_STRATEGT_MAPPING")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")   
   
    load_dotenv() 
    um = UserManagement()  # 启动用户的自选股更新信号侦听
    # um.startWatch()    
    stm = SimTraderManagement()  # 启动模拟账户的模拟交易信号侦听
    # stm.startWatch()      
    weComNotification = WeComNotification()  # 启动模拟账户的模拟交易信号侦听
    weComNotification.startWatch()      
    if args.dev:
        job()
    else:
        # 定时任务，每3秒执行一次
        schedule.every(60).seconds.do(timed_job)
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(1)
if __name__ == "__main__":   
    main()        