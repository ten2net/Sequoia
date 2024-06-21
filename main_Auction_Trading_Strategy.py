import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
from termcolor import colored

# ==================      集合竞价策略 （游资合力股的集合竞价策略）      ======================
# 
# 1、两市剔除ST股、剔除科创板股、剔除北交所股
# 2、9.25分按集合竞价金额降序排序，选出开盘金额最大前20只股
# 3、选出市值低于300亿的个股
# 4、剔除近20日没有涨停的股
# 5、选出前三日股价上升的个股
# 6、选出今日高开的个股
# 7、判定个股是否为近日的热点板块概念股
# 8、9.25分挂单往上价格笼子顶的价位买入一笔
# 9、9.35分股价大于分时均线，继续买入一笔
# 10、若是9.25分买入时候没成交，需要撤单后在9.30分另外买入，若是快速秒板则不需要等到9.35分继续买入。
# =========================================================================================

class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        import requests
        import datetime

        now = datetime.datetime.now()
        formatted_now = now.strftime("%m月%d日")
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="comment">甘州图灵竞价策略{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()


def cta_strategy(df):
    # 市值小于300亿
    df = df.where(df['market_cap'] < 300, np.nan).dropna(subset=['market_cap'])

    # 近20日有涨停
    df = df.where(df['has_zt_in_20d'], np.nan).dropna(subset=['has_zt_in_20d'])
    
    # 前三日股价上升的个股（昨天的收盘价大于4天前的开盘价）
    df['last_3_high'] = df['close_price'] > df['last_open_4']
    df = df.where(df['last_3_high'], np.nan).dropna(
        subset=['last_3_high'])
    
    # 昨天收盘价低于今日开盘价（今日高开）
    df['today_open_high'] = df['open_price'] > df['close_price']
    df = df.where(df['today_open_high'], np.nan).dropna(
        subset=['today_open_high'])

    # 是否是热点股票
    df = df.where(df['is_hot_stock'], np.nan).dropna(subset=['is_hot_stock'])
    # 计算集合竞价涨幅后，按涨幅从大到小排序
    df["涨幅"] = round(
        100 * (df["open_price"] - df["close_price"]) / df["close_price"], 2)
    df = df[["code", "name", "close_price", "open_price", "涨幅"]]
    df.sort_values(by='涨幅', ascending=False, inplace=True)
    
    return df

# 定义获取股票数据的函数


def get_stock_data(stock_code):
    start_date = datetime.now() - timedelta(days=30)
    start_date_str = start_date.strftime('%Y%m%d')
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_code, start_date=start_date_str, adjust='')
    # 获取前一日的收盘价和今日的开盘价
    last_close = stock_zh_a_hist_df.iloc[-2]['收盘']
    today_open = stock_zh_a_hist_df.iloc[-1]['开盘']
    # 获取前三日的开盘价
    last_open_4 = stock_zh_a_hist_df.iloc[-4]['开盘']

    # 检查股票是否在近20日有过涨停
    stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期'])
    stock_zh_a_hist_df.sort_values(by='日期', ascending=False, inplace=True)
    recent_20_days_df = stock_zh_a_hist_df.head(20)
    has_zt_in_20d = (recent_20_days_df['涨跌幅'] >= 9.9).any()

    # 获取总市值和行业
    stock_info = ak.stock_individual_info_em(symbol=stock_code)
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
        'close_price': last_close,
        'open_price': today_open,
        'last_open_4': last_open_4,
        'is_hot_stock': is_hot_stock
    }


def build_markdown_msg(stocks_df):
    stocks_df['markdown'] = stocks_df[['code', 'close_price', 'open_price', '涨幅', 'name']].apply(
        lambda x: f"""[{x[0]} {x[4]}](https://www.iwencai.com/unifiedwap/result?w={x[0]}&querytype=stock)"""
        + ' <font color="warning">' + f"{x[1]:.2f}" + '</font>'
        + ' <font color="comment">' + f"{x[2]:.2f}" + '</font>'
        + f" {x[3]:.2f}", axis=1)

    stocks_df['markdown'] = stocks_df['markdown'].astype(str)
    stocks_list = stocks_df['markdown'].tolist()
    return "\n".join(stocks_list)

def get_top_30_deal_volume_stocks(pbar):
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

    stock_zh_a_spot_df_sorted = stock_zh_a_spot_df.sort_values(
        by='成交额', ascending=False)
    top_30_stocks = stock_zh_a_spot_df_sorted.head(30)
    stock_codes = top_30_stocks['代码'].to_list()
    data = [get_stock_data(code) for code in stock_codes]

    # 运行策略函数
    df = pd.DataFrame(data)
    selected_stocks = cta_strategy(df)
    # print(selected_stocks)

    msg = build_markdown_msg(selected_stocks)
    keys = [
        '88aa58e5-818a-471d-8786-84ee85984467',
        'e312ad13-1f18-430b-9c66-304922694dc3'
    ]
    for key in keys:
        webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
        wecom = WeCom(webhook_url)
        response = wecom.send_message(msg)
        
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
    hour = 9
    minute = 26
    seconds_to_target = next_exec_seconds(hour,minute)  
    # print(seconds_to_target)
    
    pbar = tqdm(range(seconds_to_target), desc='正在等待任务执行...',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

    EXEC_TIME = f"{'0' + str(hour) if hour < 10 else str(hour)}:{minute}"
    schedule.every().day.at(EXEC_TIME).do(
        lambda: get_top_30_deal_volume_stocks(pbar))
    # schedule.every(3).minutes.do(
    #     lambda: get_top_30_deal_volume_stocks())
    while True:
        schedule.run_pending()
        time.sleep(1)
        pbar.update(1)  # 手动更新进度条

    # get_top_30_deal_volume_stocks()
