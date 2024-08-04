import os

from dotenv import load_dotenv
from account.account import AccountManagement
from trader.sim.trader import Trader, TraderManagement

if __name__ == "__main__":
    os.environ.pop("EM_APPKEY")
    os.environ.pop("EM_HEADER")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")       
    # os.environ.pop("SIM_TRADER_ACCOUNT")       
    load_dotenv() 
    
    account_manager = AccountManagement()
    accounts = account_manager.get_accounts()
    for account in accounts:
      print(account.username, 50 * "——")
      # 600535 600
      print(account.buy(code = "600535",price = 15.78, stock_num=200 ))
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




