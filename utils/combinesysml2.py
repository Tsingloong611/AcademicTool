# -*- coding: utf-8 -*-
# @Time    : 1/17/2025 1:32 PM
# @FileName: combinesysml2.py
# @Software: PyCharm

import json
import os

def combine_sysml2(input_dir: str, output_dir: str, config_path: str = 'config.json'):
    """
    将指定目录下的所有 SysML2 .txt 文件按照类别合并为四个文件，并从 config.json 中读取各类别的 action def 和 state def，
    将其加入到相应的类别中。

    文件命名规则：类别名+实体名.txt
    类别名有四种：AffectedElement, HazardElement, EnvironmentElement, ResponsePlanElement

    修复要点：
    1. 不再将 'ref part' 独立存储，而是保留在所属的 part 定义体内部。
    2. 允许 'ref part' 重复。
    3. 其余解析逻辑保持与原版本类似，动作、状态定义等在包级别合并。

    :param input_dir: 输入目录路径，包含要合并的 .txt 文件
    :param output_dir: 输出目录路径，生成合并后的 .txt 文件
    :param config_path: 配置文件路径，默认为 'config.json'
    """

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 定义四种类别
    categories = ['AffectedElement', 'HazardElement', 'EnvironmentElement', 'ResponsePlanElement']

    # 初始化一个字典来存储每个类别对应的定义集合
    # 这里使用 list 而非 set，以便允许重复，也保留原有顺序（如需去重可改回 set）。
    category_defs = {
        category: {
            'action_defs': [],
            'state_defs': [],
            'item_defs': [],
            'part_defs': []
        }
        for category in categories
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

    # 为四个类别额外添加来自 config.json 的 action def / state def
    # 注意：此处仍然使用“多段”拆分来兼容可能的多个定义
    for category in categories:
        # 处理 action-def
        actions = action_definitions.get(category, "").strip()
        if actions:
            # 简单按关键字 "action def" 拆分
            action_parts = actions.split("action def ")[1:]  # 第一个分割部分为空
            for action_part in action_parts:
                action_def = "action def " + action_part.strip()
                category_defs[category]['action_defs'].append(action_def)

        # 处理 state-def
        states = state_definitions.get(category, "").strip()
        if states:
            state_parts = states.split("state def ")[1:]  # 第一个分割部分为空
            for state_part in state_parts:
                state_def = "state def " + state_part.strip()
                category_defs[category]['state_defs'].append(state_def)

    # 依次遍历输入目录下的所有 .txt 文件
    for filename in os.listdir(input_dir):
        if not filename.endswith('.txt'):
            continue

        # 根据文件名来判断所属类别
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

        # 查找包定义开头
        package_start = f"package {matched_category}{{"
        start_index = content.find(package_start)
        if start_index == -1:
            print(f"警告：文件 '{filename}' 中未找到包定义 '{package_start}'，跳过。")
            continue

        # 解析包体（考虑可能的嵌套大括号）
        brace_count = 1  # 初始进入 package ... { 之后，brace_count=1
        inner_lines = []
        # 从 package_start 之后开始分行处理
        lines_after_package = content[start_index + len(package_start):].split('\n')

        for line in lines_after_package:
            # 统计本行的 '{' 与 '}'
            open_braces = line.count('{')
            close_braces = line.count('}')
            # 先将 line 放入 inner_lines（以便后面解析）
            inner_lines.append(line.rstrip('\r'))  # 去掉多余换行符

            # brace_count 需要先增后减，保证遇到形如 "}{" 的情况也能正确处理
            brace_count += open_braces
            brace_count -= close_braces

            # 如果brace_count回到0，说明主 package 已经闭合
            if brace_count <= 0:
                break

        # 现在 inner_lines 中就是 package { ... } 内部的内容（不含 package 声明本身）。
        # 解析其中的 action/state/item/part 四类定义：
        # 注意：我们将所有的解析都基于多行（包含花括号）存储下来，不在此阶段拆开 ref part。

        current_def_type = None  # 当前正在解析的定义类别('action_defs','state_defs','item_defs','part_defs')或None
        collected_lines = []     # 暂存当前定义的所有行

        def flush_definition(def_type, lines_buffer):
            """将已收集的行合并为一个字符串，添加到对应的 category_defs 中。"""
            if not def_type or not lines_buffer:
                return
            definition_str = "\n".join(lines_buffer).strip()
            if definition_str:
                category_defs[matched_category][def_type].append(definition_str)

        # 我们采用“碰到新的定义开始符”就 flush 上一个定义的方式
        # 并使用大括号计数来识别定义边界
        local_brace_count = 0
        parsing_definition = False

        for line in inner_lines:
            stripped = line.strip()
            if not stripped:
                # 空行直接加入当前定义中
                if parsing_definition:
                    collected_lines.append(line)
                continue

            # 判断是否碰到新的定义开始
            # 允许四种定义开始:
            #   "action def " / "state def " / "item def " / "part XXX: Category"
            #   以及 "part def XXX{"
            # 注意：如果已经在解析某个定义体( braces>0 )，就应该把所有内容都归入该定义体直到其 braces=0。
            if not parsing_definition:
                # 尚未进入任何定义体，检查是否有新的定义开始
                if stripped.startswith("action def "):
                    # flush 上一个(若有)
                    flush_definition(current_def_type, collected_lines)
                    # 重置
                    current_def_type = "action_defs"
                    collected_lines = [line]
                    parsing_definition = True
                    # 根据本行判断是否有 '{'
                    local_brace_count = stripped.count('{') - stripped.count('}')
                    if local_brace_count < 0:
                        # 可能没有花括号(或写法问题), 视作本行就是完整定义
                        # 这里保持与原逻辑一致：只要本行完结，不等后续花括号了
                        flush_definition(current_def_type, collected_lines)
                        current_def_type = None
                        parsing_definition = False

                elif stripped.startswith("state def "):
                    flush_definition(current_def_type, collected_lines)
                    current_def_type = "state_defs"
                    collected_lines = [line]
                    parsing_definition = True
                    local_brace_count = stripped.count('{') - stripped.count('}')
                    if local_brace_count < 0:
                        flush_definition(current_def_type, collected_lines)
                        current_def_type = None
                        parsing_definition = False

                elif stripped.startswith("item def "):
                    flush_definition(current_def_type, collected_lines)
                    current_def_type = "item_defs"
                    collected_lines = [line]
                    parsing_definition = True
                    local_brace_count = stripped.count('{') - stripped.count('}')
                    if local_brace_count < 0:
                        flush_definition(current_def_type, collected_lines)
                        current_def_type = None
                        parsing_definition = False

                elif stripped.startswith("part def ") and stripped.endswith("{}"):
                    # 特例：跳过 "part def Category{}" 这样的空定义
                    if f"part def {matched_category}{{}}" in stripped:
                        # 直接跳过，不保存
                        continue
                    else:
                        # 如果是有内容的 part def
                        flush_definition(current_def_type, collected_lines)
                        current_def_type = "part_defs"
                        collected_lines = [line]
                        parsing_definition = True
                        local_brace_count = stripped.count('{') - stripped.count('}')
                        if local_brace_count <= 0:
                            flush_definition(current_def_type, collected_lines)
                            current_def_type = None
                            parsing_definition = False

                elif (stripped.startswith("part ") and ":" in stripped):
                    # 形如 "part 1234 : SomeCategory {"
                    flush_definition(current_def_type, collected_lines)
                    current_def_type = "part_defs"
                    collected_lines = [line]
                    parsing_definition = True
                    local_brace_count = stripped.count('{') - stripped.count('}')
                    if local_brace_count <= 0:
                        flush_definition(current_def_type, collected_lines)
                        current_def_type = None
                        parsing_definition = False

                else:
                    # 既不是action/state/item/part开头，就看是否要丢弃还是保留？
                    # 大多数情况，这些行都是包裹在part之内的“普通行”（如 ref part, perform action）
                    # 如果不在任何定义内，就视为在package层面的“散行”。可以忽略或保存。
                    # 这里选择“忽略”即可，也可以把它当做零散行存储到某个结构里。
                    # 如果你有需求，可在此处理“散行”。
                    pass
            else:
                # 已经在解析某个定义体，所有行都收集进去
                collected_lines.append(line)
                # 更新本地大括号计数
                local_brace_count += stripped.count('{')
                local_brace_count -= stripped.count('}')

                # 如果 local_brace_count <= 0，则表示该定义体结束
                if local_brace_count <= 0:
                    # flush
                    flush_definition(current_def_type, collected_lines)
                    # 重置
                    current_def_type = None
                    parsing_definition = False
                    collected_lines = []
                    local_brace_count = 0

        # 处理文件最后部分可能残留的定义体
        flush_definition(current_def_type, collected_lines)
        current_def_type = None
        parsing_definition = False
        collected_lines = []

    # 全部文件解析完成后，开始为每个类别生成合并后的文件
    for category in categories:
        # 构建输出内容
        combined_lines = []
        combined_lines.append(f"package {category}{{")
        combined_lines.append("")  # 空行
        combined_lines.append(f"    part def {category}{{}}")
        combined_lines.append("")  # 空行
        # 各category_defs 中的定义去掉重复的
        category_defs[category]['action_defs'] = list(set(category_defs[category]['action_defs']))
        category_defs[category]['state_defs'] = list(set(category_defs[category]['state_defs']))
        category_defs[category]['item_defs'] = list(set(category_defs[category]['item_defs']))
        category_defs[category]['part_defs'] = list(set(category_defs[category]['part_defs']))


        # 依次写出 action_defs
        for ad in category_defs[category]['action_defs']:
            # 缩进
            action_def_indented = indent_block(ad, 4)
            combined_lines.append(action_def_indented)
            combined_lines.append("")

        # 写出 state_defs
        for sd in category_defs[category]['state_defs']:
            state_def_indented = indent_block(sd, 4)
            combined_lines.append(state_def_indented)
            combined_lines.append("")

        # 写出 item_defs
        for idf in category_defs[category]['item_defs']:
            item_def_indented = indent_block(idf, 4)
            combined_lines.append(item_def_indented)
            combined_lines.append("")

        # 写出 part_defs
        for pdf in category_defs[category]['part_defs']:
            part_def_indented = indent_block(pdf, 4)
            combined_lines.append(part_def_indented)
            combined_lines.append("")

        combined_lines.append("}")
        combined_lines.append("")

        # 写入合并后的文件
        output_filename = f"{category}.txt"
        output_path = os.path.join(output_dir, output_filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write("\n".join(combined_lines))
            print(f"已生成合并文件: {output_path}")
        except Exception as e:
            print(f"错误：无法写入合并文件 '{output_filename}'。错误信息: {e}")


def indent_block(text, spaces=4):
    """
    将多行字符串缩进指定的空格数。
    """
    lines = text.split("\n")
    return "\n".join((" " * spaces + line) if line.strip() else "" for line in lines)

if __name__ == '__main__':
    # 举例的默认路径，可自行修改
    input_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/combined')
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    combine_sysml2(input_dir, output_dir, config_path)
