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
