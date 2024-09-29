import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

# 创建示例数据
data = {
    'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
    'close': [100, 102, 101, 105, 110],
}
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])  # 转换日期格式
df.set_index('date', inplace=True)  # 设置日期为索引

# 计算简单移动平均线（SMA）
df['SMA_10'] = ta.sma(df['close'], length=2)

# 计算指数移动平均线（EMA）
df['EMA_10'] = ta.ema(df['close'], length=2)

print(df)


# 绘制收盘价
df['close'].plot(label='Close Price')

# 绘制SMA
df['SMA_10'].plot(label='SMA 10', linestyle='--')

# 绘制EMA
df['EMA_10'].plot(label='EMA 10', linestyle='-.')

# 添加图例
plt.legend()