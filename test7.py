# -*- coding: utf-8 -*-
# @Time    : 1/20/2025 2:31 PM
# @FileName: test7.py
# @Software: PyCharm
import json

import cairosvg
from PIL import Image
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
#onto = get_ontology(r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\ScenarioOntology.owl").load()
onto = get_ontology(r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Scenario.owl").load()
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
#print(onto.classes())
node_resilience = bn.add(gum.LabelizedVariable("ScenarioResilience", 'resilienceLevel', 2))

for cls in onto.classes():
    #print(cls)
    if cls.name == "Scenario":
        capacities = list(cls.subclasses())
        for capacity in capacities:
            capacityName = capacity.name.replace("Scenario", "") + 'Capacity'
            bn.add(gum.LabelizedVariable(capacityName, 'capacityLevel', 2))
            bn.addArc(capacityName, "ScenarioResilience")
    elif cls.name == "ResilienceInfluentialFactors":
        factorProperties = list(cls.subclasses())
        for pro in factorProperties:
            for dp in data_properties_info:
                #                 print(pro.name)
                if dp['domain'] == pro.name:
                    #print("dict_factor_node_values:", dict_factor_node_values)
                    #print("dp['name']:", dp['name'])
                    # if dp['name'] not in dict_factor_node_values:
                    #     print(f"Warning: {dp['name']} not found in dict_factor_node_values")
                    #     continue  # 跳过这个数据属性
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


data = pd.read_excel(r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\prior prob test.xlsx")
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

df = pd.read_excel(r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\expert estimation test.xlsx")


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


df_expert = pd.read_excel(r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\expertInfo.xlsx")
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

import pyAgrum as gum
import graphviz
import os

import pyAgrum as gum
import graphviz
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

import graphviz
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


def create_probability_bar_svg(width, height, prob, y_offset=0, label=None):
    """Create SVG string for a probability bar with consistent margins"""
    total_width = width - 60  # 留出空间给文本
    bar_width = total_width * prob
    y = y_offset

    # 设置上下边距一致
    margin = (height - 20) // 2  # 保证概率条和背景条上下间距一致

    # 背景条
    svg = f'''
    <g transform="translate(0,{y})">
        <rect x="30" y="{margin}" width="{total_width}" height="{height - 2 * margin}" fill="#f3f4f6"/>
        <rect x="30" y="{margin}" width="{bar_width}" height="{height - 2 * margin}" fill="#bbf7d0"/>
        <text x="{total_width + 40}" y="{height / 2 + margin}" font-size="14" fill="#333">{label or f'{prob*100:.2f}%'}%</text>
    </g>
    '''

    return svg



def get_state_name(node_name, index):
    """Get state name for given node and index"""
    state_mapping = {
        'roadPassibility': ['Impassable', 'Passable'],
        'emergencyType': ['Vehicle_Self_Accident', 'Vehicle_to_Fixed_Object_Accident', 'Collision_Acident'],
        'roadLoss': ['Not_Loss', 'Loss'],
        'casualties': ['No_Casualties', 'Casualties'],
        'AidResource': ['Not_Used', 'Used'],
        'TowResource': ['Not_Used', 'Used'],
        'FirefightingResource': ['Not_Used', 'Used'],
        'RescueResource': ['Not_Used', 'Used'],
        'emergencyPeriod': ['Early_Morning', 'Morning', 'Afternoon', 'Evening'],
        'responseDuration': ['0-15min', '15-30min', '30-60min', '60min+'],
        'disposalDuration': ['0-15min', '15-30min', '30-60min', '60min+'],
        'AbsorptionCapacity': ['Good', 'Bad'],
        'AdaptionCapacity': ['Good', 'Bad'],
        'RecoveryCapacity': ['Good', 'Bad'],
        'ScenarioResilience': ['Good', 'Bad']
    }

    states = state_mapping.get(node_name, [str(i) for i in range(10)])
    return states[index] if index < len(states) else str(index)


def create_node_label(node_name, posterior=None):
    """Create HTML-like label for a node using table layout with improved spacing"""
    # Start with node name, adding more padding
    label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="8" STYLE="ROUNDED">\n'
    label += f'<TR><TD COLSPAN="3" BORDER="1" CELLPADDING="8"><FONT POINT-SIZE="11">{node_name}</FONT></TD></TR>\n'

    # Add probability bars if posterior exists
    if posterior is not None:
        probs = posterior.tolist()
        for i, prob in enumerate(probs):
            state_name = get_state_name(node_name, i)

            # Create table row with improved spacing
            label += '<TR>'
            # State name cell with increased padding
            label += f'<TD WIDTH="80" ALIGN="RIGHT" PORT="f{i}" CELLPADDING="6"><FONT POINT-SIZE="10">{state_name}</FONT></TD>'
            # Bar cell with consistent padding
            label += f'<TD WIDTH="120" ALIGN="LEFT" BGCOLOR="white" CELLPADDING="6">'
            # Nested table for the probability bar with even spacing
            label += f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">'
            label += f'<TR><TD BGCOLOR="#f3f4f6" WIDTH="120" HEIGHT="16">'  # Fixed height for consistency
            # Center the probability bar vertically and only show green bar if probability > 0
            label += f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR>'
            if prob > 0:  # Only add green bar if probability is greater than 0
                label += f'<TD WIDTH="{int(120 * prob)}" BGCOLOR="#4ade80"></TD>'
            if prob < 1:  # Only add gray background if probability is less than 1
                label += f'<TD WIDTH="{int(120 * (1-prob))}" BGCOLOR="#f3f4f6"></TD>'
            label += '</TR></TABLE>'
            label += '</TD></TR></TABLE></TD>'
            # Percentage cell with increased padding
            label += f'<TD ALIGN="RIGHT" WIDTH="40" CELLPADDING="6"><FONT POINT-SIZE="10">{prob:.2%}</FONT></TD>'
            label += '</TR>\n'

    label += '</TABLE>>'
    return label

def create_network_dot(bn, ie=None, evidence=None):
    """Create a DOT representation of the Bayesian network with improved spacing"""
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB')  # Top to bottom layout
    dot.attr('graph',
             nodesep='0.5',  # Increased node separation
             ranksep='0.8',  # Increased rank separation
             splines='polyline'
             )

    # Set global node styles with improved margins
    dot.attr('node',
             shape='none',
             margin='0.3',  # Increased margin
             fontname='Arial'
             )

    # Group nodes by their layer
    layers = get_network_layers(bn)

    # Create subgraphs for each layer
    for layer_idx, layer_nodes in enumerate(layers):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for node_name in layer_nodes:
                posterior = None
                if ie is not None:
                    try:
                        posterior = ie.posterior(node_name)
                    except Exception:
                        pass

                label = create_node_label(node_name, posterior)

                if evidence and node_name in evidence:
                    s.node(node_name, label, color='#3b82f6', penwidth='2.0')
                else:
                    s.node(node_name, label)

    # Add edges with improved styling
    for arc in bn.arcs():
        tail = bn.variable(arc[0]).name()
        head = bn.variable(arc[1]).name()
        dot.edge(tail, head, penwidth='1.2', color='#64748b')

    return dot

def get_network_layers(bn):
    """Determine the hierarchical layers of nodes in the network"""
    layers = []
    processed_nodes = set()

    # Start with root nodes (nodes with no parents)
    current_layer = [bn.variable(node).name() for node in bn.nodes()
                     if len(list(bn.parents(node))) == 0]

    while current_layer:
        layers.append(current_layer)
        processed_nodes.update(current_layer)

        # Find children of current layer nodes that have all parents processed
        next_layer = []
        for node in bn.nodes():
            node_name = bn.variable(node).name()
            if node_name not in processed_nodes:
                parents = [bn.variable(p).name() for p in bn.parents(node)]
                if all(p in processed_nodes for p in parents):
                    next_layer.append(node_name)

        current_layer = next_layer

    return layers


def create_network_dot(bn, ie=None, evidence=None):
    """Create a DOT representation of the Bayesian network with optimized spacing"""
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB')

    # Optimize graph attributes for better width control
    dot.attr('graph',
             nodesep='0.3',  # Reduced node separation
             ranksep='0.5',  # Reduced rank separation
             splines='polyline',
             margin='0',  # Remove graph margin
             pad='0.2',  # Minimal padding
             )

    # Optimize node attributes
    dot.attr('node',
             shape='none',
             margin='0',
             fontname='Arial',
             width='0',  # Let node size be determined by content
             height='0'
             )

    # Group nodes by their layer
    layers = get_network_layers(bn)

    # Create subgraphs for each layer with optimized spacing
    for layer_idx, layer_nodes in enumerate(layers):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for node_name in layer_nodes:
                posterior = None
                if ie is not None:
                    try:
                        posterior = ie.posterior(node_name)
                    except Exception:
                        pass

                label = create_node_label(node_name, posterior)

                if evidence and node_name in evidence:
                    s.node(node_name, label, color='#3b82f6', penwidth='2.0')
                else:
                    s.node(node_name, label)

    # Add edges with minimal styling
    for arc in bn.arcs():
        tail = bn.variable(arc[0]).name()
        head = bn.variable(arc[1]).name()
        dot.edge(tail, head, penwidth='1.0', color='#64748b')

    return dot

def save_network_visualizations(bn, evidence=None):
    """Save three phases of network visualization"""
    # 1. Save network structure
    dot_structure = create_network_dot(bn)
    dot_structure.render('bn_structure', format='svg', cleanup=True)

    # 2. Save network with initial inference
    ie = gum.LazyPropagation(bn)
    ie.makeInference()
    dot_inference = create_network_dot(bn, ie)
    dot_inference.render('bn_inference', format='svg', cleanup=True)

    # 3. Save network with evidence
    if evidence:
        for node, value in evidence.items():
            ie.setEvidence({node: value})
        ie.makeInference()
        dot_evidence = create_network_dot(bn, ie, evidence)
        dot_evidence.render('bn_inference_with_evidence', format='svg', cleanup=True)

    return ie


def get_svg_dimensions(svg_file):
    """Get dimensions of an SVG file"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    width = float(root.get('width').replace('pt', ''))
    height = float(root.get('height').replace('pt', ''))
    return width, height


def combine_svg_files(output_file='combined_bn.svg'):
    """Combine SVG files into a single vertical layout with optimized width"""
    svg_files = ["bn_structure.svg", "bn_inference.svg", "bn_inference_with_evidence.svg"]
    titles = ["Network Structure", "Initial Inference", "Inference with Evidence"]

    # Get maximum content width and heights
    max_content_width = 0
    heights = []
    spacing = 30
    title_height = 30
    scale_factor = 0.8
    padding = 20  # Add small padding for margins

    for file in svg_files:
        if os.path.exists(file):
            width, height = get_svg_dimensions(file)
            max_content_width = max(max_content_width, width)
            heights.append(height)

    # Calculate optimized dimensions
    total_width = (max_content_width * scale_factor) + (2 * padding)
    total_height = sum(h * scale_factor for h in heights) + (len(heights) * (title_height + spacing))

    # Create new SVG document with optimized dimensions
    doc = minidom.Document()
    svg_root = doc.createElement('svg')
    svg_root.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    svg_root.setAttribute('width', f'{total_width}pt')
    svg_root.setAttribute('height', f'{total_height}pt')
    svg_root.setAttribute('viewBox', f'0 0 {total_width} {total_height}')
    doc.appendChild(svg_root)

    # Add styles
    style = doc.createElement('style')
    style.setAttribute('type', 'text/css')
    style.appendChild(doc.createTextNode('''
        .title { font-family: Arial; font-size: 14pt; font-weight: bold; text-align: center; }
    '''))
    svg_root.appendChild(style)

    # Add SVGs vertically with proper centering
    y_offset = 0
    existing_files = [f for f in svg_files if os.path.exists(f)]

    for i, file in enumerate(existing_files):
        title = titles[svg_files.index(file)]

        # Create a group for each section
        section_group = doc.createElement('g')
        section_group.setAttribute('transform', f'translate({padding},{y_offset})')

        # Add centered title
        text = doc.createElement('text')
        text.setAttribute('x', f'{(total_width - 2*padding) / 2}')
        text.setAttribute('y', f'{title_height / 2}')
        text.setAttribute('text-anchor', 'middle')
        text.setAttribute('class', 'title')
        text.appendChild(doc.createTextNode(title))
        section_group.appendChild(text)

        # Add SVG content with proper scaling
        tree = ET.parse(file)
        svg_content = tree.getroot()
        content_group = doc.createElement('g')
        transform = f'translate(0,{title_height}) scale({scale_factor})'
        content_group.setAttribute('transform', transform)

        for child in svg_content:
            if child.tag.split('}')[-1] != 'defs':  # Skip defs to avoid duplicate definitions
                content_group.appendChild(doc.importNode(minidom.parseString(ET.tostring(child)).documentElement, True))

        section_group.appendChild(content_group)
        svg_root.appendChild(section_group)

        y_offset += (heights[i] * scale_factor) + title_height + spacing

    # Save combined SVG
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc.toprettyxml())

    # Clean up temporary files
    for file in svg_files:
        if os.path.exists(file):
            os.remove(file)

def visualize_bayesian_network(bn, evidence=None):
    """Generate complete Bayesian network visualization"""
    ie = save_network_visualizations(bn, evidence)
    combine_svg_files('combined_bn.svg')
    return ie


# 7.执行推理：使用lazyPropagation推理引擎精确推断
ie = gum.LazyPropagation(bn)
# 没有新数据的推断
ie.makeInference()


print(ie.posterior("ScenarioResilience"))
print(ie.posterior("RecoveryCapacity"))

#evidence = {'AidResource': 0}
evidence = None
ie = visualize_bayesian_network(bn, evidence)


def save_bn_structure(bn, filepath):
    """
    Save the Bayesian network structure to a file.

    Parameters:
    bn (pyAgrum.BayesNet): The Bayesian network to save
    filepath (str): Path where to save the network structure
    """
    try:
        gum.saveBN(bn, filepath)
    except Exception as e:
        print(f"Error saving network structure: {e}")
        raise


def save_bn_parameters(bn, filepath):
    """
    Save the Bayesian network parameters (CPTs) to a JSON file.

    Parameters:
    bn (pyAgrum.BayesNet): The Bayesian network whose parameters to save
    filepath (str): Path where to save the parameters
    """
    parameters = {}

    # For each node in the network
    for node in bn.nodes():
        node_name = bn.variable(node).name()
        cpt = bn.cpt(node)

        # Get variables involved in this CPT (node and its parents)
        var_names = [bn.variable(parent).name() for parent in bn.parents(node)]
        var_names.append(node_name)  # Add the node itself

        # Get domain sizes and labels for all variables
        var_domains = {}
        for var in var_names:
            var_domains[var] = {
                'size': bn.variable(var).domainSize(),
                'labels': [bn.variable(var).label(i) for i in range(bn.variable(var).domainSize())]
            }

        # Convert CPT to dictionary format
        node_params = {
            'variables': var_names,
            'variable_domains': var_domains,
            'values': cpt.tolist()
        }
        parameters[node_name] = node_params

    # Save to JSON file
    try:
        with open(filepath, 'w') as f:
            json.dump(parameters, f, indent=4)
    except Exception as e:
        print(f"Error saving parameters: {e}")
        raise


def save_complete_bn(bn, directory):
    """
    Save both structure and parameters of the Bayesian network.

    Parameters:
    bn (pyAgrum.BayesNet): The Bayesian network to save
    directory (str): Directory where to save the files

    Returns:
    tuple: (structure_path, params_path) - Paths to the saved files
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Save structure
    structure_path = os.path.join(directory, 'bn_structure.bif')
    save_bn_structure(bn, structure_path)

    # Save parameters
    params_path = os.path.join(directory, 'bn_parameters.json')
    save_bn_parameters(bn, params_path)

    return structure_path, params_path


def load_bn(structure_path, params_path):
    """
    Load a Bayesian network from saved files.

    Parameters:
    structure_path (str): Path to the structure file
    params_path (str): Path to the parameters file

    Returns:
    pyAgrum.BayesNet: The loaded Bayesian network
    """
    try:
        # Load structure
        bn = gum.loadBN(structure_path)

        # Load parameters
        with open(params_path, 'r') as f:
            parameters = json.load(f)

        # Restore CPTs
        for node_name, node_params in parameters.items():
            cpt = bn.cpt(node_name)
            cpt.fillWith(node_params['values'])

        return bn
    except Exception as e:
        print(f"Error loading Bayesian network: {e}")
        raise

output_directory = "./scenario_bn"
structure_path, params_path = save_complete_bn(bn, output_directory)
print(f"Saved network structure to: {structure_path}")
print(f"Saved network parameters to: {params_path}")


def extract_node_data(bn):
    """
    Extract node data from a Bayesian network into a dictionary format.

    Args:
        bn: pyAgrum.BayesNet object

    Returns:
        dict: Dictionary where keys are node names and values are lists of tuples
              containing (state_name, probability)
    """
    node_data = {}
    ie = gum.LazyPropagation(bn)
    ie.makeInference()

    # State mapping dictionary from the original code
    state_mapping = {
        'roadPassibility': ['Impassable', 'Passable'],
        'emergencyType': ['Vehicle_Self_Accident', 'Vehicle_to_Fixed_Object_Accident', 'Collision_Acident'],
        'roadLoss': ['Not_Loss', 'Loss'],
        'casualties': ['No_Casualties', 'Casualties'],
        'AidResource': ['Not_Used', 'Used'],
        'TowResource': ['Not_Used', 'Used'],
        'FirefightingResource': ['Not_Used', 'Used'],
        'RescueResource': ['Not_Used', 'Used'],
        'emergencyPeriod': ['Early_Morning', 'Morning', 'Afternoon', 'Evening'],
        'responseDuration': ['0-15min', '15-30min', '30-60min', '60min+'],
        'disposalDuration': ['0-15min', '15-30min', '30-60min', '60min+'],
        'AbsorptionCapacity': ['Good', 'Bad'],
        'AdaptionCapacity': ['Good', 'Bad'],
        'RecoveryCapacity': ['Good', 'Bad'],
        'ScenarioResilience': ['Good', 'Bad']
    }

    # Iterate through all nodes in the network
    for node in bn.nodes():
        node_name = bn.variable(node).name()
        posterior = ie.posterior(node_name).tolist()

        # Get state names for this node
        states = state_mapping.get(node_name, [f"状态{i + 1}" for i in range(len(posterior))])

        # Create list of (state, probability) tuples
        node_states = list(zip(states, posterior))

        # Add to dictionary
        node_data[node_name] = node_states

    return node_data
node_data = extract_node_data(bn)
print(json.dumps(node_data, indent=4, ensure_ascii=False))
# 保存节点数据
with open(os.path.join(output_directory, 'node_data.json'), 'w', encoding='utf-8') as f:
    json.dump(node_data, f, indent=4, ensure_ascii=False)