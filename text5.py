from constantDefinition import categories
def classify_items(items_to_classify):
    # 分类结果
    classified_items = {}

    # 遍历要分类的商品，并将其归入合适的类别
    for item in items_to_classify:
        found = False
        for main_category, sub_categories in categories.items():
            if isinstance(sub_categories, dict):
                for sub_category, items in sub_categories.items():
                    if item in items:
                        if main_category not in classified_items:
                            classified_items[main_category] = {}
                        if sub_category not in classified_items[main_category]:
                            classified_items[main_category][sub_category] = []
                        classified_items[main_category][sub_category].append(item)
                        found = True
                        break
            else:
                if item in sub_categories:
                    if main_category not in classified_items:
                        classified_items[main_category] = []
                    classified_items[main_category].append(item)
                    found = True
            if found:
                break

    return classified_items

# 要分类的商品列表
items_to_classify = ["20号胶", "塑料", "PVC", "乙二醇", "螺纹钢", "豆粕", "菜籽粕"]

# 调用分类函数并打印结果
classified_result = classify_items(items_to_classify)
print(classified_result)