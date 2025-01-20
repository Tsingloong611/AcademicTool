# -*- coding: utf-8 -*-
# @Time    : 1/20/2025 2:31 PM
# @FileName: test7.py
# @Software: PyCharm
from owlready2 import *
import pyAgrum as gum
# import pyAgrum.lib.notebook as gnb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import truncnorm, norm
import pyAgrum.lib.image as gumimage
import random
import graphviz
import openpyxl
import ast

# 1. 读入OWL文件
onto = get_ontology(r'D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Scenario.owl').load()
# 准备存储信息的数据结构
data_properties_info = []
object_properties_info = []
bn = gum.BayesNet('ScenarioDeductionBN')
# 2. 提取dataproperty元素的名称、domain和range
for dps in onto.data_properties():
    data_properties_info.append({"name": dps.name, "domain": dps.domain[0].name, "range": dps.range[0]})

# 将resourseType具体转化为 4 种
for item in data_properties_info:
    if item['name'] == 'resourceType':
        info = item
        break
for resource in ['AidResource', 'TowResource', 'FirefightingResource', 'RescueResource']:
    item = info.copy()
    item['name'] = resource
    data_properties_info.append(item)
data_properties_info = [item for item in data_properties_info if item['name'] != 'resourceType']

print(data_properties_info)

# 创建一个字典，键为factor nodes，值为其对应的状态变量
dict_factor_node_values = {
    'roadPassibility': ['Passable', 'Impassable'],
    'emergencyType': ['Vehicle_Self_Accident', 'Vehicle_to_Fixed_Object_Accident', 'Collision_Accident'],
    'roadLoss': ['Loss', 'Not_Loss'],
    'casualties': ['Casualties', 'No_Casualties'],
    #    'resourceType': ['Aid_Resource', 'Tow_Resource', 'Firefighting_Resource', 'Rescue_Resource'],
    'AidResource': ['Not_Used', 'Used'],
    'TowResource': ['Not_Used', 'Used'],
    'FirefightingResource': ['Not_Used', 'Used'],
    'RescueResource': ['Not_Used', 'Used'],
    'emergencyPeriod': ['Early_Morning', 'Morning', 'Afternoon', 'Evening'],
    'responseDuration': ['0-15min', '15-30min', '30-60min', '60min+'],
    'disposalDuration': ['0-15min', '15-30min', '30-60min', '60min+']
}
# 创建一个字典，键为capacity nodes，值为其对应的factor nodes
dict_factor_capacity = {
    'AbsorptionScenario': ['roadPassibility', 'roadLoss'],
    'AdaptionScenario': ['emergencyType', 'emergencyPeriod'],
    'RecoveryScenario': ['AidResource', 'TowResource', 'FirefightingResource', 'RescueResource', 'responseDuration',
                         'disposalDuration', 'casualties']
}


def find_capacity_by_factor(factor, c_f_dict):
    matching_keys = []
    for key, values in c_f_dict.items():
        if factor in values:
            matching_keys.append(key)
    return matching_keys


# 3. ontology转换为bn
classes = [cls.name for cls in onto.classes()]
for cls in onto.classes():
    #     print(cls)
    if cls.name == "ScenarioResilience":
        node_resilience = bn.add(gum.LabelizedVariable(cls.name, 'resilienceLevel', 2))
    if cls.name == "Scenario":
        capacities = list(cls.subclasses())
        for capacity in capacities:
            capacityName = capacity.name.replace("Scenario", "") + 'Capacity'
            #             print(capacityName)
            bn.add(gum.LabelizedVariable(capacityName, 'capacityLevel', 2))
            bn.addArc(capacityName, "ScenarioResilience")
    elif cls.name == "ResillienceInfluentialFactors":
        factorProperties = list(cls.subclasses())
        for pro in factorProperties:
            for dp in data_properties_info:
                #                 print(pro.name)
                if dp['domain'] == pro.name:
                    bn.add(
                        gum.LabelizedVariable(dp['name'], 'factorLevel', len(dict_factor_node_values.get(dp['name']))))
                    result = find_capacity_by_factor(dp['name'], dict_factor_capacity)
                    #                     print(f"'{dp['name']}' 在字典中的对应键为: {', '.join(result)}")
                    for arc in result:
                        capacityName = arc.replace("Scenario", "") + 'Capacity'
                        bn.addArc(dp['name'], capacityName)


# print(bn)

# dot_structure = bn.toDot()
# print(dot_structure)

def calculate_DiscreteVariable_Prior(node_name, data):
    category_counts = data.value_counts()
    # 计算总样本数
    total_samples = category_counts.sum()

    # 计算每个类别的概率分布
    category_probabilities = category_counts / total_samples
    #     print(category_probabilities.tolist())
    bn.cpt(node_name).fillWith(category_probabilities.tolist())


def calculate_ContinuousVariable_Thorm(data):
    # 计算均值和标准差
    mu, std = norm.fit(data)
    # 打印拟合的均值和标准差
    #     print(f"Fitted Mean (μ): {mu:.2f}")
    #     print(f"Fitted Standard Deviation (σ): {std:.2f}")

    lower_bound = np.percentile(data, 5)  # 5th percentile
    upper_bound = np.percentile(data, 95)  # 95th percentile
    #     print(f"Lower Bound: {lower_bound}, Upper Bound: {upper_bound}")
    # Calculate the z-scores for the truncation bounds
    a = (lower_bound - mu) / std  # Lower bound in terms of z-score
    b = (upper_bound - mu) / std  # Upper bound in terms of z-score

    # Create a truncated normal distribution with the calculated parameters
    truncated_normal = truncnorm(a, b, loc=mu, scale=std)
    return truncated_normal


def discretize_calculate_probabilities(x, truncated_normal):
    prob = truncated_normal.cdf(x)
    #     print(f"P(X < {x}) for a truncated normal distribution is: {prob}")
    return (prob)


def draw_thorm(truncated_normal, data):
    mu, std = norm.fit(data)
    lower_bound = np.percentile(data, 5)  # 5th percentile
    upper_bound = np.percentile(data, 95)  # 95th percentile
    sampled_values = truncated_normal.rvs(size=1000)
    plt.figure(figsize=(10, 6))
    plt.hist(sampled_values, bins=30, density=True, alpha=0.6, color='g', label='Data Histogram')

    # 绘制截断正态分布曲线
    x = np.linspace(lower_bound, upper_bound, 1000)
    p = truncated_normal.pdf(x)
    plt.plot(x, p, 'k', linewidth=2, label=f'Truncated Normal Fit (μ={mu:.2f}, σ={std:.2f})')

    # 添加标签和图例
    plt.title('Truncated Normal Distribution Fit')
    plt.xlabel('Continuous Variable')
    plt.ylabel('Density')
    plt.legend()

    # 显示图形
    plt.show()


data = pd.read_excel(r"D:\科研\贝叶斯实验\prior prob test.xlsx")
df = pd.DataFrame(data)

# 4.设置根节点的先验概率
for node in bn.nodes():
    node_name = bn.variable(node).name()
    #     print(node_name != "emergencyPeriod")
    if (len(bn.parents(node)) == 0):
        if node_name not in ["disposalDuration", "responseDuration"]:
            #         print(node_name)
            calculate_DiscreteVariable_Prior(node_name, df[node_name])
        elif node_name in ["disposalDuration", "responseDuration"]:
            truncated_normal = calculate_ContinuousVariable_Thorm(df[node_name])
            prob_0_15 = discretize_calculate_probabilities(15, truncated_normal)
            prob_15_30 = discretize_calculate_probabilities(30, truncated_normal) - prob_0_15
            prob_30_60 = discretize_calculate_probabilities(60, truncated_normal) - discretize_calculate_probabilities(
                30, truncated_normal)
            prob_morethan_60 = 1 - discretize_calculate_probabilities(60, truncated_normal)
            #             print(prob_0_15,prob_15_30,prob_30_60,prob_morethan_60)
            bn.cpt(node_name).fillWith([prob_0_15, prob_15_30, prob_30_60, prob_morethan_60])

# 定义评估结果与模糊数的映射关系
mapping_evaluation_fuzzy = {
    'VL': (0.0, 0.0, 0.1, 0.2),
    'L': (0.1, 0.2, 0.2, 0.3),
    'M': (0.2, 0.3, 0.4, 0.5),
    'H': (0.5, 0.6, 0.7, 0.8),
    'VH': (0.8, 0.9, 1.0, 1.0)
}

df = pd.read_excel(r"D:\科研\贝叶斯实验\expert estimation test.xlsx")


# print(df)

def calculate_fuzzy(row):
    fuzzy_numbers = [mapping_evaluation_fuzzy[r] for r in row]
    return fuzzy_numbers


df['fuzzy'] = df.iloc[:, -7:].apply(calculate_fuzzy, axis=1)
df['Condition'] = df['Condition'].tolist()


# print(df)

def calculate_similarity(row):
    # 初始化结果列表，用于存储每个元素与其他元素差值的平均值
    ss = []
    avg_similarity = []
    relative_similarity = []
    # 获取数组的长度
    n = len(row)
    k = list(range(n))

    # 遍历数组中的每个元素（元组）
    for i in range(n):
        temp = []
        k_filtered = [element for element in k if element != i]
        for j in k_filtered:
            differences_sum = 1 - (sum(abs(a - b) for a, b in zip(row[i], row[j]))) / len(row[i])
            temp.append(differences_sum)
        avg_similarity.append(sum(temp) / len(temp))
        ss.append(temp)
        relative_similarity.append(avg_similarity[i] / sum(avg_similarity))
    #     print(avg_similarity)
    #     print(relative_similarity)

    return ss, avg_similarity, relative_similarity


df_expert = pd.read_excel(r"D:\科研\贝叶斯实验\expertInfo.xlsx")
scores = df_expert.iloc[:, 1:].sum(axis=1)
total_score = scores.sum()
weight_list = list(scores / total_score)
print(weight_list)


def calculate_aggrated_fuzzy(row):
    b = 0.5
    aggrated_fuzzy = [0.0, 0.0, 0.0, 0.0]  # 四个位置对应四个加权平均数
    global weight_list

    ss, avg_s, rela_s = calculate_similarity(row)
    cc = [(b * weight_list[i] + (1 - b) * rela_s[i]) for i in range(len(rela_s))]
    weight = [i / sum(cc) for i in cc]  # 归一化，使和为1

    # 计算加权平均数
    for weights, tup in zip(weight, row):
        #         print(weights)
        for i in range(len(tup)):
            #             print('i:',tup[i])
            #             print(tup[i] * weights)
            aggrated_fuzzy[i] += tup[i] * weights

    a1, a2, a3, a4 = aggrated_fuzzy
    defuzzified_possibility = ((a4 + a3) ** 2 - a4 * a3 - (a1 + a2) ** 2 + a1 * a2) / (3 * (a4 + a3 - a2 - a1))

    return defuzzified_possibility


# 条件概率填充到 df
conditonProbability = []
for row in df['fuzzy']:
    conditonProbability.append(calculate_aggrated_fuzzy(row))
#    print(calculate_aggrated_fuzzy(row))
df['conditonProbability'] = conditonProbability


# 条件概率归一化
def normalize(group):
    s = group['conditonProbability'].sum()
    group['conditonProbability'] = group['conditonProbability'] / s
    return group


normalized_prob = (df.groupby(['Node', 'Condition']).apply(normalize))['conditonProbability']
df['conditonProbability'] = normalized_prob.tolist()
# print(df)

# 将 Condition 和 State 结合为 cpt 填充时的索引列表
index = []
for i, row in df.iterrows():
    sublist = ast.literal_eval(row['Condition'])
    sublist.append(row['State'])
    index.append(sublist)
# print(index)

# 创建 Potential 对象字典
cpt = {'AbsorptionCapacity': bn.cpt('AbsorptionCapacity'), 'AdaptionCapacity': bn.cpt('AdaptionCapacity'),
       'RecoveryCapacity': bn.cpt('RecoveryCapacity'), 'ScenarioResilience': bn.cpt('ScenarioResilience')}
# 条件概率填充
for i, row in df.iterrows():
    (cpt[row['Node']])[ast.literal_eval(','.join(str(x) for x in index[i]))] = row['conditonProbability']
# 将 Potential 对象赋值给 cpt
for i in ['AbsorptionCapacity', 'AdaptionCapacity', 'RecoveryCapacity', 'ScenarioResilience']:
    bn.cpt(i).fillWith(cpt[i])
# print(bn.cpt("AbsorptionCapacity"))

# 6.证据更新
# onto = get_ontology("file://ScenarioOntology.owl")
# onto.load()
# print(list(onto.data_properties()))
# print(list(onto.properties()))
# with onto:
#    rule1 = Imp()
#     rule1.set_as_rule("""""")
# 当保存预案时，更新预案实例
# 执行swrl推理
# sync_reasoner_pellet(infer_property_values = True, infer_data_property_values = True)

# 7.执行推理：使用lazyPropagation推理引擎精确推断
ie = gum.LazyPropagation(bn)
# 没有新数据的推断
ie.makeInference()
print(ie.posterior("ScenarioResilience"))
print(ie.posterior("RecoveryCapacity"))

# 有新数据的推断
ie.setEvidence({'AidResource': 0})
ie.makeInference()
print(ie.posterior("ScenarioResilience"))
print(ie.posterior("RecoveryCapacity"))