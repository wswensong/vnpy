"""利用均线做的简单策略,均线构造方法为:移动平均线和高斯平滑"""
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
from position_analysis import main
from vnpy.trader.constant import Interval
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from sqlite_module import SQLiteModule
from tool import tools


class maStrategy(CtaTemplate):
    author = "Your Name"

    # 参数列表
    ma1: int = 3
    ma2: int = 5


    parameters = ["ma1", "ma2"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(
            self.on_bar,
            window=1,
            interval=Interval.DAILY,
            daily_end=time(hour=22, minute=59)
        )
        self.am = ArrayManager(5)

    def on_init(self):
        """初始化策略（必须由用户继承实现）"""
        self.write_log("初始化策略")
        self.load_bar(50)  # 加载历史数据用于初始化

    def on_start(self):
        """启动策略（必须由用户继承实现）"""
        self.write_log("启动策略")

    def on_stop(self):
        """停止策略（必须由用户继承实现）"""
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
        member_data = main('memberPositions', data['datetime'])
        print(member_data)
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

    def high_low(self, data, MA1, MA2, List=False):
        # 计算不同周期的移动平均线
        # 计算小区间和大区间的变化，并将其转换为1和-1表示
        # 处理小区间和大区间的噪声，填充缺失值
        # 根据小区间的变化确定高低点，并返回相应的数据
        ma1 = data['close'].rolling(window=MA1).mean().values
        # ma2 = data['close'].rolling(window=MA2).mean().values

        # ma1 = gaussian_filter1d(data['close'], sigma=1)
        ma2 = gaussian_filter1d(data['close'], sigma=3)
        small_interval = ma1 - ma2
        small_interval = np.where(np.isnan(small_interval), small_interval, np.sign(small_interval))
        small_interval = np.array(tools().replace_noise_with_previous(list(small_interval), MA1))
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
            # return ma1, ma2, h1, l1
            return h1, l1