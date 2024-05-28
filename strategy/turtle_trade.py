# -*- coding: UTF-8 -*-
import settings
# 总市值
BALANCE = 200000


# 最后一个交易日收市价为指定区间内最高价
import pandas as pd

def check_enter(code_name, data, end_date=None, threshold=60):
    """
    判断股票是否在最近指定天数内创新高。
    
    Args:
        code_name (str): 股票代码。
        data (pd.DataFrame): 包含股票历史数据的DataFrame，需包含列'日期'和'收盘'。
        end_date (str, optional): 截止日期，格式为'yyyy-mm-dd'。默认为None，表示不限制截止日期。
        threshold (int, optional): 最近指定天数，用于判断股票是否创新高。默认为60。
    
    Returns:
        bool: 若股票在最近指定天数内创新高，则返回True；否则返回False。
    
    """
    if code_name[0] not in settings.top_list:
        return False    
    
    if end_date is not None:
        data = data[data['日期'] <= end_date]
    
    # 确保至少有threshold条数据
    if len(data) < threshold:
        return False
    
    # 使用Pandas的向量化操作来找到最大收盘价
    max_price = data['收盘'].tail(n=threshold).max()
    last_close = data['收盘'].iloc[-1]
    
    return last_close >= max_price
def check_enter2(code_name, data, end_date=None, threshold=60):
    """
    判断股票是否在最近指定天数内创新高。
    
    Args:
        code_name (str): 股票代码。
        data (pd.DataFrame): 包含股票历史数据的DataFrame，需包含列'日期'和'收盘'。
        end_date (str, optional): 截止日期，格式为'yyyy-mm-dd'。默认为None，表示不限制截止日期。
        threshold (int, optional): 最近指定天数，用于判断股票是否创新高。默认为60。
    
    Returns:
        bool: 若股票在最近指定天数内创新高，则返回True；否则返回False。
    
    """
    if code_name[0] not in settings.top_list:
        return False    
    max_price = 0
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    if data is None:
        return False
    data = data.tail(n=threshold)
    if len(data) < threshold:
        return False
    for index, row in data.iterrows():
        if row['收盘'] > max_price:
            max_price = float(row['收盘'])

    last_close = data.iloc[-1]['收盘']

    if last_close >= max_price:
        return True

    return False
