import json
import pandas as pd
from mysqlApi import MySQLInterface
def is_valid_json(json_str):
    """检查字符串是否是有效的JSON"""
    try:
        json.loads(json_str)
        return True
    except ValueError:
        return False
db = MySQLInterface(host='localhost', database='wsuong', user='root', password='Ws,1008351110')
db.connect()
positionData = db.fetch_data("SELECT * FROM (SELECT * FROM memberPositions ORDER BY datetime DESC LIMIT 30) AS subquery ORDER BY datetime ASC;")
db.disconnect()
for row in positionData:
    for key, value in row.items():
        if isinstance(value, str) and is_valid_json(value):
            row[key] = json.loads(value)
df = pd.DataFrame(positionData)['国泰君安']
