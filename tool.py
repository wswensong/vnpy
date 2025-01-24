import akshare as ak
import pandas as pd
import numpy as np
import json
import re

from settings import VARIETY, VARIETY_EN

class tools():
    
        
    def calculate_sharpness(self, arr, indices):
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


    def get_main_contract(self, variety: VARIETY):
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

    def get_monthly_data(self, df):
        """
        从给定的数据框中提取每月特定日期（优先12日）或之后最近日期的数据。

        参数:
        df (pd.DataFrame): 包含日期列('date')的数据框。行情历史数据.

        返回:
        pd.DataFrame: 包含每月提取数据的结果数据框。
        """
        # 初始化一个空的数据框，用于存储结果，列名与输入数据框相同
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
                    result_df = pd.concat([result_df, monthly_df[monthly_df['date'] == target_date]])
                else:
                    # 如果12日没有数据，则获取12日后的第一条数据
                    after_target_date_df = monthly_df[monthly_df['date'] > target_date].sort_values(by='date')
                    if not after_target_date_df.empty:
                        # 将12日后第一条数据添加到结果数据框中
                        result_df = pd.concat([result_df, after_target_date_df.head(1)])

        # 返回结果数据框，并重置索引
        return result_df.reset_index(drop=True)

    def ppi_cpi_close_corr(self, ppi_cpi):
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
            quotes_data_month = self.get_monthly_data(quotes_data)
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

        # 尝试读取'setting.json'文件中的现有数据
        try:
            with open('setting.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，则初始化一个空字典
            data = {}

        # 更新或添加 "corr" 键
        data["corr"] = corr

        # 写入更新后的内容到文件，指定编码为 utf-8
        with open('setting.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)


    def json_write(self, filename: str, cls: str, key: str, value: dict):
        # 步骤1：读取现有的JSON数据
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 步骤2：修改或添加数据
        # 假设data是一个字典，并且我们想要添加一个新的键值对
        new_entry = {cls: {key: value}}  # 新的键值对，例如{"new_key": "new_value"}}
        data.update(new_entry)  # 如果data是字典
        # 或者如果是列表，可以使用append方法添加新元素
        # data.append(new_entry)  # 如果data是列表

        # 步骤3：写入更新后的数据
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False)


    def sqlite_insert_data(self, condition_value: list):
        """
        在指定数据库表中插入数据的函数.

        参数:
        condition_value: 一个包含要插入数据的条件值的列表.
        """
        table_name = 'state'
        # 插入数据到指定表的操作
        set_columns_values = ['commodity', 'one', 'two', 'three']
        # 将条件值序列化为JSON格式
        condition_value = [json.dumps(i) for i in condition_value]
        self.db_manager.insert_data(table_name, set_columns_values, condition_value)
        
        
    def sqlite_update_data(self, name, listing, Value, condition_value):
            self.db_manager.update_data(
            table_name=name,
            set_columns_values={listing:Value},
            condition_column="id",
            condition_value=condition_value
        )

    def replace_noise_with_previous(self, data, threshold):
        # 替换低于阈值的噪声数据为前一个有效值
        if not data or threshold <= 0:
            return []

        cleaned_data = []
        current_value = data[0]
        count = 1

        for i, value in enumerate(data[1:], start=1):
            if value == current_value:
                count += 1
            else:
                if count < threshold:
                    prev_value = cleaned_data[-1] if cleaned_data else current_value
                    cleaned_data.extend([prev_value] * count)
                else:
                    cleaned_data.extend([current_value] * count)
                current_value = value
                count = 1

        if count < threshold:
            prev_value = cleaned_data[-1] if cleaned_data else current_value
            cleaned_data.extend([prev_value] * count)
        else:
            cleaned_data.extend([current_value] * count)

        return cleaned_data

    def construct_array_low(self, input_array, reference_df):
        """
        根据给定的规则构建数组 b:
        - 如果 input_array[i] 是 NaN，则 b[i] 也是 NaN。
        - 如果 input_array[i] 是 -1，则找到对应的 reference_df 中的最小值，并将该区间最后一个位置设为这个最小值，其他位置设为 0。
        - 如果 input_array[i] 是 1，则从 b[i-1] 复制值，如果 b 为空则从 reference_df 中获取当前值。

        参数:
        input_array (np.array): 输入数组 a。
        reference_df (pd.DataFrame): 包含值的参考数据框。

        返回:
        np.array: 构建的数组 b。
        """
        # 初始化数组 b
        output_array = []

        # 遍历输入数组并根据规则填充输出数组
        index = 0
        while index < len(input_array):
            if np.isnan(input_array[index]):
                output_array.append(np.nan)
            elif input_array[index] == -1:
                start_index = index
                while index < len(input_array) and input_array[index] == -1:
                    index += 1
                min_value = reference_df[start_index:index].min()
                output_array.extend([0] * (index - start_index))
                output_array[-1] = min_value
                continue
            elif input_array[index] == 1:
                if output_array:  # 确保 output_array 不为空
                    output_array.append(output_array[-1])
                else:
                    output_array.append(reference_df[index])  # 如果 output_array 为空，则添加当前值
            index += 1

        # 将列表转换为 numpy 数组
        output_array = np.array(output_array)

        return output_array