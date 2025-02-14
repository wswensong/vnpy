from constantDefinition import categories, breedCode, breedUnits
import akshare as ak
from mysqlApi import MySQLInterface
import json
import pandas as pd
import requests

def breed_index_classification(items_to_classify):
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

def breed_data_cleaning(data):
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

def data_cleansing(employees):
    """
    清理员工数据：
    - 移除 'id' 字段。
    - 对非空 JSON 字符串进行解析。
    - 清除值为 '{}' 和 None 的字段。
    """
    cleaned_employees = [{key: (json.loads(value) if isinstance(value, str) and value.strip() != '{}' else value) 
                for key, value in emp.items() if key != 'id' and value not in ('{}', None)}for emp in employees]
    return cleaned_employees

def data_wrangling(linked_list_of_positions):
    db = MySQLInterface(host='101.132.121.208', database='quotes', user='wsuong', password='Ws,1008351110')
    # db = MySQLInterface(host='localhost', database='quotes', user='root', password='Ws,1008351110')
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
            clean_value = breed_data_cleaning(value)    # 清洗后的数据,后期也使用此数据
            class_value = breed_index_classification(clean_value)   # 指数分类
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

# def collate_into_visual_data(member_dict):
#     organized_data = {}

#     for date, companies in member_dict.items():
#         organized_data[date] = {}
#         for company, commodities in companies.items():
#             for commodity_type, prices in commodities.items():
#                 if commodity_type not in organized_data[date]:
#                     organized_data[date][commodity_type] = {}
#                 for commodity, price in prices.items():
#                     if commodity not in organized_data[date][commodity_type]:
#                         organized_data[date][commodity_type][commodity] = []
#                     organized_data[date][commodity_type][commodity].append(round(price, 1))

#     # 计算每个日期下每个商品的总和
#     summed_data = []

#     for date, commodity_types in organized_data.items():
#         for commodity_type, commodities in commodity_types.items():
#             for commodity, prices in commodities.items():
#                 summed_data.append({
#                     'Date': date,
#                     'Commodity Type': commodity_type,
#                     'Commodity': commodity,
#                     'Sum of Prices': round(sum(prices), 1)
#                 })

#     # 转换为DataFrame
#     df = pd.DataFrame(summed_data)

#     # 按商品类型和商品分组，并将价格总和转换为列表
#     grouped_df = df.pivot(index=['Commodity Type', 'Commodity'], columns='Date', values='Sum of Prices').reset_index()
#     return grouped_df



def calculate_weighted_change_rate(prices):
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

def collate_into_weighted_change_rate(member_dict):
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
        weighted_change_rate = calculate_weighted_change_rate(prices)
        result_data.append({
            '指数': commodity_type,
            '商品': commodity,
            '走势': round(weighted_change_rate, 4)
        })

    # 转换为DataFrame
    df = pd.DataFrame(result_data)
    return df
def send_dingtalk_message(message):
        webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=4956a876dbe7fced88a9e02d2dfb1be1888f243164b9e0e7ed0b8d38d245f6c3"
        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        requests.post(webhook_url, headers=headers, data=json.dumps(data))

def main(sql_name):
    # memberPositionsValet  memberPositions
    db = MySQLInterface(host='101.132.121.208', database='position', user='wsuong', password='Ws,1008351110')
    # db = MySQLInterface(host='localhost', database='position', user='root', password='Ws,1008351110')
    db.connect()
    select_query = f"SELECT * FROM {sql_name} ORDER BY datetime DESC LIMIT 3;"
    # id_query = f"SELECT id FROM {sql_name} WHERE datetime = '{datetime}';"
    # id_mysql = db.fetch_data(id_query)[0]['id']
    # select_query = f"SELECT * FROM {sql_name} WHERE id <= {id_mysql} ORDER BY datetime DESC LIMIT 3;"
    employees = db.fetch_data(select_query)
    db.disconnect()
    cleaned_employees = data_cleansing(employees)
    organize_member_position_data = data_wrangling(cleaned_employees)
    grouped_df = collate_into_weighted_change_rate(organize_member_position_data)
    # return grouped_df
    print(grouped_df.to_markdown(index=False))
    send_dingtalk_message(f'通知\n{grouped_df.to_markdown(index=False)}')
    
if __name__ == "__main__":
    main('memberPositions')
    main('memberPositionsValet')