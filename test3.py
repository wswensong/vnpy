import json

import pandas as pd
import re
import akshare as ak
from scipy.ndimage import gaussian_filter1d
from settings import VARIETY_EN
from sqlite_module import SQLiteModule

def get_monthly_data(df):
    result_df = pd.DataFrame(columns=df.columns)

    for year in df['date'].dt.year.unique():
        for month in df[df['date'].dt.year == year]['date'].dt.month.unique():
            # 过滤出当前年份和月份的数据
            monthly_df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

            # 尝试获取12日的数据
            target_date = pd.Timestamp(year=year, month=month, day=12)
            if target_date in monthly_df['date'].values:
                result_df = pd.concat([result_df, monthly_df[monthly_df['date'] == target_date]])
            else:
                # 如果12日没有数据，则获取12日后的第一条数据
                after_target_date_df = monthly_df[monthly_df['date'] > target_date].sort_values(by='date')
                if not after_target_date_df.empty:
                    result_df = pd.concat([result_df, after_target_date_df.head(1)])

    return result_df.reset_index(drop=True)


# ppi_df = ak.macro_china_ppi_yearly()
# # ppi_df['日期'] = ppi_df['日期'] // 1000
# ppi_df['日期'] = pd.to_datetime(ppi_df['日期'])
# ppi_df = ppi_df[['日期', '今值']]
# ppi_df = ppi_df.rename(columns={'日期': 'date', '今值': 'ppi'})
# ppi_df['date'] = ppi_df['date'].dt.strftime('%Y-%m')
#
# cpi_df = ak.macro_china_cpi_yearly()
# # cpi_df['日期'] = cpi_df['日期'] // 1000
# cpi_df['日期'] = pd.to_datetime(cpi_df['日期'])
# cpi_df = cpi_df[['日期', '今值']]
# cpi_df = cpi_df.rename(columns={'日期': 'date', '今值': 'cpi'})
# cpi_df['date'] = cpi_df['date'].dt.strftime('%Y-%m')
#
# ppi_cpi = pd.merge(ppi_df, cpi_df, on='date', how='outer')
# ppi_cpi = ppi_cpi.dropna()
# ppi_cpi['price'] = ppi_cpi['ppi'] - ppi_cpi['cpi']
#
# # 高斯滤波平滑
# ppi_cpi['ppigaussian'] = gaussian_filter1d(ppi_cpi['ppi'], sigma=1)
# ppi_cpi['cpigaussian'] = gaussian_filter1d(ppi_cpi['cpi'], sigma=1)
# ppi_cpi['pricegaussian'] = gaussian_filter1d(ppi_cpi['price'], sigma=1)
db_manager = SQLiteModule('wsuong.db')
#
# a = db_manager.query_cond('ppicpi', condition='date > "2024-11-01"')
# a = db_manager.query_cond('corr', condition='commodity = "RB"')
# print(a)
# 创建表
# db_manager.create_table('state', [
#     ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
#     ('commodity', 'TEXT NOT NULL'),
#     ('operate', 'TEXT NOT NULL'),
#     ('th', 'INTEGER NOT NULL'),
# ])
# db_manager.insert_bulk_data('ppicpi', ppi_cpi)

# ppi_cpi =db_manager.fetch_data_to_df('ppicpi')
#
# db_manager.create_table('corr', [
#     ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
#     ('commodity', 'TEXT NOT NULL'),
#     ('ppi', 'REAL NOT NULL'),
#     ('cpi', 'REAL NOT NULL'),
#     ('price', 'REAL NOT NULL'),
# ])



# corr = {}
# for i in VARIETY_EN:
#     name = re.sub(r'\d+', '', i)
#     quotes_data = ak.futures_zh_daily_sina(symbol=f'{name}0')
#     quotes_data['date'] = pd.to_datetime(quotes_data['date'])
#     quotes_data_month = get_monthly_data(quotes_data)
#     quotes_data_month = quotes_data_month[['date', 'close']]
#     quotes_data_month['date'] = quotes_data_month['date'].dt.strftime('%Y-%m')
#     merged_df = pd.merge(ppi_cpi, quotes_data_month, on='date', how='outer')
#     merged_df = merged_df.dropna()
#     ppi_x = merged_df['ppigaussian'].corr(merged_df['close'])
#     cpi_x = merged_df['cpigaussian'].corr(merged_df['close'])
#     price_x = merged_df['pricegaussian'].corr(merged_df['close'])
#     # corr[f'{name}'] = {'ppi': ppi_x, 'cpi': cpi_x, 'price': price_x}
#     db_manager.insert_data('corr', ['commodity', 'ppi', 'cpi', 'price'], [f'{name}', ppi_x, cpi_x, price_x])
#     a = db_manager.fetch_data_to_df('corr')
#     print(a)
# db_manager.close()
# 打开setting.json写入数据
# try:
#     with open('setting.json', 'r', encoding='utf-8') as f:
#         data = json.load(f)
# except FileNotFoundError:
#     data = {}
#
# # 更新或添加 "corr" 键
# data["corr"] = corr
#
# # 写入更新后的内容到文件，指定编码为 utf-8
# with open('setting.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, ensure_ascii=False)



    # 高斯滤波平滑
    # sigma = 1
    # y_gaussian = gaussian_filter1d(merged_df['ppi'], sigma=sigma)

# if new_h > original_h and close_arr[-1] > (new_h - new_l) * golden_ratio[i[0]] + h:
#     self.sell(close_arr[-1], 1)
#     self.sqlite_update_data('state', frequency, {}, 1)
#     operate = True
# elif new_h < original_h and h - (new_h - new_l) * golden_ratio[i[0]] < close_arr[-1] < (new_h - new_l) * golden_ratio[
#     i[0]] + h:
#     self.sqlite_update_data('state', frequency,
#                             {'oap': oap, 'original_trend': new_trend, 'original_h': new_h,
#                              'original_l': new_l,
#                              'original_h_date': new_h_date, 'original_l_date': new_l_date,
#                              'take_profit_price': (new_h - new_l) * golden_ratio[i[0]] + h,
#                              'stop_price': h - (new_h - new_l) * golden_ratio[i[0]]}, 1)



