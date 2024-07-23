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
import os
import pandas_ta as ta

# ==================      三角旗型突破策略     ======================
#
# 1、两市剔除ST股、剔除科创板股、剔除北交所股
# 2、9.25分按集合竞价金额降序排序，选出开盘金额最大前20只股
# 3、选出市值低于300亿的个股
# 4、剔除近20日没有涨停的股
# 5、选出前三日股价上升的个股
# 6、选出今日高开的个股
# 7、判定个股是否为近日的热点板块概念股
# 8、9.35分买入一笔
# 9、9.35分股价大于分时均线，继续买入一笔
# 10、若是快速秒板则涨停板上继续买入。
# ===================================================================


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
                "content": f'## <font color="comment">回测-甘州图灵932甄选策略{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()
# def load_all_stack_info_df():
#     global all_skocks_info_df
#     all_skocks_info_df = pd.read_csv('all_skocks_info.csv',dtype={'代码': 'str'})
    
def load_all_stack_info_df():
    global all_skocks_info_df
    all_skocks_info_df = ak.stock_zh_a_spot_em()
    return all_skocks_info_df  
  
def symbol_info(symbol):
    info = all_skocks_info_df[all_skocks_info_df['代码'] == symbol].iloc[0]
    return info

def is_trading_time():
    from datetime import datetime, time
    now = datetime.now()
    work_start_1 = time(9, 32)
    work_end_1 = time(11, 32)
    work_start_2 = time(13, 0)
    work_end_2 = time(14, 55)

    # 判断是否为工作日（周一到周五）
    if now.weekday() < 5:  # 0是周一，4是周五
        # 判断当前时间是否在上班时间内
        if work_start_1 <= now.time() <= work_end_1:
            return True
        if work_start_2 <= now.time() <= work_end_2:
            return True  # 下午不交易
    return False
def build_markdown_msg(stocks_df):

    columns = stocks_df.columns.tolist()
    # title = " ".join(columns) # ['代码','股票简称','热度排名', '开盘2分钟涨幅','最新涨跌幅','最新价']
    title = "代码 简称 开盘2分钟涨幅\n  热度 最新涨幅 最新价"
    
    markdown_df = stocks_df.apply(
        lambda x: f'[{x[0]} {x[1]} {x[5]:.2f}%](https://www.iwencai.com/unifiedwap/result?w={x[0]}&querytype=stock)'
        + f'\n  <font color="warning">{x[2]:.0f} {x[7]:.2f}%</font> {x[6]:.2f}'
        , axis=1)
    # markdown_df = stocks_df.apply(
    #     lambda x: f'[{x[0]} {x[1]} {x[2]:.0f}](https://www.iwencai.com/unifiedwap/result?w={x[0]}&querytype=stock)  {x[3]:.2f}'
    #     + f'\n  {x[4]:.2f} {x[5]:.2f}%'
    #     # + f'\n <font color="warning">{x[4]:.2f} {x[5]:.2f}%</font>'
    #     + f' {x[6]:.2f} {x[7]:.2f}%'
    #     , axis=1)
    markdown_df = markdown_df.astype(str)
    stocks_list = markdown_df.tolist()
    return f"\n{title}\n"+"\n".join(stocks_list)

def trading_detail_before(symbol:str):
  df = ak.stock_zh_a_hist_pre_min_em(symbol=symbol, start_time="09:00:00", end_time="09:32:00")
  roc = round(((df.iloc[-1]['收盘'] - df.iloc[-3]['开盘']) / df.iloc[-3]['开盘']) * 100,3)
  volume_times =True #( df.iloc[-2]['成交量'] / df.iloc[-7]['成交量'] )> 2
  #   volume_times_32 = ( df.iloc[-1]['成交量'] / df.iloc[-2]['成交量'] )> 0.75
  volume_times_32 = ( df.iloc[-1]['最高'] > df.iloc[-3]['最高'] ) and ( df.iloc[-1]['最低'] > df.iloc[-2]['最低'] )
  price_gt_3 = df.iloc[-1]['最新价'] > 3
  volume_gt_2000 = (df.iloc[-7]['最新价']<10 and df.iloc[-7]['成交量'] > 2500) or(df.iloc[-7]['最新价']>=10 and df.iloc[-7]['成交量'] > 2000)
  return (volume_times and volume_times_32 and price_gt_3 and volume_gt_2000 ,
          roc,
          df.iloc[-3]['开盘'], 
          df.iloc[-7]['成交量'],
          df.iloc[-7]['最新价'],
          df.iloc[-2]['开盘'],
          df.iloc[-2]['收盘'],
          df.iloc[-2]['最高'],
          df.iloc[-2]['最低'],
          df.iloc[-2]['成交量'],
          df.iloc[-2]['最新价'],
          df.iloc[-1]['开盘'],
          df.iloc[-1]['收盘'],
          df.iloc[-1]['最高'],
          df.iloc[-1]['最低'],
          df.iloc[-1]['成交量'],
          df.iloc[-1]['最新价'])
def trading_detail_before_bak(symbol:str):
  df = ak.stock_zh_a_hist_pre_min_em(symbol=symbol, start_time="09:00:00", end_time="09:32:00")
  volume_times =True #( df.iloc[-2]['成交量'] / df.iloc[-7]['成交量'] )> 2
  volume_times_32 = ( df.iloc[-1]['成交量'] / df.iloc[-2]['成交量'] )> 0.75
  price_times =( df.iloc[-1]['最新价'] / df.iloc[-7]['最新价'] )>1.000
  price_gt_3 = df.iloc[-1]['最新价'] > 3
  volume_gt_2000 = (df.iloc[-7]['最新价']<10 and df.iloc[-7]['成交量'] > 1000) or(df.iloc[-7]['最新价']>=10 and df.iloc[-7]['成交量'] > 2000)
  return (volume_times and price_times and volume_times_32 and price_gt_3 and volume_gt_2000 ,
          df.iloc[-3]['开盘'], 
          df.iloc[-7]['成交量'],
          df.iloc[-7]['最新价'],
          df.iloc[-2]['开盘'],
          df.iloc[-2]['收盘'],
          df.iloc[-2]['最高'],
          df.iloc[-2]['最低'],
          df.iloc[-2]['成交量'],
          df.iloc[-2]['最新价'],
          df.iloc[-1]['开盘'],
          df.iloc[-1]['收盘'],
          df.iloc[-1]['最高'],
          df.iloc[-1]['最低'],
          df.iloc[-1]['成交量'],
          df.iloc[-1]['最新价'])
  
def get_today_ohlc(symbol):
    thirty_days_ago = datetime.today() - timedelta(days=30) # 确保可以计算出最后一天的5日均价、十日均价、20日均价
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=thirty_days_ago.strftime('%Y%m%d'))
    df['昨天开盘'] = df['开盘'].shift(1)
    df['昨天最高'] = df['最高'].shift(1)
    df['昨天最低'] = df['最低'].shift(1)
    df['昨天收盘'] = df['收盘'].shift(1)
    df['昨天成交量'] = df['成交量'].shift(1)
    df['昨天涨跌幅'] = df['涨跌幅'].shift(1)
    df['昨天换手率'] = df['换手率'].shift(1)
    
    df['前天成交量'] = df['成交量'].shift(2)
    df['前天涨跌幅'] = df['涨跌幅'].shift(2)
    df['前天换手率'] = df['换手率'].shift(2)
    
    df['5日均价'] = df['收盘'].rolling(window=5).mean().fillna(method='ffill')    
    df['10日均价'] = df['收盘'].rolling(window=10).mean().fillna(method='ffill')    
    df['5日均价'] = df['5日均价'].round(2)      
    df['10日均价'] = df['10日均价'].round(2)      
      
    df['5日均量'] = df['成交量'].rolling(window=5).mean().fillna(method='ffill')    
    df['10日均量'] = df['成交量'].rolling(window=10).mean().fillna(method='ffill')    
    df['5日均量'] = df['5日均量'].round(0)      
    df['10日均量'] = df['10日均量'].round(0)      
     
    df['5日均换'] = df['换手率'].rolling(window=5).mean().fillna(method='ffill')    
    df['10日均换'] = df['换手率'].rolling(window=10).mean().fillna(method='ffill')    
    df['5日均换'] = df['5日均换'].round(2)      
    df['10日均换'] = df['10日均换'].round(2) 
    
    df_ta=ta_ind(symbol) 
    df['ROC_X_CMF'] = df_ta.iloc[-1]['ROC_X_CMF']
    df['CMF_GT_0'] = df_ta.iloc[-1]['CMF_GT_0']
 
    return df.iloc[-1]

last_save_time = None
def update_today_final_data():
    directory_path = './results'        
    file_name = f"""甘州图灵甄选932_{datetime.now().strftime('%Y%m%d')}.csv"""
    file_path = os.path.join(directory_path, file_name)    
    df = pd.read_csv(file_path,dtype={'代码': 'str'})
    today_trading_data = df['代码'].apply(get_today_ohlc)
    df = df.assign(**today_trading_data)   # df = pd.concat([df, today_trading_data], axis=1)
    df['当日浮盈'] = round(100 * (df['收盘'] - df['close32']) / df['close32'],2)
    df.sort_values(by='当日浮盈', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['浮盈排名'] = df.index + 1
    file_name = f"""甘州图灵甄选932_{datetime.now().strftime('%Y%m%d_%H-%M')}_full.csv"""
    file_path = os.path.join(directory_path, file_name)   
    df.to_csv(file_path, index=False, encoding='utf_8_sig')
    
def ta_ind(symbol:str):
  df = ak.stock_zh_a_hist_pre_min_em(symbol=symbol, start_time="09:00:00", end_time="09:32:00")

  df['时间'] = pd.to_datetime(df['时间'])
  df = df.set_index('时间',drop=True)
  df.ta.roc(close='收盘',volume='成交量', length=1,append=True)
  df.ta.cmf(open="开盘",high="最高",low="最低",close='收盘',volume='成交量', length=1,append=True)
  df.ta.obv(close='收盘',volume='成交量', length=1,append=True)
  df['ROC']=df['ROC_1'] # - df['ROC_1'].shift(1)
  df['CMF']=df['CMF_1'] #- df['CMF_1'].shift(1)
  df['CMF_GT_0']=df['CMF'] >= 0
  df['OBV_DIR']=df['OBV'] / abs(df['OBV']) 
  # df['ROC_2'] - df['ROC_2'].shift(1)
  # df['ROC_X_CMF']=df['ROC'] * df['CMF'] * df['OBV_DIR'] 
  df['ROC_X_CMF']=df['ROC'] * df['CMF'] 
  # df.ta.vwap(open="开盘",high="最高",low="最低",close='收盘',price="最新价",volume='成交量', length=1,append=True)
  # df.ta.rsi(open="开盘",high="最高",low="最低",close='收盘',volume='成交量', length=1,append=True)
  return df
    

def get_top_30_deal_volume_stocks(pbar=None,dev=False):
    from datetime import datetime, time
    if dev or is_trading_time():
        df = ak.stock_zh_a_spot_em()
        try:
          # 个股热度前300名
          # query = f"个股热度前200名"
          # df = pywencai.get(query=query, query_type="stock",loop=True)
          
          directory_path = './results'        
          # file_name = f"""甘州图灵甄选932_{datetime.now().strftime('%Y%m%d')}.csv"""
          file_name = f"""甘州图灵甄选932_20240712.csv"""
          file_path = os.path.join(directory_path, file_name)    
          df = pd.read_csv(file_path,dtype={'代码': 'str'})
          today_trading_data = df['代码'].apply(get_today_ohlc)
          df = df.assign(**today_trading_data)   # df = pd.concat([df, today_trading_data], axis=1)
  
          df['最新价'] = df['最新价'].astype('float64')
          df['最新涨跌幅'] = df['最新涨跌幅'].astype('float64')
          
          df["总市值"]=df['代码'].apply(lambda symbol: symbol_info(symbol)['总市值'])
          df["60日涨跌幅"]=df['代码'].apply(lambda symbol: symbol_info(symbol)['60日涨跌幅'])

          df['总市值大于800亿'] = df['总市值'].astype(float) < 800 * 10000 * 10000
          df = df.where(df['总市值大于800亿'], np.nan).dropna(
              subset=['总市值大于800亿'])  
                  
          df['60日涨跌幅大于0'] = df['60日涨跌幅'].astype(float) > 0
          df = df.where(df['60日涨跌幅大于0'], np.nan).dropna(
              subset=['60日涨跌幅大于0']) 
                  
          # df['60日涨跌幅不大'] = np.all(df['60日涨跌幅'].astype(float) < 50 ,df['CMF_GT_0'].astype(float) > 0)
          # df['60日涨跌幅不大'] =df['60日涨跌幅'].astype(float) < 35
          # df['60日涨跌幅不大'] =((df['60日涨跌幅'].astype(float) < 35) & 
          #                 (df['OBV_DIR'].astype(float) > 0))
          df['60日涨跌幅不大'] =df['OBV_DIR'].astype(float) > 0
          df = df.where(df['60日涨跌幅不大'], np.nan).dropna(
              subset=['60日涨跌幅不大'])          

          df['最大可能涨幅'] = df['代码'].apply(lambda code: 20 if str(code).startswith('3') else 10) 
          
          df['涨跌幅大于-3'] = df['最新涨跌幅'].astype(float) > -8
          df = df.where(df['涨跌幅大于-3'], np.nan).dropna(
              subset=['涨跌幅大于-3'])
          
          df['最大当日浮盈大于3'] = (df['最大可能涨幅'] - df['最新涨跌幅']).astype(float) >= 0
          df = df.where(df['最大当日浮盈大于3'], np.nan).dropna(
              subset=['最大当日浮盈大于3'])
          df['trading_detail_before'] = df['代码'].apply(trading_detail_before)
          df['upup'] = df['trading_detail_before'].map(lambda x: x[0])

          df['roc'] = df['trading_detail_before'].map(lambda x: x[-16])
   
          df = df.where(df['upup'], np.nan).dropna(
              subset=['upup'])                    

          df['当日浮盈'] = round(100 * (df['收盘'] - df['close32']) / df['close32'],2)
          df.sort_values(by='当日浮盈', ascending=False, inplace=True)
          df.reset_index(drop=True, inplace=True)
          df['浮盈排名'] = df.index + 1
          
          # df.sort_values(by=['最大可能涨幅','roc'], ascending=[False,False], inplace=True)
          # print(df)
          df.sort_values(by=['CMF_GT_0','ROC_X_CMF'], ascending=[False,False], inplace=True)
          print(df)
          
          directory_path = './results'
          if not os.path.exists(directory_path):
            os.makedirs(directory_path)          
          file_name = f"""甘州图灵甄选932_{datetime.now().strftime('%Y%m%d')}_backtest.csv"""
          file_path = os.path.join(directory_path, file_name)
          df_save = df[['代码','股票简称','热度排名','开盘', '开盘2分钟价格','开盘2分钟涨幅','最新价','最新涨跌幅',
                            'open30',
                            'volume25',
                            'price25',
                            'open31',
                            'close31',
                            'high31',
                            'low31',
                            'volume31',
                            'price31',
                            'open32',
                            'close32',
                            'high32',
                            'low32',
                            'volume32',
                            'price32',
                            '最大可能涨幅',
                            'roc',
                            '当日浮盈',
                            '浮盈排名'                           
                                                 
                         ]]
          df_save['热度排名'] = df_save['热度排名'].astype(int)
          df_save.to_csv(file_path, index=False, encoding='utf_8_sig')
          print(f'文件已保存: {file_path}')       

               
          selected_stocks = df[['代码','股票简称','热度排名','开盘', '开盘2分钟价格','开盘2分钟涨幅','收盘','涨跌幅']]
          if len(selected_stocks) < 1:
              return
          # print(selected_stocks)
          msg = build_markdown_msg(selected_stocks.head(26))
          keys = [
              # '88aa58e5-818a-471d-8786-84ee85984467',
              'e312ad13-1f18-430b-9c66-304922694dc3'
          ]
          for key in keys:
              webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
              wecom = WeCom(webhook_url)
              response = wecom.send_message(msg)
              print(response,f"""消息长度:{len(msg)},甄选股数:{len(selected_stocks)}""")
              
          update_today_final_data()    
        except Exception as e:
            print(repr(e), df)

    if pbar:
        seconds_to_target = 2 * 60
        pbar.reset(seconds_to_target)


def next_exec_seconds(hour=9, minute=41):
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, hour, minute)
    if now >= target_time:
        target_time += timedelta(days=1)
    time_difference = target_time - now
    seconds_to_target = round(time_difference.total_seconds())
    return seconds_to_target


if __name__ == '__main__':
    load_all_stack_info_df() #加载全部股票基本数据到全局变量all_stack_info_df中
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true',
                        help='Set dev mode to true')
    args = parser.parse_args()

    if args.dev:
        get_top_30_deal_volume_stocks(dev = True)
        # update_today_final_data()
    else:
        hour = 9
        minute = 41
        seconds_to_target = next_exec_seconds(hour, minute)
        seconds_to_target = 2 * 60
        pbar = tqdm(range(seconds_to_target), desc='正在等待任务执行...',
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

        # EXEC_TIME = f"{'0' + str(hour) if hour < 10 else str(hour)}:{minute}"
        # schedule.every().day.at(EXEC_TIME).do(
        #     lambda: get_top_30_deal_volume_stocks(pbar))
        schedule.every(2).minutes.do(
            lambda: get_top_30_deal_volume_stocks(pbar))
        # if is_trading_time():        
        #     schedule.every(10).minutes.do(
        #         lambda: update_today_final_data())
        while True:
            schedule.run_pending()
            time.sleep(1)
            pbar.update(1)  # 手动更新进度条
