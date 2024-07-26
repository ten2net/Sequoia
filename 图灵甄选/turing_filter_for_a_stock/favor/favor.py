from typing import List

from dotenv import load_dotenv
import favor.em_favor_api as em
import requests
import os
import json


class StockFavorManagement:
    def __init__(self):
        load_dotenv()  
        self.session = requests.Session()

        appkey = os.environ.get('EM_APPKEY')
        appHeader =json.loads(os.environ.get('EM_HEADER'))
     
        em.APIKEY = appkey
        em.HEADER['Cookie']=appHeader[0]

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
