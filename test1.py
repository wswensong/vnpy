import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
import matplotlib.pyplot as plt

# 假设我们有一个CSV文件包含期货价格数据
data = pd.read_csv('rb.csv')
# 提取收盘价并重塑为二维数组
prices = data['close'].values.reshape(-1, 1)

# 数据标准化，将特征缩放至0-1之间
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_prices = scaler.fit_transform(prices)

# 创建训练集和测试集，使用80%的数据作为训练集
train_size = int(len(scaled_prices) * 0.8)
test_size = len(scaled_prices) - train_size
train_data, test_data = scaled_prices[0:train_size,:], scaled_prices[train_size:len(scaled_prices),:]

def create_dataset(dataset, time_step=1):
    """
    创建数据集，将时间序列数据转换为监督学习问题

    参数:
    dataset: 输入的数据集
    time_step: 时间步长，默认为1

    返回:
    X: 特征数据集
    Y: 目标数据集
    """
    X, Y = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]
        X.append(a)
        Y.append(dataset[i + time_step, 0])
    return np.array(X), np.array(Y)

# 定义时间步长
time_step = 60
X_train, y_train = create_dataset(train_data, time_step)
X_test, y_test = create_dataset(test_data, time_step)

# 将输入重塑为 [samples, time steps, features] 的格式
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# 构建LSTM模型
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(time_step, 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=1))

# 编译模型，使用Adam优化器和均方误差损失函数
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型，使用20%的数据作为验证集
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=100, batch_size=32, verbose=1)

# 进行预测
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# 反归一化，将预测值和真实值转换回原始范围
train_predict = scaler.inverse_transform(train_predict)
test_predict = scaler.inverse_transform(test_predict)
y_train = scaler.inverse_transform([y_train])
y_test = scaler.inverse_transform([y_test])

# 绘制结果，显示测试集上的实际价格和预测价格
plt.figure(figsize=(14,5))
plt.plot(y_test[0], label='Actual Futures Price')
plt.plot(test_predict, label='Predicted Futures Price')
plt.title('Futures Price Prediction using LSTM with Grid')
plt.xlabel('Time')
plt.ylabel('Price')
plt.legend()
plt.grid(True)  # 加入网格
plt.show()
