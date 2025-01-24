"""高低线构造,画图,均线使用了移动平均线和高斯平滑"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from tool import tools
from scipy.ndimage import gaussian_filter1d


def high_low(data, MA1, MA2, N, List=False):
    # 计算不同周期的移动平均线
    # 计算小区间和大区间的变化，并将其转换为1和-1表示
    # 处理小区间和大区间的噪声，填充缺失值
    # 根据小区间的变化确定高低点，并返回相应的数据
    ma1 = data['close'].rolling(window=MA1).mean().values
    ma2 = data['close'].rolling(window=MA2).mean().values

    # ma1 = gaussian_filter1d(data['close'], sigma=1)
    # ma2 = gaussian_filter1d(data['close'], sigma=3)
    small_interval = ma1 - ma2
    small_interval = np.where(np.isnan(small_interval), small_interval, np.sign(small_interval))
    # small_interval = np.array(tools().replace_noise_with_previous(list(small_interval), N))
    small_interval[np.isnan(small_interval)] = 0
    small_interval_date = np.where(np.diff(small_interval) != 0)[0] + 1
    ha, h1 = [], np.full(len(data), np.nan)
    la, l1 = [], np.full(len(data), np.nan)
    if len(small_interval_date) > 2:
        sid = small_interval_date
        for i in range(0, len(sid)):
            if i != len(sid) - 1:
                if small_interval[sid[0]] == 1:
                    if i % 2 == 0:
                        h1[sid[i]:sid[i + 1]] = max(data['high'][sid[i]:sid[i + 1]])
                        ha.append(max(data['high'][sid[i]:sid[i + 1]]))
                    else:
                        h1[sid[i]:sid[i + 1]] = ha[-1]
                else:
                    if i % 2 == 0:
                        if ha:
                            h1[sid[i]:sid[i + 1]] = ha[-1]
                    else:
                        h1[sid[i]:sid[i + 1]] = max(data['high'][sid[i]:sid[i + 1]])
                        ha.append(max(data['high'][sid[i]:sid[i + 1]]))
            else:
                h1[sid[i]:len(data)] = ha[-1]
        for i in range(0, len(sid)):
            if i != len(sid) - 1:
                if small_interval[sid[0]] == -1:
                    if i % 2 == 0:
                        l1[sid[i]:sid[i + 1]] = min(data['low'][sid[i]:sid[i + 1]])
                        la.append(min(data['low'][sid[i]:sid[i + 1]]))
                    else:
                        l1[sid[i]:sid[i + 1]] = la[-1]
                else:
                    if i % 2 == 0:
                        if la:
                            l1[sid[i]:sid[i + 1]] = la[-1]
                    else:
                        l1[sid[i]:sid[i + 1]] = min(data['low'][sid[i]:sid[i + 1]])
                        la.append(l1[sid[i]])
            else:
                l1[sid[i]:len(data)] = la[-1]
    if List:
        if small_interval[-1] == 1:
            h_date = small_interval_date[-2]
            l_date = small_interval_date[-1]
        else:
            h_date = small_interval_date[-1]
            l_date = small_interval_date[-2]
        return (h1[-1], l1[-1], h_date, l_date)

    else:
        return ma1, ma2, h1, l1
        # return h1, l1

    # big_interval = np.where(np.isnan(big_interval), big_interval, np.sign(big_interval))
    # big_interval = np.array(tools().replace_noise_with_previous(list(big_interval), MA2))
    # big_interval[np.isnan(big_interval)] = 0
    # big_interval_date = np.where(np.diff(big_interval) != 0)[0] + 1

data = pd.read_csv('rb.csv')[500:]
data = data.reset_index(drop=True)
ma1, ma2, h_new_data, l_new_data = high_low(data, 5, 10, 3)
data.columns = data.columns.str.lower()

# 创建图形和轴
# 绘制K线图需要的数据格式：(index, open, high, low, close)
# 绘制K线图
# 设置x轴的刻度格式为索引值
# 添加h_new_data和l_new_data的数据点
# 添加ma均线
# 添加标签和标题
# 显示网格
# 添加图例
# 调整子图参数以防止裁剪标签
# 显示图形
fig, ax = plt.subplots(figsize=(14, 7))
ohlc_data = list(zip(data.index, data['open'], data['high'], data['low'], data['close']))
candlestick_ohlc(ax, ohlc_data,
                 width=0.6, colorup='green', colordown='red')
ax.set_xticks(data.index)
ax.set_xticklabels(data.index, rotation=45)
ax.plot(range(0, len(h_new_data)), h_new_data, label='H Data', markersize=2, linestyle='-', marker='o', color='blue')
ax.plot(range(0, len(l_new_data)), l_new_data, label='L Data', markersize=2, linestyle='-', marker='x', color='orange')
ax.plot(range(len(ma1)), ma1, label='MA1', linestyle='-', color='purple', linewidth=1)
ax.plot(range(len(ma2)), ma2, label='MA2', linestyle='-', color='blue', linewidth=1)
ax.set_xlabel('Index')
ax.set_ylabel('Price')
ax.set_title('K-line Chart with H and L Data')
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.show()

