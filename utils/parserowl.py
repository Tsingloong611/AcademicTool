# -*- coding: utf-8 -*-
# @Time    : 1/20/2025 11:51 AM
# @FileName: parserowl.py
# @Software: PyCharm

import os.path

from owlready2 import *
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, field
import re
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClassInfo:
    """类信息"""
    uri: str
    local_name: str
    label: Optional[str] = None
    comment: Optional[str] = None
    annotations: Dict[str, List[str]] = field(default_factory=dict)
    super_classes: Set[str] = field(default_factory=set)
    sub_classes: Set[str] = field(default_factory=set)
    equivalent_classes: Set[str] = field(default_factory=set)
    disjoint_classes: Set[str] = field(default_factory=set)
    properties: List[str] = field(default_factory=list)
    instances: List[str] = field(default_factory=list)
    # 新增：存储实例的属性取值信息
    # 格式: { "instanceName": {"dataPropName": [...], "objPropName": [...]}, ...}
    instance_values: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)


@dataclass
class PropertyInfo:
    """属性信息"""
    uri: str
    local_name: str
    property_type: str  # DatatypeProperty 或 ObjectProperty
    label: Optional[str] = None
    comment: Optional[str] = None
    domain: List[str] = field(default_factory=list)
    range: Optional[str] = None
    inverse_of: Optional[str] = None
    characteristics: Set[str] = field(default_factory=set)
    sub_properties: Set[str] = field(default_factory=set)
    super_properties: Set[str] = field(default_factory=set)
    annotations: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class RestrictionInfo:
    """约束信息"""
    type: str  # someValuesFrom, allValuesFrom, hasValue, cardinality等
    property: str
    value: Any
    cardinality: Optional[int] = None


@dataclass
class BehaviorInfo:
    """行为信息"""
    type: str  # SWRL, PropertyCharacteristic, Restriction, Action, Operation
    source: str  # 行为来源（类名或属性名）
    description: str  # 行为描述
    condition: Optional[str] = None  # 前置条件
    effect: Optional[str] = None  # 后置效果
    parameters: List[str] = field(default_factory=list)  # 参数列表
    annotations: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class AnnotationInfo:
    """注解信息"""
    property: str
    value: str
    language: Optional[str] = None


@dataclass
class RuleInfo:
    """规则信息"""
    name: str
    body: str  # 前提条件
    head: str  # 结论
    variables: Set[str] = field(default_factory=set)
    annotations: Dict[str, List[str]] = field(default_factory=dict)


class OWLParser:
    def __init__(self, owl_file_path: str):
        """
        初始化OWL解析器
        :param owl_file_path: OWL文件路径
        """
        logger.info(f"Loading ontology from {owl_file_path}")
        try:
            # 加载本体
            self.onto = get_ontology(owl_file_path).load()

            # 初始化SWRL规则
            self.swrl = []
            try:
                # 尝试获取规则
                rules = list(self.onto.rules())  # 直接调用rules()方法
                if rules:
                    self.swrl = rules
                    logger.info(f"Found {len(rules)} SWRL rules")
            except Exception as e:
                logger.warning(f"Failed to load SWRL rules: {e}")
                self.swrl = []

            # 初始化注解属性集合
            self.annotation_properties = set(self.onto.annotation_properties())

            logger.info("Successfully initialized OWL parser")
        except Exception as e:
            logger.error(f"Failed to initialize OWL parser: {e}")
            raise

    def get_annotations(self, entity) -> Dict[str, List[str]]:
        """获取实体的所有注解"""
        annotations = {}
        for prop in self.annotation_properties:
            try:
                values = [str(v) for v in entity.get_properties(prop)]
                if values:
                    annotations[prop.name] = values
            except Exception as e:
                logger.warning(f"Error getting annotation {prop.name} for {entity}: {e}")
        return annotations

    def parse_classes(self) -> Dict[str, ClassInfo]:
        """
        解析本体中的所有类
        :return: 类名到类信息的映射
        """
        logger.info("Starting to parse classes")
        class_map = {}

        try:
            for owl_class in self.onto.classes():
                if owl_class.name is None:
                    continue

                # 基本信息
                class_info = ClassInfo(
                    uri=owl_class.iri,
                    local_name=owl_class.name,
                    label=str(owl_class.label.first()) if owl_class.label else None,
                    comment=str(owl_class.comment.first()) if owl_class.comment else None,
                    annotations=self.get_annotations(owl_class)
                )

                # 获取父类
                class_info.super_classes = {
                    c.name for c in owl_class.is_a
                    if isinstance(c, ThingClass) and c.name is not None
                }

                # 获取子类
                class_info.sub_classes = {
                    c.name for c in owl_class.subclasses()
                    if isinstance(c, ThingClass) and c.name is not None
                }

                # 获取等价类
                class_info.equivalent_classes = {
                    c.name for c in owl_class.equivalent_to
                    if isinstance(c, ThingClass) and c.name is not None
                }

                # 获取互斥类
                class_info.disjoint_classes = {
                    c.name for c in owl_class.disjoints()
                    if isinstance(c, ThingClass) and c.name is not None
                }

                # 获取类的属性（仅做 domain 检查）
                class_info.properties = []
                for prop in self.onto.properties():
                    if prop.domain and any(domain == owl_class for domain in prop.domain):
                        if prop.name is not None:
                            class_info.properties.append(prop.name)

                # 获取实例
                class_info.instances = []
                try:
                    for instance in owl_class.instances():
                        if hasattr(instance, 'name') and instance.name is not None:
                            class_info.instances.append(instance.name)
                except Exception as e:
                    logger.warning(f"Error getting instances for class {owl_class.name}: {e}")

                # ============== 新增：解析实例的属性值 (data property 和 object property) =============
                # 以 { instanceName: { propertyName: [values], ... }, ... } 形式存储
                for instance in owl_class.instances():
                    if not hasattr(instance, 'name') or instance.name is None:
                        continue
                    inst_name = instance.name

                    instance_details = {}
                    # 通过 get_properties() 可获取“对该实例而言”实际使用到的属性
                    for prop in instance.get_properties():
                        values = prop[instance]
                        # 如果是数据属性
                        if isinstance(prop, DataPropertyClass):
                            prop_name = prop.name or "UnnamedDataProperty"
                            instance_details[prop_name] = [str(v) for v in values]

                        # 如果是对象属性
                        elif isinstance(prop, ObjectPropertyClass):
                            prop_name = prop.name or "UnnamedObjectProperty"
                            # 把关联到的目标个体名存下来
                            target_names = []
                            for v in values:
                                if hasattr(v, 'name') and v.name:
                                    target_names.append(v.name)
                                else:
                                    target_names.append(str(v))
                            instance_details[prop_name] = target_names

                    class_info.instance_values[inst_name] = instance_details

                # 放到映射中
                class_map[owl_class.name] = class_info

                logger.debug(
                    f"Parsed class {owl_class.name} with {len(class_info.properties)} properties "
                    f"and {len(class_info.instances)} instances"
                )

            logger.info(f"Successfully parsed {len(class_map)} classes")
            return class_map

        except Exception as e:
            logger.error(f"Error parsing classes: {e}")
            raise

    def parse_properties(self) -> Dict[str, List[PropertyInfo]]:
        """
        解析本体中的所有属性
        :return: 类名到属性列表的映射
        """
        logger.info("Starting to parse properties")
        property_map = {}

        try:
            # 解析数据类型属性
            for data_prop in self.onto.data_properties():
                if data_prop.name is None:
                    continue

                prop_info = self._create_property_info(data_prop, "DatatypeProperty")
                self._add_property_to_map(property_map, prop_info)

            # 解析对象属性
            for obj_prop in self.onto.object_properties():
                if obj_prop.name is None:
                    continue

                prop_info = self._create_property_info(obj_prop, "ObjectProperty")
                self._add_property_to_map(property_map, prop_info)

            logger.info(f"Successfully parsed properties for {len(property_map)} classes")
            return property_map

        except Exception as e:
            logger.error(f"Error parsing properties: {e}")
            raise

    def _create_property_info(self, prop, prop_type: str) -> PropertyInfo:
        """创建属性信息对象"""
        characteristics = set()

        # 检查属性特性
        if hasattr(prop, "is_functional") and prop.is_functional():
            characteristics.add("Functional")
        if hasattr(prop, "is_transitive") and prop.is_transitive():
            characteristics.add("Transitive")
        if hasattr(prop, "is_symmetric") and prop.is_symmetric():
            characteristics.add("Symmetric")
        if hasattr(prop, "is_asymmetric") and prop.is_asymmetric():
            characteristics.add("Asymmetric")
        if hasattr(prop, "is_reflexive") and prop.is_reflexive():
            characteristics.add("Reflexive")
        if hasattr(prop, "is_irreflexive") and prop.is_irreflexive():
            characteristics.add("Irreflexive")
        if hasattr(prop, "is_inverse_functional") and prop.is_inverse_functional():
            characteristics.add("InverseFunctional")

        # 获取反向属性
        inverse_name = None
        try:
            if hasattr(prop, 'Inverse'):
                inverses = list(prop.Inverse)
                if inverses and hasattr(inverses[0], 'name'):
                    inverse_name = inverses[0].name
        except Exception as e:
            logger.debug(f"No inverse property found for {prop.name}: {e}")

        # 获取值域
        range_name = None
        try:
            if prop.range:
                first_range = prop.range[0]
                if hasattr(first_range, 'name'):
                    range_name = first_range.name
                else:
                    range_name = str(first_range)
        except Exception as e:
            logger.debug(f"Error getting range for {prop.name}: {e}")

        return PropertyInfo(
            uri=prop.iri,
            local_name=prop.name,
            property_type=prop_type,
            label=str(prop.label[0]) if prop.label else None,
            comment=str(prop.comment[0]) if prop.comment else None,
            domain=[d.name for d in prop.domain if hasattr(d, 'name')],
            range=range_name,
            inverse_of=inverse_name,
            characteristics=characteristics,
            sub_properties={p.name for p in prop.subproperties() if p.name} if hasattr(prop, 'subproperties') else set(),
            super_properties={p.name for p in prop.is_a if hasattr(p, 'name')},
            annotations=self.get_annotations(prop)
        )

    def _add_property_to_map(self, property_map: Dict[str, List[PropertyInfo]], prop_info: PropertyInfo):
        """将属性信息添加到映射中，避免重复"""
        for domain_class in prop_info.domain:
            if domain_class not in property_map:
                property_map[domain_class] = []

            # 检查是否已存在相同名称和类型的属性
            existing_prop = next(
                (p for p in property_map[domain_class]
                 if p.local_name == prop_info.local_name
                 and p.property_type == prop_info.property_type),
                None
            )

            if existing_prop:
                # 如果存在，可以选择更新现有属性或跳过
                # 这里选择跳过，保留第一次出现的属性信息
                logger.debug(f"Skipping duplicate property {prop_info.local_name} for class {domain_class}")
            else:
                property_map[domain_class].append(prop_info)

    def parse_behaviors(self) -> List[BehaviorInfo]:
        """
        解析本体中的所有行为信息
        :return: 行为信息列表
        """
        logger.info("Starting to parse behaviors")
        behaviors = []

        try:
            # 1. 从SWRL规则解析行为
            behaviors.extend(self._parse_swrl_behaviors())

            # 2. 从属性特性解析行为
            behaviors.extend(self._parse_property_behaviors())

            # 3. 从注释解析行为
            behaviors.extend(self._parse_annotation_behaviors())

            # 4. 从约束解析行为
            behaviors.extend(self._parse_restriction_behaviors())

            logger.info(f"Successfully parsed {len(behaviors)} behaviors")
            return behaviors

        except Exception as e:
            logger.error(f"Error parsing behaviors: {e}")
            raise

    def _parse_swrl_behaviors(self) -> List[BehaviorInfo]:
        """解析SWRL规则中的行为"""
        behaviors = []
        if self.swrl:
            for rule in self.swrl:
                try:
                    behavior = BehaviorInfo(
                        type="SWRL",
                        source=rule.name if hasattr(rule, 'name') else "UnnamedRule",
                        description=str(rule),
                        condition=str(rule.body) if hasattr(rule, 'body') else None,
                        effect=str(rule.head) if hasattr(rule, 'head') else None,
                        annotations=self.get_annotations(rule) if hasattr(rule, 'annotations') else {}
                    )
                    behaviors.append(behavior)
                except Exception as e:
                    logger.warning(f"Error parsing SWRL rule: {e}")
        return behaviors

    def _parse_property_behaviors(self) -> List[BehaviorInfo]:
        """从属性特性解析行为"""
        behaviors = []
        for prop in self.onto.properties():
            if not prop.name:
                continue

            try:
                # 检查各种属性特性
                if hasattr(prop, 'is_transitive') and prop.is_transitive():
                    behaviors.append(BehaviorInfo(
                        type="PropertyCharacteristic",
                        source=prop.name,
                        description=f"Transitive property: If {prop.name}(x,y) and {prop.name}(y,z) then {prop.name}(x,z)",
                        parameters=["x", "y", "z"]
                    ))

                if hasattr(prop, 'is_symmetric') and prop.is_symmetric():
                    behaviors.append(BehaviorInfo(
                        type="PropertyCharacteristic",
                        source=prop.name,
                        description=f"Symmetric property: If {prop.name}(x,y) then {prop.name}(y,x)",
                        parameters=["x", "y"]
                    ))

                if hasattr(prop, 'is_functional') and prop.is_functional():
                    behaviors.append(BehaviorInfo(
                        type="PropertyCharacteristic",
                        source=prop.name,
                        description=f"Functional property: For each x, there can be at most one y such that {prop.name}(x,y)",
                        parameters=["x", "y"]
                    ))

                # 这里可以添加其他属性特性的行为解析...

            except Exception as e:
                logger.warning(f"Error parsing property behavior for {prop.name}: {e}")

        return behaviors

    def _parse_annotation_behaviors(self) -> List[BehaviorInfo]:
        """从注释解析行为信息"""
        behaviors = []

        # 行为相关的注释标记
        behavior_patterns = {
            r'@action\s*[:：]\s*(.+)': "Action",
            r'@behavior\s*[:：]\s*(.+)': "Behavior",
            r'@operation\s*[:：]\s*(.+)': "Operation",
            r'when\s+(.+)\s+then\s+(.+)': "Rule",
            r'if\s+(.+)\s+then\s+(.+)': "Rule",
            r'@pre\s*[:：]\s*(.+)': "Precondition",
            r'@post\s*[:：]\s*(.+)': "Postcondition",
            r'@invariant\s*[:：]\s*(.+)': "Invariant"
        }

        for entity in list(self.onto.classes()) + list(self.onto.properties()):
            if not entity.comment:
                continue

            try:
                for comment in entity.comment:
                    comment_text = str(comment)

                    # 解析每种行为模式
                    for pattern, behavior_type in behavior_patterns.items():
                        matches = re.finditer(pattern, comment_text, re.MULTILINE | re.IGNORECASE)
                        for match in matches:
                            if len(match.groups()) == 2:  # if-then 或 when-then 模式
                                behaviors.append(BehaviorInfo(
                                    type=behavior_type,
                                    source=entity.name,
                                    description=match.group(0),
                                    condition=match.group(1).strip(),
                                    effect=match.group(2).strip(),
                                    annotations=self.get_annotations(entity)
                                ))
                            else:  # 单一描述模式
                                behaviors.append(BehaviorInfo(
                                    type=behavior_type,
                                    source=entity.name,
                                    description=match.group(1).strip(),
                                    annotations=self.get_annotations(entity)
                                ))

                    # 解析方法签名和参数
                    method_pattern = r'@method\s*[:：]\s*(\w+)\s*\((.*?)\)'
                    method_matches = re.finditer(method_pattern, comment_text, re.MULTILINE)
                    for match in method_matches:
                        method_name = match.group(1)
                        params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                        behaviors.append(BehaviorInfo(
                            type="Method",
                            source=entity.name,
                            description=f"Method {method_name}",
                            parameters=params,
                            annotations=self.get_annotations(entity)
                        ))

            except Exception as e:
                logger.warning(f"Error parsing annotation behaviors for {entity.name}: {e}")

        return behaviors

    def _parse_restriction_behaviors(self) -> List[BehaviorInfo]:
        """从约束解析行为信息"""
        behaviors = []

        for cls in self.onto.classes():
            if not cls.name:
                continue

            try:
                # 获取所有限制
                for restriction in cls.is_a:
                    if isinstance(restriction, Restriction):
                        behavior_desc = self._parse_restriction_behavior(restriction)
                        if behavior_desc:
                            behaviors.append(BehaviorInfo(
                                type="Restriction",
                                source=cls.name,
                                description=behavior_desc,
                                annotations=self.get_annotations(cls)
                            ))

            except Exception as e:
                logger.warning(f"Error parsing restriction behaviors for {cls.name}: {e}")

        return behaviors

    def _parse_restriction_behavior(self, restriction) -> Optional[str]:
        """解析约束并转换为行为描述"""
        if not hasattr(restriction, 'property') or not restriction.property.name:
            return None

        try:
            prop_name = restriction.property.name

            # 根据约束类型生成描述
            if restriction.type == SOME:
                value = restriction.value.name if hasattr(restriction.value, 'name') else str(restriction.value)
                return f"Must have some {prop_name} relationship with {value}"

            elif restriction.type == ONLY:
                value = restriction.value.name if hasattr(restriction.value, 'name') else str(restriction.value)
                return f"Can only have {prop_name} relationship with {value}"

            elif restriction.type == VALUE:
                value = restriction.value.name if hasattr(restriction.value, 'name') else str(restriction.value)
                return f"Must have {prop_name} relationship with specific value {value}"

            elif restriction.type == MIN:
                return f"Must have at least {restriction.cardinality} {prop_name} relationships"

            elif restriction.type == MAX:
                return f"Must have at most {restriction.cardinality} {prop_name} relationships"

            elif restriction.type == EXACTLY:
                return f"Must have exactly {restriction.cardinality} {prop_name} relationships"

        except Exception as e:
            logger.warning(f"Error parsing restriction behavior: {e}")

        return None

    def parse_rules(self) -> List[RuleInfo]:
        """解析本体中的所有规则"""
        rules = []

        if self.swrl:
            for rule in self.swrl:
                try:
                    # 提取规则中的变量
                    variables = set()
                    if hasattr(rule, 'variables'):
                        variables = {str(var) for var in rule.variables}

                    rule_info = RuleInfo(
                        name=rule.name if hasattr(rule, 'name') else "UnnamedRule",
                        body=str(rule.body) if hasattr(rule, 'body') else "",
                        head=str(rule.head) if hasattr(rule, 'head') else "",
                        variables=variables,
                        annotations=self.get_annotations(rule) if hasattr(rule, 'annotations') else {}
                    )
                    rules.append(rule_info)

                except Exception as e:
                    logger.warning(f"Error parsing rule: {e}")

        return rules

    def export_json(self, output_file: str = None):
        """
        导出本体为JSON格式
        :param output_file: 可选的输出文件路径，如果不提供则返回字典
        :return: 如果没有提供输出文件，则返回字典格式的数据
        """
        try:
            # 准备数据结构
            ontology_dict = {}

            # 获取所有类和属性信息
            class_map = self.parse_classes()
            property_map = self.parse_properties()

            # 构建每个类的信息
            for class_name, class_info in class_map.items():
                class_dict = {
                    "parent_class": list(class_info.super_classes)[0] if class_info.super_classes else "",
                    "Properties": [],
                    # Instances 原有结构
                    "Instances": {}
                }

                # ---- 对当前类的所有属性, 添加 property_value ----
                if class_name in property_map:
                    for prop in property_map[class_name]:
                        prop_name = prop.local_name
                        # 收集所有实例对这个属性的取值
                        all_values = []
                        for inst_name, prop_vals_dict in class_info.instance_values.items():
                            if prop_name in prop_vals_dict:
                                for v in prop_vals_dict[prop_name]:
                                    if v not in all_values:
                                        all_values.append(v)

                        # 如果没有取值，就写 "None"
                        if not all_values:
                            prop_value = "None"
                        else:
                            prop_value = all_values

                        prop_dict = {
                            "property_name": prop_name,
                            "property_type": prop.property_type,
                            "property_range": prop.range if prop.range else "",
                            "property_value": prop_value
                        }
                        class_dict["Properties"].append(prop_dict)

                # ---- 实例信息（沿用之前的逻辑）----
                for inst_name in class_info.instances:
                    if inst_name in class_info.instance_values:
                        class_dict["Instances"][inst_name] = class_info.instance_values[inst_name]
                    else:
                        class_dict["Instances"][inst_name] = {}

                ontology_dict[class_name] = class_dict

            # 如果提供了输出文件路径，则写入文件
            if output_file:
                import json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(ontology_dict, f, indent=2, ensure_ascii=False)
                logger.info(f"Successfully exported JSON to {output_file}")

            return ontology_dict

        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            raise

    def export_documentation(self, output_file: str):
        """
        导出本体文档
        :param output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 写入文档头部
                f.write(f"# Ontology Documentation\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # 写入类信息
                f.write("## Classes\n\n")
                class_map = self.parse_classes()
                for class_name, class_info in sorted(class_map.items()):
                    f.write(f"### {class_name}\n\n")
                    if class_info.label:
                        f.write(f"Label: {class_info.label}\n\n")
                    if class_info.comment:
                        f.write(f"Description: {class_info.comment}\n\n")
                    if class_info.super_classes:
                        f.write(f"Super classes: {', '.join(sorted(class_info.super_classes))}\n\n")
                    if class_info.properties:
                        f.write(f"Properties: {', '.join(sorted(class_info.properties))}\n\n")

                    # 展示一下实例及其属性值
                    if class_info.instances:
                        f.write(f"Instances:\n\n")
                        for inst_name in class_info.instances:
                            f.write(f"- **{inst_name}**\n\n")
                            if inst_name in class_info.instance_values:
                                for prop_name, values in class_info.instance_values[inst_name].items():
                                    f.write(f"  - {prop_name}: {values}\n")
                            f.write("\n")

                    f.write("\n")

                # 写入属性信息
                f.write("## Properties\n\n")
                property_map = self.parse_properties()
                for c_name, properties in sorted(property_map.items()):
                    f.write(f"### Properties of {c_name}\n\n")
                    for prop in sorted(properties, key=lambda x: x.local_name):
                        f.write(f"#### {prop.local_name}\n\n")
                        f.write(f"Type: {prop.property_type}\n\n")
                        if prop.range:
                            f.write(f"Range: {prop.range}\n\n")
                        if prop.characteristics:
                            f.write(f"Characteristics: {', '.join(sorted(prop.characteristics))}\n\n")
                        f.write("\n")

                # 写入行为信息
                f.write("## Behaviors\n\n")
                behaviors = self.parse_behaviors()
                for behavior in sorted(behaviors, key=lambda x: (x.type, x.source)):
                    f.write(f"### {behavior.type} in {behavior.source}\n\n")
                    f.write(f"Description: {behavior.description}\n\n")
                    if behavior.condition:
                        f.write(f"Condition: {behavior.condition}\n\n")
                    if behavior.effect:
                        f.write(f"Effect: {behavior.effect}\n\n")
                    if behavior.parameters:
                        f.write(f"Parameters: {', '.join(behavior.parameters)}\n\n")
                    f.write("\n")

                # 写入规则信息
                f.write("## Rules\n\n")
                rules = self.parse_rules()
                for rule in sorted(rules, key=lambda x: x.name):
                    f.write(f"### {rule.name}\n\n")
                    f.write(f"Body: {rule.body}\n\n")
                    f.write(f"Head: {rule.head}\n\n")
                    if rule.variables:
                        f.write(f"Variables: {', '.join(sorted(rule.variables))}\n\n")
                    f.write("\n")

            logger.info(f"Successfully exported documentation to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting documentation: {e}")
            raise


def parse_owl(owl_file_path: str):
    # 创建解析器实例
    parser = OWLParser(owl_file_path)

    owl_name = os.path.splitext(os.path.basename(owl_file_path))[0]
    output_path = os.path.dirname(owl_file_path)

    # 解析并导出JSON（可在 JSON 中查看属性对应的 property_value）
    json_data = parser.export_json(os.path.join(output_path, f"{owl_name}_ontology_structure.json"))

    # 打印部分数据作为示例
    print("\n=== JSON Export Sample ===")
    import json
    # 仅展示前 3 个类的结构
    print(json.dumps(dict(list(json_data.items())[:3]), indent=2, ensure_ascii=False))

    # 原有的解析展示代码...
    # 1. 解析类
    print("\n=== Classes ===")
    class_map = parser.parse_classes()
    for class_name, class_info in class_map.items():
        print(f"\nClass: {class_name}")
        print(f"URI: {class_info.uri}")
        print(f"Super classes: {class_info.super_classes}")
        if class_info.comment:
            print(f"Comment: {class_info.comment}")
        # 展示实例及其属性值
        if class_info.instances:
            print(f"Instances of {class_name}:")
            for inst_name in class_info.instances:
                print(f"  - {inst_name}")
                if inst_name in class_info.instance_values:
                    for prop_name, val_list in class_info.instance_values[inst_name].items():
                        print(f"    {prop_name} => {val_list}")

    # 2. 解析属性
    print("\n=== Properties ===")
    property_map = parser.parse_properties()
    for c_name, properties in property_map.items():
        print(f"\nProperties of {c_name}:")
        for prop in properties:
            print(f"  {prop.local_name} ({prop.property_type})")
            if prop.range:
                print(f"    Range: {prop.range}")
            if prop.characteristics:
                print(f"    Characteristics: {prop.characteristics}")

    # 3. 解析行为
    print("\n=== Behaviors ===")
    behaviors = parser.parse_behaviors()
    for behavior in behaviors:
        print(f"\n{behavior.type} in {behavior.source}:")
        print(f"  Description: {behavior.description}")
        if behavior.condition:
            print(f"  Condition: {behavior.condition}")
        if behavior.effect:
            print(f"  Effect: {behavior.effect}")

    # 4. 解析规则
    print("\n=== Rules ===")
    rules = parser.parse_rules()
    for rule in rules:
        print(f"\nRule: {rule.name}")
        print(f"Body: {rule.body}")
        print(f"Head: {rule.head}")
        if rule.variables:
            print(f"Variables: {rule.variables}")

    # 5. 导出文档（Markdown）
    parser.export_documentation(os.path.join(output_path, f"{owl_name}_ontology_documentation.md"))


def main():
    # 本体文件路径（自行修改）
    owl_file_path = r"C:\Users\Tsing_loong\Desktop\Work Section\owl\Emergency.owl"
    parse_owl(owl_file_path)


if __name__ == "__main__":
    main()
