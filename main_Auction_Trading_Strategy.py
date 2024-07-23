import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
from termcolor import colored
import argparse
import pywencai
import math
import pandas_ta as ta
import em_favor_api as em

# ==================      封神榜策略 （中小市值的集合竞价策略）      ======================
# 
# 修改了集合竞价的选股策略，让该策略在每天9点和14点的26,32,35,40,45,50,55,59分16个时间点执行（原来是只在9.26执行）。

# 该策略池的主要选股条件：

# 1、两市剔除ST股、剔除科创板股、剔除北交所股
# 2、从9.25分集合竞价结束后，按成交金额降序排序，选出开盘金额最大前50只股
# 3、选出总市值在30~700亿的个股
# 4、剔除近20日没有涨停的股
# 5、选出前三日股价上升不大的个股（昨天的收盘价大于4天前的开盘价,并且前三日涨幅小于20%
# 6、选出上个交易日当日浮盈不大且支撑强（小实体或长下影）且昨天上影线大于下影线但未显著放量（遇到阻力但抛压不重，视为洗盘蓄势）
# 7、选出今日没有大幅低开（>-3.0 %）的个股
# 8、判定个股是否为近日的热点板块概念股
# 9、9.25分挂单往上价格笼子顶的价位买入一笔
# 10、9.35分股价大于分时均线，继续买入一笔
# 11、若是9.25分买入时候没成交，需要撤单后在9.30分另外买入，若是快速秒板则不需要等到9.35分继续买入。

# =========================================================================================

# 开盘10分钟内大单净额/流通市值排名前20

class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        import requests
        import datetime

        now = datetime.datetime.now()
        formatted_now = now.strftime("%m月%d日 %H:%M")
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="comment">甘州图灵竞价封神榜{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()
def cta_strategy(df):
    # 总市值小于700亿
    df = df.where(df['market_cap'] < 700, np.nan).dropna(subset=['market_cap'])
    # 总市值大于30亿
    df = df.where(df['market_cap'] > 30, np.nan).dropna(subset=['market_cap'])
    # 近20日有涨停
    df = df.where(df['has_zt_in_20d'], np.nan).dropna(subset=['has_zt_in_20d'])
    # 前三日股价上升的个股（昨天的收盘价大于4天前的开盘价,并且前三日涨幅小于20%）
    df['last_3_high'] = (df['close_price'] > df['last_open_4']) & ((df['close_price'] - df['last_open_4'])/df['last_open_4'] < 0.20)
    df = df.where(df['last_3_high'], np.nan).dropna(
        subset=['last_3_high'])
    # 头一天小实体或长下影
    df['最大可能涨幅'] = df['code'].apply(lambda code: 20 if str(code).startswith('3') else 10)
    df['min_oc'] = df[['last_open', 'close_price']].min(axis=1)
    df['max_oc'] = df[['last_open', 'close_price']].max(axis=1)
    df['body'] = df['max_oc'] - df['min_oc']
    df['down_body'] = df['min_oc'] - df['last_low']
    df['up_body'] = df['last_high'] - df['max_oc']
    
    df['short_body'] = (df['body'] / df['min_oc'] < df['最大可能涨幅'] / 250 ) | ( df['down_body'] > 0.8 * df['body'] )
    df = df.where(df['short_body'], np.nan).dropna(
        subset=['short_body'])
    # 昨天上影线大于下影线但未显著放量（遇到阻力但抛压不重，视为洗盘蓄势）
    df['short_up_line'] = (df['up_body'] >  df['down_body']) & (df['last_volume'] /  df['last_volume_2'] <1.3)
    df = df.where(df['short_up_line'], np.nan).dropna(
        subset=['short_up_line'])
    # 昨天收盘价低于今日开盘价（今日高开）
    df['today_open_high'] = df['open_price'] > 0.6 * df['close_price']
    df = df.where(df['today_open_high'], np.nan).dropna(
        subset=['today_open_high'])
    print(df)
    # 是否是热点股票
    df = df.where(df['is_hot_stock'], np.nan).dropna(subset=['is_hot_stock'])
    # 计算集合竞价涨幅后，按涨幅从大到小排序
    df["涨幅"] = round(
        100 * (df["open_price"] - df["close_price"]) / df["close_price"], 2)
    df = df[["code", "name", "close_price", "open_price", "涨幅","最大可能涨幅","today_pct","today_close","slope","last_pct"]]
    df['强度'] = (df['最大可能涨幅'] - df['today_pct'])
    # df.sort_values(by=['最大可能涨幅','强度'], ascending=[False,False], inplace=True)
    df.sort_values(by=['强度'], ascending=[False], inplace=True)
    
    return df

# 定义获取股票数据的函数


def get_stock_data(stock_code):
    start_date = datetime.now() - timedelta(days=30)
    start_date_str = start_date.strftime('%Y%m%d')
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_code, start_date=start_date_str, adjust='')
    today_pct = stock_zh_a_hist_df.iloc[-1]['涨跌幅']
    today_close = stock_zh_a_hist_df.iloc[-1]['收盘']
    # 获取前一日的收盘价和今日的开盘价
    # print(stock_code,stock_zh_a_hist_df)
    last_open = stock_zh_a_hist_df.iloc[-1]['收盘']
    last_close = stock_zh_a_hist_df.iloc[-1]['开盘']
    last_pct = stock_zh_a_hist_df.iloc[-1]['涨跌幅']
    last_high = stock_zh_a_hist_df.iloc[-1]['最高']
    last_low = stock_zh_a_hist_df.iloc[-1]['最低']    
    today_open = stock_zh_a_hist_df.iloc[-1]['开盘']
    last_open_4 = stock_zh_a_hist_df.iloc[-1]['开盘']
    last_volume = stock_zh_a_hist_df.iloc[-1]['成交量']
    last_volume_2 = stock_zh_a_hist_df.iloc[-1]['成交量']
    
    
    if len(stock_zh_a_hist_df) > 4:  # 非新股特殊处理
        last_open = stock_zh_a_hist_df.iloc[-2]['开盘']
        last_close = stock_zh_a_hist_df.iloc[-2]['收盘']
        last_pct = stock_zh_a_hist_df.iloc[-2]['涨跌幅']
        last_high = stock_zh_a_hist_df.iloc[-2]['最高']
        last_low = stock_zh_a_hist_df.iloc[-2]['最低']
        today_open = stock_zh_a_hist_df.iloc[-1]['开盘']
        # 获取前三日的开盘价
        last_open_4 = stock_zh_a_hist_df.iloc[-4]['开盘']
        last_volume = stock_zh_a_hist_df.iloc[-2]['成交量']
        last_volume_2 = stock_zh_a_hist_df.iloc[-3]['成交量']

    # 检查股票是否在近20日有过涨停
    stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期'])
    stock_zh_a_hist_df.sort_values(by='日期', ascending=True, inplace=True)
    recent_20_days_df = stock_zh_a_hist_df.tail(20)
    has_zt_in_20d = (recent_20_days_df['涨跌幅'] >= 9.9).any()
    
    # recent_20_days_df['SLOPE'] = ta.slope(close=recent_20_days_df.收盘, length=3)
    stock_zh_a_hist_df['SLOPE'] = ta.slope(close=stock_zh_a_hist_df.收盘, length=3).apply(math.degrees)
    slope =  stock_zh_a_hist_df.iloc[-1]['SLOPE']    

    # 获取总市值和行业
    stock_info = ak.stock_individual_info_em(symbol=stock_code)
    print(stock_info.iloc[0])
    total_mv = stock_info.iloc[0]['value'] / (10000 * 10000)  # 总市值
    industry = stock_info.iloc[2]['value']  # 行业
    stock_name = stock_info.iloc[5]['value']  # 股票简称

    # item          value
    # 0   总市值  55740263855.5
    # 1  流通市值  55740263855.5
    # 2    行业            半导体
    # 3  上市时间       20030603
    # 4  股票代码         600584
    # 5  股票简称           长电科技
    # 6   总股本   1789414570.0
    # 7   流通股   1789414570.0

    is_hot_stock = True  # 假设是热点股票

    return {
        'code': stock_code,
        'name': stock_name,
        'market_cap': total_mv,
        'has_zt_in_20d': has_zt_in_20d,
        'last_open': last_open,
        'last_high': last_high,
        'last_low': last_low,
        'close_price': last_close,
        'open_price': today_open,
        'last_open_4': last_open_4,
        'is_hot_stock': is_hot_stock,
        'today_pct':today_pct,
        'today_close':today_close,
        'slope':slope,
        'last_pct':last_pct,
        'last_volume':last_volume,
        'last_volume_2':last_volume_2,
        
    }

last_ganzhou_index = None
def build_markdown_msg(stocks_df,ganzhou_index):
    global last_ganzhou_index
    ganzhou_index_direct=""
    if last_ganzhou_index is None:
        last_ganzhou_index = ganzhou_index
    else:
        ganzhou_index_direct = "↑" if ganzhou_index > last_ganzhou_index else "↓"
    last_ganzhou_index = ganzhou_index
    ganzhou_index_title =f'情绪指数：{ganzhou_index} {ganzhou_index_direct}'
    title = "代码 简称 \n 昨收 昨天涨幅\n 今开 开盘涨幅\n 最新价 最新涨幅"   
    stocks_df['markdown'] = stocks_df[['code', 'close_price', 'open_price', '涨幅', 'name','today_close','today_pct','last_pct']].apply(
        lambda x: f"""[{x[0]} {x[4]}](https://www.iwencai.com/unifiedwap/result?w={x[0]}&querytype=stock)"""
        + f"\n {x[1]:.2f}  {x[7]:.2f}%"
        + '\n <font color="info">' + f"{x[2]:.2f}  {x[3]:.2f}%" + '</font>'
        + '\n <font color="warning">' + f"{x[5]:.2f}  {x[6]:.2f}%" + '</font>', axis=1)

    # stocks_df['markdown'] = stocks_df['markdown'] #.astype(str)
    stocks_list = stocks_df['markdown'].tolist()
    # return "\n".join(stocks_list)
    return f"\n* 情绪指数(0~1)越大，出票越多\n  {ganzhou_index_title}\n\n\n{title}\n"+"\n".join(stocks_list)

def get_top_30_deal_volume_stocks(pbar=None):
    stock_zh_a_spot_df = ak.stock_zh_a_spot_em()
    # 两市剔除ST股、剔除科创板股、剔除北交所股
    stock_zh_a_spot_df = stock_zh_a_spot_df[~stock_zh_a_spot_df['代码'].astype(
        str).str.startswith('4')]
    stock_zh_a_spot_df = stock_zh_a_spot_df[~stock_zh_a_spot_df['代码'].astype(
        str).str.startswith('8')]
    stock_zh_a_spot_df = stock_zh_a_spot_df[~stock_zh_a_spot_df['代码'].astype(
        str).str.startswith('68')]
    stock_zh_a_spot_df = stock_zh_a_spot_df[~stock_zh_a_spot_df['名称'].astype(
        str).str.startswith('N')]
    # 按集合竞价金额降序排序，选出开盘金额最大前50只股
    stock_zh_a_spot_df_sorted = stock_zh_a_spot_df.sort_values(
        by='成交额', ascending=False)
    top_20_stocks = stock_zh_a_spot_df_sorted.head(50)
    stock_codes = top_20_stocks['代码'].to_list()
    data = [get_stock_data(code) for code in stock_codes]

    # 运行策略函数
    df = pd.DataFrame(data)
    selected_stocks = cta_strategy(df)
    if len(selected_stocks)<1:
        return
    ganzhou_index  = round(len(selected_stocks) / 25,3)  # 甘州指数
    # 添加到东方财富自选股
    results = selected_stocks.head(10).copy() 
    results =  results['code'].to_list()  
    symbol_list =  results[::-1]  #确保新加自选的在上面
    em.update_em_favor_list(symbol_list,group_full_name="封神全榜",group_new_name="封神最新") 
    # 发送企业微信消息
    msg = build_markdown_msg(selected_stocks.head(10).copy(),ganzhou_index)
    keys = [
        # '88aa58e5-818a-471d-8786-84ee85984467',
        'e312ad13-1f18-430b-9c66-304922694dc3',
        '1c491e27-508d-478c-947d-75a752433138'
    ]
    for key in keys:
        webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
        wecom = WeCom(webhook_url)
        response = wecom.send_message(msg)
    if pbar:    
        seconds_to_target = next_exec_seconds(hour=9,minute=26)        
        pbar.reset(seconds_to_target)

def next_exec_seconds(hour=9,minute=26):
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, hour, minute)
    if now >= target_time:
        target_time += timedelta(days=1)
    time_difference = target_time - now
    seconds_to_target = round(time_difference.total_seconds())
    return seconds_to_target

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true', help='Set dev mode to true')
    args = parser.parse_args()
    
    if args.dev:
        get_top_30_deal_volume_stocks()
    else:
        houres = [9,14]
        minutes = [26,32,33,35,40,45,50,55,59]
        pbar_list =[]
        for hour in houres:            
            for minute in minutes:            
                seconds_to_target = next_exec_seconds(hour,minute)  
                
                pbar = tqdm(range(seconds_to_target), desc=f'正在等待{hour}:{minute}任务执行...',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

                EXEC_TIME = f"{'0' + str(hour) if hour < 10 else str(hour)}:{minute}"
                schedule.every().day.at(EXEC_TIME).do(
                    lambda: get_top_30_deal_volume_stocks(pbar))
                pbar_list.append(pbar)
        while True:
            schedule.run_pending()
            time.sleep(1)
            for pbar in pbar_list:
                pbar.update(1)  # 手动更新进度条

