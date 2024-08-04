from datetime import datetime
import math
from typing import List
from account.account import AccountManagement
from core.constants import Constants
from collector.akshare_data_collector import AkshareDataCollector
from filter.filter_chain import FilterChain
from filter.fund.fund_filter import NameFilter, SymbolFilter, TotalCapitalFilter
from filter.trading.amount_filter import AmountFilter
from notification.wecom import WeComNotification
from radar.base import StockRadar
from favor.favor import FavorManager, StockFavorManagement
from pool.pool import HotSymbolStockPool
import os
from termcolor import colored
import pandas as pd

class HotSymbolStockRadar(StockRadar):
    def __init__(self,name:str="热股强势", topN:int = 22):
        self.name = name
        self.topN = min(topN,22)
    def startup(self):
        # 1 准备市场行情快照，获取股票代码、名称、总市值、PE、PB等指标，用于筛选股票
        try:
            akshareDataCollector = AkshareDataCollector()
            market_spot_df = akshareDataCollector.get_stock_zh_a_spot_em()
            market_spot_df_all = market_spot_df
            market_spot_df = market_spot_df[Constants.SPOT_EM_COLUMNS_BASE] 
        except Exception as e:
            print(f'Akshare接口调用异常{e}')
            return
        # 2、准备主股票池和其他附加股票池
        mainStockPool = HotSymbolStockPool()        
        stockPools = [mainStockPool]  
        symbols = []
        for stockPool in stockPools:
            symbols += stockPool.get_symbols(k = 5)
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
        if df.shape[0] == 0:
            print(colored("未到集合竞价时间！",'red'))
            return
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
            print(colored("无满足条件的股票！",'yellow'))
        else:
            # 计算情绪指数
            ganzhou_index =self.compute_market_sentiment_index()
            # 7、评分            
            # df['score'] = PriceScorer().score(df) + VolumeScorer().score(df) + PEScorer().score(df) +
            #               SentimentScorer().score(df)
            
            # 8、排序            
            df = df.head(round(1.5 * self.topN))  #自选股不受长度限制
            df['is_hot_industry'] = True # df['code'].apply(lambda code: akshareDataCollector.is_hot_industry(code))
            
            df.sort_values(by=['is_hot_industry','pct'], ascending=[False,False], inplace=True)
            df = df.reset_index(drop=True)
            print(colored(f"""{self.name}发现了 {df.shape[0]} 个目标：{df['name'].tolist()}""","green"))
            # 9、自选股与模拟盘  
            try:
                # 9.1、更新自选股   
                results =df['code'].tolist()
                results =  results[::-1]  #确保新加自选的在上面
                favorManager =FavorManager()
                favorManager.update_favor(results, group_name=self.name)
                # 9.2、模拟盘 
                # 9.2.1 卖出逻辑
                # sfm = StockFavorManagement()
                # hold_position = sfm.get_position()
                account_manager = AccountManagement()
                accounts = account_manager.get_accounts()
                for account in accounts:  
                    selled:List[str]=[] # 刚下了卖单的股票代码，避免刚卖出后又买进来
                    not_needed_add_position:List[str]=[] # 不可加仓的股票代码，已持仓的股票当前涨幅5%以上的不再补仓
                    hold_position = account.get_position()

                    if hold_position is not None and len(hold_position)>0:
                        now = datetime.now()
                        lock_position =False
                        if ganzhou_index >= 0.1 and now.hour < 14:  # 情绪好时，只在下午14点后，才考虑卖出股票
                          lock_position =True  # 仓位锁仓

                        df_hold = pd.DataFrame(data=hold_position)
                        df_hold['quantity'] = df_hold['quantity'].astype(int)
                        df_hold['quantity_can_use'] = df_hold['quantity_can_use'].astype(int)
                        df_hold['purchase_price'] = df_hold['purchase_price'].astype(float)
                        
                        df_host_current = df_hold.merge(market_spot_df_all, on="code", how="left")
                        # 计算持仓浮盈
                        df_host_current['pct_hold'] = (df_host_current['close'] - df_host_current['purchase_price']) / df_host_current['purchase_price']
                        df_can_sell = df_host_current[df_host_current['quantity_can_use'] > 0]  # 过滤掉不能卖出的股票，避免废单

                        for index, row in df_can_sell.iterrows():
                            quantity_can_use = row['quantity_can_use']
                            
                            sell_price = max(round(row['close'] * 0.995 , 2) ,row["lower_limit"])  # 确保尽量能出手
                            if math.isnan(sell_price):  # 对于停牌股票的卖出策略，临时先这样处理：涨8个点卖出
                                sell_price = row['close_yesterday'] + 0.08 * row['close_yesterday']
                            print(sell_price,row['code'],quantity_can_use,row['close'],row["lower_limit"], row['close_yesterday'])
                            if ganzhou_index < 0.05 :   # 情绪太差，一键清仓
                                print(account.sell(code=row['code'], price=sell_price, stock_num=quantity_can_use))
                                selled.append(row['code'])                    
                            elif lock_position == False:
                                sell_signal =(row['high'] - row['low']) / row['open'] > 0.1 or (row['high'] > row['open'] and row['close'] < row['open'])
                                if sell_signal and row['pct_hold'] < -0.01 :   # 浮亏1%以上，卖空
                                    print(account.sell(code=row['code'], price=sell_price, stock_num=quantity_can_use))
                                    selled.append(row['code'])
                                elif sell_signal and 0.03 < row['pct_hold'] <= 0.1 and row['pct'] < 9  :   # 浮盈3%以上但没有涨停，卖出一半仓位
                                    quantity_can_use =round(quantity_can_use / 2 , 0) if quantity_can_use > 100 else quantity_can_use
                                    quantity_can_use = quantity_can_use - (quantity_can_use % 100)  # 确保是整手
                                    print(account.sell(code=row['code'], price=sell_price, stock_num=quantity_can_use)) 
                                    selled.append(row['code'])
                                elif sell_signal and 0.1 < row['pct_hold'] and row['pct'] < 9  :   # 浮盈10%以上但没有涨停，卖空
                                    print(account.sell(code=row['code'], price=sell_price, stock_num=quantity_can_use)) 
                                    selled.append(row['code'])
                        
                            if row['pct'] > 5  :   # 已持仓的股票当前涨幅5%以上的不再补仓
                                not_needed_add_position.append(row['code'])
                    
                    # 8.2.2、买入逻辑                            
                    if ganzhou_index >= -0.05:      # 开仓条件。情绪不是太差，才可以开仓 
                        now = datetime.now()
                        df['upper_rate'] = df['code'].apply(lambda x: 20 if (x.startswith('3') or x.startswith('68'))  else 10)
                        
                        df['space_limit'] = (df['upper_limit_y'] - df["close"]) / df['upper_limit_y']
                        
                        # if now.hour >= 10:  # 上午10点后，只追离涨停还有7%以上上涨空间的股票，10点前只追离涨停还有2%以上上涨空间的股票
                        #     df = df[((df['upper_limit_y'] - df["close"]) / df['upper_limit_y']) > 0.07 ]                    
                        # else:
                        #     df = df[((df['upper_limit_y'] - df["close"]) / df['upper_limit_y']) > 0.02 ]  
                        # print(df[['code','close','upper_limit_y','upper_rate','pct','space_limit']] )                  
                        if now.hour >= 10:  # 上午10点后，只追离涨停还有还有空间的
                          df = df[(df['upper_rate'] - df['pct']) > (df['upper_rate'] /3)]  # 过滤掉上涨空间还有三分之一的股票                     
                        else:
                            df = df[(df['upper_rate'] - df['pct']) > (df['upper_rate'] /5)]  # 过滤掉当日上涨空间已经不多的股票                    
                   
                        # df_buy = df.head(int(self.topN/2)) # 只买前排
                        df_buy = df[~df['code'].isin(selled)]  # 过滤掉已经卖出的股票            
                        df_buy = df[~df['code'].isin(not_needed_add_position)]  # 过滤掉不需要补仓的股票   
                        
                        df_buy = df[df['close'] > df['open']]  # 只买红票

                        position_ratio = ganzhou_index  # 仓位比例，情绪越差，仓位比例越低，情绪越好，仓位比例越高          
                        
                        price_rate = 1 + ganzhou_index / 100  # 价格调整比例,情绪越好，挂价越高于现价，情绪越差，挂价越低于现价
                        
                        df_buy=df_buy.head(5) # 只买最强的5个股票
                        
                        stock_prices={row['code']:min(round(row['close'] * price_rate,2),row['upper_limit_y'])  for index, row in df_buy.iterrows()} # 股票价格
              
                        # print(sfm.execute_buy(stock_prices = stock_prices, position_ratio = position_ratio ))
                        
                        # 9.3、模拟盘，上午开盘，买入8大行业先锋股前
                        now = datetime.now()
                        if now.hour == 9 and now.minute <=35:  # 上午开盘，买入8大行业先锋股前
                            account_manager = AccountManagement()
                            accounts = account_manager.get_accounts()
                            for account in accounts:  
                                print(account.username,position_ratio, 50 * "——")
                                buy_batch_result = account.buy_batch(stock_prices=stock_prices, position_ratio=position_ratio)
                                print(buy_batch_result)
                
            except Exception as e:
              print(f'东方财富接口调用异常:{e}')
            # 10、发送消息通知  
            now = datetime.now()                               
            if now.hour >= 14:  # 上午10点后，通知中会过滤掉涨幅大于10%的股票 
                df = df[df["pct"] < 10 ]
            # print(df.columns)
            df = df.head(self.topN)   
            df['name'] =  df.apply(lambda row: "☀"+ row['name'] if row['is_hot_industry'] else row['name'], axis=1)     
            wecom_msg_enabled= os.environ.get('WECOM_MSG_ENABLED').lower() == 'true'
            if wecom_msg_enabled and df.shape[0] > 0:
                WeComNotification().send_stock_df(title=self.name, df=df, ganzhou_index=ganzhou_index)
