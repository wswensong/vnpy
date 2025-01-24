from constantDefinition import categories
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

# 要分类的商品列表
items_to_classify = ["20号胶", "塑料", "PVC", "乙二醇", "螺纹钢", "豆粕", "菜籽粕"]

# 调用分类函数并打印结果
classified_result = classify_items(items_to_classify)
print(classified_result)