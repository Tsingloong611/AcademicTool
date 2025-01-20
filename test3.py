# -*- coding: utf-8 -*-
# @Time    : 1/19/2025 2:28 PM
# @FileName: test3.py
# @Software: PyCharm
# 从result.json读取数据
import json
import os

# 读取json文件
with open('result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

template = []
for i in data:
    id = i['entity_type_id']
    categories = i['categories']
    categories_id = [item['category_id'] for item in categories]
    temp = {'id': id, 'categories': categories_id}
    template.append(temp)
for i in template:
    if len(i['categories']) > 1:
        for j in i['categories']:
            temp = {'id': i['id'], 'categories': [j]}
            template.append(temp)
        template.remove(i)
for i in template:
    i['categories'] = i['categories'][0]
print(template)


