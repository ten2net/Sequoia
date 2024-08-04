import math
from typing import List, Optional

from dotenv import load_dotenv
from account.account import AccountManagement
import favor.em_favor_api as em
import requests
import os
import json


class FavorManager:
    def __init__(self):
        account_manager = AccountManagement()
        self.appkey , self.account_tokens = account_manager.get_favor_config()
    def update_favor(self,symbols:List[str], group_name:str):
        stockFavorManagement = StockFavorManagement()
        for account_token in self.account_tokens:
            stockFavorManagement.set_appkey(self.appkey)
            stockFavorManagement.set_token(account_token)
            stockFavorManagement.add_to_group(symbols, group_name=group_name)

class StockFavorManagement:
    def __init__(self):
        self.session = requests.Session()
        load_dotenv()  
        appkey = os.environ.get('EM_APPKEY')
        appHeader =json.loads(os.environ.get('EM_HEADER'))
        em.APIKEY = appkey
        em.HEADER['Cookie']=appHeader[0]  # 缺省账户，用来测试
    
    def set_appkey(self,appkey: str=""):
        em.APIKEY = appkey
    def set_token(self,token: str=""):
        em.HEADER['Cookie'] = token

    def get_symbols(self, group_name="自选股"):
        symbols = em.list_entities(group_name=group_name, session=self.session)
        return symbols

    def add_to_group(self, symbols: List[str] = [], group_name: str = "斐纳斯精选"):
        em.update_em_favor_list(
            symbols, group_full_name=f"{group_name[:3]}全榜", group_new_name=group_name)
    def del_from_group(self, symbols: List[str] = [], group_name: str = "斐纳斯精选"):
        # print(em.del_from_group(" ".join(symbols), group_name=group_name, entity_type="stock"))
        for symbol in symbols:
            print(em.del_from_group(symbol, group_name=group_name, entity_type="stock"))
    def buy(self, symbol:str, price:float, stock_num:int):
       stock_num=math.floor(stock_num)
       return em.buy(symbol, price, stock_num)
    def sell(self, symbol:str, price:float, stock_num:int):
       stock_num=math.floor(stock_num)
       return em.sell(symbol, price, stock_num)
       
    def get_position(self)->Optional[List[dict]]:
        return em.get_position()
    
    def execute_buy(self, stock_prices, position_ratio):
        """
        执行买入操作的函数。        

        :param position_ratio: 仓位比例（例如0.1表示10%）
        :param stock_prices: 每只股票的当前价格列表（字典形式，键为股票名称或代码，值为价格）
        :return: 买入的股票及其数量
        """
        # 先撤销未成交的挂单
        can_cancel_orderes =em.get_can_cancel_order()
        if can_cancel_orderes is not None:
            for order in can_cancel_orderes:
                if order['mmflag'] == '0':
                    print(em.cancel_order(code=order["code"],order_no=order["order_no"]))        
                
        if position_ratio < 0 or position_ratio > 1:
            raise ValueError("仓位比例必须在0和1之间")
        
        balance_info = em.get_balance_info()  # {'account': '241990400000029517', 'total_money': '999160.83', 'account_pct': '-0.30', 'account_return': '-839.17', 'market_value': '348792.72', 'can_use_money': '650368.12', 'freeze_money': '74128.72'}

        if 0 < position_ratio < 0.3 and (float(balance_info['market_value']) /float(balance_info['total_money'])) > 0.7:
            return {}
        if -0.1 < position_ratio < 0 and (float(balance_info['market_value']) /float(balance_info['total_money'])) > 0.5:
            return {}
        # 计算单次买入金额
        buy_amount_per_stock = float(balance_info['can_use_money']) * position_ratio // len(stock_prices)
        
        # 计算每只股票的买入数量
        transactions = {}
        for stock, price in stock_prices.items():
            buy_quantity = math.floor(buy_amount_per_stock / price)
            buy_quantity = buy_quantity - (buy_quantity % 100)  # 确保是整手
            if buy_quantity > 0:
                result:str = em.buy(stock, price, buy_quantity)
                transactions[stock] = (price,buy_quantity,result)
        return transactions
