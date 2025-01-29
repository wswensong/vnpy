from constantDefinition import categories, breedCode, continuousContracts
import akshare as ak
from mysqlApi import MySQLInterface
import json
def classify_items(items_to_classify):
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

def merge_and_rename_keys(data):

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


# memberPositionsValet
# db = MySQLInterface(host='101.132.121.208', database='position', user='wsuong', password='Ws,1008351110')
db = MySQLInterface(host='localhost', database='position', user='root', password='Ws,1008351110')
db.connect()
select_query = "SELECT * FROM memberPositions ORDER BY datetime DESC LIMIT 5;"
employees = db.fetch_data(select_query)
db.disconnect()
with open('officeName.json', 'r', encoding='utf-8') as f:
    officeName = json.load(f).keys()
for employee in employees:
    for office in officeName:
        if office in employee and employee[office]:
            reviseEmployee = merge_and_rename_keys(json.loads(employee[office]))
            print(classify_items(reviseEmployee))    
        