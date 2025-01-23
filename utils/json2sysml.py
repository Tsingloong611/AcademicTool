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

    :param json_str: JSON 数据的字符串表示
    :param element_data: 一个字典，用于映射实体的 ID 到其名称
    :param custom_action_defs: 用户自定义的 action def 字符串
    :param custom_state_defs: 用户自定义的 state def 字符串
    :return: 字符串形式的 SysML2 文本表示
    """
    try:
        # 解析 JSON 字符串
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON 数据: {e}")

    # 替换字符串 "null"、"true"、"false" 为 Python 的 None、True、False
    parsed_json = replace_strings_with_literals(parsed_json)

    lines = []
    indent = "    "
    print(parsed_json)

    # 1. 解析 Package 名称
    categories = parsed_json.get('categories', [])
    if not categories:

        raise ValueError("JSON 数据中缺少 'categories' 信息。")

    # 假设第一个类别作为包名
    package_name = categories[0].get('category_name', 'UnknownPackage')
    lines.append(f"package {package_name}{{")
    lines.append("")  # 空行

    # 2. 定义基础 Part
    lines.append(f"{indent}part def {package_name}{{}}")
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
    # 如果 'attribute_type_code' 为 'Item'，则定义为 item def
    attributes = parsed_json.get('attributes', [])
    items = []
    for attr in attributes:
        if attr.get('attribute_type_code') == 'Item':
            item_name = attr.get('attribute_code_name')
            item_type = attr.get('attribute_type_code')
            if item_name:
                items.append((item_name, item_type))

    # 去重
    unique_items = list({item[0]: item for item in items}.values())

    for item_name, item_type in unique_items:
        lines.append(f"{indent}item def {item_name}{{")
        # 可以根据需要添加属性
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
    # 这里假设 main part 是 'HazardVehicle' 或从 JSON 提取
    entity_name = parsed_json.get('entity_name', 'UnknownEntity')
    lines.append(f"{indent}part {entity_name} : {package_name}{{")

    # 添加属性，跳过类型为 'Item' 或 'Entity' 的属性
    for attr in attributes:
        attr_type = attr.get('attribute_type_code', 'String')
        if attr_type in ['Item', 'Entity']:
            continue  # 跳过 Item 和 Entity 类型的属性

        attr_name = attr.get('attribute_code_name')
        attr_type = attr.get('attribute_type_code', 'String')
        default_value = attr.get('default_value')
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

    # 添加 Items
    for item in unique_items:
        item_name = item[0]
        lines.append(f"{indent * 2}item {item_name} : {item_name};")

    # 添加 References (如果有)
    # 使用 element_data 来获取引用实体的名称
    referenced_entities = []
    for attr in attributes:
        refs = attr.get('referenced_entities', [])
        # print(f"refs: {refs}")
        for ref in refs:
            for key, value in element_data.items():
                # print(f"key: {key}, value: {value}")
                if key == ref:
                    referenced_entities.append(value['entity_name'])
                    # print(f"referenced_entities: {referenced_entities}")


    for ref in referenced_entities:
        lines.append(f"{indent * 2}ref part {ref};")

    lines.append("")  # 空行

    # 添加 Performs (Actions)
    # 根据 'behaviors' 进行添加
    for beh in behaviors:
        action_code_name = beh.get('behavior_code_name')
        if action_code_name:
            lines.append(f"{indent * 2}perform action {action_code_name};")

    # 添加 States (如果有)
    # 这里暂时忽略，因为 JSON 示例中没有相关信息

    lines.append("")  # 空行

    lines.append(f"{indent}}}")
    lines.append("")  # 空行

    # 结束 Package
    lines.append("}")
    # 将所有行组合成一个字符串
    txt_output = "\n".join(lines)

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 定义目标文件夹相对路径
    relative_dir = f"../data/sysml2/{json.loads(json_str)['scenario_id']}"

    # 计算目标文件夹的绝对路径
    absolute_dir = os.path.abspath(os.path.join(script_dir, relative_dir))

    # 确保目录存在
    os.makedirs(absolute_dir, exist_ok=True)

    # 拼接绝对路径的文件名
    file_path = os.path.join(absolute_dir, f"{package_name}_{entity_name}.txt")

    with open(file_path, "w",encoding="utf-8") as f:
        f.write(txt_output)

    print(f"Saving file to: {file_path}")

    return txt_output
