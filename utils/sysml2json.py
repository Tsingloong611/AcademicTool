import json
import re
import openpyxl
import os
import argparse
from typing import List, Dict, Any, Tuple


def parse_arguments() -> Tuple[str, str]:
    """解析命令行参数，获取输入和输出路径。"""
    parser = argparse.ArgumentParser(description="Process SysML files and convert them to JSON and Excel.")
    parser.add_argument('-i', '--input_dir', required=True, help='输入SysML文件的目录路径（包含 .txt 文件）')
    parser.add_argument('-o', '--output_dir', required=True, help='输出文件的目录路径（将生成 .json 和 .xlsx 文件）')
    args = parser.parse_args()
    return args.input_dir, args.output_dir


def read_input_file(input_path: str) -> str:
    """读取输入文件内容，删除空行。"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_str = f.read()
        input_str = re.sub(r'\n\s*\n', '\n', input_str)  # 删除空行
        return input_str
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_path}' 未找到。")
        return ""
    except Exception as e:
        print(f"读取输入文件时发生错误：{e}")
        return ""


def parse_to_json(input_text: str) -> Dict[str, Any]:
    stack = []
    result = {"@type": "package", "@name": "", "children": []}
    current = result

    lines = input_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if 'package' in line:
            _, name = line.split(' ', 1)
            current["@name"] = name.rstrip('{').strip()
        elif line.endswith('{'):
            parts = line[:-1].strip().split(' ')
            type_name = parts[0]
            tar_name = parts[1] if len(parts) > 1 else ""

            new_dict = {"@type": type_name, "@name": "", "children": []}

            # 检查是否有冒号（表示继承关系）
            if ':' in parts:
                colon_index = parts.index(':')
                new_dict["@type"] += "Sub"
                new_dict["@name"] = parts[1]
                # 明确设置 parent
                new_dict["parent"] = parts[colon_index + 1].strip()
            elif len(parts) > 2 and "def" in parts[1]:
                new_dict["@type"] += f" {parts[1]}"
                new_dict["@name"] = parts[2]
            else:
                new_dict["@name"] = parts[1] if len(parts) > 1 else ""

            current["children"].append(new_dict)
            stack.append(current)
            current = new_dict

        elif line == '}':
            if stack:
                current = stack.pop()
        elif line:
            parts = [p.replace(';', '') for p in line.split(' ')]
            if ':' in parts:
                idx = parts.index(':')
                name = parts[idx - 1]
                type_parts = ' '.join(parts[:idx - 1])

                if any(keyword in parts[idx + 1] for keyword in ['Boolean', 'String', 'Integer', 'Real', 'Enum','Bool']):
                    datavalue = ' '.join(parts[idx + 3:]) if (idx + 2 < len(parts) and parts[idx + 2] == '=') else None
                    attribute = {
                        "@type": type_parts,
                        "@name": name,
                        "datatype": parts[idx + 1],
                        "owner": tar_name
                    }
                    if datavalue:
                        attribute["datavalue"] = datavalue
                    current["children"].append(attribute)
                elif 'ref' in parts and 'part' in parts:
                    current["children"].append({
                        "@type": 'partAssociate',
                        "@name": ''.join(parts[2]),
                        "datavalue": parts[idx + 1],
                        "owner": tar_name
                    })
                elif 'perform' in parts and 'action' in parts:
                    current["children"].append({
                        "@type": 'actionSub',
                        "@name": ''.join(name),
                        'parent': ''.join(parts[idx + 1]),
                        'owner': tar_name
                    })
                elif 'item' in parts:
                    current["children"].append({
                        "@type": type_parts,
                        "@name": ''.join(name),
                        'parent': ''.join(parts[idx + 1]),
                        'owner': tar_name
                    })
                else:
                    current["children"].append({
                        "@type": type_parts,
                        "@name": name,
                        "datavalue": parts[idx + 1]
                    })
            else:
                if len(parts) == 1:
                    current["children"].append({"@type": current.get("@name", ""), "@name": parts[0]})
                elif 'def' in parts:
                    current["children"].append({"@type": ' '.join(parts[:2]), "@name": ''.join(parts[2:]).rstrip('{}')})
                elif 'ref' in parts and 'part' in parts:
                    current["children"].append({
                        "@type": 'partAssociate',
                        "@name": ''.join(parts[2]),
                        'owner': tar_name
                    })
                elif 'perform' in parts and 'action' in parts:
                    current["children"].append({
                        "@type": 'actionSub',
                        "@name": ''.join(parts[2]),
                        'owner': tar_name
                    })
                elif 'exhibit' in parts and 'state' in parts:
                    current["children"].append({
                        "@type": 'exhibitState',
                        "@name": ''.join(parts[2]),
                        'owner': tar_name
                    })
                elif 'redefines' in parts:
                    if parts[-2] == '=':
                        current["children"].append({
                            "@type": parts[0],
                            "@name": parts[2],
                            "datavalue": ''.join(parts[-1]),
                            'owner': tar_name
                        })
                    else:
                        current["children"].append({
                            "@type": parts[0],
                            "@name": parts[2],
                            'owner': tar_name
                        })
                else:
                    name = parts[1] if len(parts) > 1 else ""
                    current["children"].append({
                        "@type": parts[0],
                        "@name": name
                    })

    return result


def extract_data(data: Any) -> List[Tuple[str, Any]]:
    result = []
    if isinstance(data, dict):
        # 首先添加基本字段
        for key in ["@type", "@name", "parent"]:  # 明确列出要保留的字段
            if key in data:
                result.append((key, data[key]))

        # 然后处理其他字段
        for key, value in data.items():
            if key not in ["@type", "@name", "parent"]:  # 跳过已处理的字段
                if isinstance(value, list):
                    for item in value:
                        result.extend(extract_data(item))
                elif isinstance(value, dict):
                    result.extend(extract_data(value))
                else:
                    result.append((key, value))
    elif isinstance(data, list):
        for item in data:
            result.extend(extract_data(item))
    return result

def process_states(result: List[Dict[str, Any]]) -> None:
    """处理状态相关的数据。"""
    state_info = [i for i in result if i.get('@type') in ['state def', 'state', 'accept', 'then']]

    # 按 '@type': 'state def' 分割
    split_state_info = []
    temp_part = []
    for item in state_info:
        if item.get('@type') == 'state def':
            if temp_part:
                split_state_info.append(temp_part)
                temp_part = []
        temp_part.append(item)
    if temp_part:
        split_state_info.append(temp_part)

    state_list_wh = []
    for group in split_state_info:
        state_names = list(dict.fromkeys([item["@name"] for item in group]))
        if len(state_names) < 1:
            continue
        transitions = []
        for n in range(1, len(state_names) - 2, 2):
            transitions.append({
                'source': state_names[n],
                'transit': state_names[n + 1],
                'target': state_names[n + 2]
            })
        state_list_wh.append((state_names[0], transitions))

    for state_name, transitions in state_list_wh:
        for item in result:
            if item.get('@type') == "state def" and item.get('@name') == state_name:
                item["transitions"] = transitions

    # 移除不需要的类型
    result[:] = [i for i in result if i.get('@type') not in ['then', 'entry', 'accept', 'state']]


def process_actions(result: List[Dict[str, Any]]) -> None:
    """处理动作相关的数据。"""
    # 处理输入参数
    action_info_in = [i for i in result if i.get('@type') in ['action def', 'in']]
    split_action_info_in = []
    temp_part = []
    for item in action_info_in:
        if item.get('@type') == 'action def':
            if temp_part:
                split_action_info_in.append(temp_part)
                temp_part = []
        temp_part.append(item)
    if temp_part:
        split_action_info_in.append(temp_part)

    action_list_wh_in = []
    for group in split_action_info_in:
        names = [item["@name"] for item in group]
        action_list_wh_in.append(names)

    # 处理输出参数
    action_info_out = [i for i in result if i.get('@type') in ['action def', 'out']]
    split_action_info_out = []
    temp_part = []
    for item in action_info_out:
        if item.get('@type') == 'action def':
            if temp_part:
                split_action_info_out.append(temp_part)
                temp_part = []
        temp_part.append(item)
    if temp_part:
        split_action_info_out.append(temp_part)

    action_list_wh_out = []
    for group in split_action_info_out:
        names = [item["@name"] for item in group]
        action_list_wh_out.append(names)

    # 关联输入参数
    for action in action_list_wh_in:
        if not action:
            continue
        action_name = action[0]
        inparams = action[1:]
        for item in result:
            if item.get('@type') == 'action def' and item.get('@name') == action_name:
                item["inparams"] = inparams

    # 关联输出参数
    for action in action_list_wh_out:
        if not action:
            continue
        action_name = action[0]
        outparams = action[1:]
        for item in result:
            if item.get('@type') == 'action def' and item.get('@name') == action_name:
                item["outparams"] = outparams


def rename_types(result: List[Dict[str, Any]]) -> None:
    """重命名类型以统一命名规范。"""
    type_mapping = {
        'part def': 'part',
        'item': 'itemComposition',
        'item def': 'item',
        'attribute def': 'attribute',
        'action def': 'action',
        'state def': 'state',
        'partSub': 'partSub'  # 确保保留partSub类型
    }
    for item in result:
        original_type = item.get('@type')
        if original_type in type_mapping:
            item['@type'] = type_mapping[original_type]


def process_attributes(result: List[Dict[str, Any]]) -> None:
    """处理属性和其重定义。"""
    datatype_mapping = {item['@name']: item['datatype'] for item in result if item['@type'] == 'attribute' and 'datatype' in item}

    # 为缺少datatype的attribute添加datatype
    for item in result:
        if item['@type'] == 'attribute' and 'datatype' not in item:
            item['datatype'] = datatype_mapping.get(item['@name'], 'none')

    # 合并属性
    attribute_data = [item for item in result if item.get('@type') == 'attribute']
    attribute_dict = {}
    for item in attribute_data:
        name = item['@name']
        owner = item.get('owner', 'none')
        if name not in attribute_dict or (owner != 'def' and attribute_dict[name].get('owner') == 'def'):
            attribute_dict[name] = item

    for name, item in attribute_dict.items():
        if item.get('owner') == 'def':
            item['owner'] = 'none'

    # 更新结果
    result[:] = [item for item in result if item.get('@type') != 'attribute'] + list(attribute_dict.values())


def process_part_associates(result: List[Dict[str, Any]]) -> None:
    """处理部分关联和其重定义。"""
    partass_data = [item for item in result if item.get('@type') == 'partAssociate']
    partass_dict = {}
    for item in partass_data:
        name = item['@name']
        owner = item.get('owner', 'none')
        if name not in partass_dict or (owner != 'def' and partass_dict[name].get('owner') == 'def'):
            partass_dict[name] = item

    for name, item in partass_dict.items():
        if item.get('owner') == 'def':
            item['owner'] = 'none'

    # 更新结果
    result[:] = [item for item in result if item.get('@type') != 'partAssociate'] + list(partass_dict.values())


def save_json(result: List[Dict[str, Any]], json_path: str) -> None:
    """将结果保存为JSON文件。"""
    try:
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
        print(f"成功保存 JSON 文件：{json_path}")
    except Exception as e:
        print(f"保存 JSON 文件时发生错误：{e}")


def create_type_name_dict(result: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """创建类型与名称的对应表。"""
    type_name_dict = {}
    for item in result:
        item_type = item.get("@type")
        item_name = item.get("@name")
        if item_type and item_name:
            type_name_dict.setdefault(item_type, []).append(item_name)
    return type_name_dict


def print_type_name_dict(type_name_dict: Dict[str, List[str]]) -> None:
    """打印类型与名称的对应表。"""
    print("\nType 与 Name 对应表:")
    for item_type, item_names in type_name_dict.items():
        print(f"type: '{item_type}' ------> name: {item_names}")


def save_to_excel(result: List[Dict[str, Any]], excel_path: str) -> None:
    """将结果保存为 Excel 文件。"""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    headers = [
        "type", "name", "children", "parent", "datatype",
        "datavalue", "owner", "inparams", "outparams",
        "transitions.source", "transitions.transit", "transitions.target"
    ]
    sheet.append(headers)

    for item in result:
        base_data = [
            item.get("@type", ""),
            item.get("@name", ""),
            json.dumps(item.get("children", ""), ensure_ascii=False) if "children" in item else "",
            item.get("parent", ""),
            item.get("datatype", ""),
            item.get("datavalue", ""),
            item.get("owner", "")
        ]

        # 处理 transitions
        if "transitions" in item:
            for transition in item["transitions"]:
                row = base_data + [
                    transition.get("source", ""),
                    transition.get("transit", ""),
                    transition.get("target", "")
                ]
                sheet.append(row)
        else:
            # 处理 inparams 和 outparams
            inparams = item.get("inparams", [])
            outparams = item.get("outparams", [])
            max_len = max(len(inparams), len(outparams)) if inparams or outparams else 1
            for i in range(max_len):
                row = base_data.copy()
                row += [
                    inparams[i] if i < len(inparams) else "",
                    outparams[i] if i < len(outparams) else "",
                    "",
                    "",
                    ""
                ]
                sheet.append(row)

            if not inparams and not outparams:
                sheet.append(base_data)

    try:
        workbook.save(excel_path)
        print(f"成功保存 Excel 文件：{excel_path}")
    except Exception as e:
        print(f"保存 Excel 文件时发生错误：{e}")


def process_file(input_path: str, output_dir: str) -> None:
    input_str = read_input_file(input_path)
    filename = os.path.splitext(os.path.basename(input_path))[0]

    if not input_str:
        return

    parsed_json = parse_to_json(input_str)
    data_new = extract_data(parsed_json)

    result = []
    temp = {}

    for key, value in data_new:
        if key == '@type':
            if temp:
                result.append(temp)
            temp = {}
        temp[key] = value

        # 确保 parent 字段被保留
        if key == 'parent' and value:
            temp['parent'] = value

    if temp:
        result.append(temp)
    # 处理不同的数据部分
    process_states(result)
    process_actions(result)
    rename_types(result)
    process_attributes(result)
    process_part_associates(result)

    # 保存 JSON
    json_output_path = os.path.join(output_dir, f"{filename}.json")
    save_json(result, json_output_path)

    # 创建并打印类型与名称对应表
    type_name_dict = create_type_name_dict(result)
    print_type_name_dict(type_name_dict)

    # 保存到 Excel
    excel_output_path = os.path.join(output_dir, f"{filename}.xlsx")
    save_to_excel(result, excel_output_path)


def main():
    input_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/combined')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/result')
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 遍历输入目录中的所有 .txt 文件
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.txt'):
            input_path = os.path.join(input_dir, file_name)
            process_file(input_path, output_dir)

    print("\n所有文件处理完成。")


if __name__ == "__main__":
    main()
