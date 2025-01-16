import json
import re
import argparse
import os

from openpyxl.styles.builtins import output


def parse_to_json(input_text):
    # 初始化栈和结果字典
    stack = []
    result = {"@type": "package", "@name": "", "children": []}
    current = result

    # 分割输入文本为行
    lines = input_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue  # 跳过空行

        if 'package' in line:
            _, name = line.split(' ', 1)
            current["@name"] = name.rstrip('{').strip()

        elif line.endswith('{'):
            # 移除末尾的 '{' 并分割
            parts = line[:-1].strip().split()
            type_name = parts[0]
            new_dict = {"@type": type_name, "@name": "", "children": []}

            if "def" in parts:
                # 处理包含 'def' 的情况
                def_index = parts.index("def")
                new_dict["@type"] += " def"
                if def_index + 1 < len(parts):
                    new_dict["@name"] = parts[def_index + 1]
            elif ':' in parts:
                # 处理包含 ':' 的情况
                colon_index = parts.index(':')
                new_dict["@name"] = parts[colon_index - 1]
                new_dict["parent"] = parts[colon_index + 1] if colon_index + 1 < len(parts) else ""
                new_dict["@type"] += " Sub"
            else:
                # 其他情况
                new_dict["@name"] = parts[1] if len(parts) > 1 else ""

            current["children"].append(new_dict)
            stack.append(current)
            current = new_dict

        elif line == '}':
            if stack:
                current = stack.pop()

        else:
            # 处理属性和其他元素
            parts = line.replace(';', '').split()
            if not parts:
                continue

            if ':' in parts:
                colon_index = parts.index(':')
                name = parts[colon_index - 1]
                type_parts = ' '.join(parts[:colon_index - 1])
                remainder = parts[colon_index + 1:]

                # 判断datavalue是否存在
                if '=' in remainder:
                    eq_index = remainder.index('=')
                    datatype = remainder[0]
                    datavalue = ' '.join(remainder[eq_index + 1:])
                    current["children"].append({
                        "@type": type_parts,
                        "@name": name,
                        "datatype": datatype,
                        "datavalue": datavalue
                    })
                else:
                    datatype = remainder[0] if remainder else ""
                    current["children"].append({
                        "@type": type_parts,
                        "@name": name,
                        "datatype": datatype
                    })
            else:
                # 其他情况，直接添加@type和@name
                current["children"].append({
                    "@type": parts[0],
                    "@name": parts[1] if len(parts) > 1 else ""
                })
    return result


def extract_data(data):
    result = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                result.append((key, ''))  # 将键名以元组的形式添加到result中
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


def process_parsed_data(parsed_json):
    data_new = extract_data(parsed_json)
    result = []
    temp = {}

    for key, value in data_new:
        if key == "@type":
            if temp:
                result.append(temp)
                temp = {}
        temp[key] = value

    if temp:
        result.append(temp)

    # 过滤并处理状态和动作等
    # 这里可以根据具体需求进一步处理

    # 处理名称转换
    for item in result:
        type_mapping = {
            'part def': 'part',
            'item': 'itemComposition',
            'item def': 'item',
            'attribute def': 'attribute',
            'action def': 'action',
            'state def': 'state'
        }
        if item.get('@type') in type_mapping:
            item['@type'] = type_mapping[item['@type']]

    # 移除不需要的类型
    result = [i for i in result if i.get('@type') not in ['in', 'out']]

    return result


def sysml2json(input_file):
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"输入文件不存在: {input_file}")
        return

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        input_str = f.read()

    # 保存到当前py文件所在目录
    output_file = os.path.join(os.path.dirname(__file__), f'{input_file}_output.json')

    # 删除连续的空行
    input_str = re.sub(r'\n\s*\n', '\n', input_str)

    # 解析为JSON
    parsed_json = parse_to_json(input_str)

    # 处理解析后的数据
    processed_data = process_parsed_data(parsed_json)

    # 保存为JSON文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        print(f"成功保存JSON文件：{output_file}")
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将SysML格式的txt文件转换为JSON文件")
    parser.add_argument('input_file', help="输入的txt文件路径")
    parser.add_argument('output_file', help="输出的JSON文件路径")
    args = parser.parse_args()

    sysml2json(args.input_file, args.output_file)
