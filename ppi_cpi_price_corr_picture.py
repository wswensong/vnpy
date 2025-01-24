"""商品价格与ppi,cpi相关性的可视化"""
import pandas as pd
from sqlite_module import SQLiteModule
import matplotlib.pyplot as plt
import akshare as ak

def get_monthly_data(df):
    """
    从给定的数据框中提取每月特定日期（优先12日）或之后最近日期的数据。

    参数:
    df (pd.DataFrame): 包含日期列('date')的数据框。行情历史数据.

    返回:
    pd.DataFrame: 包含每月提取数据的结果数据框。
    """
    # 初始化一个空的数据框，用于存储结果，列名与输入数据框相同
    df['date'] = pd.to_datetime(df['date'])
    result_df = pd.DataFrame(columns=df.columns)

    # 遍历数据框中的每一年
    for year in df['date'].dt.year.unique():
        # 遍历当前年份中的每个月
        for month in df[df['date'].dt.year == year]['date'].dt.month.unique():
            # 过滤出当前年份和月份的数据
            monthly_df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

            # 尝试获取12日的数据
            target_date = pd.Timestamp(year=year, month=month, day=12)
            if target_date in monthly_df['date'].values:
                # 如果12日有数据，则将该数据添加到结果数据框中
                row_to_add = monthly_df[monthly_df['date'] == target_date].copy()
                row_to_add['date'] = row_to_add['date'].dt.strftime('%Y-%m')
                result_df = pd.concat([result_df, row_to_add])
            else:
                # 如果12日没有数据，则获取12日后的第一条数据
                after_target_date_df = monthly_df[monthly_df['date'] > target_date].sort_values(by='date')
                if not after_target_date_df.empty:
                    # 将12日后第一条数据添加到结果数据框中，并格式化日期
                    row_to_add = after_target_date_df.head(1).copy()
                    row_to_add['date'] = row_to_add['date'].dt.strftime('%Y-%m')
                    result_df = pd.concat([result_df, row_to_add])

    # 重置索引并返回结果数据框
    result_df.reset_index(drop=True, inplace=True)
    return result_df

# 示例使用
data = ak.futures_zh_daily_sina(symbol='RU0')
data = data.reset_index(drop=True)
data = get_monthly_data(data)
data_close = data[['date', 'close']]
data_close.rename(columns={'date': 'date'}, inplace=True)
db_module = SQLiteModule('wsuong.db')
ppicpi = db_module.fetch_data_to_df('ppicpi')
# 按照'date'把data和ppicpi合并
data = pd.merge(data_close, ppicpi, on='date')
# date   close   id  ppi  ...  price  ppigaussian  cpigaussian  pricegaussian
dates = data['date']
close = data['close']
ppi = data['ppi']
ppigaussia = data['ppigaussian']

fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:red'
ax1.set_xlabel('Date')
ax1.set_ylabel('Close', color=color)
ax1.plot(dates, close, color=color, linestyle='-', label='Close')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('PPI', color=color)  # we already handled the x-label with ax1
ax2.plot(dates, ppi, color=color, linestyle='--', label='PPI')
ax2.tick_params(axis='y', labelcolor=color)

ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))  # offset the third y-axis to the right

color = 'tab:green'
ax3.set_ylabel('PPIGaussian', color=color)  # we already handled the x-label with ax1
ax3.plot(dates, ppigaussia, color=color, linestyle=':', label='PPIGaussian')
ax3.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped

# 添加网格
ax1.grid(True)

# 显示图形
plt.title('Stock Price and Indicators Over Time')
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.show()





