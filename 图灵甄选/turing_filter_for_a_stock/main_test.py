import os

from dotenv import load_dotenv
from account.account import AccountManagement
from core.topic import FavorSignalTopic, TradeSignalTopic
from pool.pool import FavorStockPool
from trader.base import OrderMessage
from trader.sim.trader import Trader
from trader.trader_management import SimTraderManagement
from user.user_management import UserManagement
from pubsub import pub

if __name__ == "__main__":
    os.environ.pop("EM_APPKEY")
    os.environ.pop("EM_HEADER")
    os.environ.pop("USER_CONFIG_LIST")
    os.environ.pop("ACCOUNT_STRATEGT_MAPPING")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")    
     
    load_dotenv() 
    
    # account_manager = AccountManagement()
    # accounts = account_manager.get_accounts()
    # for account in accounts:
    #   print(account.username, 50 * "——")
      # 600535 600
      # print(account.buy(code = "600535",price = 15.78, stock_num=200 ))
      # print(account.get_balance())
      # print(account.get_position())
      # print(account.creat_group(groupName= "动态创建2", desc="用API创建",authority=1))
      # print(account.get_groups())

      
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
    
    # um = UserManagement() 
    # users = um.get_users()
    # for user in users:
    #   print(user.username, 50 * "——")
    #   accounts = user.get_accounts()
    #   for account in accounts:
    #     # print(account.accountNo ,account.accountName,account.total_money,account.strategyName)
    #     # print(account.trader.buy(code = "603270",price = 19.40, stock_num=300 ))
        
    #     hangup_order =account.trader.get_can_cancel_order()
    #     print(hangup_order)
    #     for item in hangup_order:
    #         # if item['mmflag'] == '0':
    #         print(account.trader.cancel_order(code=item["code"],order_no=item["order_no"]))     
    tm = SimTraderManagement()
    tm.startWatch()   

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
    favor_message={
      "group_name": "热股强势",
      "symbols": ['000002','000001']
    }
    # pub.sendMessage(str(FavorSignalTopic.UPDATE_FAVOR),message=favor_message)   
    
    users = um.get_users()
    for user in users:
      # pass
      print(user.username, 50 * "——")
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
      
      print(FavorStockPool(["自选股","无雷"],user).get_symbols())
    



