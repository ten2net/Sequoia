from typing import List
from dotenv import load_dotenv
import favor.em_favor_api as em
import requests
import os
import json

from trader.sim.trader import Trader
from user.user import User

class UserManagement:
    def __init__(self):
        self.session = requests.Session()
        load_dotenv()
        user_config_list = json.loads(os.environ.get('USER_CONFIG_LIST'))    
        self.users =[User(user_config) for user_config in user_config_list ]  

    def get_users(self):
        return self.users

