# -*- coding: utf-8 -*-
# @Time    : 1/17/2025 1:32 PM
# @FileName: combinesysml2.py
# @Software: PyCharm
import json
import os
import re


def combine_sysml2(input_dir: str, output_dir: str, config_path: str = 'config.json'):
    """
    将指定目录下的所有 SysML2 .txt 文件按照类别合并为四个文件，并从 config.json 中读取各类别的 action def 和 state def，
    将其加入到相应的类别中。

    文件命名规则：类别名+实体名.txt
    类别名有四种：AffectedElement, HazardElement, EnvironmentElement, ResponsePlanElement

    :param input_dir: 输入目录路径，包含要合并的 .txt 文件
    :param output_dir: 输出目录路径，生成合并后的 .txt 文件
    :param config_path: 配置文件路径，默认为 'config.json'
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 定义四种类别
    categories = ['AffectedElement', 'HazardElement', 'EnvironmentElement', 'ResponsePlanElement']

    # 初始化一个字典来存储每个类别对应的定义集合
    category_defs = {
        category: {
            'action_defs': set(),
            'state_defs': set(),
            'item_defs': set(),
            'part_defs': set(),
            'ref_parts': set(),
            'perform_actions': set()
        } for category in categories
    }

    # 读取并解析 config.json
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
    except Exception as e:
        print(f"错误：无法读取配置文件 '{config_path}'。错误信息: {e}")
        return

    # 从 config.json 中提取 action-def 和 state-def 并添加到 category_defs
    action_definitions = config.get('action-def', {})
    state_definitions = config.get('state-def', {})

    for category in categories:
        # 处理 action-def
        actions = action_definitions.get(category, "").strip()
        if actions:
            # 使用正则表达式分割多个 action def
            action_parts = actions.split('action def ')[1:]  # 第一个分割部分为空
            for action in action_parts:
                action_def = 'action def ' + action.strip()
                category_defs[category]['action_defs'].add(action_def)

        # 处理 state-def
        states = state_definitions.get(category, "").strip()
        if states:
            # 使用正则表达式分割多个 state def
            state_parts = states.split('state def ')[1:]  # 第一个分割部分为空
            for state in state_parts:
                state_def = 'state def ' + state.strip()
                category_defs[category]['state_defs'].add(state_def)

    # 遍历输入目录下的所有 .txt 文件
    for filename in os.listdir(input_dir):
        if not filename.endswith('.txt'):
            continue

        # 解析文件名以获取类别名
        matched_category = None
        for category in categories:
            if filename.startswith(category):
                matched_category = category
                break

        if not matched_category:
            print(f"警告：文件 '{filename}' 不符合命名规则，跳过。")
            continue

        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"警告：无法读取文件 '{filename}'。错误信息: {e}")
            continue

        # 手动解析 package 内容，考虑嵌套大括号
        package_start = f"package {matched_category}{{"
        start_index = content.find(package_start)
        if start_index == -1:
            print(f"警告：文件 '{filename}' 中未找到包定义 '{package_start}'，跳过。")
            continue

        # Initialize brace_count
        brace_count = 1
        inner_lines = []
        lines = content[start_index + len(package_start):].split('\n')
        for line in lines:
            stripped_line = line.strip()
            brace_count += stripped_line.count('{')
            brace_count -= stripped_line.count('}')
            if brace_count < 0:
                print(f"警告：文件 '{filename}' 中包定义 '{package_start}' 未正确结束，跳过。")
                break
            if brace_count == 0:
                break
            inner_lines.append(stripped_line)

        if brace_count != 0:
            print(f"警告：文件 '{filename}' 中包定义 '{package_start}' 未正确结束，跳过。")
            continue

        # 解析包内内容
        current_def = None
        def_lines = []
        for line in inner_lines:
            if line.startswith("action def ") or line.startswith("state def ") or \
                    line.startswith("item def ") or (line.startswith("part ") and ':' in line) or \
                    line.startswith("ref part "):

                # 检查是否为 'part def CategoryName{}' 并跳过
                if line.startswith("part def ") and line == f"part def {matched_category}{{}}":
                    continue  # 跳过添加此定义

                if current_def and def_lines:
                    # 添加之前的定义
                    definition = '\n'.join(def_lines).strip()
                    if current_def == 'action_defs':
                        category_defs[matched_category]['action_defs'].add(definition)
                    elif current_def == 'state_defs':
                        category_defs[matched_category]['state_defs'].add(definition)
                    elif current_def == 'item_defs':
                        category_defs[matched_category]['item_defs'].add(definition)
                    elif current_def == 'part_defs':
                        category_defs[matched_category]['part_defs'].add(definition)
                    elif current_def == 'ref_parts':
                        category_defs[matched_category]['ref_parts'].add(definition)
                    def_lines = []

                # 确定当前定义类型
                if line.startswith("action def "):
                    current_def = 'action_defs'
                elif line.startswith("state def "):
                    current_def = 'state_defs'
                elif line.startswith("item def "):
                    current_def = 'item_defs'
                elif line.startswith("part ") and ':' in line:
                    current_def = 'part_defs'
                elif line.startswith("ref part "):
                    current_def = 'ref_parts'
                else:
                    current_def = None

                if current_def:
                    def_lines.append(line)
            elif current_def:
                def_lines.append(line)
                # 检查定义是否结束
                if line.endswith('}'):
                    # 结束当前定义
                    definition = '\n'.join(def_lines).strip()
                    if current_def == 'action_defs':
                        category_defs[matched_category]['action_defs'].add(definition)
                    elif current_def == 'state_defs':
                        category_defs[matched_category]['state_defs'].add(definition)
                    elif current_def == 'item_defs':
                        category_defs[matched_category]['item_defs'].add(definition)
                    elif current_def == 'part_defs':
                        category_defs[matched_category]['part_defs'].add(definition)
                    elif current_def == 'ref_parts':
                        category_defs[matched_category]['ref_parts'].add(definition)
                    def_lines = []
                    current_def = None

        # 处理文件末尾可能未闭合的定义
        if current_def and def_lines:
            definition = '\n'.join(def_lines).strip()
            if current_def == 'action_defs':
                category_defs[matched_category]['action_defs'].add(definition)
            elif current_def == 'state_defs':
                category_defs[matched_category]['state_defs'].add(definition)
            elif current_def == 'item_defs':
                category_defs[matched_category]['item_defs'].add(definition)
            elif current_def == 'part_defs':
                category_defs[matched_category]['part_defs'].add(definition)
            elif current_def == 'ref_parts':
                category_defs[matched_category]['ref_parts'].add(definition)
            def_lines = []
            current_def = None

    # 生成合并后的文件
    for category in categories:
        combined_lines = []
        combined_lines.append(f"package {category}{{")
        combined_lines.append("")  # 空行
        combined_lines.append(f"    part def {category}{{}}")
        combined_lines.append("")  # 空行

        # 添加唯一的 action defs
        for action_def in sorted(category_defs[category]['action_defs']):
            # 缩进每行 action_def
            action_def_indented = '\n'.join(['    ' + line if line else '' for line in action_def.split('\n')])
            combined_lines.append(action_def_indented)
            combined_lines.append("")  # 空行

        # 添加唯一的 state defs
        for state_def in sorted(category_defs[category]['state_defs']):
            # 缩进每行 state_def
            state_def_indented = '\n'.join(['    ' + line if line else '' for line in state_def.split('\n')])
            combined_lines.append(state_def_indented)
            combined_lines.append("")  # 空行

        # 添加唯一的 item defs
        for item_def in sorted(category_defs[category]['item_defs']):
            # 缩进每行 item_def
            item_def_indented = '\n'.join(['    ' + line if line else '' for line in item_def.split('\n')])
            combined_lines.append(item_def_indented)
            combined_lines.append("")  # 空行

        # 添加所有 ref parts
        for ref_part in sorted(category_defs[category]['ref_parts']):
            # 缩进每行 ref_part
            ref_part_indented = '\n'.join(['    ' + line if line else '' for line in ref_part.split('\n')])
            combined_lines.append(ref_part_indented)
            combined_lines.append("")  # 空行

        # 添加所有 part_defs
        for part_def in sorted(category_defs[category]['part_defs']):
            # 缩进每行 part_def
            part_def_indented = '\n'.join(['    ' + line if line else '' for line in part_def.split('\n')])
            combined_lines.append(part_def_indented)
            combined_lines.append("")  # 空行

        # 添加所有 perform actions (确保这些在相应的 part_def 中)
        # 这里假设 perform actions 已经在 part_defs 内部，如果需要放在外部，可以调整逻辑
        # 如果需要外部添加 perform actions, 可以 uncomment the following lines:

        # for perform_action in sorted(category_defs[category]['perform_actions']):
        #     perform_action_indented = '\n'.join(['    ' + line if line else '' for line in perform_action.split('\n')])
        #     combined_lines.append(perform_action_indented)
        #     combined_lines.append("")  # 空行

        # 结束包
        combined_lines.append("}")
        combined_lines.append("")  # 空行

        # 写入合并后的文件
        output_filename = f"{category}.txt"
        output_path = os.path.join(output_dir, output_filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write('\n'.join(combined_lines))
            print(f"已生成合并文件: {output_path}")
        except Exception as e:
            print(f"错误：无法写入合并文件 '{output_filename}'。错误信息: {e}")

if __name__ == '__main__':
    input_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/combined')
    # config路径为D:\PythonProjects\AcademicTool_PySide\config.json
    # 当前文件路径为D:\PythonProjects\AcademicTool_PySide\utils\combinesysml2.py
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    combine_sysml2(input_dir, output_dir,config_path)