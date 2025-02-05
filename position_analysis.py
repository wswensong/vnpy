from constantDefinition import categories, breedCode, continuousContracts, breedUnits
import akshare as ak
from mysqlApi import MySQLInterface
import json
from datetime import datetime as dt

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


# memberPositionsValet
# db = MySQLInterface(host='101.132.121.208', database='position', user='wsuong', password='Ws,1008351110')
db = MySQLInterface(host='localhost', database='position', user='root', password='Ws,1008351110')
db.connect()
select_query = "SELECT * FROM memberPositions ORDER BY datetime DESC LIMIT 3;"
employees = db.fetch_data(select_query)
db.disconnect()
cleaned_employees = data_cleansing(employees)

db = MySQLInterface(host='localhost', database='quotes', user='root', password='Ws,1008351110')
db.connect()
the_amount_of_funds_held_by_the_member = {}
for i in cleaned_employees:
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
                query = f"SELECT close FROM {breedCode[j].split('0')[0]} WHERE datetime='{position_data_time}'" # 查询收盘价
                close = float(db.fetch_data(query)[0]['close']) # 收盘价
                single_symbol_position_funds = (clean_value[j][-2] - clean_value[j][-1]) * breedUnits[j] / 10000 * close    # 单个品种持仓资金量
                the_amount_of_funds_held_by_the_member[position_data_time][key][index][j] = single_symbol_position_funds
print(the_amount_of_funds_held_by_the_member)
db.disconnect()
