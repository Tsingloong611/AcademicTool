# -*- coding: utf-8 -*-
# @Time    : 1/17/2025 12:31 PM
# @FileName: json2sysml.py
# @Software: PyCharm

import json
import os
from typing import Any, Dict, Optional


def replace_strings_with_literals(obj: Any) -> Any:
    """
    递归遍历 JSON 对象，将字符串 "null"、"true"、"false" 转换为对应的 Python 类型。

    :param obj: 需要处理的 JSON 对象
    :return: 处理后的 JSON 对象
    """
    if isinstance(obj, dict):
        return {k: replace_strings_with_literals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_strings_with_literals(item) for item in obj]
    elif isinstance(obj, str):
        lower_val = obj.lower()
        if lower_val == "null":
            return None
        elif lower_val == "true":
            return True
        elif lower_val == "false":
            return False
        else:
            return obj
    else:
        return obj


def json_to_sysml2_txt(
        json_str: str,
        element_data: Dict[int, Dict[str, Any]],
        custom_action_defs: Optional[str] = None,
        custom_state_defs: Optional[str] = None
) -> str:
    """
    将提供的 JSON 数据解析回 SysML2 文本格式，并允许用户传入自定义的 action def 和 state def。

    如果 JSON 中有多个类别，则依次为每个类别创建对应的 SysML2 文件。

    :param json_str: JSON 数据的字符串表示
    :param element_data: 一个字典，用于映射实体的 ID 到其名称
    :param custom_action_defs: 用户自定义的 action def 字符串
    :param custom_state_defs: 用户自定义的 state def 字符串
    :return: 如果生成多个文件，则返回所有生成文件的绝对路径（以换行符分隔的字符串）
    """
    map_dict = {
        1: 'Vehicle',
        2: 'Road',
        3: 'Meteorology',
        4: 'ResponseResource',
        5: 'ResponseAction',
        6: 'VehiclePart',
        7: 'VehicleLoad',
        8: 'Facility',
        11: 'Lane',
        12: 'People',
        13: 'ResponsePlan'
    }
    # 例如：1   车辆    Vehicle

    try:
        # 解析 JSON 字符串
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON 数据: {e}")

    # 将 "null"、"true"、"false" 字符串转换为对应的 Python 字面量
    parsed_json = replace_strings_with_literals(parsed_json)

    indent = "    "

    # 1. 解析 Package 所用的类别信息
    categories = parsed_json.get('categories', [])
    if not categories:
        raise ValueError("JSON 数据中缺少 'categories' 信息。")
    # 如果有多个类别，则依次取出类别名
    package_names = [cat.get('category_name', 'UnknownPackage') for cat in categories]

    # 提前获取主实体名称
    entity_name = parsed_json.get('entity_name', 'UnknownEntity')

    # 计算输出目录（与当前脚本所在目录相关）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    relative_dir = f"../data/sysml2/{parsed_json.get('scenario_id', 'default')}"
    absolute_dir = os.path.abspath(os.path.join(script_dir, relative_dir))
    os.makedirs(absolute_dir, exist_ok=True)

    output_file_paths = []  # 用于保存所有生成的文件路径

    # 对于每个包名分别生成 SysML2 文本文件
    for package_name in package_names:
        lines = []
        # 开始 Package 定义
        lines.append(f"package {package_name}{{")
        lines.append("")  # 空行

        # 2. 定义基础 Part
        if parsed_json['entity_type_id'] in [4, 5]:
            lines.append(f"{indent}part def {map_dict[parsed_json['entity_type_id']]}{{}}")
        else:
            lines.append(f"{indent}part def {package_name}{{")
            lines.append("")  # 空行

        # 3. 添加自定义的 Action Definitions
        if custom_action_defs:
            for line in custom_action_defs.strip().split('\n'):
                lines.append(f"{indent}{line}")
            lines.append("")  # 空行

        # 4. 添加自定义的 State Definitions
        if custom_state_defs:
            for line in custom_state_defs.strip().split('\n'):
                lines.append(f"{indent}{line}")
            lines.append("")  # 空行

        # 5. 解析 Items
        attributes = parsed_json.get('attributes', [])
        items = []
        for attr in attributes:
            if attr.get('attribute_type_code') == 'Item':
                item_code = attr.get('reference_target_type_id')
                if item_code:
                    items.append(item_code)
        # 去重
        unique_items = list(set(items))

        for item_code in unique_items:
            lines.append(f"{indent}item def {map_dict.get(item_code, 'UnknownItem')}{{")
            # 可根据需要添加属性
            lines.append(f"{indent}}}")
            lines.append("")  # 空行

        # 6. 解析 Actions
        behaviors = parsed_json.get('behaviors', [])
        actions = []
        for beh in behaviors:
            action_name = beh.get('behavior_code_name')
            if action_name:
                in_vars = beh.get('in', [])
                out_vars = beh.get('out', [])
                actions.append({
                    'name': action_name,
                    'in': in_vars,
                    'out': out_vars
                })

        for action in actions:
            lines.append(f"{indent}action def {action['name']}{{")
            # 添加 'in' 参数
            for in_var in action['in']:
                lines.append(f"{indent * 2}in {in_var} = true;")
            # 添加 'out' 参数
            for out_var in action['out']:
                lines.append(f"{indent * 2}out {out_var} = true;")
            lines.append(f"{indent}}}")
            lines.append("")  # 空行

        # 7. 解析 Attributes 作为 Part 的属性
        if parsed_json['entity_type_id'] in [4, 5]:
            lines.append(f"{indent}part {entity_name} : {map_dict[parsed_json['entity_type_id']]}{{")
        else:
            lines.append(f"{indent}part {entity_name} : {package_name}{{")

        # 添加属性，跳过类型为 'Item' 或 'Entity' 的属性
        for attr in attributes:
            attr_type = attr.get('attribute_type_code', 'String')
            if attr_type in ['Item', 'Entity']:
                continue
            attr_name = attr.get('attribute_code_name')
            # 再次使用 attr_type（可根据需要调整）
            default_value = attr.get('attribute_value')
            if default_value is None:
                default_str = "null"
            elif isinstance(default_value, str):
                default_str = f"\"{default_value}\""
            elif isinstance(default_value, bool):
                default_str = str(default_value).lower()
            else:
                default_str = str(default_value)
            lines.append(f"{indent * 2}attribute {attr_name} : {attr_type} = {default_str};")

        lines.append("")  # 空行

        # 添加 Items：根据 element_data 查找属于本实体的 item（参照属性中的 item code）
        for item in unique_items:
            for key, value in element_data.items():
                if value['entity_type_id'] == item and value['entity_parent_id'] == parsed_json['entity_id']:
                    item_name = value['entity_name']
                    lines.append(f"{indent * 2}item {item_name} : {map_dict.get(item, 'UnknownItem')};")
        # 添加 References（如果有）
        referenced_entities = []
        for attr in attributes:
            refs = attr.get('referenced_entities', [])
            for ref in refs:
                for key, value in element_data.items():
                    if key == ref:
                        referenced_entities.append(value['entity_name'])

        for ref in referenced_entities:
            lines.append(f"{indent * 2}ref part {ref};")

        lines.append("")  # 空行

        # 添加 Performs (Actions)
        for beh in behaviors:
            action_code_name = beh.get('behavior_code_name')
            if action_code_name:
                lines.append(f"{indent * 2}perform action {action_code_name};")

        # 如果有 States（此处暂不处理，可按需要扩展）
        lines.append("")  # 空行

        # 关闭主 Part
        lines.append(f"{indent}}}")
        lines.append("")  # 空行

        # 结束 Package 定义
        lines.append("}")

        # 组合所有行为最终文本
        txt_output = "\n".join(lines)

        # 拼接输出文件的绝对路径（文件名包含包名与实体名）
        file_path = os.path.join(absolute_dir, f"{package_name}_{entity_name}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(txt_output)
        print(f"Saving file to: {file_path}")
        output_file_paths.append(file_path)

    # 如果生成了多个文件，则返回所有文件的路径（以换行符分隔）
    return "\n".join(output_file_paths)