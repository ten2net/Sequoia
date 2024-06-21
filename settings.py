# -*- encoding: UTF-8 -*-
import yaml
import os
import akshare as ak
import pywencai
from termcolor import colored
import pandas as pd

def init(q=""):

    global config
    global top_list
    global lhb_df
    global query
    global leaderboard   # 排行版
    
    # 初始化排行版
    data_types = {
        '股票代码': str,      
        '当前行情': str,    
        '预测收益率': float       
    }
    
    leaderboard = []

    root_dir = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root
    config_file = os.path.join(root_dir, 'config.yaml')
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    if q == "":
        return
    # df_lhb = ak.stock_lhb_stock_statistic_em(symbol="近六月")  #龙虎榜个股上榜统计
    # mask = (df_lhb['买方机构次数'] > 1)  # 机构买入次数大于1
    # df_lhb = df_lhb.loc[mask]
    # # top_list = df['代码'].tolist()
    # df_lhb = df_lhb[['代码','名称']]
    
    query=q
    print(colored(q,'yellow'))
    df = pywencai.get(query=query)
    if df is not None:
        try:
            df = df[['股票代码','股票简称']]
            df['股票代码'] = df['股票代码'].str.slice(start=0, stop=6)
            df = df[~df['股票代码'].str.startswith('68')]  # 排除以 '68' 开头的代码
            df = df[~df['股票代码'].str.startswith('4')]  # 排除以 '4' 开头的代码
            # df.index=df[]
            df.columns = ['代码','名称']
            
            # # 使用merge求交集
            # intersection = df_lhb.merge(df, on='代码', how='inner')
            # lhb_df =intersection
            # top_list=intersection['代码'].tolist()  
                  
            lhb_df =df
            top_list=df['代码'].tolist()        
            # lhb_df =df_lhb
            # top_list=df_lhb['代码'].tolist()        
            
        except:
          print('An exception occurred')
 
    


def config():
    return config