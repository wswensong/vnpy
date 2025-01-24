import akshare as ak
import pandas as pd
import json
import re
from settings import VARIETY, VARIETY_EN


def calculate_sharpness(arr, indices):
    """
    计算给定数组在指定索引位置的尖锐程度。

    本函数通过计算每个指定索引位置前后两点的斜率变化来评估该位置的尖锐程度。
    这对于检测数据中的突变或峰值很有用。

    参数:
    arr: 一个数字数组，可以是任何支持索引和长度属性的序列。
    indices: 一个包含需要计算尖锐程度的索引列表。

    返回:
    一个浮点数列表，表示每个索引位置的尖锐程度。如果索引位置不满足计算条件，则返回0。
    """
    sharpness = []
    for index in indices:
        # 检查索引是否在有效范围内，以避免边界效应导致的计算错误
        if index > 1 and index < len(arr) - 2:
            # 使用前两个和后两个点来计算斜率变化
            slope_before = (arr[index] - arr[index - 2]) / 2
            slope_after = (arr[index + 2] - arr[index]) / 2
            # 将计算出的尖锐程度的绝对值添加到结果列表中
            sharpness.append(abs(slope_before - slope_after))
        else:
            # 对于边界情况，无法计算尖锐程度，返回0
            sharpness.append(0)
    return sharpness


def get_main_contract(variety: VARIETY):
    """
    获取指定品种的主力合约列表。

    :param variety: 品种列表
    :return: 主力合约列表
    """
    main_contract = []  # 主力合约列表
    for symbol in variety:
        try:
            futures_zh_realtime_df = ak.futures_zh_realtime(symbol=symbol)

            # 删除 'name' 列没有数字字符的行
            futures_zh_realtime_df = futures_zh_realtime_df[
                futures_zh_realtime_df['name'].str.contains(r'\d')
            ]

            # 按 'position' 列降序排序
            sorted_df = futures_zh_realtime_df.sort_values(by='position', ascending=False)

            # 获取 'position' 列中数值排名第1和第2的两列
            top_two_positions = sorted_df.head(2).copy()

            # 提取 'name' 列中的数字部分
            top_two_positions['name_numeric'] = top_two_positions['name'].apply(
                lambda name: int(re.findall(r'\d+', name)[0]) if re.findall(r'\d+', name) else 0
                )

            # 选择 'name_numeric' 最大的那一列
            selected_row = top_two_positions.loc[top_two_positions['name_numeric'].idxmax()]

            # 获取选中的行数据
            main_contract.append(selected_row['symbol'])
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    return main_contract  # 输出品种的主力合约编码

def get_monthly_data(df):
    """

   参数:
    df (pd.DataFrame): 包含日期列('date')的数据框。行情历史数据.

    返回:
   pd.DataFrame: 包含每月提取数据的结果数据框。
    """
    # 初始化一个空的数据框，用于存储结果，列名与输入数据框相同
    result_df = pd.DataFrame(columns=df.columns)

    # 遍历数据框中的每一年
    for year in df['date'].dt.year.unique():
        # 遍历每个月
        for month in range(1, 13):
            # 尝试获取12日的数据
            target_date = pd.Timestamp(year=year, month=month, day=12)
            if target_date in df['date'].values:
                # 如果12日有数据，则将该数据添加到结果数据框中
                result_df = pd.concat([result_df, df[df['date'] == target_date]])
            else:
                # 如果12日没有数据，则获取12日后的第一条数据
                after_target_date_df = df[df['date'] > target_date].sort_values(by='date')
                if not after_target_date_df.empty:
                    # 将12日后第一条数据添加到结果数据框中
                    result_df = pd.concat([result_df, after_target_date_df.head(1)])

    # 返回结果数据框，并重置索引
    return result_df.reset_index(drop=True)


def ppi_cpi_close_corr(ppi_cpi):
    """
    计算并存储每个品种的PPI、CPI和价格与收盘价的相关性。

    参数:
    ppi_cpi - 包含PPI、CPI和价格数据的DataFrame，其索引为日期。

    返回值:
    无直接返回值，但会将计算得到的相关性数据写入'setting.json'文件。
    """
    # 初始化一个空字典来存储相关性数据
    corr = {}

    # 遍历每个品种代码
    for i in VARIETY_EN:
        # 移除品种代码中的数字，获取品种名称
        name = re.sub(r'\d+', '', i)

        # 获取指定品种的期货日报数据
        quotes_data = ak.futures_zh_daily_sina(symbol=f'{name}0')
        # 将日期列转换为datetime类型
        quotes_data['date'] = pd.to_datetime(quotes_data['date'])

        # 将日报数据转换为月报数据，并仅保留日期和收盘价两列
        quotes_data_month = get_monthly_data(quotes_data)
        quotes_data_month = quotes_data_month[['date', 'close']]
        # 将日期列格式化为'YYYY-MM'格式
        quotes_data_month['date'] = quotes_data_month['date'].dt.strftime('%Y-%m')

        # 将PPI、CPI和价格数据与期货收盘价数据按日期进行外连接
        merged_df = pd.merge(ppi_cpi, quotes_data_month, on='date', how='outer')
        # 删除包含NaN的数据行
        merged_df = merged_df.dropna()

        # 计算PPI、CPI和价格与收盘价之间的相关性
        ppi_x = merged_df['PpiGaussian'].corr(merged_df['close'])
        cpi_x = merged_df['CpiGaussian'].corr(merged_df['close'])
        price_x = merged_df['PriceGaussian'].corr(merged_df['close'])

        # 将相关性数据存储到字典中
        corr[f'{name}'] = {'ppi': ppi_x, 'cpi': cpi_x, 'price': price_x}



