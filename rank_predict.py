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
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from joblib import dump, load
import pickle

# 假设df是包含股票交易数据的DataFrame

# 选择特征列
feature_columns = [
    '开盘'	,'开盘2分钟价格'	,'开盘2分钟涨幅',
    # 'open30', 
    'price25', 'volume25', 
    'close31', 'high31', 'low31', 'volume31', 'price31',
    'close32', 'high32', 'low32', 'volume32', 'price32', 
    '昨天开盘', '昨天最高', '昨天最低',
    '昨天收盘', '昨天成交量', '昨天涨跌幅', '昨天换手率'
    , '前天成交量', '前天涨跌幅', '前天换手率',
    '5日均价', '10日均价', '5日均量', '10日均量', '5日均换', '10日均换'
]

directory_path = './results'        
file_name = f"""甘州图灵甄选932_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}_15-12_full.csv"""
file_path = os.path.join(directory_path, file_name)    
df1 = pd.read_csv(file_path,dtype={'代码': 'str'})

file_name = f"""甘州图灵甄选932_{(datetime.now() - timedelta(days=2)).strftime('%Y%m%d')}_15-06_full.csv"""
file_path = os.path.join(directory_path, file_name)    
df2 = pd.read_csv(file_path,dtype={'代码': 'str'})

file_name = f"""甘州图灵甄选932_{(datetime.now() - timedelta(days=0)).strftime('%Y%m%d')}_11-30_full.csv"""
file_path = os.path.join(directory_path, file_name)    
df2 = pd.read_csv(file_path,dtype={'代码': 'str'})

df = pd.concat([df1, df2], ignore_index=True)
df = df.sample(frac=1).reset_index(drop=True) 
# 首先，剔除包含NaN的行
df = df.dropna(subset=feature_columns)
X = df[feature_columns]

# print(X)
y = df['浮盈排名']

# 数据分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
# print (X_train,y_train)
# print (X_test,y_test)
# 特征缩放
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 模型训练
model = RandomForestRegressor(n_estimators=200,
                              max_depth=10,
                              max_features=0.8,
                              criterion='absolute_error',
                            #   min_samples_leaf=1,
                            #   min_samples_split=2,
                              bootstrap=False,
                              random_state=88)
model.fit(X_train_scaled, y_train)

directory_path = './models'
if not os.path.exists(directory_path):
    os.makedirs(directory_path)          
dump(model, f'{directory_path}/甘州图灵932_model.joblib')
dump(scaler, f'{directory_path}/甘州图灵932_scaler.joblib')

# 保存模型
with open(f'{directory_path}/甘州图灵932_model.pkl', 'wb') as file:
    pickle.dump(model, file)
with open(f'{directory_path}/甘州图灵932_scaler.pkl', 'wb') as file:
    pickle.dump(scaler, file)

# 模型评估
predictions = model.predict(X_test_scaled)
mse = mean_squared_error(y_test, predictions)
print(f"Mean Squared Error: {mse}")
# print(predictions)

# print (X_test)
# print (y_test)
# 将预测结果添加到DataFrame中
X_test['RANK'] =y_test
X_test['Predicted_RANK'] = predictions 

# 显示结果
print(X_test[['RANK', 'Predicted_RANK']])

print("=" * 30)

directory_path = './results' 
file_name = f"""甘州图灵甄选932_{(datetime.now() - timedelta(days=2)).strftime('%Y%m%d')}_14-50_full.csv"""
file_path = os.path.join(directory_path, file_name)    
# 首先，剔除包含NaN的行
df14_50_source = pd.read_csv(file_path,dtype={'代码': 'str'})

df14_50 = df14_50_source.dropna(subset=feature_columns)

X = df14_50[feature_columns]

data = scaler.transform(X)
predictions = model.predict(data)

df14_50['预测排名'] = predictions 
df14_50['预测排名'] = df14_50['预测排名'].round().astype('int64')
print(df14_50[:49])
print(df14_50[49:])

directory_path = './results'
if not os.path.exists(directory_path):
    os.makedirs(directory_path)          
file_name = f"""甘州图灵甄选932_{(datetime.now() - timedelta(days=2)).strftime('%Y%m%d')}_14-50_full_with_predict.csv"""
file_path = os.path.join(directory_path, file_name)

df14_50.to_csv(file_path, index=False, encoding='utf-8')





