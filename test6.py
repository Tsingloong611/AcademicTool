# -*- coding: utf-8 -*-
# @Time    : 1/20/2025 11:50 AM
# @FileName: test6.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
# @Time    : 1/20/2025 11:50 AM
# @FileName: test6.py
# @Software: PyCharm
import multiprocessing
import os
import json
import logging
import traceback
from datetime import datetime
from rdflib import Graph
import owlready2 as owl2
from owlready2 import default_world
from semantictools import core as smt
import nxv
from logging.handlers import RotatingFileHandler, QueueListener


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            self.log_queue.put_nowait(record)
        except Exception:
            self.handleError(record)


def setup_main_logger(log_queue):
    """
    配置主进程的日志记录器，添加QueueHandler和RotatingFileHandler。
    并启动QueueListener监听日志队列。
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 创建一个将日志记录发送到队列的处理器
    queue_handler = QueueHandler(log_queue)
    formatter = logging.Formatter('%(asctime)s - %(processName)s [PID %(process)d] - %(levelname)s - %(message)s')
    queue_handler.setFormatter(formatter)
    logger.addHandler(queue_handler)

    # 添加旋转文件处理器
    log_file = os.path.join(os.getcwd(), "processing.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(processName)s [PID %(process)d] - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 创建QueueListener，将日志分发给FileHandler
    listener = QueueListener(log_queue, file_handler)
    listener.start()

    logger.debug(f"日志记录器已配置，日志文件: '{log_file}'。")

    return listener


def setup_child_logger(log_queue):
    """
    配置子进程的日志记录器，仅添加QueueHandler。
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 移除现有的处理器
    while logger.handlers:
        logger.handlers.pop()

    # 创建一个将日志记录发送到队列的处理器
    queue_handler = QueueHandler(log_queue)
    formatter = logging.Formatter('%(asctime)s - %(processName)s [PID %(process)d] - %(levelname)s - %(message)s')
    queue_handler.setFormatter(formatter)
    logger.addHandler(queue_handler)

    logger.debug("子进程日志记录器已配置，仅使用QueueHandler。")


def is_jsonld(file_path):
    process_name = multiprocessing.current_process().name
    process_id = os.getpid()
    logging.debug(f"[{process_name} PID:{process_id}] 检查文件是否为JSON-LD: '{file_path}'")
    try:
        if not os.path.exists(file_path):
            logging.error(f"[{process_name} PID:{process_id}] 文件未找到: '{file_path}'")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_path}' 是空的。")
                return False
            json_data = json.loads(content)
            if isinstance(json_data, list):
                if any('@id' in obj or '@type' in obj for obj in json_data):
                    logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_path}' 是JSON-LD格式（列表）。")
                    return True
            elif isinstance(json_data, dict):
                if '@id' in json_data or '@type' in json_data:
                    logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_path}' 是JSON-LD格式（字典）。")
                    return True
            logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_path}' 是有效的JSON，但不是JSON-LD格式。")
            return False
    except json.JSONDecodeError as jde:
        logging.warning(f"[{process_name} PID:{process_id}] 文件 '{file_path}' 中的JSON无效: {jde}")
        return False
    except Exception as e:
        logging.error(f"[{process_name} PID:{process_id}] 检查JSON-LD时发生未知错误: {e}\n{traceback.format_exc()}")
        return False


def process_jsonld(file_name, output_dir):
    process_name = multiprocessing.current_process().name
    process_id = os.getpid()
    start_time = datetime.now()
    logging.info(f"[{process_name} PID:{process_id}] 开始检查JSON-LD文件: '{file_name}'.")

    if is_jsonld(file_name):
        logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_name}' 是JSON-LD格式，开始转换为RDF/XML。")
        try:
            g = Graph()
            g.parse(file_name, format="json-ld")
            logging.debug(f"[{process_name} PID:{process_id}] 成功解析JSON-LD文件 '{file_name}'。")
            output_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(file_name))[0]}_converted.owl")
            g.serialize(output_file, format="xml")
            logging.debug(f"[{process_name} PID:{process_id}] 成功序列化RDF/XML到文件 '{output_file}'。")
            end_time = datetime.now()
            logging.info(
                f"[{process_name} PID:{process_id}] 成功将文件 '{file_name}' 转换为RDF/XML，保存为 '{output_file}'，耗时 {end_time - start_time}.")
            return output_file
        except Exception as e:
            logging.error(
                f"[{process_name} PID:{process_id}] 无法将文件 '{file_name}' 转换为RDF/XML: {e}\n{traceback.format_exc()}")
            return None
    else:
        logging.info(f"[{process_name} PID:{process_id}] 文件 '{file_name}' 不是JSON-LD格式，跳过转换。")
        return file_name


def process_owl(file_name, output_dir):
    process_name = multiprocessing.current_process().name
    process_id = os.getpid()
    start_time = datetime.now()
    logging.info(f"[{process_name} PID:{process_id}] 开始处理OWL文件: '{file_name}'.")

    try:
        if not os.path.exists(file_name):
            logging.error(f"[{process_name} PID:{process_id}] OWL文件未找到: '{file_name}'")
            return None

        default_world.ontologies.clear()
        path = os.path.abspath(file_name)
        logging.debug(f"[{process_name} PID:{process_id}] 加载OWL文件 '{path}'。")
        ontology = owl2.get_ontology(path).load()
        logging.debug(f"[{process_name} PID:{process_id}] 成功加载本体 '{path}'。")

        logging.debug(f"[{process_name} PID:{process_id}] 生成分类图。")
        G = smt.generate_taxonomy_graph_from_onto(owl2.Thing)
        if G is None:
            logging.warning(f"[{process_name} PID:{process_id}] 无法从文件 '{file_name}' 生成分类图。")
            return None

        logging.debug(f"[{process_name} PID:{process_id}] 分类图生成成功。")

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

        logging.debug(f"[{process_name} PID:{process_id}] 开始渲染SVG图形。")
        svg_data = nxv.render(G, style, format="svg")
        svg_fname = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(file_name))[0]}.svg")
        with open(svg_fname, "wb") as svgfile:
            svgfile.write(svg_data)
        logging.debug(f"[{process_name} PID:{process_id}] SVG图形成功写入文件 '{svg_fname}'。")
        end_time = datetime.now()
        logging.info(f"[{process_name} PID:{process_id}] 成功生成SVG文件: '{svg_fname}'，耗时 {end_time - start_time}.")
        return svg_fname
    except Exception as e:
        logging.error(
            f"[{process_name} PID:{process_id}] 处理OWL文件 '{file_name}' 时出错: {e}\n{traceback.format_exc()}")
        return None


def handle_file(file_name, output_dir, log_queue):
    # 在子进程中配置日志
    setup_child_logger(log_queue)

    process_name = multiprocessing.current_process().name
    process_id = os.getpid()
    logging.debug(f"[{process_name} PID:{process_id}] 开始处理文件 '{file_name}'.")

    try:
        # 首先检查文件是否为JSON-LD
        processed_file = process_jsonld(file_name, output_dir)
        if processed_file:
            logging.debug(f"[{process_name} PID:{process_id}] 文件 '{file_name}' 已处理为 '{processed_file}'。")
            # 无论是否转换，都尝试处理为OWL
            result = process_owl(processed_file, output_dir)
            if result:
                logging.debug(f"[{process_name} PID:{process_id}] 完成文件 '{file_name}' 的处理，输出: '{result}'。")
            else:
                logging.warning(f"[{process_name} PID:{process_id}] 文件 '{file_name}' 的OWL处理未生成输出。")
        else:
            logging.warning(f"[{process_name} PID:{process_id}] 文件 '{file_name}' 的JSON-LD处理失败或被跳过。")
    except Exception as e:
        logging.error(
            f"[{process_name} PID:{process_id}] 处理文件 '{file_name}' 时发生未知错误: {e}\n{traceback.format_exc()}")
    finally:
        logging.info(f"[{process_name} PID:{process_id}] 完成处理文件 '{file_name}'。")


def process_files(file_list, output_dir, log_queue):
    if not file_list:
        logging.error("没有要处理的文件。")
        return

    logging.info(f"开始处理 {len(file_list)} 个文件，输出目录为 '{output_dir}'。")
    processes = []
    for file_name in file_list:
        p = multiprocessing.Process(
            target=handle_file,
            args=(file_name, output_dir, log_queue),
            name=f"Process-{os.path.basename(file_name)}"
        )
        processes.append(p)
        logging.info(f"启动进程 {p.name} 处理文件 '{file_name}'。")
        p.start()

    for p in processes:
        p.join()
        logging.info(f"进程 {p.name} 已完成。")

    logging.info("所有文件处理完成.")

def convert_owl_to_svg(files_to_process, output_directory):
    multiprocessing.freeze_support()  # 兼容Windows

    # 创建一个用于日志记录的多进程队列
    log_queue = multiprocessing.Queue()

    # 配置主日志记录器并启动监听器
    listener = setup_main_logger(log_queue)

    try:

        # 确保输出目录存在
        os.makedirs(output_directory, exist_ok=True)

        # 开始处理文件
        process_files(files_to_process, output_directory, log_queue)

    finally:
        # 确保在程序结束时停止QueueListener
        listener.stop()


def main():
    files_to_process = [
        r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Merge.owl",
        r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Scenario.owl",
        r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\ScenarioElement.owl",
        r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\21\owl\Emergency.owl"
    ]
    output_directory = r"C:\Users\Tsing_loong\Desktop\Work Section\transformationTool_sysml2owl(2)\transformationTool_sysml2owl\sysml2json\New folder"
    convert_owl_to_svg(files_to_process, output_directory)


if __name__ == "__main__":
    main()