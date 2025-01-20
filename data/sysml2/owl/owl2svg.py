
import time

print(time.ctime())


import os
from IPython.display import SVG, display, HTML

# for graphviz visualization of networkx graphs
import nxv

import owlready2 as owl2
from semantictools import core as smt




# 脚本路径是D:\PythonProjects\AcademicTool_PySide\data\sysml2\owl\owl2svg.py
# 文件路径是D:\PythonProjects\AcademicTool_PySide\data\sysml2\result\Emergency.owl
# 相对路径,用os转为绝对路径

file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "result", "ScenarioElement.owl"))



from rdflib import Graph
import json
from rdflib import Graph
import json
import re


def is_jsonld(file_path):
    """
    判断文件是否为 JSON-LD 格式：
    - 文件内容能被解析为 JSON。
    - 包含 JSON-LD 的标记，例如 @id 或 @type。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():  # 检查文件是否为空
                print(f"文件 '{file_path}' 是空的。")
                return False
            # 尝试解析 JSON
            json_data = json.loads(content)
            # 判断是否符合 JSON-LD 格式
            if isinstance(json_data, list):
                return any('@id' in obj or '@type' in obj for obj in json_data)
            elif isinstance(json_data, dict):
                return '@id' in json_data or '@type' in json_data
            else:
                print(f"文件 '{file_path}' 的内容不是有效的 JSON-LD 结构。")
                return False
    except json.JSONDecodeError:
        print(f"文件 '{file_path}' 不是合法的 JSON 格式，跳过判断。")
        return False
    except FileNotFoundError:
        print(f"文件 '{file_path}' 未找到，请检查路径。")
        return False
    except Exception as e:
        print(f"处理文件 '{file_path}' 时发生未知错误：{e}")
        return False


if is_jsonld(file_name):
    print(f"文件 '{file_name}' 是 JSON-LD 格式。")
    # 加载 JSON-LD 文件
    g = Graph()
    g.parse(file_name, format="json-ld")

    # 转换为 RDF/XML 格式并保存
    output_file = f"{file_name}_converted.owl"
    g.serialize(output_file, format="xml")

    print(f"文件内容为 JSON-LD 格式，已转换为 RDF/XML 格式，保存为 '{output_file}'。")
    file_name = output_file
else:
    print(f"文件 '{file_name}' 不是 JSON-LD 格式或无效，跳过处理。")



path = os.path.join(file_name)
bfo = owl2.get_ontology(path).load()
G = smt.generate_taxonomy_graph_from_onto(owl2.Thing)

G.number_of_nodes()
G = smt.generate_taxonomy_graph_from_onto(owl2.Thing)

G.number_of_nodes()
style = nxv.Style(
    graph={"rankdir": "BT"},
    node=lambda u, d: {
        "shape": "circle",
        "fixedsize": True,
        "width": 1,
        "fontsize": 10,
    },
    edge=lambda u, v, d: {"style": "solid", "arrowType": "normal", "label": "is a"},
)

svg_data = nxv.render(G, style, format="svg")
svg_fname = f"{file_name}.svg"

with open(svg_fname, "wb") as svgfile:
    svgfile.write(svg_data)

display(HTML(f"<a href='{svg_fname}'>{svg_fname}</a>"))

HTML(
    f'<a href="{svg_fname}" title="click for original size"><img width="100%" src="{svg_fname}"></a>'
)