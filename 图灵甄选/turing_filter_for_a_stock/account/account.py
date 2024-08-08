from typing import List
from dotenv import load_dotenv
import favor.em_favor_api as em
import requests
import os
import json

class Account:
    def __init__(self, account_config: dict):
        self.__dict__.update(account_config)

class AccountManagement:
    def __init__(self):
        self.session = requests.Session()
        load_dotenv()
        self.appkey = os.environ.get('EM_APPKEY')
        self.account_tokens = json.loads(os.environ.get('EM_HEADER'))

    def get_favor_config(self):
        return self.appkey, self.account_tokens

