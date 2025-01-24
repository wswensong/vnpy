# market_data.py
import pandas as pd
import akshare as ak
import re
from settings import VARIETY

def get_main_contract(variety):
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


def process_contracts(contract_list, trend):
    """
    处理合约数据，计算移动平均线和高低点。

    :param contract_list: 合约列表
    :return: 结果字典
    """

    def calculate_ma(df, window, trend_internal):
        """
        计算移动平均线及其变化趋势。

        :param df: 数据框
        :param window: 移动平均窗口大小
        """
        df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
        df[f'ma_{window}_diff'] = df[f'ma_{window}'].diff()
        df[f'ma_{window}'] = df[f'ma_{window}_diff'].apply(
            lambda x: 1 if x > 0 else (trend_internal if x == 0 else -1)
        )
        df.drop(columns=[f'ma_{window}_diff'], inplace=True)

    def high_low(data, ma_name, n):
        """
        计算移动平均线的变化高低点。

        :param data: 数据框
        :param ma_name: 移动平均线名称
        :param n: 计算高低点的窗口大小
        :return: 高低点列表
        """
        change_indices = data[ma_name].ne(data[ma_name].shift()).to_numpy().nonzero()[0]
        if len(change_indices) < 3:
            return {}

        ma_name_first_value = data[ma_name].iloc[0]
        a = {}

        if ma_name_first_value == 1:
            a['ma_name'] = ma_name
            a['trend'] = 1
            a['low'] = data['low'].iloc[change_indices[1]:change_indices[1] + n].min()
            a['high'] = data['high'].iloc[change_indices[2]:change_indices[2] + n].max()
            a['low_date'] = data.loc[data['low'].iloc[change_indices[1]:change_indices[1] + n].idxmin(), 'date']
            a['high_date'] = data.loc[data['high'].iloc[change_indices[2]:change_indices[2] + n].idxmax(), 'date']
        elif ma_name_first_value == -1:
            a['ma_name'] = ma_name
            a['trend'] = -1
            a['high'] = data['high'].iloc[change_indices[1]:change_indices[1] + n].max()
            a['low'] = data['low'].iloc[change_indices[2]:change_indices[2] + n].min()
            a['low_date'] = data.loc[data['low'].iloc[change_indices[2]:change_indices[2] + n].idxmin(), 'date']
            a['high_date'] = data.loc[data['high'].iloc[change_indices[1]:change_indices[1] + n].idxmax(), 'date']

        return a

    results = {}
    for symbol in contract_list:
        try:
            temp_df = ak.futures_zh_daily_sina(symbol=symbol)
            selected_columns = temp_df.copy()
            temp_df['date'] = pd.to_datetime(temp_df['date'])
            temp_df.set_index('date', inplace=True)

            if len(selected_columns) < 40:
                print(f"Insufficient data for {symbol}, skipping.")
                continue
            print(selected_columns)
            calculate_ma(selected_columns, 10, trend)
            calculate_ma(selected_columns, 20, trend)
            calculate_ma(selected_columns, 40, trend)

            selected_columns_ = selected_columns.iloc[::-1].reset_index(drop=True)

            hl_10 = high_low(selected_columns_, 'ma_10', 10)
            hl_20 = high_low(selected_columns_, 'ma_20', 20)
            hl_40 = high_low(selected_columns_, 'ma_40', 40)
            hl = pd.DataFrame([hl_10, hl_20, hl_40])
            results[symbol] = {
                'data': temp_df,
                'hl': hl
            }
        except Exception as e:
            print(f"Error processing data for {symbol}: {e}")

    return results


# 示例调用
if __name__ == "__main__":
    main_contract = get_main_contract(VARIETY)
    print("Main Contracts:", main_contract)

    # results = process_contracts(main_contract, TREND)
    # print("Results:", results)
