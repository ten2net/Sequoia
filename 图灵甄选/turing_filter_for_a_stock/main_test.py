import os

from dotenv import load_dotenv
from collector.akshare_data_collector import AkshareDataCollector
from core.topic import FavorSignalTopic, TradeSignalTopic
from pool.pool import ATPStockPool, AmountStockPool, BidAskStockPool, FavorStockPool
from radar.best_targets import BestTargetStockRadar
from radar.everyday_targets import EverydayTargetStockRadar
from strategy.fib import FibonacciTradingSignal
from trader.base import OrderMessage
from trader.sim.trader import Trader
from trader.trader_management import SimTraderManagement
from user.user_management import UserManagement
from pubsub import pub

from main import task_for_del_all_from_group

if __name__ == "__main__":
    os.environ.pop("EM_APPKEY")
    os.environ.pop("EM_HEADER")
    os.environ.pop("USER_CONFIG_LIST")
    os.environ.pop("ACCOUNT_STRATEGT_MAPPING")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")    
     
    load_dotenv() 
    
      
      # hangup_order =account.get_can_cancel_order()
      # print(hangup_order)
      # for item in hangup_order:
      #     # if item['mmflag'] == '0':
      #     print(account.cancel_order(code=item["code"],order_no=item["order_no"]))
      # symbols =['300397', '002611', '600621', '000828', '002837', '003026', '002001', '603662', '600216', '000957', '600200', '002869', '002296', '300446', '300123', '002735', '300455', '600336', '603988', '600843', '002979', '300011', '600719', '001208', '600990', '600764', '600686', '600817', '603686', '001379', '002685', '301112', '000547', '000868', '000901', '002829', '603508', '603107', '000880', '000572', '603390', '600386', '300053', '300424']
      # # symbols =['300397', '000001']
      # for code in symbols:
      #   print(account.buy(code = code ,price = 9.65, stock_num=1000 ))
    
    
    # print(tm.commit_buy_or_sell_order(code = "603270",price = 19.40, stock_num=300,order_type ="spo_order_limit" ) )
  #  print(tm.get)

    # symbols =['000421', '002611', '600621', '000828', '002837', '003026', '002001', '603662', '600216', '000957', '600200', '002869', '002296', '300446', '300123', '002735', '300455', '600336', '603988', '600843', '002979', '300011', '600719', '001208', '600990', '600764', '600686', '600817', '603686', '001379', '002685', '301112', '000547', '000868', '000901', '002829', '603508', '603107', '000880', '000572', '603390', '600386', '300053', '300424']
    # for code in symbols:
    #    print(tm.buy(code = code ,price = "1.02", stock_num=300 ))
    
    # print(commit_buy_or_sell_order(code = "603270",price = 19.40, stock_num=300,order_type ="spo_order_limit" ) )
    # print(buy(code = "603270",price = 19.40, stock_num=300 ) )
    # print(sell(code = "000099",price = 18.40, stock_num=100.0 ) )
    # print(get_can_cancel_order())
    adc = AkshareDataCollector()
    # print(adc.get_hot_symbols(10))
    um = UserManagement() 
    users = um.get_users()
    # for user in users:
    #   print(user.username, 50 * "——")
    #   accounts = user.get_accounts()
    #   for account in accounts:
    #     # print(account.accountNo ,account.accountName,account.total_money,account.strategyName)
    #     # print(account.trader.buy(code = "603270",price = 19.40, stock_num=300 ))
        
    #     hangup_order =account.trader.get_can_cancel_order()
    #     # print(hangup_order)
    #     for item in hangup_order:
    #         # if item['mmflag'] == '0':
    #         print(account.trader.cancel_order(code=item["code"],order_no=item["order_no"]))     
    # tm = SimTraderManagement()
    # tm.startWatch()   

    # message_center.sendMessage('buy_signal', 'ssssssssssssssss','ddd')
    # message_center.sendMessage('buy.signal', message={"aa":"mm"})
    # message_center.sendMessage('sell.signal', message={"aa":"mm"})
    
    # print()
    # pub.sendMessage(str(TradeSignalTopic.BUY), message = OrderMessage(symbol="300397", price=9.30, pct=1.2), index=0.3)
    # pub.sendMessage(str(TradeSignalTopic.SELL_ALL),message=OrderMessage(strategyName="热股强势", symbol=None, price=None, pct=None ,index=0.5))
    # pub.sendMessage(str(TradeSignalTopic.SELL),message=OrderMessage(strategyName="热股强势", symbol=None, price=None, pct=None ,index=-0.001)) 
    # pub.sendMessage(str(TradeSignalTopic.SELL_HALF),message=OrderMessage(strategyName="热股强势", symbol=None, price=None, pct=None ,index=-0.001)) 
    # pub.sendMessage(str(TradeSignalTopic.SELL_QUARTER),message=OrderMessage(strategyName="热股强势", symbol=None, price=None, pct=None ,index=-0.001)) 
    
    um = UserManagement() 
    um.startWatch()
    # favor_message={
    #   "group_name": "热股强势",
    #   "symbols": ['000002','000001']
    # }
    # pub.sendMessage(str(FavorSignalTopic.UPDATE_FAVOR),message=favor_message)   
    
    # users = um.get_users()
    # for user in users:
    #   # pass
    #   print(user.username, 50 * "——")
      # groups = user.favor.get_groups()
      # print(groups)
      # group_name = 'Test'
      # group =user.favor.create_group(group_name)
      # print(user.favor.rename_group(group['gid'],group_name+"123"))
      # print(user.favor.del_group(group_name+"123"))
      # group_name = '热股强势'
      # print(user.favor.get_symbols(group_name))
      
      # print(user.favor.update_favor(['000002','000001'],"API"))
      # print(user.favor.add_to_group(code='000002',group_name="API全"))
      # print(user.favor.del_from_group(code='000002',group_name="API全"))
      
      # print(FavorStockPool(["自选股","无雷"],user).get_symbols())
      
    # fib =FibonacciTradingSignal(27.19,22.62)
    # print([0.236, 0.382, 0.500, 0.618, 0.786, 1.000, 1.618, 2.618])
    # print(fib.fib_levels)
    # print(fib.generate_signal(23.45))
    # df = adc.get_stock_hot_rank()
    # df =df[(df["rank"]<50)]
    # print(df[:50])
    # print(df[50:])
    
    # task_for_del_all_from_group()
    # EverydayTargetStockRadar(name="每日情绪榜",topN=300).startup()
    BestTargetStockRadar(name="封神榜",k=300,n=20).startup()
    
    # stockPool = ATPStockPool(k=300)
    # df = stockPool.get_topN()
    # print(len(df))
    # print(df)
    
    # symbols = stockPool.get_symbols()    
    # print(symbols)
    
    # df =adc.get_large_buy()
    # df =df[df['volume']>3000000]
    # print(df.head(50))
    
    # df =ATPStockPool(k=300).get_topN()    
    # print(df)
    
    # df =BidAskStockPool(k=300,n=30).get_stat_data_df()
    # print(df)
    # df =BidAskStockPool(k=300,n=30).get_symbols()
    # print(df)
    
    



    

    



    



