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
from vnpy.trader.constant import Interval
import pandas as pd
from constantDefinition import categories, breedCode, breedUnits
import akshare as ak
from mysqlApi import MySQLInterface
import json
import pandas as pd
import requests


class maStrategy(CtaTemplate):
    author = "Your Name"

    # 参数列表
    day: int = 2
    up_value: int = 0
    dow_value: int = 0


    parameters = ['day', 'up_value', 'dow_value']

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
        member_data = self.analyze_positions('memberPositions', data['datetime'][-1])
        commodity_trend_value1 = member_data[0].loc[member_data[0]['商品'] == '不锈钢', '走势'].values[0]
        commodity_trend_value2 = member_data[1].loc[member_data[1]['商品'] == '不锈钢', '走势'].values[0]
        if self.pos == 0 and commodity_trend_value1 > 0 and commodity_trend_value2 > 0:# and commodity_trend_value1 > commodity_trend_value2:
            self.buy(data['close'][-1], 1)
            print('买入')
        # if self.pos == 0 and commodity_trend_value1 > 0 and commodity_trend_value2 < 0:
        #     self.buy(data['close'][-1], 1)
        #     print('买入')
        elif self.pos == 0 and commodity_trend_value1 < 0 and commodity_trend_value2 < 0:# and commodity_trend_value1 < commodity_trend_value2:
            self.short(data['close'][-1], 1)
            print('卖出')
        # elif self.pos == 0 and commodity_trend_value1 < 0 and commodity_trend_value2 > 0:
        #     self.short(data['close'][-1], 1)
        #     print('卖出')
        elif self.pos > 0 and commodity_trend_value1 > 0 and commodity_trend_value2 > 0 and commodity_trend_value1 < commodity_trend_value2:
            self.sell(data['close'][-1], 1)
            print('买平')
        elif self.pos > 0 and commodity_trend_value1 < 0 and commodity_trend_value2 < 0 and commodity_trend_value1 < commodity_trend_value2:
            self.sell(data['close'][-1], 1)
            print('买平')
        elif self.pos > 0 and commodity_trend_value1 < 0 and commodity_trend_value2 > 0:
            self.sell(data['close'][-1], 1)
            print('买平')
        elif self.pos < 0 and commodity_trend_value1 > 0 and commodity_trend_value2 > 0 and commodity_trend_value1 > commodity_trend_value2:
            self.cover(data['close'][-1], 1)
            print('卖平')
        elif self.pos < 0 and commodity_trend_value1 > 0 and commodity_trend_value2 < 0:
            self.cover(data['close'][-1], 1)
            print('卖平')
        elif self.pos < 0 and commodity_trend_value1 < 0 and commodity_trend_value2 < 0 and commodity_trend_value1 > commodity_trend_value2:
            self.cover(data['close'][-1], 1)
            print('卖平')
        self.put_event()
        # commodity_trend_value = member_data.loc[member_data['商品'] == '螺纹钢', '走势'].values[0]
        # print(data['datetime'][-1], commodity_trend_value)
        # if self.pos == 0:
        #     if commodity_trend_value > self.up_value/100:
        #         self.buy(data['close'][-1], 1)
        #         print('买入')
        #     else:
        #         self.short(data['close'][-1], 1)
        #         print('卖出')
        # if self.pos > 0:
        #     if commodity_trend_value < self.dow_value/100:
        #         self.sell(data['close'][-1], 1)
        #         self.short(data['close'][-1], 1)
        #         print('买平卖空')
        # if self.pos < 0:
        #     if commodity_trend_value > self.up_value/100:
        #         self.cover(data['close'][-1], 1)
        #         self.buy(data['close'][-1], 1)
        #         print('卖平买多')
        # self.put_event()
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

    

    def breed_index_classification(self, items_to_classify):
        # 分类结果
        classified_items = {}
        
        # 遍历要分类的商品，并将其归入合适的类别
        for item in items_to_classify:
            found = False
            for category, items in categories.items():
                if item in items:
                    if category not in classified_items:
                        classified_items[category] = []
                    classified_items[category].append(item)
                    found = True
                    break
            if not found:
                if "其他" not in classified_items:
                    classified_items["其他"] = []
                classified_items["其他"].append(item)

        return classified_items

    def breed_data_cleaning(self, data):
        if "锌" in data and "沪锌" in data:
            data["锌"] = [a + b for a, b in zip(data["锌"], data["沪锌"])]
            del data["沪锌"]
        elif "沪锌" in data:
            data["锌"] = data.pop("沪锌")

        # 合并 "号胶" 和 "20号胶"
        if "号胶" in data and "20号胶" in data:
            data["20号胶"] = [a + b for a, b in zip(data["号胶"], data["20号胶"])]
            del data["号胶"]
        elif "号胶" in data:
            data["20号胶"] = data.pop("号胶")
        return data

    def data_cleansing(self, employees):
        """
        清理员工数据：
        - 移除 'id' 字段。
        - 对非空 JSON 字符串进行解析。
        - 清除值为 '{}' 和 None 的字段。
        """
        cleaned_employees = [{key: (json.loads(value) if isinstance(value, str) and value.strip() != '{}' else value) 
                    for key, value in emp.items() if key != 'id' and value not in ('{}', None)}for emp in employees]
        return cleaned_employees

    def data_wrangling(self, linked_list_of_positions):
        # db = MySQLInterface(host='101.132.121.208', database='quotes', user='wsuong', password='Ws,1008351110')
        db = MySQLInterface(host='localhost', database='quotes', user='root', password='Ws,1008351110')
        db.connect()
        the_amount_of_funds_held_by_the_member = {}
        collection_of_closing_prices = {}
        for i in linked_list_of_positions:
            position_data_time = str(i['datetime']).split(' ')[0]
            the_amount_of_funds_held_by_the_member[position_data_time] = {}
            for key, value in i.items():
                if key == 'datetime':
                    continue
                the_amount_of_funds_held_by_the_member[position_data_time][key] = {}
                clean_value = self.breed_data_cleaning(value)    # 清洗后的数据,后期也使用此数据
                class_value = self.breed_index_classification(clean_value)   # 指数分类
                for index, variety in class_value.items():
                    the_amount_of_funds_held_by_the_member[position_data_time][key][index] = {}
                    for j in variety:
                        product_code = breedCode[j].split('0')[0]
                        if product_code + position_data_time not in collection_of_closing_prices:
                            query = f"SELECT close FROM {product_code} WHERE datetime='{position_data_time}'" # 查询收盘价
                            close = float(db.fetch_data(query)[0]['close']) # 收盘价
                            collection_of_closing_prices[product_code + position_data_time] = close
                        single_symbol_position_funds = (clean_value[j][-2] - clean_value[j][-1]) * breedUnits[j] / 10000 * collection_of_closing_prices[product_code + position_data_time]   # 单个品种持仓资金量
                        the_amount_of_funds_held_by_the_member[position_data_time][key][index][j] = single_symbol_position_funds
        db.disconnect()
        return the_amount_of_funds_held_by_the_member


    def calculate_weighted_change_rate(self, prices):
        """
        计算加权平均变化率
        :param prices: 三天的价格列表，顺序为 [第1天, 第2天, 第3天]
        :return: 加权平均变化率
        """
        if len(prices) != 3:
            raise ValueError("需要三天的价格数据来计算加权平均变化率")
        
        # 计算第1天到第2天的变化率
        change_rate_1 = (prices[1] - prices[0]) / abs(prices[0]) if prices[0] != 0 else 0
        # 计算第2天到第3天的变化率
        change_rate_2 = (prices[2] - prices[1]) / abs(prices[1]) if prices[1] != 0 else 0
        
        # 设置权重（第2天到第3天的权重更高）
        w1, w2 = 1, 2
        weighted_change_rate = (w1 * change_rate_1 + w2 * change_rate_2) / (w1 + w2)
        
        return weighted_change_rate

    def collate_into_weighted_change_rate(self, member_dict):
        organized_data = {}

        # Step 1: 按日期、商品类型、商品汇总净持仓
        for date, companies in member_dict.items():
            organized_data[date] = {}
            for company, commodities in companies.items():
                for commodity_type, prices in commodities.items():
                    if commodity_type not in organized_data[date]:
                        organized_data[date][commodity_type] = {}
                    for commodity, price in prices.items():
                        if commodity not in organized_data[date][commodity_type]:
                            organized_data[date][commodity_type][commodity] = 0.0
                        # 累加所有公司的净持仓
                        organized_data[date][commodity_type][commodity] += price

        # Step 2: 按商品类型和商品整理三天的净持仓
        result_data = []
        # 获取所有日期并按顺序排序
        sorted_dates = sorted(organized_data.keys())
        if len(sorted_dates) != 3:
            raise ValueError("需要三天的数据")

        # 遍历所有商品类型和商品
        commodity_info = {}
        for date in sorted_dates:
            for commodity_type, commodities in organized_data[date].items():
                for commodity, price in commodities.items():
                    key = (commodity_type, commodity)
                    if key not in commodity_info:
                        commodity_info[key] = []
                    commodity_info[key].append(round(price, 1))

        # Step 3: 计算加权平均变化率
        for (commodity_type, commodity), prices in commodity_info.items():
            if len(prices) != 3:
                continue  # 跳过不完整的数据
            weighted_change_rate = self.calculate_weighted_change_rate(prices)
            result_data.append({
                '指数': commodity_type,
                '商品': commodity,
                '走势': round(weighted_change_rate, 4)
            })

        # 转换为DataFrame
        df = pd.DataFrame(result_data)
        return df
    def send_dingtalk_message(self, message):
            webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=4956a876dbe7fced88a9e02d2dfb1be1888f243164b9e0e7ed0b8d38d245f6c3"
            headers = {'Content-Type': 'application/json'}
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            requests.post(webhook_url, headers=headers, data=json.dumps(data))

    def analyze_positions(self, sql_name, datetime):
        # memberPositionsValet  memberPositions
        # db = MySQLInterface(host='101.132.121.208', database='position', user='wsuong', password='Ws,1008351110')
        db = MySQLInterface(host='localhost', database='position', user='root', password='Ws,1008351110')
        db.connect()
        # select_query = f"SELECT * FROM {sql_name} ORDER BY datetime DESC LIMIT 3;"
        id_query = f"SELECT id FROM {sql_name} WHERE datetime = '{datetime}';"
        id_mysql = db.fetch_data(id_query)[0]['id']
        select_query = f"SELECT * FROM {sql_name} WHERE id <= {id_mysql} ORDER BY datetime DESC LIMIT 4;"
        employees1 = db.fetch_data(select_query)[1:]
        employees2 = db.fetch_data(select_query)[:-1]
        db.disconnect()
        cleaned_employees1 = self.data_cleansing(employees1)
        cleaned_employees2 = self.data_cleansing(employees2)
        organize_member_position_data1 = self.data_wrangling(cleaned_employees1)
        organize_member_position_data2 = self.data_wrangling(cleaned_employees2)
        grouped_df1 = self.collate_into_weighted_change_rate(organize_member_position_data1)
        grouped_df2 = self.collate_into_weighted_change_rate(organize_member_position_data2)
        return [grouped_df2, grouped_df1]