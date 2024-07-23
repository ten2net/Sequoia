from typing import List
import stock_favor_management.em_favor_api as em
import requests
import os
import json


class StockFavorManagement:
    def __init__(self):
        self.session = requests.Session()
        appkey = os.environ.get('EM_APPKEY')
        appHeader =json.loads(os.environ.get('EM_HEADER'))        
        em.APIKEY = appkey
        em.HEADER['Cookie']=appHeader[0]

    def get_symbols(self, group_name="自选股"):
        symbols = em.list_entities(group_name=group_name, session=self.session)
        return symbols

    # def get_symbols(self, group_names: List[str] = ["自选股"]):
    #     symbols = []
    #     for group in group_names:
    #         symbols += em.list_entities(group_name=group, session=self.session)
    #     return list(set(symbols))

    def add_to_group(self, symbols: List[str] = [], group_name: str = "斐纳斯精选"):
        em.update_em_favor_list(
            symbols, group_full_name=f"{group_name[:3]}全榜", group_new_name=group_name)
