# -*- coding: utf-8 -*-
# @Time    : 1/21/2025 12:01 AM
# @FileName: test8.py
# @Software: PyCharm
import json
import os
from typing import Dict, List, Tuple, Optional, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom
import ast

import graphviz
import numpy as np
import pandas as pd
import pyAgrum as gum
from owlready2 import *
from scipy.stats import truncnorm, norm


class FuzzyEvaluation:
    """处理模糊评估相关的功能"""
    def __init__(self):
        self.mapping_evaluation_fuzzy = {
            'VL': (0.0, 0.0, 0.1, 0.2),
            'L': (0.1, 0.2, 0.2, 0.3),
            'M': (0.2, 0.3, 0.4, 0.5),
            'H': (0.5, 0.6, 0.7, 0.8),
            'VH': (0.8, 0.9, 1.0, 1.0)
        }

    def calculate_fuzzy(self, row: pd.Series) -> List[Tuple[float, float, float, float]]:
        """将评估等级转换为模糊数"""
        return [self.mapping_evaluation_fuzzy[r] for r in row]

    def calculate_similarity(self, row: List[Tuple[float, float, float, float]]) -> Tuple[
        List[List[float]], List[float], List[float]]:
        """计算模糊数之间的相似度"""
        ss = []
        avg_similarity = []
        relative_similarity = []
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

        return ss, avg_similarity, relative_similarity

    def calculate_aggregated_fuzzy(self, row: List[Tuple[float, float, float, float]],
                                expert_weights: List[float], beta: float = 0.5) -> float:
        """计算聚合模糊数并进行清晰化"""
        aggrated_fuzzy = [0.0, 0.0, 0.0, 0.0]
        ss, avg_s, rela_s = self.calculate_similarity(row)
        cc = [(beta * expert_weights[i] + (1 - beta) * rela_s[i]) for i in range(len(rela_s))]
        weight = [i / sum(cc) for i in cc]

        for weights, tup in zip(weight, row):
            for i in range(len(tup)):
                aggrated_fuzzy[i] += tup[i] * weights

        a1, a2, a3, a4 = aggrated_fuzzy
        defuzzified_possibility = ((a4 + a3) ** 2 - a4 * a3 - (a1 + a2) ** 2 + a1 * a2) / (3 * (a4 + a3 - a2 - a1))
        return defuzzified_possibility


class ScenarioResilience:
    """情景韧性分析的主类"""

    def __init__(self, ontology_path: str):
        """
        初始化情景韧性分析器

        Args:
            ontology_path (str): 本体文件路径
        """
        self.onto = get_ontology(ontology_path).load()
        self.bn = gum.BayesNet('ScenarioDeductionBN')
        self.data_properties_info = []
        self.ie = None
        self.fuzzy_evaluator = FuzzyEvaluation()
        self.current_evidence = {}  # 添加追踪当前证据的属性

        # 定义状态映射
        self.state_mapping = {
            'roadPassibility': ['Impassable', 'Passable'],
            'emergencyType': ['Vehicle_Self_Accident', 'Vehicle_to_Fixed_Object_Accident', 'Collision_Accident'],
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

        # 定义因子-能力关系
        self.factor_capacity = {
            'AbsorptionScenario': ['roadPassibility', 'roadLoss'],
            'AdaptionScenario': ['emergencyType', 'emergencyPeriod'],
            'RecoveryScenario': ['AidResource', 'TowResource', 'FirefightingResource',
                                 'RescueResource', 'responseDuration', 'disposalDuration', 'casualties']
        }

    def process_expert_evaluation(self, expert_info_path: str, expert_estimation_path: str) -> pd.DataFrame:
        """处理专家评估数据"""
        # 读取专家信息和计算权重
        df_expert = pd.read_excel(expert_info_path)
        scores = df_expert.iloc[:, 1:].sum(axis=1)
        expert_weights = list(scores / scores.sum())

        # 读取并处理专家评估数据
        df = pd.read_excel(expert_estimation_path)
        df['fuzzy'] = df.iloc[:, -7:].apply(self.fuzzy_evaluator.calculate_fuzzy, axis=1)
        df['Condition'] = df['Condition'].tolist()

        # 计算条件概率
        condition_probability = []
        for row in df['fuzzy']:
            prob = self.fuzzy_evaluator.calculate_aggregated_fuzzy(row, expert_weights)
            condition_probability.append(prob)

        df['conditonProbability'] = condition_probability

        # 按组归一化
        normalized_prob = df.groupby(['Node', 'Condition']).apply(
            lambda group: pd.DataFrame({
                'conditonProbability': group['conditonProbability'] / group['conditonProbability'].sum()
            })
        )['conditonProbability']

        df['conditonProbability'] = normalized_prob.values
        return df

    def set_conditional_probabilities(self, df: pd.DataFrame) -> None:
        """
        设置贝叶斯网络的条件概率表

        Args:
            df (pd.DataFrame): 包含条件概率的数据框
        """
        # 创建索引列表
        index = []
        for _, row in df.iterrows():
            sublist = ast.literal_eval(row['Condition'])
            sublist.append(row['State'])
            index.append(sublist)

        # 创建CPT字典
        cpt = {
            'AbsorptionCapacity': self.bn.cpt('AbsorptionCapacity'),
            'AdaptionCapacity': self.bn.cpt('AdaptionCapacity'),
            'RecoveryCapacity': self.bn.cpt('RecoveryCapacity'),
            'ScenarioResilience': self.bn.cpt('ScenarioResilience')
        }

        # 填充条件概率
        for i, row in df.iterrows():
            idx = ast.literal_eval(','.join(str(x) for x in index[i]))
            cpt[row['Node']][idx] = row['conditonProbability']

        # 更新网络CPT
        for node in cpt:
            self.bn.cpt(node).fillWith(cpt[node])

    def extract_data_properties(self) -> None:
        """从本体中提取数据属性"""
        for dps in self.onto.data_properties():
            self.data_properties_info.append({
                "name": dps.name,
                "domain": dps.domain[0].name,
                "range": dps.range[0]
            })

        # 处理资源类型
        resource_info = next(item for item in self.data_properties_info
                             if item['name'] == 'resourceType')
        resources = ['AidResource', 'TowResource', 'FirefightingResource', 'RescueResource']

        for resource in resources:
            new_item = resource_info.copy()
            new_item['name'] = resource
            self.data_properties_info.append(new_item)

        self.data_properties_info = [item for item in self.data_properties_info
                                     if item['name'] != 'resourceType']

    def create_bayesian_network(self) -> None:
        """创建贝叶斯网络结构"""
        node_resilience = self.bn.add(gum.LabelizedVariable("ScenarioResilience",
                                                            'resilienceLevel', 2))

        for cls in self.onto.classes():
            if cls.name == "Scenario":
                self._process_scenario_class(cls)
            elif cls.name == "ResilienceInfluentialFactors":
                self._process_influential_factors(cls)

    def _process_scenario_class(self, cls: Any) -> None:
        """处理场景类以添加能力节点"""
        for capacity in cls.subclasses():
            capacity_name = f"{capacity.name.replace('Scenario', '')}Capacity"
            self.bn.add(gum.LabelizedVariable(capacity_name, 'capacityLevel', 2))
            self.bn.addArc(capacity_name, "ScenarioResilience")

    def _process_influential_factors(self, cls: Any) -> None:
        """处理影响因素以添加因子节点和弧"""
        for factor_property in cls.subclasses():
            for dp in self.data_properties_info:
                if dp['domain'] == factor_property.name:
                    self._add_factor_node(dp)

    def _add_factor_node(self, dp: Dict) -> None:
        """向贝叶斯网络添加因子节点"""
        if dp['name'] not in self.state_mapping:
            return

        self.bn.add(gum.LabelizedVariable(dp['name'], 'factorLevel',
                                          len(self.state_mapping[dp['name']])))

        for scenario in self._find_capacity_by_factor(dp['name']):
            capacity_name = f"{scenario.replace('Scenario', '')}Capacity"
            self.bn.addArc(dp['name'], capacity_name)

    def _find_capacity_by_factor(self, factor: str) -> List[str]:
        """找到与给定因子相关的能力"""
        return [key for key, values in self.factor_capacity.items()
                if factor in values]

    def set_prior_probabilities(self, data_path: str) -> None:
        """
        设置先验概率

        Args:
            data_path (str): 包含先验概率的Excel文件路径
        """
        data = pd.read_excel(data_path)
        df = pd.DataFrame(data)

        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            if len(self.bn.parents(node)) == 0:
                if node_name not in ["disposalDuration", "responseDuration"]:
                    self._set_discrete_prior(node_name, df[node_name])
                else:
                    self._set_continuous_prior(node_name, df[node_name])

    def _set_discrete_prior(self, node_name: str, data: pd.Series) -> None:
        """设置离散变量的先验概率"""
        category_counts = data.value_counts()
        probabilities = (category_counts / category_counts.sum()).tolist()
        self.bn.cpt(node_name).fillWith(probabilities)

    def _set_continuous_prior(self, node_name: str, data: pd.Series) -> None:
        """使用截断正态分布设置连续变量的先验概率"""
        truncated_normal = self._fit_truncated_normal(data)
        probs = [
            self._calculate_interval_probability(truncated_normal, 0, 15),
            self._calculate_interval_probability(truncated_normal, 15, 30),
            self._calculate_interval_probability(truncated_normal, 30, 60),
            1 - truncated_normal.cdf(60)
        ]
        self.bn.cpt(node_name).fillWith(probs)

    @staticmethod
    def _fit_truncated_normal(data: pd.Series) -> truncnorm:
        """拟合截断正态分布"""
        mu, std = norm.fit(data)
        lower = np.percentile(data, 5)
        upper = np.percentile(data, 95)
        a = (lower - mu) / std
        b = (upper - mu) / std
        return truncnorm(a, b, loc=mu, scale=std)

    @staticmethod
    def _calculate_interval_probability(dist: truncnorm, start: float, end: float) -> float:
        """计算截断正态分布中区间的概率"""
        return dist.cdf(end) - dist.cdf(start)

    def make_inference(self, evidence: Optional[Dict] = None) -> None:
        """
        在贝叶斯网络上执行推理

        Args:
            evidence (Dict, optional): 推理中要考虑的证据
        """
        self.ie = gum.LazyPropagation(self.bn)

        # 更新当前证据
        if evidence is not None:
            self.current_evidence = evidence.copy()
        else:
            self.current_evidence = {}  # 如果没有提供证据，则清空当前证据

        if self.current_evidence:
            for node, value in self.current_evidence.items():
                self.ie.setEvidence({node: value})

        self.ie.makeInference()

    def clear_evidence(self) -> None:
        """清除所有证据并重新进行推理"""
        self.current_evidence = {}
        self.make_inference()

    def save_network(self, output_dir: str) -> Tuple[str, str]:
        """
        保存贝叶斯网络结构和参数

        Args:
            output_dir (str): 保存网络文件的目录

        Returns:
            Tuple[str, str]: 保存的结构和参数文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        structure_path = os.path.join(output_dir, 'bn_structure.bif')
        params_path = os.path.join(output_dir, 'bn_parameters.json')

        self._save_structure(structure_path)
        self._save_parameters(params_path)
        self._save_node_data(output_dir)

        return structure_path, params_path

    def _save_structure(self, filepath: str) -> None:
        """保存网络结构到文件"""
        gum.saveBN(self.bn, filepath)

    def _save_parameters(self, filepath: str) -> None:
        """保存网络参数到JSON文件"""
        parameters = {}
        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            parameters[node_name] = self._get_node_parameters(node)

        with open(filepath, 'w') as f:
            json.dump(parameters, f, indent=4)

    def _get_node_parameters(self, node: int) -> Dict:
        """获取特定节点的参数"""
        node_name = self.bn.variable(node).name()
        var_names = [self.bn.variable(parent).name() for parent in self.bn.parents(node)]
        var_names.append(node_name)

        var_domains = {
            var: {
                'size': self.bn.variable(var).domainSize(),
                'labels': [self.bn.variable(var).label(i)
                           for i in range(self.bn.variable(var).domainSize())]
            }
            for var in var_names
        }

        return {
            'variables': var_names,
            'variable_domains': var_domains,
            'values': self.bn.cpt(node_name).tolist()
        }

    def _save_node_data(self, output_dir: str) -> None:
        """保存节点数据到JSON文件"""
        if not self.ie:
            self.make_inference()

        node_data = {}
        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            posterior = self.ie.posterior(node_name).tolist()
            states = self.state_mapping.get(node_name,
                                            [f"State{i + 1}" for i in range(len(posterior))])
            node_data[node_name] = list(zip(states, posterior))

        with open(os.path.join(output_dir, 'node_data.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(node_data, f, indent=4, ensure_ascii=False)


class NetworkVisualizer:
    """贝叶斯网络可视化类"""

    @staticmethod
    def create_node_label(node_name: str, posterior: Optional[np.ndarray] = None,
                         state_mapping: Dict[str, List[str]] = None) -> str:
        """创建更紧凑的节点标签"""
        # 减小内边距和字体大小
        label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" STYLE="ROUNDED">\n'
        label += f'<TR><TD COLSPAN="3" BORDER="1" CELLPADDING="4"><FONT POINT-SIZE="10">{node_name}</FONT></TD></TR>\n'

        if posterior is not None:
            probs = posterior.tolist()
            for i, prob in enumerate(probs):
                state_name = state_mapping.get(node_name, [f"State{i + 1}"])[i] if state_mapping else f"State{i + 1}"

                label += '<TR>'
                # 减小状态名称和概率条的宽度
                label += f'<TD WIDTH="60" ALIGN="RIGHT" PORT="f{i}" CELLPADDING="3"><FONT POINT-SIZE="9">{state_name}</FONT></TD>'
                label += f'<TD WIDTH="80" ALIGN="LEFT" BGCOLOR="white" CELLPADDING="3">'
                label += f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
                label += f'<TR><TD BGCOLOR="#f3f4f6" WIDTH="80" HEIGHT="12">'
                label += f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR>'
                if prob > 0:
                    label += f'<TD WIDTH="{int(80 * prob)}" BGCOLOR="#4ade80"></TD>'
                if prob < 1:
                    label += f'<TD WIDTH="{int(80 * (1 - prob))}" BGCOLOR="#f3f4f6"></TD>'
                label += '</TR></TABLE>'
                label += '</TD></TR></TABLE></TD>'
                label += f'<TD ALIGN="RIGHT" WIDTH="30" CELLPADDING="3"><FONT POINT-SIZE="9">{prob:.2%}</FONT></TD>'
                label += '</TR>\n'

        label += '</TABLE>>'
        return label

    @staticmethod
    def get_network_layers(bn: gum.BayesNet) -> List[List[str]]:
        """确定网络中节点的层次结构"""
        layers = []
        processed_nodes = set()

        # 开始于根节点（无父节点的节点）
        current_layer = [bn.variable(node).name() for node in bn.nodes()
                         if len(list(bn.parents(node))) == 0]

        while current_layer:
            layers.append(current_layer)
            processed_nodes.update(current_layer)

            # 找出当前层节点的子节点
            next_layer = []
            for node in bn.nodes():
                node_name = bn.variable(node).name()
                if node_name not in processed_nodes:
                    parents = [bn.variable(p).name() for p in bn.parents(node)]
                    if all(p in processed_nodes for p in parents):
                        next_layer.append(node_name)

            current_layer = next_layer

        return layers

    def create_network_dot(self, bn: gum.BayesNet, ie: Optional[gum.LazyPropagation] = None,
                           evidence: Optional[Dict] = None, state_mapping: Optional[Dict] = None) -> graphviz.Digraph:
        """创建水平布局的贝叶斯网络DOT表示"""
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR')
        dot.attr('graph',
                 nodesep='0.15',
                 ranksep='0.2',
                 splines='ortho',
                 margin='0',
                 pad='0.05')
        dot.attr('node',
                 shape='none',
                 margin='0',
                 fontname='Arial',
                 width='0',
                 height='0')
        dot.attr('edge',
                 penwidth='0.8',
                 color='#64748b')

        layers = self.get_network_layers(bn)
        for layer_idx, layer_nodes in enumerate(layers):
            with dot.subgraph() as s:
                s.attr(rank='same')
                for node_name in layer_nodes:
                    # 确保使用正确的后验概率
                    posterior = None
                    if ie is not None:
                        # 使用 try-except 来处理可能的错误
                        try:
                            # 对于有证据的节点，获取其确定性分布
                            if evidence and node_name in evidence:
                                # 创建一个确定性分布
                                domain_size = bn.variable(node_name).domainSize()
                                posterior = np.zeros(domain_size)
                                posterior[evidence[node_name]] = 1.0
                            else:
                                # 对于没有证据的节点，获取后验分布
                                posterior = ie.posterior(node_name)
                        except Exception as e:
                            print(f"Error getting posterior for {node_name}: {e}")
                            continue

                    label = self.create_node_label(node_name, posterior, state_mapping)

                    if evidence and node_name in evidence:
                        s.node(node_name, label, color='#3b82f6', penwidth='1.5')
                    else:
                        s.node(node_name, label)

        for arc in bn.arcs():
            tail = bn.variable(arc[0]).name()
            head = bn.variable(arc[1]).name()
            dot.edge(tail, head)

        return dot

    def visualize_network(self, bn: gum.BayesNet, output_dir: str,
                          evidence: Optional[Dict] = None,
                          state_mapping: Optional[Dict] = None,
                          ie: Optional[gum.LazyPropagation] = None) -> gum.LazyPropagation:
        """生成完整的贝叶斯网络可视化"""
        os.makedirs(output_dir, exist_ok=True)

        # 清理旧的evidence文件
        evidence_file = os.path.join(output_dir, 'bn_inference_with_evidence.svg')
        if os.path.exists(evidence_file):
            os.remove(evidence_file)

        # 1. 保存网络结构
        dot_structure = self.create_network_dot(bn)
        dot_structure.render(os.path.join(output_dir, 'bn_structure'), format='svg', cleanup=True)

        # 2. 创建一个新的推理引擎用于初始状态
        initial_ie = gum.LazyPropagation(bn)
        initial_ie.makeInference()

        # 保存初始推理结果（无证据状态）
        dot_inference = self.create_network_dot(bn, initial_ie, None, state_mapping)
        dot_inference.render(os.path.join(output_dir, 'bn_inference'), format='svg', cleanup=True)

        # 3. 使用提供的推理引擎处理证据状态
        current_ie = ie if ie is not None else gum.LazyPropagation(bn)

        # 4. 如果有证据，创建带证据的图形
        if evidence:
            dot_evidence = self.create_network_dot(bn, current_ie, evidence, state_mapping)
            dot_evidence.render(os.path.join(output_dir, 'bn_inference_with_evidence'), format='svg', cleanup=True)

        self.combine_visualizations(output_dir)
        return current_ie

    def combine_visualizations(self, output_dir: str) -> None:
        """创建水平布局的组合可视化"""
        # 只获取实际存在的SVG文件
        all_svg_files = ["bn_structure.svg", "bn_inference.svg", "bn_inference_with_evidence.svg"]
        all_titles = ["Network Structure", "Initial Inference", "Inference with Evidence"]

        svg_files = []
        titles = []
        for file, title in zip(all_svg_files, all_titles):
            if os.path.exists(os.path.join(output_dir, file)):
                svg_files.append(file)
                titles.append(title)

        # 计算布局参数
        total_width = 0
        max_height = 0
        spacing = 50
        title_height = 30

        dimensions = []
        for f in svg_files:
            filepath = os.path.join(output_dir, f)
            width, height = self._get_svg_dimensions(filepath)
            dimensions.append((width, height))
            total_width += width + spacing
            max_height = max(max_height, height + title_height)

        # 创建合并的SVG
        doc = minidom.Document()
        svg_root = doc.createElement('svg')
        svg_root.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

        viewbox_width = total_width
        viewbox_height = max_height + spacing
        svg_root.setAttribute('viewBox', f'0 0 {viewbox_width} {viewbox_height}')
        svg_root.setAttribute('width', '100%')
        svg_root.setAttribute('height', '100%')
        svg_root.setAttribute('preserveAspectRatio', 'xMidYMid meet')

        doc.appendChild(svg_root)

        # 添加样式
        style = doc.createElement('style')
        style.setAttribute('type', 'text/css')
        style.appendChild(doc.createTextNode('''
            .title { font-family: Arial; font-size: 12pt; font-weight: bold; }
            @media (max-width: 1200px) { .title { font-size: 10pt; } }
            @media (max-width: 800px) { .title { font-size: 8pt; } }
        '''))
        svg_root.appendChild(style)

        # 水平布局合并SVG文件
        x_offset = spacing / 2
        for i, file in enumerate(svg_files):
            filepath = os.path.join(output_dir, file)

            # 添加标题
            title = titles[i]
            text = doc.createElement('text')
            text.setAttribute('x', str(x_offset + dimensions[i][0] / 2))
            text.setAttribute('y', str(spacing / 2))
            text.setAttribute('text-anchor', 'middle')
            text.setAttribute('class', 'title')
            text.appendChild(doc.createTextNode(title))
            svg_root.appendChild(text)

            # 添加SVG内容
            tree = ET.parse(filepath)
            svg_content = tree.getroot()

            for child in svg_content:
                if child.tag.split('}')[-1] != 'defs':
                    imported = doc.importNode(
                        minidom.parseString(ET.tostring(child)).documentElement, True)
                    group = doc.createElement('g')
                    group.setAttribute('transform', f'translate({x_offset},{title_height})')
                    group.appendChild(imported)
                    svg_root.appendChild(group)

            x_offset += dimensions[i][0] + spacing

        # 保存合并后的SVG
        with open(os.path.join(output_dir, 'combined_visualization.svg'), 'w',
                  encoding='utf-8') as f:
            f.write(doc.toprettyxml())


    @staticmethod
    def _get_svg_dimensions(filepath: str) -> Tuple[float, float]:
        """获取SVG文件的尺寸"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        width = float(root.get('width').replace('pt', ''))
        height = float(root.get('height').replace('pt', ''))
        return width, height

    def _create_combined_svg(self, output_dir: str, svg_files: List[str],
                             titles: List[str], width: float, height: float) -> None:
        """创建合并的SVG文件"""
        doc = minidom.Document()
        svg_root = doc.createElement('svg')
        svg_root.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
        svg_root.setAttribute('width', f'{width}pt')
        svg_root.setAttribute('height', f'{height}pt')
        svg_root.setAttribute('viewBox', f'0 0 {width} {height}')
        doc.appendChild(svg_root)

        # 添加样式
        style = doc.createElement('style')
        style.setAttribute('type', 'text/css')
        style.appendChild(doc.createTextNode('''
            .title { font-family: Arial; font-size: 14pt; font-weight: bold; }
        '''))
        svg_root.appendChild(style)

        # 合并SVG文件
        y_offset = 40  # 增加初始偏移
        spacing = 100  # 保持与上面相同的间距值

        for i, file in enumerate(svg_files):
            filepath = os.path.join(output_dir, file)
            if not os.path.exists(filepath):
                continue

            # 添加标题
            title = titles[i] if i < len(titles) else f"Visualization {i + 1}"
            text = doc.createElement('text')
            text.setAttribute('x', str(width / 2))
            text.setAttribute('y', str(y_offset))
            text.setAttribute('text-anchor', 'middle')
            text.setAttribute('class', 'title')
            text.appendChild(doc.createTextNode(title))
            svg_root.appendChild(text)

            y_offset += 40  # 标题和内容之间的间距

            # 添加SVG内容
            tree = ET.parse(filepath)
            svg_content = tree.getroot()
            content_width, content_height = self._get_svg_dimensions(filepath)

            for child in svg_content:
                if child.tag.split('}')[-1] != 'defs':
                    imported = doc.importNode(
                        minidom.parseString(ET.tostring(child)).documentElement, True)
                    group = doc.createElement('g')
                    group.setAttribute('transform', f'translate(0,{y_offset})')
                    group.appendChild(imported)
                    svg_root.appendChild(group)

            y_offset += content_height + spacing  # 添加内容高度和间距

        # 保存合并后的SVG
        with open(os.path.join(output_dir, 'combined_visualization.svg'), 'w',
                  encoding='utf-8') as f:
            f.write(doc.toprettyxml())


def update_with_evidence(analyzer: ScenarioResilience, evidence: Optional[Dict[str, int]] = None) -> None:
    """使用新证据更新贝叶斯网络，如果没有提供证据则清除现有证据"""
    # 执行推理
    if evidence is None:
        analyzer.clear_evidence()
    else:
        analyzer.make_inference(evidence)

    # 获取后验概率
    print("\nPosterior Probabilities after Evidence:")
    print("ScenarioResilience:", analyzer.ie.posterior("ScenarioResilience"))
    print("RecoveryCapacity:", analyzer.ie.posterior("RecoveryCapacity"))

    # 可视化更新后的网络，传入当前的推理引擎
    visualizer = NetworkVisualizer()
    ie = visualizer.visualize_network(
        bn=analyzer.bn,
        output_dir="./scenario_bn",
        evidence=analyzer.current_evidence,
        state_mapping=analyzer.state_mapping,
        ie=analyzer.ie
    )

def main():
    """主函数演示用法"""
    # 初始化分析器
    analyzer = ScenarioResilience(r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Scenario.owl")

    # 提取数据属性
    analyzer.extract_data_properties()

    # 创建贝叶斯网络结构
    analyzer.create_bayesian_network()

    # 设置先验概率
    analyzer.set_prior_probabilities(r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\prior prob test.xlsx")

    # 处理专家评估
    expert_df = analyzer.process_expert_evaluation(
        expert_info_path=r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\expertInfo.xlsx",
        expert_estimation_path=r"C:\Users\Tsing_loong\Desktop\Work Section\推演代码合成\推演代码合成\expert estimation test.xlsx"
    )

    # 设置条件概率表
    analyzer.set_conditional_probabilities(expert_df)

    # 执行推理
    analyzer.make_inference()

    # 保存网络
    structure_path, params_path = analyzer.save_network("./scenario_bn")
    print(f"Network structure saved to: {structure_path}")
    print(f"Network parameters saved to: {params_path}")

    # 可视化网络
    visualizer = NetworkVisualizer()
    ie = visualizer.visualize_network(
        bn=analyzer.bn,
        output_dir="./scenario_bn",
        state_mapping=analyzer.state_mapping
    )

    # 打印最终的推理结果
    print("\nScenario Resilience Posterior Probability:")
    print(ie.posterior("ScenarioResilience"))
    print("\nRecovery Capacity Posterior Probability:")
    print(ie.posterior("RecoveryCapacity"))

    evidence = {'AidResource': 0}

    update_with_evidence(analyzer, evidence)

    evidence = {'TowResource': 1}
    update_with_evidence(analyzer, evidence)




if __name__ == "__main__":
    main()