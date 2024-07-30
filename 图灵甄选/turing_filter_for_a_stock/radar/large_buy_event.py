from datetime import datetime
from typing import List
from core.constants import Constants
from collector.akshare_data_collector import AkshareDataCollector
from filter.filter_chain import FilterChain
from filter.fund.fund_filter import NameFilter, SymbolFilter, TotalCapitalFilter
from filter.trading.amount_filter import AmountFilter
from filter.trading.turnover_filter import TurnoverFilter
from filter.trading.volume_filter import HighVolumeFilter
from kline.kline_style import KLineStyles, KLineStyles_cdls
from notification.wecom import WeComNotification
from radar.base import StockRadar
from favor.favor import StockFavorManagement
from pool.pool import AmountStockPool, FavorStockPool, LargeBuyStockPool
from filter.trading.indictor_trading_filter import IndicatorTradingFilter
import os
from termcolor import colored
import pandas as pd

class LargeBuyStockRadar(StockRadar):
    def __init__(self,name:str="大笔买入", topN:int = 22):
        self.name = name
        self.topN = min(topN,22)
    def startup(self):
        # 1 准备市场行情快照，获取股票代码、名称、总市值、PE、PB等指标，用于筛选股票
        market_spot_df = AkshareDataCollector().get_stock_zh_a_spot_em()
        market_spot_df_all = market_spot_df[Constants.SPOT_EM_COLUMNS] 
        market_spot_df = market_spot_df[Constants.SPOT_EM_COLUMNS_BASE] 
        # 2、准备主股票池和其他附加股票池
        mainStockPool = LargeBuyStockPool()        
        stockPools = [mainStockPool]  
        symbols = []
        for stockPool in stockPools:
            symbols += stockPool.get_symbols()
        # 3、先对symbols进行基本面过滤,以便减少后续计算量
        symbols_spot_df = market_spot_df[market_spot_df['code'].isin(symbols)]
        fand_filter_list = [SymbolFilter(),
                            NameFilter(),
                            TotalCapitalFilter(min_threshold=30, max_threshold=1200), #总市值过滤
                            ]
        fand_filter_chain = FilterChain(fand_filter_list)
        symbols_spot_df = fand_filter_chain.apply(symbols_spot_df)        
        symbols = symbols_spot_df['code'].tolist()
        # 4、获取股票数据，并附加其他指标
        # df = mainStockPool.get_data_with_indictores(symbols,withCDL=False)
        df = mainStockPool.get_data(symbols)
        df = df.merge(market_spot_df, on="code", how="left")
        
        # 5、附加其他指标
        # 6、筛选股票，实现单独的过滤器，添加到过滤器链中即可
        filters = [
            AmountFilter(threshold=1.5), # 昨日成交额过滤器，过滤掉成交额小于2亿的股票
            # HighVolumeFilter(threshold=2), # 昨日成交量过滤器，过滤掉成交量大于5日均量1.3倍的股票
        ]
        filter_chain = FilterChain(filters)
        df = filter_chain.apply(df)
        
        if df.shape[0] == 0:
            print("无满足条件的股票！")
        else:
            # 计算情绪指数
            ganzhou_index =self.compute_market_sentiment_index()
            # 7、评分            
            # df['score'] = PriceScorer().score(df) + VolumeScorer().score(df) + PEScorer().score(df) +
            #               SentimentScorer().score(df)
            
            # 8、排序            
            df = df.head(round(2 * self.topN))  #自选股不受长度限制
            print(colored(f"""{self.name}发现了 {df.shape[0]} 个目标：{df['name'].tolist()}""","green"))
            # 9、更新自选股            
            sfm = StockFavorManagement()
            results =df['code'].tolist()
            results =  results[::-1]  #确保新加自选的在上面
            sfm.add_to_group(results, group_name=self.name)
            # 9.1、模拟盘  
            sfm = StockFavorManagement()   
            hold_position = sfm.get_position()
            selled:List[str]=[] # 刚下了卖单的股票代码，避免刚卖出后又买进来
            not_needed_add_position:List[str]=[] # 不可加仓的股票代码，已持仓的股票当前涨幅5%以上的不再补仓
            if hold_position is not None:
                df_hold = pd.DataFrame(data=hold_position)
                df_hold['quantity'] = df_hold['quantity'].astype(int)
                df_hold['quantity_can_use'] = df_hold['quantity_can_use'].astype(int)
                df_hold['purchase_price'] = df_hold['purchase_price'].astype(float)
                df_host_current = df_hold.merge(market_spot_df_all, on="code", how="left")
                # 计算持仓浮盈
                df_host_current['pct_hold'] = (df_host_current['close'] - df_host_current['purchase_price']) / df_host_current['purchase_price']
                df_can_sell = df_host_current[df_host_current['quantity_can_use'] > 0]  # 过滤掉不能卖出的股票，避免废单
                # print(df_can_sell[[ 'code', 'name_x','pct_hold','pct','quantity_can_use']])
                for index, row in df_can_sell.iterrows():
                    if row['pct_hold'] < -0.01 :   # 浮亏1%以上，卖空
                        print(sfm.sell(symbol=row['code'], price=row['close'], stock_num=row['quantity_can_use']))
                        selled.append(row['code'])
                    elif 0.03 < row['pct_hold'] <= 0.1 and row['pct'] < 10  :   # 浮盈3%以上但没有涨停，卖出一半仓位
                        print(sfm.sell(symbol=row['code'], price=row['close'], stock_num=round(row['quantity_can_use'] / 2 , 0))) 
                        selled.append(row['code'])
                    elif 0.1 < row['pct_hold'] <= 0.3 and row['pct'] < 0.98  :   # 浮盈10%以上但没有涨停，卖空
                        print(sfm.sell(symbol=row['code'], price=row['close'], stock_num=row['quantity_can_use'])) 
                        selled.append(row['code'])
                    elif row['pct'] > 5  :   # 已持仓的股票当前涨幅5%以上的不再补仓
                        not_needed_add_position.append(row['code'])
                    else:
                        pass
                    
            if ganzhou_index > -0.05:      # 情绪太差，不开仓    
                now = datetime.now()
                if now.hour > 10:  # 上午10点后，先过滤掉涨幅大于8%的股票，避免追高买入站岗
                    df = df[df["pct"] < 8 ]                       
                df_buy = df.head(int(self.topN/2))    
                df_buy = df[~df['code'].isin(selled)]  # 过滤掉已经卖出的股票            
                df_buy = df[~df['code'].isin(not_needed_add_position)]  # 过滤掉不需要补仓的股票            

                position_ratio = ganzhou_index  # 用当前情绪来控制仓位比例
                price_rate = 1 + ganzhou_index / 100  # 价格调整比例,情绪越好，挂价越高于现价，情绪越差，挂价越低于现价
                
                stock_prices={row['code']:round(row['close'] * price_rate,2)  for index, row in df_buy.iterrows()} # 股票价格
        
                print(sfm.execute_buy(stock_prices = stock_prices, position_ratio = position_ratio ))
            
            # 10、发送消息通知  
            now = datetime.now()
            if now.hour > 10:  # 上午10点后，通知中会过滤掉涨幅大于10%的股票 
                df = df[df["pct"] < 10 ]  
            df = df.head(self.topN)          
            wecom_msg_enabled= os.environ.get('WECOM_MSG_ENABLED').lower() == 'true'
            if wecom_msg_enabled:
                WeComNotification().send_stock_df(title=self.name, df=df, ganzhou_index=ganzhou_index)
