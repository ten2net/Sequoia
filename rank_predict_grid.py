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
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

# 假设df是包含股票交易数据的DataFrame

# 选择特征列和目标列
feature_columns = [
    '开盘'	,'开盘2分钟价格'	,'开盘2分钟涨幅',
    'open30', 'price25', 'volume25', 'close31', 'high31', 'low31', 'volume31', 'price31',
    'close32', 'high32', 'low32', 'volume32', 'price32', '昨天开盘', '昨天最高', '昨天最低',
    '昨天收盘', '昨天成交量', '昨天涨跌幅', '昨天换手率'
    # , '前天成交量', '前天涨跌幅', '前天换手率',
    # '5日均价', '10日均价', '5日均量', '10日均量', '5日均换', '10日均换'
]

directory_path = './results'        
file_name = f"""甘州图灵甄选932_{datetime.now().strftime('%Y%m%d')}_15-06_full.csv"""
file_path = os.path.join(directory_path, file_name)    
df = pd.read_csv(file_path,dtype={'代码': 'str'})
# 首先，剔除包含NaN的行
df = df.dropna(subset=feature_columns)
X = df[feature_columns]

# print(X)
y = df['浮盈排名']

# 数据分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# 定义模型
rf = RandomForestRegressor(random_state=42)

# 定义要搜索的参数网格
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['auto', 'sqrt', 0.5, 0.3],
    'bootstrap': [True, False],
    'criterion': ['mse', 'mae']
}

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['auto', 'sqrt', 0.5, 0.3],
    'bootstrap': [True, False],
    'criterion': ['squared_error', 'absolute_error', 'friedman_mse', 'poisson']  # 正确的参数值
}

# 创建网格搜索对象
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, n_jobs=-1, scoring='neg_mean_squared_error')

# 假设X_train和y_train是训练数据和目标变量
grid_search.fit(X_train, y_train)

# 打印最佳参数和最佳模型的均方误差
print("最佳参数:", grid_search.best_params_)
print("最佳模型的均方误差:", -grid_search.best_score_)

# 使用最佳参数的模型
best_rf = grid_search.best_estimator_

# # 特征缩放
# scaler = StandardScaler()
# X_train_scaled = scaler.fit_transform(X_train)
# X_test_scaled = scaler.transform(X_test)

# # 模型训练
# model = RandomForestRegressor(n_estimators=100, random_state=88)
# model.fit(X_train_scaled, y_train)

# # 模型评估
# predictions = model.predict(X_test_scaled)
# mse = mean_squared_error(y_test, predictions)
# print(f"Mean Squared Error: {mse}")
# # print(predictions)

# # print (X_test)
# # print (y_test)
# # 将预测结果添加到DataFrame中
# X_test['RANK'] =y_test
# X_test['Predicted_RANK'] = predictions 

# # 显示结果
# print(X_test[['RANK', 'Predicted_RANK']])