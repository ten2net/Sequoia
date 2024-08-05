from typing import List
from dotenv import load_dotenv
import favor.em_favor_api as em
import requests
import os
import json

from trader.sim.trader import Trader


class Account:
    def __init__(self, account_config: dict):
        self.__dict__.update(account_config)
        self.trader = Trader(self.userid, self.groupno, self.token)

    def get_trader(self):
        return self.trader

    def set_trader(self, trader: Trader):
        self.trader = trader

    def get_balance(self) -> dict:
        return self.trader.get_balance_info()

    def get_position(self) -> List[dict]:
        return self.trader.get_position()

    def get_can_cancel_order(self) -> List[dict]:
        return self.trader.get_can_cancel_order()

    def buy(self, code: str, price: float, stock_num: int) -> str:
        return self.trader.buy(code, price, stock_num)
    def buy_batch(self, stock_prices: dict, position_ratio:float)->dict:
        return self.trader.execute_buy(stock_prices, position_ratio)

    def sell(self, code: str, price: float, stock_num: int) -> str:
        return self.trader.sell(code, price, stock_num)

    def cancel_order(self, code: str, order_no: str) -> str:
        return self.trader.cancel_order(code, order_no)
      
    def get_groups(self) -> List[dict]:
        return self.trader.get_groups()
    def creat_group(self, groupName: str, desc: str = "API", authority: int = 0) -> str:
        return self.trader.create_group(groupName, desc, authority)


class AccountManagement:
    def __init__(self):
        self.session = requests.Session()
        load_dotenv()
        self.appkey = os.environ.get('EM_APPKEY')
        self.account_tokens = json.loads(os.environ.get('EM_HEADER'))

        self.trader_config = json.loads(os.environ.get('SIM_TRADER_ACCOUNT'))

    def get_favor_config(self):
        return self.appkey, self.account_tokens

    def get_accounts(self) -> List[Account]:
        return [Account(account_config) for account_config in self.trader_config]
