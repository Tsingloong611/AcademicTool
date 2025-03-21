# -*- coding: utf-8 -*-
# @Time    : 1/21/2025 10:27 AM
# @FileName: bn_svg_update.py
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
from matplotlib import pyplot as plt
from owlready2 import *
from scipy.stats import truncnorm, norm

from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.dialogs.missing_data_dialog import get_missing_rows, MissingDataDialog


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

            current_avg = sum(temp) / len(temp) if temp else 1.0  # Default to 1.0 if no comparisons
            avg_similarity.append(current_avg)
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
        self.ontology_path = ontology_path

        self.state_numb_dict = {
            'roadPassibility': [0, 1],
            'emergencyType': [0, 1, 2],
            'roadLoss': [0, 1],
            'casualties': [0, 1],
            'AidResource': [0, 1],
            'TowResource': [0, 1],
            'FirefightingResource': [0, 1],
            'RescueResource': [0, 1],
            'emergencyPeriod': [0, 1, 2, 3],
            'responseDuration': [0, 1, 2, 3],
            'disposalDuration': [0, 1, 2, 3],
            'AbsorptionCapacity': [0, 1],
            'AdaptionCapacity': [0, 1],
            'RecoveryCapacity': [0, 1],
            'ScenarioResilience': [0, 1]
        }

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
            "AbsorptionCapacity": ["roadPassibility", "roadLoss"],
            "AdaptionCapacity": ["emergencyPeriod", "emergencyType", "casualties"],
            "RecoveryCapacity": ["disposalDuration", "responseDuration",
                                 "RescueResource", "FirefightingResource", "TowResource", "AidResource"],
            "ScenarioResilience": ["RecoveryCapacity", "AdaptionCapacity", "AbsorptionCapacity"]
        }

    def process_expert_evaluation(self, expert_info_path: str, expert_estimation_path: str) -> pd.DataFrame:
        """处理专家评估数据（改进版，允许部分缺失专家数据）"""
        # 读取专家信息和计算权重
        df_expert = pd.read_excel(expert_info_path)
        scores = df_expert.iloc[:, 1:].sum(axis=1)
        expert_weights = list(scores / scores.sum())

        # 读取并处理专家评估数据
        df = pd.read_excel(expert_estimation_path)

        # 注：这里不再直接对整行 dropna，而是只对其他必填项做检查，
        # 如果仅专家列缺失则允许继续处理（只使用可用的专家数据）
        # 例如：检查除专家列之外的列是否存在缺失值
        non_expert_columns = [col for col in df.columns if not re.match(r'^E\d+$', col)]
        missing_non_expert = df[non_expert_columns].isna().any(axis=1)
        if missing_non_expert.any():
            # 这里可以弹出对话框提示用户
            dialog = MissingDataDialog(df.loc[missing_non_expert, non_expert_columns])
            dialog.exec()
            # 根据需求决定是否舍弃这些行
            df = df.loc[~missing_non_expert].copy()

        # 动态获取专家列（假定列名格式为 E1, E2, ...）
        expert_columns = [col for col in df.columns if re.match(r'^E\d+$', col)]
        expert_columns.sort(key=lambda x: int(x[1:]))

        # 对每一行，只提取非空的专家数据及对应权重
        def extract_fuzzy_and_weights(row: pd.Series) -> pd.Series:
            fuzzy_values = []
            used_weights = []
            for col in expert_columns:
                val = row[col]
                if pd.notna(val):
                    key = str(val).strip()
                    if key in self.fuzzy_evaluator.mapping_evaluation_fuzzy:
                        fuzzy_values.append(self.fuzzy_evaluator.mapping_evaluation_fuzzy[key])
                        # 根据专家列在 expert_columns 中的位置获取对应的权重
                        expert_index = expert_columns.index(col)
                        used_weights.append(expert_weights[expert_index])
                    else:
                        # 若评估值不在映射中，可选择记录警告或跳过
                        print(f"Warning: 未识别的评估值 '{key}' 在列 {col}")
            return pd.Series({'fuzzy': fuzzy_values, 'used_weights': used_weights})

        # 使用新函数生成两个新列：fuzzy 和 used_weights
        df[['fuzzy', 'used_weights']] = df[expert_columns].apply(extract_fuzzy_and_weights, axis=1)

        # 计算条件概率：对每一行，使用仅有的专家数据及对应权重进行聚合
        condition_probability = []
        for idx, row in df.iterrows():
            fuzzy_list = row['fuzzy']
            weights_list = row['used_weights']
            if len(fuzzy_list) > 0:
                prob = self.fuzzy_evaluator.calculate_aggregated_fuzzy(fuzzy_list, weights_list)
            else:
                # 若某行完全没有专家数据，可设置默认值或抛出错误
                prob = 0.0
                print(f"Warning: 节点 {row['Node']} 的行 {idx} 没有任何专家评估数据")
            condition_probability.append(prob)

        df['conditonProbability'] = condition_probability

        print("\n===== 归一化前 =====")
        print(df[['Node', 'Condition', 'State', 'conditonProbability']])

        df = self._fill_missing_binary_states(df)

        # 按组归一化
        df['conditonProbability'] = df.groupby(['Node', 'Condition'])['conditonProbability'] \
            .transform(lambda x: x / x.sum())

        print("\n===== 归一化后 =====")
        print(df[['Node', 'Condition', 'State', 'conditonProbability']])
        return df

    def _fill_missing_binary_states(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对二元节点的 (Node, Condition) 分组进行检查，如果只出现了一种状态，
        则自动补齐另一种状态的行，且设概率 = 1 - 已有概率。
        """
        new_rows = []

        # 按 (Node, Condition) 分组遍历
        grouped = df.groupby(['Node', 'Condition'], as_index=False, group_keys=False)
        for (node, cond), group_data in grouped:
            # 如果此 node 是二元节点
            if node in self.state_mapping and len(self.state_mapping[node]) == 2:
                # print(f"Checking binary node: {node} ({cond}), group data: {group_data}")
                if len(group_data) == 1:
                    # 只有一条记录，检查缺失状态
                    print(f"Only one row for {node} ({cond}), checking for missing state")
                    existing_state = group_data['State'].iloc[0]
                    existing_prob = group_data['conditonProbability'].iloc[0]

                    all_states = set(self.state_numb_dict[node])
                    print(f"All states: {all_states}")
                    print(f"Existing state: {existing_state}")
                    missing_states = list(all_states - {existing_state})
                    print(f"Missing states: {missing_states}")

                    # 如果确实缺少另一种状态，就补齐
                    if len(missing_states) == 1:
                        missing_state = missing_states[0]
                        # 复制group_data那一行的其他列，再改 State, conditonProbability
                        row_copy = group_data.iloc[0].copy()
                        row_copy['State'] = missing_state
                        row_copy['conditonProbability'] = 1 - existing_prob
                        new_rows.append(row_copy)
                        print(f"Added missing row for {node} ({cond}): {missing_state}, {1 - existing_prob}")

        if new_rows:
            # 把补齐的行合并回去
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        return df

    def set_conditional_probabilities(self, df: pd.DataFrame) -> None:
        """使用字典索引方式设置贝叶斯网络的条件概率表"""
        # 按节点分组处理数据
        grouped_df = df.groupby('Node')

        for node, node_df in grouped_df:
            try:
                print(f"\n处理节点: {node}")

                # 获取节点的父节点
                node_id = self.bn.idFromName(node)
                parent_ids = list(self.bn.parents(node_id))
                actual_parents = [self.bn.variable(p).name() for p in parent_ids]

                print(f"节点 {node} 的父节点: {actual_parents}")

                # 处理每个条件概率
                for _, row in node_df.iterrows():
                    condition_str = row['Condition']
                    state = int(row['State'])
                    prob = row['conditonProbability']

                    # 解析条件
                    if isinstance(condition_str, str):
                        condition = ast.literal_eval(condition_str)
                    else:
                        condition = condition_str

                    # 创建条件字典
                    condition_dict = {}

                    # 对于每个节点，尝试两种索引方式
                    # 1. 标准方式：将条件与父节点一一对应
                    standard_dict = {}
                    for i, parent in enumerate(actual_parents):
                        if i < len(condition):
                            standard_dict[parent] = condition[i]

                    # 2. 使用 factor_capacity 中定义的顺序（如果存在）
                    factor_dict = {}
                    if node in self.factor_capacity:
                        expected_parents = self.factor_capacity[node]
                        print(f"预期父节点顺序: {expected_parents}")

                        for i, expected_parent in enumerate(expected_parents):
                            if i < len(condition) and expected_parent in actual_parents:
                                factor_dict[expected_parent] = condition[i]

                    # 判断哪个字典更合适
                    if factor_dict and len(factor_dict) == len(actual_parents):
                        condition_dict = factor_dict
                    else:
                        condition_dict = standard_dict

                    # 检查条件字典是否完整
                    if len(condition_dict) != len(actual_parents):
                        print(f"警告: 条件字典不完整 {condition_dict}，需要 {len(actual_parents)} 个父节点")
                        continue

                    try:
                        # 首先获取当前条件下的所有状态概率
                        current_probs = list(self.bn.cpt(node)[condition_dict])

                        # 更新特定状态的概率
                        current_probs[state] = prob

                        # 设置整个条件下的概率分布
                        self.bn.cpt(node)[condition_dict] = current_probs

                        print(f"成功设置 {node} {condition_dict} 状态 {state} 的概率: {prob}")

                        # 检查设置是否成功
                        actual_prob = self.bn.cpt(node)[{**condition_dict, node: state}]
                        print(f"验证: {node} {condition_dict} 状态 {state} 的概率: {actual_prob}")


                    except Exception as e:
                        print(f"设置 {node} {condition_dict} 时出错: {e}")

                        # 尝试使用索引元组方式作为备选方案
                        try:
                            # 构建索引元组
                            idx_tuple = []
                            for parent in actual_parents:
                                idx_tuple.append(condition_dict[parent])
                            idx_tuple.append(state)

                            # 使用索引元组设置CPT
                            self.bn.cpt(node)[tuple(idx_tuple)] = prob
                            print(f"使用索引元组成功设置 {node} {tuple(idx_tuple)} = {prob}")
                        except Exception as e2:
                            print(f"索引元组方式也失败: {e2}")

            except Exception as e:
                print(f"处理节点 {node} 时出错: {e}")
                import traceback
                print(traceback.format_exc())

        # 完成后验证所有CPT
        self._verify_all_cpts()

    def _verify_all_cpts(self):
        """验证所有节点的CPT是否正确设置和归一化"""
        print("\n验证所有CPT:")
        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            parent_ids = list(self.bn.parents(node))

            if not parent_ids:  # 根节点
                probs = self.bn.cpt(node_name).tolist()
                total = sum(probs)
                print(f"根节点 {node_name} 的概率和: {total}")
                if not abs(total - 1.0) < 1e-10:
                    print(f"警告: 根节点 {node_name} 的概率和不为1")
            else:
                # 获取所有父节点的取值范围
                parent_vars = [self.bn.variable(p) for p in parent_ids]
                parent_domains = [var.domainSize() for var in parent_vars]
                parent_names = [var.name() for var in parent_vars]

                # 获取所有可能的父节点组合
                all_combinations = list(itertools.product(*[range(dom) for dom in parent_domains]))

                for combo in all_combinations:
                    # 创建条件字典
                    cond_dict = {parent_names[i]: combo[i] for i in range(len(parent_names))}

                    # 获取该条件下的所有状态概率
                    probs = self.bn.cpt(node_name)[cond_dict]
                    total = sum(probs)

                    if not abs(total - 1.0) < 1e-10:
                        print(f"警告: 节点 {node_name} 条件 {cond_dict} 下的概率和为 {total}")

        print("CPT验证完成")

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

    def _node_exists(self, node_name: str) -> bool:
        """检查节点是否存在于贝叶斯网络中"""
        try:
            # 尝试通过名称获取节点ID
            node_id = self.bn.idFromName(node_name)
            return self.bn.exists(node_id)
        except Exception:
            # 如果上面的方法失败，尝试直接使用名称
            try:
                return self.bn.exists(node_name)
            except Exception:
                # 如果both方法都失败，假设节点不存在
                return False

    def create_bayesian_network(self) -> None:
        """创建贝叶斯网络结构，确保按照 factor_capacity 中定义的顺序添加节点和弧"""
        print("开始创建贝叶斯网络...")

        # 首先创建所有节点（但不添加弧）
        for node_name in self.state_mapping.keys():
            if not self._node_exists(node_name):
                domain_size = len(self.state_mapping[node_name])
                self.bn.add(gum.LabelizedVariable(node_name, f'{node_name}_states', domain_size))
                print(f"创建节点: {node_name}，域大小: {domain_size}")

        # 然后按照 factor_capacity 中的顺序添加弧
        for scenario, factors in self.factor_capacity.items():
            if scenario == 'ScenarioResilience':
                # 特殊处理根节点
                for capacity in factors:  # 按照定义的顺序添加弧
                    if not self.bn.existsArc(capacity, "ScenarioResilience"):
                        self.bn.addArc(capacity, "ScenarioResilience")
                        print(f"添加弧: {capacity} -> ScenarioResilience")
            else:
                # 处理其他能力节点
                capacity_name = f"{scenario.replace('Scenario', 'Capacity')}"
                # 确保按照 factor_capacity 中定义的确切顺序添加弧
                for factor in factors:
                    if not self.bn.existsArc(factor, capacity_name):
                        self.bn.addArc(factor, capacity_name)
                        print(f"添加弧: {factor} -> {capacity_name}")

        # 打印最终的网络结构以验证
        print("\n=== 最终网络结构 ===")
        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            parents = [self.bn.variable(p).name() for p in self.bn.parents(node)]
            print(f"节点: {node_name}, 父节点: {parents}")
            if parents:
                # 检查父节点顺序是否与 factor_capacity 一致
                for scenario, factors in self.factor_capacity.items():
                    if scenario.replace('Scenario', 'Capacity') == node_name:
                        if parents != factors:
                            print(f"警告: {node_name} 的父节点顺序与 factor_capacity 不一致!")
                            print(f"  - 实际顺序: {parents}")
                            print(f"  - 期望顺序: {factors}")
                        break
                if node_name == "ScenarioResilience":
                    if parents != self.factor_capacity["ScenarioResilience"]:
                        print(f"警告: ScenarioResilience 的父节点顺序与 factor_capacity 不一致!")
                        print(f"  - 实际顺序: {parents}")
                        print(f"  - 期望顺序: {self.factor_capacity['ScenarioResilience']}")

        print("贝叶斯网络创建完成")

    def _process_scenario_class(self, cls: Any) -> None:
        """处理场景类以添加能力节点"""
        for capacity in cls.subclasses():
            capacity_name = f"{capacity.name.replace('Scenario', 'Capacity')}"
            if not self._node_exists(capacity_name):
                self.bn.add(gum.LabelizedVariable(capacity_name, 'capacityLevel', 2))
                if not self.bn.existsArc(capacity_name, "ScenarioResilience"):
                    self.bn.addArc(capacity_name, "ScenarioResilience")

    def _process_influential_factors(self, cls: Any) -> None:
        """处理影响因素以添加因子节点和弧"""
        for factor_property in cls.subclasses():
            for dp in self.data_properties_info:
                if dp['domain'] == factor_property.name:
                    self._add_factor_node(dp)

    def _add_factor_node(self, dp: Dict) -> None:
        print(f"Attempting to add factor node: {dp['name']}")
        if dp['name'] not in self.state_mapping:
            print(f"Warning: {dp['name']} not found in state_mapping")
            return

        if not self._node_exists(dp['name']):
            self.bn.add(gum.LabelizedVariable(dp['name'], 'factorLevel',
                                              len(self.state_mapping[dp['name']])))
            print(f"Added node: {dp['name']}")
        else:
            print(f"Node {dp['name']} already exists, skipping addition")

        for scenario in self._find_capacity_by_factor(dp['name']):
            capacity_name = f"{scenario.replace('Scenario', 'Capacity')}"
            print(f"Attempting to add arc from {dp['name']} to {capacity_name}")
            try:
                if self._node_exists(capacity_name):
                    if not self.bn.existsArc(dp['name'], capacity_name):
                        self.bn.addArc(dp['name'], capacity_name)
                        print(f"Added arc: {dp['name']} -> {capacity_name}")
                    else:
                        print(f"Arc from {dp['name']} to {capacity_name} already exists")
                else:
                    print(f"Warning: Node {capacity_name} does not exist")
            except Exception as e:
                print(f"Error adding arc from {dp['name']} to {capacity_name}: {e}")

    def _find_capacity_by_factor(self, factor: str) -> List[str]:
        """找到与给定因子相关的能力"""
        return [key for key, values in self.factor_capacity.items()
                if factor in values]

    def set_prior_probabilities(self, data_path: str) -> None:
        data = pd.read_excel(data_path)
        df = pd.DataFrame(data)

        for node in self.bn.nodes():
            node_name = self.bn.variable(node).name()
            if len(self.bn.parents(node)) == 0:
                if node_name in df.columns:
                    if node_name not in ["disposalDuration", "responseDuration"]:
                        self._set_discrete_prior(node_name, df[node_name])
                    else:
                        self._set_continuous_prior(node_name, df[node_name])
                else:
                    print(
                        f"Warning: Column {node_name} not found in the dataframe. Skipping prior probability setting for this node.")

    def _set_discrete_prior(self, node_name: str, data: pd.Series) -> None:
        """设置离散变量的先验概率"""
        # category_counts = data.value_counts()
        # probabilities = (category_counts / category_counts.sum()).tolist()
        # self.bn.cpt(node_name).fillWith(probabilities)
        category_probabilities = data.value_counts(normalize=True).sort_index().tolist()
        print(category_probabilities)
        self.bn.cpt(node_name).fillWith(category_probabilities)

    def _set_continuous_prior(self, node_name: str, data: pd.Series) -> None:
        """使用截断正态分布设置连续变量的先验概率"""
        truncated_normal = self._fit_truncated_normal(data)
        self.draw_thorm(node_name, truncated_normal, data, debug=True)
        probs = [
            self._calculate_interval_probability(truncated_normal, 0, 15),
            self._calculate_interval_probability(truncated_normal, 15, 30),
            self._calculate_interval_probability(truncated_normal, 30, 60),
            1 - truncated_normal.cdf(60)
        ]
        self.bn.cpt(node_name).fillWith(probs)


    def draw_thorm(self,node_name:str,truncated_normal: truncnorm, data: pd.Series, debug = False) -> None:
        # 绘图，以便调试
        if not debug:
            return
        data = data.dropna()
        mu, std = norm.fit(data)

        lower_bound = np.percentile(data, 5)  # 5th percentile
        upper_bound = np.percentile(data, 95)  # 95th percentile

        a = (lower_bound - mu) / std  # Lower bound in terms of z-score
        b = (upper_bound - mu) / std  # Upper bound in terms of z-score
        #     a = (min(data) - mu) / std  # Lower bound in terms of z-score
        #     b = (max(data) - mu) / std  # Upper bound in terms of z-score
        # Generate sampled values from the truncated normal distribution
        sampled_values = truncated_normal.rvs(size=1000)

        plt.figure(figsize=(10, 6))
        plt.hist(sampled_values, bins=50, density=True, alpha=0.6, color='g', label='Data Histogram')

        # 绘制截断正态分布曲线
        #     x = np.linspace(min(data), max(data), 1000)
        # x = np.linspace(truncnorm.ppf(0.01, a, b),
        #                 truncnorm.ppf(0.99, a, b), 100)
        x = np.linspace(lower_bound, upper_bound, 1000)
        p = truncated_normal.pdf(x)
        plt.plot(x, p, 'k-', linewidth=2, label=f'Truncated Normal Fit (μ={mu:.2f}, σ={std:.2f})')

        # 添加标签和图例
        plt.title('Truncated Normal Distribution Fit')
        plt.xlabel('Continuous Variable')
        plt.ylabel('Density')
        plt.legend()
        # 保存
        # 保存路径
        scenario_id = os.path.basename(os.path.dirname(os.path.dirname(self.ontology_path)))
        output_path = os.path.abspath(os.path.join(os.path.dirname(self.ontology_path), f'../../../bn/{scenario_id}'))
        os.makedirs(output_path, exist_ok=True)
        plt.savefig(f'{output_path}/{node_name}_truncated_normal_fit.png')
        print(f"Saved truncated normal fit plot for {node_name} to {output_path}")

    @staticmethod
    def _fit_truncated_normal(data: pd.Series) -> truncnorm:
        """拟合截断正态分布"""
        # mu, std = norm.fit(data)
        # lower = np.percentile(data, 5)
        # upper = np.percentile(data, 95)
        # a = (lower - mu) / std
        # b = (upper - mu) / std
        # return truncnorm(a, b, loc=mu, scale=std)

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
        执行带有给定证据的贝叶斯网络推理
        """
        # 创建新的推理引擎
        self.ie = gum.LazyPropagation(self.bn)

        # 更新当前证据
        if evidence is not None:
            self.current_evidence = evidence.copy()
        else:
            self.current_evidence = {}

        # 如果有证据需要设置
        if self.current_evidence:
            print("Setting all evidence at once...")
            print(self.current_evidence)
            try:
                # 设置所有证据
                self.ie.setEvidence(self.current_evidence)

                # 执行推理 - 在访问任何后验之前
                self.ie.makeInference()

                # 只有推理成功后才检查后验
                print("Evidence successfully set and inference completed.")

            except Exception as e:
                print(f"Error during evidence setting or inference: {e}")
                # 创建一个没有证据的新推理引擎
                self.ie = gum.LazyPropagation(self.bn)
                self.ie.makeInference()
                print("Falling back to inference without evidence.")
        else:
            # 无证据情况下的推理
            self.ie.makeInference()

        print("Inference completed.")

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
        all_titles = ["Network Structure", "Prior Possibility", "Inference with Evidence"]

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


def export_detailed_cpts(bn, output_file):
    """
    导出详细的条件概率表到文件，同时打印到控制台

    Args:
        bn: 贝叶斯网络对象
        output_file (str): 输出文件路径
    """
    # 准备输出内容
    content = []
    content.append("贝叶斯网络条件概率表详细信息")
    content.append("=" * 80 + "\n")

    for node in bn.nodes():
        node_name = bn.variable(node).name()
        node_size = bn.variable(node).domainSize()
        node_states = [bn.variable(node).label(i) for i in range(node_size)]

        content.append(f"节点: {node_name}")
        content.append(f"状态: {node_states}")

        # 获取父节点
        parent_ids = list(bn.parents(node))
        if parent_ids:
            parents = []
            parent_states = []

            for p_id in parent_ids:
                p_name = bn.variable(p_id).name()
                p_size = bn.variable(p_id).domainSize()
                p_labels = [bn.variable(p_id).label(i) for i in range(p_size)]

                parents.append(p_name)
                parent_states.append(p_labels)

            content.append(f"父节点: {parents}")

            # 生成所有可能的父节点状态组合
            parent_combinations = list(itertools.product(*[range(len(s)) for s in parent_states]))

            content.append("条件概率详情:")
            content.append("-" * 80)

            # 表头
            header = " | ".join(parents + [f"{node_name} = {state}" for state in node_states])
            content.append(header)
            content.append("-" * len(header))

            # 每一行代表一种父节点状态组合
            for combo in parent_combinations:
                # 构建条件组合描述
                condition_desc = []
                for i, val in enumerate(combo):
                    p_name = parents[i]
                    p_state = parent_states[i][val]
                    condition_desc.append(f"{p_name}={p_state}")

                # 获取该条件下每个状态的概率
                probs = []
                for state in range(node_size):
                    idx = tuple(list(combo) + [state])
                    try:
                        prob = bn.cpt(node_name)[idx]
                        probs.append(f"{prob:.6f}")
                    except Exception as e:
                        probs.append(f"错误: {e}")

                # 写入一行
                line = " | ".join([", ".join(condition_desc)] + probs)
                content.append(line)
        else:
            # 根节点只有先验概率
            content.append("无父节点（根节点）")
            content.append("先验概率:")

            for i, state in enumerate(node_states):
                prob = bn.cpt(node_name)[i]
                content.append(f"{state}: {prob:.6f}")

        content.append("\n" + "=" * 80 + "\n")

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))

    # 打印到控制台
    for line in content:
        print(line)

    print(f"\n详细的条件概率表已导出到: {output_file}")


def save_cpt_tables(bn, output_file):
    """完整保存和打印所有节点的CPT表格到文件和控制台，不省略任何内容"""
    # 收集所有CPT表格的字符串
    content = []
    content.append("贝叶斯网络条件概率表")
    content.append("=" * 80 + "\n")

    for node in bn.nodes():
        node_name = bn.variable(node).name()
        content.append(f"节点: {node_name}")

        # 获取父节点
        parent_ids = list(bn.parents(node))
        parent_names = [bn.variable(p).name() for p in parent_ids]

        content.append(f"父节点: {parent_names}\n")

        # 获取CPT表格的字符串表示
        cpt_str = str(bn.cpt(node_name))
        # 分割表格的每一行
        cpt_lines = cpt_str.strip().split('\n')

        # 添加所有行，不省略
        for line in cpt_lines:
            content.append(line)

        content.append("\n" + "=" * 80 + "\n")

    # 添加一条完整保存确认信息
    content.append("全部保存完成")

    # 打印到控制台
    for line in content:
        print(line)

    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    print(f"\nCPT表格已完整保存到: {output_file}")

def update_with_evidence(analyzer: ScenarioResilience, evidence: Optional[Dict[str, int]] = None,output_dir = "./scenario_bn") -> None:
    """使用新证据更新贝叶斯网络，如果没有提供证据则清除现有证据"""
    # 执行推理
    # export_detailed_cpts(analyzer.bn, os.path.join(output_dir, 'detailed_cpts.txt'))
    # save_cpt_tables(analyzer.bn, os.path.join(output_dir, 'cpt_tables.txt'))
    if evidence is None:
        analyzer.clear_evidence()
    else:
        # 保存到 evidence.log 中
        with open('evidence.log', 'a') as f:
            import time
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            evidence_str = f"{timestamp} - {str(evidence)}\n"
            f.write(evidence_str)
        analyzer.make_inference(evidence)

    # 构建后验概率的字典，使用状态名称作为键
    posterior_dict = {}
    for node in analyzer.bn.nodes():
        node_name = analyzer.bn.variable(node).name()
        print(f"142315{node_name}")
        # 打印条件概率表，不要省略

        print(analyzer.bn.cpt(node_name))
        posterior = analyzer.ie.posterior(node_name).tolist()
        print(f"142315{posterior}")


        # 获取该节点的状态映射
        state_labels = analyzer.state_mapping.get(node_name, [])

        if not state_labels:
            # 如果没有找到映射，则使用索引作为键
            posterior_with_labels = {index: prob for index, prob in enumerate(posterior)}
        else:
            # 确保状态标签的数量与后验概率的长度一致
            if len(state_labels) != len(posterior):
                raise ValueError(f"节点 '{node_name}' 的状态标签数量与后验概率数量不匹配。")
            # 使用状态名称作为键
            posterior_with_labels = {state: prob for state, prob in zip(state_labels, posterior)}

        posterior_dict[node_name] = posterior_with_labels

    # 打印为带状态名称的 JSON 格式
    print("\nPosterior Probabilities after Evidence:")
    print(json.dumps(posterior_dict, indent=4, ensure_ascii=False))
    # 保存到文件,如果目录不存在则创建
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'posterior_probabilities.json'), 'w',
              encoding='utf-8') as f:
        json.dump(posterior_dict, f, indent=4, ensure_ascii=False)

    # 可视化更新后的网络，传入当前的推理引擎
    visualizer = NetworkVisualizer()
    ie = visualizer.visualize_network(
        bn=analyzer.bn,
        output_dir=output_dir,
        evidence=analyzer.current_evidence,
        state_mapping=analyzer.state_mapping,
        ie=analyzer.ie
    )

def bn_svg_update():
    """主函数演示用法"""
    # 初始化分析器
    analyzer = ScenarioResilience(r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\3\owl\Scenario.owl")

    # 提取数据属性
    analyzer.extract_data_properties()

    # 创建贝叶斯网络结构
    analyzer.create_bayesian_network()

    # 设置先验概率
    analyzer.set_prior_probabilities(r"D:\PythonProjects\AcademicTool_PySide\data\required_information\prior prob test.xlsx")

    # 处理专家评估
    expert_df = analyzer.process_expert_evaluation(
        expert_info_path=r"D:\PythonProjects\AcademicTool_PySide\data\required_information\expertInfo.xlsx",
        expert_estimation_path=r"D:\PythonProjects\AcademicTool_PySide\data\required_information\expert estimation test.xlsx"
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

    # evidence = {'AidResource': 0}
    #
    # update_with_evidence(analyzer, evidence)
    #
    evidence = {'roadPassibility': 0, 'roadLoss': 0, 'casualties': 1, 'AidResource': 1, 'TowResource': 1, 'RescueResource': 1, 'FirefightingResource': 1, 'disposalDuration': 3}

    update_with_evidence(analyzer, evidence)

if __name__ == "__main__":
    bn_svg_update()