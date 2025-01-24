import numpy as np
from datetime import time
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval
from tool import tools
import pandas as pd
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import akshare as ak
import re
import json



class ws_strategy(CtaTemplate):
    author = "Your Name"

    # 参数列表
    ma1: int = 10
    ma2: int = 20
    ma3: int = 40

    # 变量列表
    trend: int = 1

    parameters = ["ma1", "ma2", "ma3"]
    variables = ["trend"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(
            self.on_bar,
            window=1,
            interval=Interval.DAILY,
            daily_end=time(hour=22, minute=59)
        )
        self.am = ArrayManager(self.ma3 * 3)
        self.vt_symbol = vt_symbol
        self.tools = tools()
    def on_init(self):
        """初始化策略（必须由用户继承实现）"""
        self.write_log("初始化策略")
        self.load_bar(self.ma3)  # 加载历史数据用于初始化

    def on_start(self):
        """启动策略（必须由用户继承实现）"""
        self.write_log("启动策略")

    def on_stop(self):
        """停止策略（必须由用户继承实现）"""
        self.tools.db_manager.close()
        self.write_log("停止策略")

    def on_tick(self, tick: TickData):
        """收到行情tick推送（必须由用户继承实现）"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """收到Bar推送（必须由用户继承实现）"""
        self.cancel_all()

        # 更新BarGenerator和ArrayManager
        self.bg.update_bar(bar)
        self.am.update_bar(bar)

        # self.tools.db_manager.create_table('state', [
        #     ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
        #     ('commodity', 'TEXT NOT NULL'),
        #     ('one', 'TEXT NOT NULL'),
        #     ('two', 'TEXT NOT NULL'),
        #     ('three', 'TEXT NOT NULL'),
        # ])

        # 检查ArrayManager是否已初始化，若未初始化则返回
        if not self.am.inited:
            return
        # 构建数据字典并转换为DataFrame
        data = {
            'datetime': pd.to_datetime(self.am.datetime_array, unit='D', origin='1970-01-01'),
            'open': self.am.open_array,
            'high': self.am.high_array,
            'low': self.am.low_array,
            'close': self.am.close_array,
            'volume': self.am.volume_array,
            'turnover': self.am.turnover_array
        }
        selected_columns = pd.DataFrame(data).set_index('datetime')

        # 计算高低价位
        hl = self.high_low(selected_columns, self.ma1, self.ma2, self.ma3)

        # 提取商品符号
        symbol = re.sub(r'\d+', '', self.vt_symbol).split('.')[0].upper()

        try:
            # 查询数据库中的最新记录
            db_hl = self.tools.db_manager.query_cond('hl', f'commodity = "{symbol}"')[-1]

            if hl:
                h, l, h_date, l_date = hl
                self.tools.db_manager.update_data(
                    table_name="hl",
                    set_columns_values={"h": h, "l": l, "h_date": h_date, "l_date": l_date},
                    condition_column="id",
                    condition_value=db_hl[0]
                )
            else:
                h, l, h_date, l_date = db_hl[2], db_hl[3], db_hl[4], db_hl[5]
        except IndexError:
            if hl:
                h, l, h_date, l_date = hl
                self.tools.db_manager.insert_data('hl', ['commodity', 'h', 'l', 'h_date', 'l_date'],
                                            (symbol, h, l, h_date, l_date))
            else:
                print('数据库为空, hl未输出数据')
                return

        # 获取相关性最高的指标
        gaussian_db = self.tools.db_manager.query_cond('corr', f'commodity = "{symbol}"')[-1][2:]
        gaussian_db_ = max(gaussian_db)

        if gaussian_db_ > 0.4:
            gaussian_name = ['ppi', 'cpi', 'price'][list(gaussian_db).index(gaussian_db_)]
        else:
            return
        # 获取当前月份和前一个月的数据
        current_date = selected_columns.index[-1].strftime('%Y-%m')
        previous_month = (pd.to_datetime(current_date) - pd.DateOffset(months=1)).strftime('%Y-%m')

        # 查询gaussian数据
        a = self.tools.db_manager.fetch_data_to_df('ppicpi', f'date = "{current_date}"')[f'{gaussian_name}gaussian'].values[0]
        b = self.tools.db_manager.fetch_data_to_df('ppicpi', f'date = "{previous_month}"')[f'{gaussian_name}gaussian'].values[
            0]

        # 确定趋势
        self.trend = 1 if a > b else -1
        close_arr = selected_columns['close'].values
        # 计算黄金分割点
        price_range = h - l
        support_1, support_2, support_3 = (price_range * 0.382, price_range * 0.5, price_range * 0.618)
        # buy, sell, short, cover


        def position_status(close_arr, state_liat):
            if state_liat:
                for i in state_liat:
                    if i[0] == 1 and close_arr[-1] > i[3]:
                        self.sell(close_arr[-1], i[1])
                        self.tools.sqlite_update_data('state', 'one', [], state_liat[0])
        # state的内容为(id, 商品名,[趋势, id, 原始h, 原始l, 止盈价, 止损价, 新h, 新l]
                                # [趋势, id, 原始h, 原始l, 止盈价, 止损价, 新h, 新l]
                                # [趋势, id, 原始h, 原始l, 止盈价, 止损价, 新h, 新l])



        try:
            state = self.tools.db_manager.query_cond('state', f'commodity = "{symbol}"')[2:]
        except:
            self.tools.sqlite_insert_data([symbol, '', '', ''])
            state = ['', '', '']
        state = [(index, value) for index, value in enumerate((0,)+state) if value]
        if position_status():
            pass





    def get_data(self):
        # 实现获取数据的逻辑
        pass

    def update_data(self):
        # 实现更新数据的逻辑
        pass

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def high_low(self, data, MA1, MA2, MA3):
        """
        计算给定数据中的高点和低点。

        参数:
        - data: 包含股票价格数据的DataFrame，必须至少包含'close', 'high', 和 'low' 列。
        - MA1, MA2, MA3: 用于计算移动平均的窗口大小。

        返回:
        - (h, l, h_date, l_date): 最显著高点和低点及其对应日期。
        """

        def ma_hl(ma_data, n):
            """
            计算给定移动平均窗口大小内的高点和低点。

            参数:
            - ma_data: 包含股票价格数据的DataFrame。
            - n: 移动平均的窗口大小。

            返回:
            - [[高点值, 高点的陡峭度, 高点的索引], [低点值, 低点的陡峭度, 低点的索引]]
            """

            # 计算对数移动平均线
            ma = np.log(ma_data['close'].rolling(window=n).mean()).values
            # 峰值
            peaks, _ = find_peaks(ma)
            # 谷值
            valleys, _ = find_peaks(-ma)
            # 如果峰值或谷值不足2个，则不进行后续计算
            if len(peaks) < 2 or len(valleys) < 2:
                return
            # 计算峰值和谷值的陡峭度
            peak_sharpness = self.tools.calculate_sharpness(ma, peaks)
            valley_sharpness = self.tools.calculate_sharpness(ma, valleys)
            # 根据峰值和谷值的位置关系，确定高点和低点
            if peaks[-1] > valleys[-1] and peaks[-1] - peaks[-2] > n:
                h_ = data['high'].values[valleys[-1]: peaks[-1]]
                l_ = data['low'].values[peaks[-2]: valleys[-1]]
            elif peaks[-1] < valleys[-1] and valleys[-1] - valleys[-2] > n:
                h_ = data['high'].values[valleys[-2]: peaks[-1]]
                l_ = data['low'].values[peaks[-1]: valleys[-1]]
            else:
                return
            # 返回高点和低点及其对应的陡峭度和索引
            return [[np.max(h_), peak_sharpness[-1], peaks[-1]],
                    [np.min(l_), valley_sharpness[-1], valleys[-1]]]

        # 使用不同的移动平均窗口计算高点和低点
        ma1 = ma_hl(data, MA1)
        ma2 = ma_hl(data, MA2)
        ma3 = ma_hl(data, MA3)
        # 如果所有计算结果都为空，则增加移动平均窗口大小重新计算
        while not ma1 and not ma2 and not ma3:
            if MA3 > len(data):
                return
            MA1 += 10
            MA2 += 10
            MA3 += 10
            ma1 = ma_hl(data, MA1)
            ma2 = ma_hl(data, MA2)
            ma3 = ma_hl(data, MA3)
        # 整理计算结果
        hl_temp = [ma1, ma2, ma3]
        h_temp = []
        l_temp = []
        for i in [hl_temp[i] for i in range(len(hl_temp)) if hl_temp[i]]:
            h_temp.append(i[0])
            l_temp.append(i[1])
        # 将结果转换为DataFrame，以便后续处理
        h_temp = pd.DataFrame(h_temp)
        h = h_temp.iloc[h_temp.iloc[:, 1].argmax()]
        l_temp = pd.DataFrame(l_temp)
        l = l_temp.iloc[l_temp.iloc[:, 1].argmax()]
        # 提取高点、低点及其日期
        h, _, h_date = h.values
        l, _, l_date = l.values
        # 返回结果
        return (h, l, h_date, l_date)

    def ppi_cpi_price_corr(self):
        """
        计算并返回中国年产出价格指数(PP)和居民消费价格指数(CPI)的相关数据。

        该方法从两个不同的API获取PP和CPI数据，进行数据预处理，包括重命名列、格式化日期，
        然后将两个数据集合并，并计算价格差。最后，应用高斯滤波器对数据进行平滑处理。

        返回:
        DataFrame: 包含PP、CPI及其差值的价格，经过高斯滤波器平滑处理后的数据。

        需要在策略引擎CtaEngine里添加
        def _init_strategy(self, strategy_name: str) -> None:
            # Call load_external_data method of strategy
            strategy: CtaTemplate = self.strategies[strategy_name]
            strategy.load_external_data()

        ...
        """
        # 获取并处理PPI数据
        ppi_df = ak.macro_china_ppi_yearly()
        ppi_df['日期'] = pd.to_datetime(ppi_df['日期'])
        ppi_df = ppi_df[['日期', '今值']]
        ppi_df = ppi_df.rename(columns={'日期': 'date', '今值': 'ppi'})
        ppi_df['date'] = ppi_df['date'].dt.strftime('%Y-%m')

        # 获取并处理CPI数据
        cpi_df = ak.macro_china_cpi_yearly()
        cpi_df['日期'] = pd.to_datetime(cpi_df['日期'])
        cpi_df = cpi_df[['日期', '今值']]
        cpi_df = cpi_df.rename(columns={'日期': 'date', '今值': 'cpi'})
        cpi_df['date'] = cpi_df['date'].dt.strftime('%Y-%m')

        # 合并PPI和CPI数据集，并计算价格差
        ppi_cpi = pd.merge(ppi_df, cpi_df, on='date', how='outer')
        ppi_cpi = ppi_cpi.dropna()
        ppi_cpi['price'] = ppi_cpi['ppi'] - ppi_cpi['cpi']

        # 高斯滤波平滑
        ppi_cpi['PpiGaussian'] = gaussian_filter1d(ppi_cpi['ppi'], sigma=1)
        ppi_cpi['CpiGaussian'] = gaussian_filter1d(ppi_cpi['cpi'], sigma=1)
        ppi_cpi['PriceGaussian'] = gaussian_filter1d(ppi_cpi['price'], sigma=1)


