# -*- encoding: UTF-8 -*-
import yaml
import os
import akshare as ak
import pywencai
from termcolor import colored

def init(q=""):

    global config
    global top_list
    global lhb_df
    global query
    root_dir = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root
    config_file = os.path.join(root_dir, 'config.yaml')
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    if q == "":
        return
    # df = ak.stock_lhb_stock_statistic_em(symbol="近三月")  #龙虎榜个股上榜统计
    # df = df.loc[mask]
    # mask = (df['买方机构次数'] > 1)  # 机构买入次数大于1
    # top_list = df['代码'].tolist()
    # lhb_df = df[['代码','名称']]
    query=q
    print(colored(q,'yellow'))
    df = pywencai.get(query=query)

    df = df[['股票代码','股票简称']]
    # print(df)
    df['股票代码'] = df['股票代码'].str.slice(start=0, stop=6)
    df = df[~df['股票代码'].str.startswith('68')]  # 排除以 '68' 开头的代码
    df = df[~df['股票代码'].str.startswith('4')]  # 排除以 '4' 开头的代码
    # df.index=df[]
    df.columns = ['代码','名称']
    lhb_df =df
    top_list=df['代码'].tolist()
    


def config():
    return config